"""
テロップ整形モジュール：GPT-4o APIを使用してテロップを整形
日本語特化版：文字レベルのタイムスタンプに対応
"""
import os
import json
import requests
import sys
import re

class JapaneseCaptionFormatter:
    def __init__(self, api_key, api_endpoint, model, max_chars_per_line=15):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        self.max_chars_per_line = max_chars_per_line
        
    def format_captions(self, transcript_text):
        """
        文字起こしテキストをテロップに適した形式に整形
        """
        print("テロップ整形を開始します...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
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
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "あなたは動画編集者のためのテロップ作成アシスタントです。元のテキストの単語順序を保ちながら整形してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                print(f"API エラー ({response.status_code}): {response.text}", file=sys.stderr)
                raise Exception(f"GPT API エラー: {response.text}")
            
            result = response.json()
            formatted_text = result['choices'][0]['message']['content'].strip()
            
            print("テロップ整形が完了しました")
            return formatted_text
            
        except Exception as e:
            print(f"テロップ整形エラー: {str(e)}", file=sys.stderr)
            raise
    
    def build_char_to_timestamp_map(self, word_timestamps):
        """
        文字レベルのタイムスタンプから元のテキストを再構築し、
        各文字位置のタイムスタンプをマッピング
        """
        original_text = ""
        char_timestamps = []
        
        for word_data in word_timestamps:
            word = word_data['word']
            start = word_data['start']
            end = word_data['end']
            
            # 各文字に対してタイムスタンプを割り当て
            for i, char in enumerate(word):
                original_text += char
                # 文字ごとに均等にタイムスタンプを分配
                char_start = start + (end - start) * i / len(word) if len(word) > 1 else start
                char_end = start + (end - start) * (i + 1) / len(word) if len(word) > 1 else end
                char_timestamps.append({
                    'char': char,
                    'start': char_start,
                    'end': char_end
                })
        
        return original_text, char_timestamps
    
    def find_text_in_original(self, search_text, original_text, char_timestamps, start_pos=0):
        """
        整形されたテキストを元のテキストから検索し、タイムスタンプを取得
        """
        # 検索テキストから空白と記号を除去
        clean_search = re.sub(r'[、。！？\s]', '', search_text)
        if not clean_search:
            return None, None, start_pos
        
        # 元のテキストでも同様に処理して検索
        for i in range(start_pos, len(original_text)):
            # 現在の位置から検索テキストの長さ分を取得
            if i + len(clean_search) <= len(original_text):
                # 元のテキストの該当部分を抽出（記号を除く）
                original_segment = ""
                j = i
                collected = 0
                
                while j < len(original_text) and collected < len(clean_search):
                    if original_text[j] not in '、。！？ ':
                        original_segment += original_text[j]
                        collected += 1
                    j += 1
                
                if original_segment == clean_search:
                    # マッチした場合、開始と終了のタイムスタンプを取得
                    if i < len(char_timestamps) and j-1 < len(char_timestamps):
                        start_time = char_timestamps[i]['start']
                        end_time = char_timestamps[j-1]['end']
                        return start_time, end_time, j
        
        return None, None, start_pos
    
    def align_captions_japanese(self, formatted_lines, word_timestamps):
        """
        日本語の文字レベルタイムスタンプを使用してタイミングを割り当て
        """
        # 文字レベルのタイムスタンプマップを構築
        original_text, char_timestamps = self.build_char_to_timestamp_map(word_timestamps)
        
        captions = []
        search_pos = 0
        
        for line in formatted_lines:
            if not line.strip():
                continue
            
            # 行のテキストを元のテキストから検索
            start_time, end_time, new_pos = self.find_text_in_original(
                line.strip(), original_text, char_timestamps, search_pos
            )
            
            if start_time is not None and end_time is not None:
                captions.append({
                    "text": line.strip(),
                    "start": start_time,
                    "end": end_time
                })
                search_pos = new_pos
            else:
                # 見つからない場合は前のキャプションの終了時刻から推定
                if captions:
                    estimated_start = captions[-1]['end']
                    estimated_end = estimated_start + 2.0  # 2秒のデフォルト長
                    captions.append({
                        "text": line.strip(),
                        "start": estimated_start,
                        "end": estimated_end
                    })
        
        return captions
    
    def save_formatted_captions(self, formatted_text, transcript_data, output_path):
        """
        整形されたテロップと文字レベルタイムスタンプ情報を組み合わせて保存
        """
        lines = formatted_text.split('\n')
        word_timestamps = transcript_data.get("words", [])
        
        if not word_timestamps:
            print("警告: 単語タイムスタンプが利用できません。")
            return self._fallback_to_segments(formatted_text, transcript_data, output_path)
        
        # 日本語用のタイミング照合
        captions = self.align_captions_japanese(lines, word_timestamps)
        
        caption_data = {
            "original_text": transcript_data.get("text", ""),
            "formatted_text": formatted_text,
            "captions": captions
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)
        
        print(f"整形済みテロップデータを保存しました（日本語版）: {output_path}")
        return caption_data
    
    def _fallback_to_segments(self, formatted_text, transcript_data, output_path):
        """フォールバック処理"""
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