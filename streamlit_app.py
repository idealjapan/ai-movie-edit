"""
AI動画カット＆テロップツール - Streamlit Web版
無音カット（EDL）と字幕生成（SRT）の両機能を提供
"""

import streamlit as st
import tempfile
import os
from pathlib import Path

# ツールのインポート
from utils.audio_extractor import AudioExtractor
from utils.transcriber_improved import ImprovedTranscriber
from utils.caption_formatter_japanese import JapaneseCaptionFormatter
from utils.silence_detector import SilenceDetector
from utils.edl_generator import EDLGenerator
from utils.video_metadata import VideoMetadataExtractor

# ページ設定
st.set_page_config(
    page_title="AI動画編集ツール",
    page_icon="🎬",
    layout="centered"
)

# タイトルと説明
st.title("🎬 AI動画編集ツール")
st.markdown("""
### 無音カット（EDL）と字幕生成（SRT）を自動化
- ✂️ **無音カット**: 無音部分を自動検出してEDL出力
- 📝 **字幕生成**: 日本語特化の高精度SRT生成
- 🚀 **編集時間を70%削減**
""")

# サイドバーでAPI設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    # 処理モード選択
    st.subheader("🎯 処理モード")
    mode = st.radio(
        "実行する処理を選択",
        ["EDLのみ（無音カット）", "SRTのみ（字幕）", "両方生成"],
        index=2
    )
    
    st.divider()
    
    # EDL設定
    if mode in ["EDLのみ（無音カット）", "両方生成"]:
        st.subheader("✂️ 無音カット設定")
        min_silence_len = st.slider(
            "最小無音時間 (ミリ秒)",
            min_value=500,
            max_value=3000,
            value=1000,
            step=100,
            help="この時間以上の無音を検出"
        )
        silence_thresh = st.slider(
            "無音判定しきい値 (dB)",
            min_value=-60,
            max_value=-20,
            value=-35,
            step=5,
            help="この音量以下を無音と判定"
        )
        keep_silence = st.slider(
            "無音マージン (ミリ秒)",
            min_value=0,
            max_value=500,
            value=200,
            step=50,
            help="カット前後に残す無音時間"
        )
    
    # SRT設定
    if mode in ["SRTのみ（字幕）", "両方生成"]:
        st.subheader("📝 字幕設定")
        api_key = st.text_input(
            "OpenAI APIキー",
            type="password",
            help="sk-で始まるAPIキーを入力してください"
        )
        max_chars = st.slider(
            "1行あたりの最大文字数",
            min_value=10,
            max_value=30,
            value=20,
            step=1
        )
    
    st.divider()
    
    st.info("""
    💡 **使い方**
    1. 処理モードを選択
    2. 必要な設定を入力
    3. 動画ファイルをアップロード
    4. 「処理開始」をクリック
    5. 生成されたファイルをダウンロード
    """)

# メインエリア
# APIキーのチェック（SRT機能を使う場合のみ）
if mode in ["SRTのみ（字幕）", "両方生成"] and not api_key:
    st.warning("⚠️ サイドバーでOpenAI APIキーを入力してください")
else:
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "動画ファイルを選択",
        type=['mp4', 'mov', 'avi', 'mkv', 'm4v'],
        help="対応形式: MP4, MOV, AVI, MKV, M4V"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ ファイルをアップロードしました: {uploaded_file.name}")
        
        # ファイル情報表示
        col1, col2 = st.columns(2)
        with col1:
            st.metric("ファイルサイズ", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
        with col2:
            file_ext = uploaded_file.name.split('.')[-1].upper()
            st.metric("ファイル形式", file_ext)
        
        # 処理開始ボタン
        button_label = {
            "EDLのみ（無音カット）": "✂️ EDLを生成",
            "SRTのみ（字幕）": "📝 字幕を生成",
            "両方生成": "🚀 EDL & SRTを生成"
        }[mode]
        
        if st.button(button_label, type="primary"):
            
            # プログレスバーとステータス
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 一時ディレクトリの作成
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 動画ファイルを保存
                    video_path = Path(temp_dir) / uploaded_file.name
                    with open(video_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 結果を格納する辞書
                    results = {}
                    
                    # 1. 音声抽出
                    status_text.text("🔊 音声を抽出中...")
                    progress_bar.progress(10)
                    
                    extractor = AudioExtractor()
                    audio_path = extractor.extract_audio(str(video_path), temp_dir)
                    
                    # EDL処理
                    if mode in ["EDLのみ（無音カット）", "両方生成"]:
                        # 無音検出
                        status_text.text("🔍 無音部分を検出中...")
                        progress_bar.progress(20)
                        
                        detector = SilenceDetector()
                        segments = detector.detect_silence(
                            audio_path,
                            min_silence_len=min_silence_len,
                            silence_thresh=silence_thresh,
                            keep_silence=keep_silence
                        )
                        
                        # メタデータ取得
                        metadata_extractor = VideoMetadataExtractor()
                        metadata = metadata_extractor.extract_metadata(str(video_path))
                        
                        # EDL生成
                        status_text.text("📋 EDLファイルを生成中...")
                        progress_bar.progress(30)
                        
                        edl_generator = EDLGenerator()
                        edl_content = edl_generator.generate_from_segments(
                            segments, metadata, str(video_path)
                        )
                        results['edl'] = edl_content
                        
                        # 統計情報
                        total_duration = metadata.get('duration', 0)
                        kept_duration = sum(seg['duration'] for seg in segments)
                        cut_percentage = ((total_duration - kept_duration) / total_duration * 100) if total_duration > 0 else 0
                        results['edl_stats'] = {
                            'total_segments': len(segments),
                            'total_duration': total_duration,
                            'kept_duration': kept_duration,
                            'cut_percentage': cut_percentage
                        }
                    
                    # SRT処理
                    if mode in ["SRTのみ（字幕）", "両方生成"]:
                        # 文字起こし
                        status_text.text("📝 音声を文字起こし中...")
                        progress_start = 40 if mode == "両方生成" else 20
                        progress_bar.progress(progress_start)
                        
                        transcriber = ImprovedTranscriber(
                            api_key,
                            "https://api.openai.com/v1/audio/transcriptions",
                            "whisper-1"
                        )
                        transcript = transcriber.transcribe(audio_path)
                        
                        if not transcript:
                            st.error("❌ 文字起こしに失敗しました")
                            st.stop()
                        
                        # 単語数を表示
                        if 'words' in transcript:
                            st.info(f"📊 文字タイムスタンプを取得: {len(transcript['words'])}文字")
                        
                        # キャプション整形
                        status_text.text("✂️ キャプションをフォーマット中...")
                        progress_bar.progress(progress_start + 20)
                        
                        formatter = JapaneseCaptionFormatter(
                            api_key,
                            "https://api.openai.com/v1/chat/completions",
                            "gpt-4o",
                            max_chars_per_line=max_chars
                        )
                        formatted_text = formatter.format_captions(transcript['text'])
                        
                        # SRT生成
                        status_text.text("📄 SRTファイルを生成中...")
                        progress_bar.progress(progress_start + 30)
                        
                        captions_data = formatter.save_formatted_captions(
                            formatted_text,
                            transcript,
                            str(Path(temp_dir) / "captions.json")
                        )
                        
                        # SRTファイル作成
                        srt_content = generate_srt_content(captions_data)
                        results['srt'] = srt_content
                        results['srt_stats'] = {
                            'caption_count': len(captions_data['captions']),
                            'total_duration': captions_data['captions'][-1]['end'] if captions_data['captions'] else 0
                        }
                    
                    # 完了
                    progress_bar.progress(100)
                    status_text.text("✅ 処理が完了しました！")
                    
                    # 結果表示
                    st.success(f"🎉 処理が完了しました！")
                    
                    # EDL結果表示
                    if 'edl' in results:
                        st.subheader("✂️ 無音カット結果")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("検出セグメント数", results['edl_stats']['total_segments'])
                        with col2:
                            st.metric("元の長さ", format_time(results['edl_stats']['total_duration']))
                        with col3:
                            st.metric("カット後", format_time(results['edl_stats']['kept_duration']))
                        with col4:
                            st.metric("削減率", f"{results['edl_stats']['cut_percentage']:.1f}%")
                        
                        # EDLダウンロード
                        st.download_button(
                            label="📥 EDLファイルをダウンロード",
                            data=results['edl'],
                            file_name=f"{Path(uploaded_file.name).stem}_cut.edl",
                            mime="text/plain"
                        )
                    
                    # SRT結果表示
                    if 'srt' in results:
                        st.subheader("📝 字幕生成結果")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("キャプション数", results['srt_stats']['caption_count'])
                        with col2:
                            st.metric("総時間", format_time(results['srt_stats']['total_duration']))
                        with col3:
                            st.metric("精度", "高（文字レベル）")
                        
                        # プレビュー
                        if 'srt' in results:
                            # SRTコンテンツから最初の5つを抽出してプレビュー
                            srt_lines = results['srt'].split('\n\n')[:5]
                            with st.expander("📝 字幕プレビュー（最初の5つ）"):
                                for srt_block in srt_lines:
                                    if srt_block.strip():
                                        st.text(srt_block)
                        
                        # SRTダウンロード
                        st.download_button(
                            label="📥 SRTファイルをダウンロード",
                            data=results['srt'],
                            file_name=f"{Path(uploaded_file.name).stem}_subtitles.srt",
                            mime="text/plain"
                        )
                    
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                st.exception(e)


def generate_srt_content(captions_data):
    """キャプションデータからSRT形式のテキストを生成"""
    lines = []
    for i, caption in enumerate(captions_data['captions'], 1):
        lines.append(str(i))
        lines.append(f"{format_srt_time(caption['start'])} --> {format_srt_time(caption['end'])}")
        lines.append(caption['text'])
        lines.append("")  # 空行
    
    return "\n".join(lines)


def format_srt_time(seconds):
    """秒数をSRTタイムコード形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_time(seconds):
    """秒数を時:分:秒形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>
    AI動画編集ツール v2.0 | 無音カット & 字幕生成 | 
    Powered by OpenAI Whisper & GPT-4
    </small>
</div>
""", unsafe_allow_html=True)