"""
無音区間検出モジュール：Whisperのセグメントタイムスタンプを解析して無音区間を特定
"""
import json
import os
from pathlib import Path

class SegmentAnalyzer:
    def __init__(self, silence_threshold=1.0, margin=0.2):
        """
        Args:
            silence_threshold (float): この長さ以上の無音は無音区間とみなす（秒）
            margin (float): 切り出す音声区間の前後に追加するマージン（秒）
        """
        self.silence_threshold = silence_threshold
        self.margin = margin
        
    def analyze(self, transcript_data):
        """
        文字起こしデータを解析して発話区間と無音区間を特定
        
        Args:
            transcript_data (dict): Whisper APIから取得した文字起こしデータ
            
        Returns:
            tuple: (keep_segments, full_transcript)
                keep_segments: 保持する音声区間のリスト [(start_time, end_time), ...]
                full_transcript: 全文字起こしテキスト
        """
        print("発話区間と無音区間の解析を開始します...")
        
        # 全文字起こしテキスト
        full_transcript = transcript_data.get("text", "")
        
        # セグメント情報を取得
        segments = transcript_data.get("segments", [])
        
        if not segments:
            # バージョンが新しいWhisperではレスポンス形式が異なる可能性がある
            # 代替方法で探す
            if "chunks" in transcript_data:
                segments = transcript_data.get("chunks", [])
            elif "results" in transcript_data and "segments" in transcript_data["results"]:
                segments = transcript_data["results"].get("segments", [])
                
            if not segments:
                print("警告: セグメント情報が見つかりません。Whisper APIのレスポンス形式を確認してください。")
                print("レスポンス内容:", transcript_data)
                
                # 最小限のセグメント情報を作成（全体を1つのセグメントとして扱う）
                duration = transcript_data.get("duration", 0)
                if duration > 0:
                    segments = [{
                        "start": 0,
                        "end": duration,
                        "text": full_transcript
                    }]
                    print(f"全体を1つのセグメントとして扱います（0秒〜{duration}秒）")
                else:
                    raise ValueError("セグメント情報が見つからず、全体の長さも不明です。")
        
        # セグメント間のギャップを計算して無音区間を特定
        keep_segments = []
        current_segment_start = None
        current_segment_end = None
        
        for i, segment in enumerate(segments):
            # 必要なフィールドが存在することを確認
            if "start" not in segment or "end" not in segment:
                print(f"警告: セグメント {i} に開始/終了時間情報がありません。スキップします。")
                continue
                
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            
            # 最初のセグメントの場合
            if i == 0:
                current_segment_start = max(0, segment_start - self.margin)
                current_segment_end = segment_end
                continue
            
            # 前のセグメントとの間のギャップを計算
            prev_end = segments[i-1].get("end", 0)
            gap = segment_start - prev_end
            
            # ギャップが閾値より大きい場合、新しいセグメントを開始
            if gap > self.silence_threshold:
                # 前のセグメントを保存（マージン付き）
                segment_end_with_margin = min(prev_end + self.margin, segment_start)
                keep_segments.append((current_segment_start, segment_end_with_margin))
                
                # 新しいセグメントを開始
                current_segment_start = max(0, segment_start - self.margin)
            
            current_segment_end = segment_end
        
        # 最後のセグメントを保存
        if current_segment_start is not None and current_segment_end is not None:
            keep_segments.append((current_segment_start, current_segment_end + self.margin))
        
        # 結果の概要を表示
        print(f"解析完了: {len(keep_segments)}個の発話区間を検出しました")
        
        return keep_segments, full_transcript
    
    def save_segments(self, keep_segments, output_path):
        """
        発話区間リストをJSONファイルとして保存
        
        Args:
            keep_segments (list): 保持する音声区間のリスト [(start_time, end_time), ...]
            output_path (str): 出力ファイルパス
        """
        # 発話区間を辞書のリスト形式に変換
        segments_data = []
        for i, (start, end) in enumerate(keep_segments):
            segments_data.append({
                "index": i,
                "start": start,
                "end": end,
                "duration": end - start
            })
        
        # JSONファイルとして保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(segments_data, f, ensure_ascii=False, indent=2)
        
        print(f"発話区間データを保存しました: {output_path}")
