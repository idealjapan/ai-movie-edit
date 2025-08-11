"""
AI動画編集統合ツール - Streamlit Web版
無音カット（EDL）と字幕生成（句読点分割）の統合版
Google Drive連携対応
"""

import streamlit as st
import tempfile
import os
import re
from pathlib import Path
import json
import time
from datetime import timedelta

# ツールのインポート
from utils.audio_extractor import AudioExtractor
from utils.silence_detector import SilenceDetector
from utils.edl_generator import EDLGenerator
from utils.video_metadata import VideoMetadataExtractor
from utils.subtitle_splitter import SubtitleSplitter
from utils.pure_fcp7_xml_generator import PureFCP7XMLGenerator
from utils.premiere_xml_generator import PremiereXMLGenerator

# ページ設定
st.set_page_config(
    page_title="AI動画編集統合ツール",
    page_icon="🎬",
    layout="wide"
)

# セッション状態の初期化
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 認証チェック
def check_auth():
    if not st.session_state.authenticated:
        st.markdown("## 🔐 ログイン")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input("パスワードを入力してください", type="password")
            if st.button("ログイン", use_container_width=True):
                # 環境変数またはSecrets.tomlから取得
                correct_password = os.getenv("ACCESS_PASSWORD", "demo2024")
                if password == correct_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("パスワードが違います")
        st.stop()

# 認証チェック実行
check_auth()

# タイトルと説明
st.title("🎬 AI動画編集統合ツール")
st.markdown("""
### 動画カット＋字幕を一括処理
- ✂️ **無音カット**: 無音部分を自動検出
- 📝 **字幕生成**: 句読点で自動分割
- 🎯 **統合出力**: FCPX/Premiere対応ファイル生成
""")

# タブ設定
tab1, tab2, tab3 = st.tabs(["📤 ファイルアップロード", "🔗 URL入力", "📊 処理履歴"])

def format_time_srt(seconds):
    """SRT形式のタイムスタンプを生成"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(lines, duration):
    """字幕リストからSRTファイルを生成"""
    srt_content = []
    
    # 固定レート：1文字0.15秒
    base_time_per_char = 0.15
    current_time = 0
    
    for i, line in enumerate(lines):
        # 字幕の表示時間を計算（最小0.8秒）
        segment_duration = max(0.8, len(line) * base_time_per_char * 1.1)
        
        # 動画の長さを超えないようにチェック
        if current_time >= duration:
            break
            
        start_time = current_time
        end_time = min(current_time + segment_duration, duration)
        
        srt_content.append(f"{i + 1}")
        srt_content.append(f"{format_time_srt(start_time)} --> {format_time_srt(end_time)}")
        srt_content.append(line)
        srt_content.append("")
        
        current_time = end_time
    
    return "\n".join(srt_content)

def process_video(video_path, script_text, settings):
    """動画とスクリプトを処理"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 動画メタデータ取得
        status_text.text("📊 動画情報を取得中...")
        progress_bar.progress(10)
        
        metadata_extractor = VideoMetadataExtractor()
        metadata = metadata_extractor.extract(video_path)
        
        duration = float(metadata['format']['duration'])
        fps = eval(metadata['streams'][0]['r_frame_rate'])
        
        st.info(f"""
        **動画情報**
        - 長さ: {timedelta(seconds=int(duration))}
        - FPS: {fps:.2f}
        - 解像度: {metadata['streams'][0]['width']}x{metadata['streams'][0]['height']}
        """)
        
        # 2. 音声抽出
        status_text.text("🎵 音声を抽出中...")
        progress_bar.progress(20)
        
        extractor = AudioExtractor()
        audio_path = extractor.extract(video_path, output_dir=tempfile.gettempdir())
        
        # 3. 無音検出
        status_text.text("🔍 無音部分を検出中...")
        progress_bar.progress(40)
        
        detector = SilenceDetector()
        silence_ranges = detector.detect_silence(
            audio_path,
            min_silence_len=settings['min_silence_len'],
            silence_thresh=settings['silence_thresh'],
            keep_silence=settings['keep_silence']
        )
        
        # カットする範囲を計算
        keep_ranges = []
        last_end = 0
        
        for start, end in silence_ranges:
            if start > last_end:
                keep_ranges.append((last_end, start))
            last_end = end
        
        if last_end < duration:
            keep_ranges.append((last_end, duration))
        
        st.success(f"✂️ {len(silence_ranges)}個の無音部分を検出しました")
        
        # 4. 字幕生成
        status_text.text("📝 字幕を生成中...")
        progress_bar.progress(60)
        
        splitter = SubtitleSplitter()
        subtitle_lines = splitter.split_by_punctuation(script_text)
        
        st.success(f"📝 {len(subtitle_lines)}行の字幕を生成しました")
        
        # 5. ファイル生成
        status_text.text("📁 ファイルを生成中...")
        progress_bar.progress(80)
        
        results = {}
        
        # EDL生成
        edl_generator = EDLGenerator()
        results['edl'] = edl_generator.generate_from_segments(
            keep_ranges, 
            duration, 
            fps,
            video_name=Path(video_path).stem
        )
        
        # SRT生成
        results['srt'] = generate_srt(subtitle_lines, duration)
        
        # FCPX XML生成（統合版）
        fcpx_generator = PureFCP7XMLGenerator()
        results['fcpxml'] = fcpx_generator.generate(
            video_path=video_path,
            segments=keep_ranges,
            metadata=metadata,
            captions=[{
                'text': line,
                'start': i * 2,
                'end': (i + 1) * 2
            } for i, line in enumerate(subtitle_lines)]
        )
        
        progress_bar.progress(100)
        status_text.text("✅ 処理完了！")
        
        # 音声ファイルを削除
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return results
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return None

# ファイルアップロードタブ
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📹 動画ファイル")
        video_file = st.file_uploader(
            "動画をアップロード（200MB以下推奨）",
            type=['mp4', 'mov', 'avi'],
            help="大きいファイルはGoogle Drive経由を推奨"
        )
    
    with col2:
        st.markdown("### 📄 広告原稿")
        script_text = st.text_area(
            "原稿を入力してください",
            height=200,
            placeholder="例：こんにちは、今日は素晴らしい商品をご紹介します。"
        )
    
    # 処理設定
    with st.expander("⚙️ 詳細設定", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_silence_len = st.slider(
                "最小無音時間(ms)", 500, 3000, 1000, 100
            )
        with col2:
            silence_thresh = st.slider(
                "無音しきい値(dB)", -60, -20, -35, 5
            )
        with col3:
            keep_silence = st.slider(
                "無音マージン(ms)", 0, 500, 200, 50
            )
    
    # 処理実行
    if st.button("🚀 処理開始", type="primary", use_container_width=True):
        if video_file and script_text:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=video_file.name) as tmp_file:
                tmp_file.write(video_file.read())
                video_path = tmp_file.name
            
            # 処理実行
            settings = {
                'min_silence_len': min_silence_len,
                'silence_thresh': silence_thresh,
                'keep_silence': keep_silence
            }
            
            results = process_video(video_path, script_text, settings)
            
            if results:
                st.success("✅ 処理が完了しました！")
                
                # ダウンロードボタン
                st.markdown("### 📥 ダウンロード")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.download_button(
                        label="📄 EDL (汎用)",
                        data=results['edl'],
                        file_name=f"{video_file.name.split('.')[0]}_edit.edl",
                        mime="text/plain"
                    )
                
                with col2:
                    st.download_button(
                        label="📝 SRT (字幕)",
                        data=results['srt'],
                        file_name=f"{video_file.name.split('.')[0]}_subtitles.srt",
                        mime="text/plain"
                    )
                
                with col3:
                    st.download_button(
                        label="🎬 FCPX XML",
                        data=results['fcpxml'],
                        file_name=f"{video_file.name.split('.')[0]}_fcpx.xml",
                        mime="text/xml"
                    )
                
                with col4:
                    # 全ファイルをZIPで
                    import zipfile
                    import io
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.writestr(f"{video_file.name.split('.')[0]}_edit.edl", results['edl'])
                        zip_file.writestr(f"{video_file.name.split('.')[0]}_subtitles.srt", results['srt'])
                        zip_file.writestr(f"{video_file.name.split('.')[0]}_fcpx.xml", results['fcpxml'])
                    
                    st.download_button(
                        label="📦 全ファイル (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"{video_file.name.split('.')[0]}_all.zip",
                        mime="application/zip"
                    )
                
                # プレビュー
                with st.expander("👀 字幕プレビュー"):
                    lines = results['srt'].split('\n\n')[:5]
                    for line in lines:
                        st.text(line)
            
            # 一時ファイル削除
            os.remove(video_path)
        else:
            st.warning("動画ファイルと原稿を両方入力してください")

# URL入力タブ
with tab2:
    st.markdown("### 🔗 Google Drive / YouTube URL")
    url_input = st.text_input(
        "共有リンクを入力",
        placeholder="https://drive.google.com/... または https://youtube.com/..."
    )
    
    st.info("""
    **Google Drive の場合**
    1. ファイルを右クリック → 「共有」
    2. 「リンクを知っている全員」に設定
    3. リンクをコピーして貼り付け
    
    **YouTube の場合**
    - 動画URLをそのまま貼り付け
    """)
    
    script_text_url = st.text_area(
        "📄 広告原稿",
        height=200,
        placeholder="例：こんにちは、今日は素晴らしい商品をご紹介します。"
    )
    
    if st.button("🚀 URL処理開始", type="primary", use_container_width=True):
        if url_input and script_text_url:
            st.info("URL処理機能は準備中です。Phase 2で実装予定です。")
        else:
            st.warning("URLと原稿を両方入力してください")

# 処理履歴タブ
with tab3:
    st.markdown("### 📊 最近の処理")
    st.info("処理履歴機能は準備中です")

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    AI動画編集統合ツール v1.0 | 社内利用限定
</div>
""", unsafe_allow_html=True)