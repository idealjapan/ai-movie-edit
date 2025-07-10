"""
テロップ整形モジュール：GPT-4o APIを使用してテロップを整形
精密版：文字列マッチングによる正確なタイミング割り当て
"""
import os
import json
import requests
import sys
import re
from difflib import SequenceMatcher

class PreciseCaptionFormatter:
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
        
        # GPT-4oへのプロンプト（改良版：元のテキストとの対応を維持）
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
6. 重要：元のテキストの単語の順序は変更しないでください

【出力形式】
整形されたテキストをそのまま出力してください。フォーマットの説明や追加コメントは不要です。
        """
        
        # APIリクエストデータ
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "あなたは動画編集者のためのテロップ作成アシスタントです。元のテキストの単語順序を保ちながら整形してください。"},
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
    
    def find_word_in_original(self, word, original_words, start_index=0):
        """
        元の単語リストから特定の単語を検索
        """
        word_clean = re.sub(r'[、。！？\s]', '', word)
        for i in range(start_index, len(original_words)):
            original_clean = re.sub(r'[、。！？\s]', '', original_words[i])
            if word_clean in original_clean or original_clean in word_clean:
                return i
        return -1
    
    def align_captions_precise(self, formatted_lines, word_timestamps, original_text):
        """
        精密な文字列マッチングを使用してタイミングを割り当て
        
        Args:
            formatted_lines (list): 整形されたテロップの行リスト
            word_timestamps (list): 単語レベルのタイムスタンプ情報
            original_text (str): 元の文字起こしテキスト
            
        Returns:
            list: タイミング情報付きのキャプションリスト
        """
        captions = []
        
        # 元のテキストを単語単位で分割（単語タイムスタンプと対応）
        original_words = [w['word'] for w in word_timestamps]
        word_index = 0
        
        for line in formatted_lines:
            if not line.strip():
                continue
            
            # 行内のテキストを単語に分割
            line_words = re.findall(r'[^\s、。！？]+[、。！？]?', line.strip())
            
            if not line_words:
                continue
            
            # 最初の単語を元のテキストから検索
            first_word_idx = self.find_word_in_original(line_words[0], original_words, word_index)
            if first_word_idx == -1:
                # 見つからない場合は次の単語から開始
                first_word_idx = word_index
            
            # 最後の単語を検索
            last_word_idx = first_word_idx
            for w in line_words[1:]:
                idx = self.find_word_in_original(w, original_words, last_word_idx + 1)
                if idx != -1:
                    last_word_idx = idx
            
            # タイムスタンプを取得
            if first_word_idx < len(word_timestamps) and last_word_idx < len(word_timestamps):
                start_time = word_timestamps[first_word_idx].get('start', 0)
                end_time = word_timestamps[last_word_idx].get('end', 0)
                
                captions.append({
                    "text": line.strip(),
                    "start": start_time,
                    "end": end_time
                })
                
                # 次の検索開始位置を更新
                word_index = last_word_idx + 1
        
        return captions
    
    def save_formatted_captions(self, formatted_text, transcript_data, output_path):
        """
        整形されたテロップと単語タイムスタンプ情報を精密に組み合わせて保存
        
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
        
        # 元のテキストを取得
        original_text = transcript_data.get("text", "")
        
        # 精密なタイミング照合
        captions = self.align_captions_precise(lines, word_timestamps, original_text)
        
        # テロップデータを構築
        caption_data = {
            "original_text": original_text,
            "formatted_text": formatted_text,
            "captions": captions
        }
        
        # JSONファイルとして保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)
        
        print(f"整形済みテロップデータを保存しました（精密版）: {output_path}")
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