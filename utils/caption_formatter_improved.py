"""
テロップ整形モジュール：GPT-4o APIを使用してテロップを整形
改良版：単語レベルのタイムスタンプを使った正確なタイミング割り当て
"""
import os
import json
import requests
import sys
import re

class ImprovedCaptionFormatter:
    def __init__(self, api_key, api_endpoint, model, max_chars_per_line=15):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        self.max_chars_per_line = max_chars_per_line
        
    def format_captions(self, transcript_text):
        """
        文字起こしテキストをテロップに適した形式に整形
        
        Args:
            transcript_text (str): 文字起こしテキスト
            
        Returns:
            str: 整形されたテロップテキスト
        """
        print("テロップ整形を開始します...")
        
        # APIリクエストのヘッダー
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # GPT-4oへのプロンプト
        prompt = f"""
文字起こしテキストをテロップ用に整形してください。

【入力テキスト】
{transcript_text}

【整形ルール】
1. フィラー語（えー、あの、まあ、など）を除去
2. 句読点を適切に配置
3. 誤字脱字を修正（可能な範囲で）
4. 1行あたり{self.max_chars_per_line}文字以内に収まるよう改行を挿入
   - 意味のある区切りで改行する
   - 「、」や「。」の後で改行を入れるのが望ましい
5. 読みやすいテロップになるよう配慮

【出力形式】
整形されたテキストをそのまま出力してください。フォーマットの説明や追加コメントは不要です。
        """
        
        # APIリクエストデータ
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "あなたは動画編集者のためのテロップ作成アシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        try:
            # APIリクエストを送信
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data
            )
            
            # レスポンスを確認
            if response.status_code != 200:
                print(f"API エラー ({response.status_code}): {response.text}", file=sys.stderr)
                raise Exception(f"GPT API エラー: {response.text}")
            
            # レスポンスからテキストを取得
            result = response.json()
            formatted_text = result['choices'][0]['message']['content'].strip()
            
            print("テロップ整形が完了しました")
            return formatted_text
            
        except Exception as e:
            print(f"テロップ整形エラー: {str(e)}", file=sys.stderr)
            raise
    
    def align_captions_with_words(self, formatted_lines, word_timestamps):
        """
        整形されたテロップ行と単語タイムスタンプを照合して正確なタイミングを割り当て
        
        Args:
            formatted_lines (list): 整形されたテロップの行リスト
            word_timestamps (list): 単語レベルのタイムスタンプ情報
            
        Returns:
            list: タイミング情報付きのキャプションリスト
        """
        captions = []
        word_index = 0
        
        for line in formatted_lines:
            if not line.strip():
                continue
                
            # 行内の実際の文字（記号を除く）を抽出
            line_text = re.sub(r'[、。！？\s]', '', line)
            line_start = None
            line_end = None
            matched_chars = 0
            
            # 単語タイムスタンプと照合
            while word_index < len(word_timestamps) and matched_chars < len(line_text):
                word_info = word_timestamps[word_index]
                word = word_info.get('word', '').strip()
                
                # 単語の文字を行のテキストと照合
                if word:
                    # 最初の単語の開始時刻を記録
                    if line_start is None:
                        line_start = word_info.get('start', 0)
                    
                    # 単語の文字数分だけマッチしたとカウント
                    matched_chars += len(re.sub(r'[、。！？\s]', '', word))
                    line_end = word_info.get('end', 0)
                    
                    # 行の文字数に達したら次の行へ
                    if matched_chars >= len(line_text) * 0.8:  # 80%マッチで十分とする
                        word_index += 1
                        break
                
                word_index += 1
            
            # タイミング情報を持つキャプションを追加
            if line_start is not None and line_end is not None:
                captions.append({
                    "text": line.strip(),
                    "start": line_start,
                    "end": line_end
                })
        
        return captions
    
    def save_formatted_captions(self, formatted_text, transcript_data, output_path):
        """
        整形されたテロップと単語タイムスタンプ情報を組み合わせて保存
        
        Args:
            formatted_text (str): 整形されたテロップテキスト
            transcript_data (dict): Whisper APIから取得した文字起こしデータ（単語タイムスタンプ付き）
            output_path (str): 出力ファイルパス
        """
        # 整形テキストを行ごとに分割
        lines = formatted_text.split('\n')
        
        # 単語タイムスタンプ情報を取得
        word_timestamps = transcript_data.get("words", [])
        
        # 単語タイムスタンプがない場合は従来のセグメントベースの処理にフォールバック
        if not word_timestamps:
            print("警告: 単語タイムスタンプが利用できません。セグメントベースの処理を使用します。")
            return self._fallback_to_segments(formatted_text, transcript_data, output_path)
        
        # 整形されたテロップと単語タイムスタンプを照合
        captions = self.align_captions_with_words(lines, word_timestamps)
        
        # テロップデータを構築
        caption_data = {
            "original_text": transcript_data.get("text", ""),
            "formatted_text": formatted_text,
            "captions": captions
        }
        
        # JSONファイルとして保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)
        
        print(f"整形済みテロップデータを保存しました: {output_path}")
        return caption_data
    
    def _fallback_to_segments(self, formatted_text, transcript_data, output_path):
        """
        単語タイムスタンプが利用できない場合の従来のセグメントベース処理
        """
        lines = formatted_text.split('\n')
        segments = transcript_data.get("segments", [])
        
        caption_data = {
            "original_text": transcript_data.get("text", ""),
            "formatted_text": formatted_text,
            "captions": []
        }
        
        line_index = 0
        for segment in segments:
            if line_index < len(lines) and lines[line_index].strip():
                caption_data["captions"].append({
                    "text": lines[line_index].strip(),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0)
                })
                line_index += 1
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)
        
        return caption_data