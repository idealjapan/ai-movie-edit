"""
テロップ整形モジュール：GPT-4o APIを使用してテロップを整形
"""
import os
import json
import requests
import sys

class CaptionFormatter:
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
    
    def save_formatted_captions(self, formatted_text, transcript_data, output_path):
        """
        整形されたテロップと元のタイムスタンプ情報を組み合わせて保存
        
        Args:
            formatted_text (str): 整形されたテロップテキスト
            transcript_data (dict): Whisper APIから取得した文字起こしデータ
            output_path (str): 出力ファイルパス
        """
        # 整形テキストを行ごとに分割
        lines = formatted_text.split('\n')
        
        # セグメント情報を取得
        segments = transcript_data.get("segments", [])
        
        # テロップデータを構築
        caption_data = {
            "original_text": transcript_data.get("text", ""),
            "formatted_text": formatted_text,
            "captions": []
        }
        
        # 簡易的なタイムコード割り当て（より精密な実装が必要な場合は調整）
        line_index = 0
        for segment in segments:
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            
            if line_index < len(lines):
                caption_data["captions"].append({
                    "text": lines[line_index],
                    "start": segment_start,
                    "end": segment_end
                })
                line_index += 1
            else:
                break
        
        # JSONファイルとして保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(caption_data, f, ensure_ascii=False, indent=2)
        
        print(f"整形済みテロップデータを保存しました: {output_path}")
        return caption_data
