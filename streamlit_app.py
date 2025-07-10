"""
AI動画カット＆テロップツール - Streamlit Web版
チーム用のシンプルなSRT生成ツール
"""

import streamlit as st
import tempfile
import os
from pathlib import Path

# ツールのインポート
from utils.audio_extractor import AudioExtractor
from utils.transcriber_improved import ImprovedTranscriber
from utils.caption_formatter_japanese import JapaneseCaptionFormatter

# ページ設定
st.set_page_config(
    page_title="AI字幕生成ツール",
    page_icon="🎬",
    layout="centered"
)

# タイトルと説明
st.title("🎬 AI字幕生成ツール")
st.markdown("""
### 動画から高精度な字幕（SRT）を自動生成
- 日本語特化の文字レベルタイムスタンプ
- OpenAI Whisper APIによる高精度文字起こし  
- GPT-4による自然な字幕整形
""")

# サイドバーでAPI設定
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input(
        "OpenAI APIキー",
        type="password",
        help="sk-で始まるAPIキーを入力してください"
    )
    
    st.divider()
    
    st.subheader("📝 字幕設定")
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
    1. OpenAI APIキーを入力
    2. 動画ファイルをアップロード
    3. 「字幕を生成」をクリック
    4. SRTファイルをダウンロード
    """)

# メインエリア
if not api_key:
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
        if st.button("🚀 字幕を生成", type="primary"):
            
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
                    
                    # 1. 音声抽出
                    status_text.text("🔊 音声を抽出中...")
                    progress_bar.progress(20)
                    
                    extractor = AudioExtractor()
                    audio_path = extractor.extract_audio(str(video_path), temp_dir)
                    
                    # 2. 文字起こし
                    status_text.text("📝 音声を文字起こし中...")
                    progress_bar.progress(40)
                    
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
                    
                    # 3. キャプション整形
                    status_text.text("✂️ キャプションをフォーマット中...")
                    progress_bar.progress(60)
                    
                    formatter = JapaneseCaptionFormatter(
                        api_key,
                        "https://api.openai.com/v1/chat/completions",
                        "gpt-4o",
                        max_chars_per_line=max_chars
                    )
                    formatted_text = formatter.format_captions(transcript['text'])
                    
                    # 4. SRT生成
                    status_text.text("📄 SRTファイルを生成中...")
                    progress_bar.progress(80)
                    
                    captions_data = formatter.save_formatted_captions(
                        formatted_text,
                        transcript,
                        str(Path(temp_dir) / "captions.json")
                    )
                    
                    # SRTファイル作成
                    srt_content = generate_srt_content(captions_data)
                    
                    # 完了
                    progress_bar.progress(100)
                    status_text.text("✅ 字幕生成が完了しました！")
                    
                    # 結果表示
                    st.success(f"🎉 字幕を生成しました！")
                    
                    # 統計情報
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("キャプション数", len(captions_data['captions']))
                    with col2:
                        total_duration = captions_data['captions'][-1]['end'] if captions_data['captions'] else 0
                        st.metric("総時間", format_time(total_duration))
                    with col3:
                        st.metric("精度", "高（文字レベル）")
                    
                    # プレビュー
                    with st.expander("📝 字幕プレビュー（最初の5つ）"):
                        for i, caption in enumerate(captions_data['captions'][:5], 1):
                            st.text(f"{i}. [{format_srt_time(caption['start'])} - {format_srt_time(caption['end'])}]")
                            st.text(f"   {caption['text']}\n")
                    
                    # ダウンロードボタン
                    st.download_button(
                        label="📥 SRTファイルをダウンロード",
                        data=srt_content,
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
    AI動画カット＆テロップツール v1.0 | 
    Powered by OpenAI Whisper & GPT-4
    </small>
</div>
""", unsafe_allow_html=True)