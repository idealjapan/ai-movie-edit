"""
日本語字幕分割モジュール
句読点での分割と動詞の結合処理を行う
"""

class SubtitleSplitter:
    def __init__(self):
        # 短い丁寧語表現のリスト（これらが単独行の場合は前の行に結合）
        self.short_expressions = [
            # 存在・有無
            'あります', 'あります。', 'ありません', 'ありません。',
            'ありました', 'ありました。', 'ありませんでした', 'ありませんでした。',
            'ございます', 'ございます。', 'ございません', 'ございません。',
            'ございました', 'ございました。', 'ございませんでした', 'ございませんでした。',
            
            # する系
            'します', 'します。', 'しません', 'しません。',
            'しました', 'しました。', 'しませんでした', 'しませんでした。',
            'いたします', 'いたします。', 'いたしません', 'いたしません。',
            'いたしました', 'いたしました。', 'いたしませんでした', 'いたしませんでした。',
            'しています', 'しています。', 'していません', 'していません。',
            'していました', 'していました。', 'していませんでした', 'していませんでした。',
            
            # なる系
            'なります', 'なります。', 'なりません', 'なりません。',
            'なりました', 'なりました。', 'なりませんでした', 'なりませんでした。',
            
            # できる系
            'できます', 'できます。', 'できません', 'できません。',
            'できました', 'できました。', 'できませんでした', 'できませんでした。',
            
            # される系（受身・尊敬）
            'されます', 'されます。', 'されません', 'されません。',
            'されました', 'されました。', 'されませんでした', 'されませんでした。',
            
            # いる系
            'います', 'います。', 'いません', 'いません。',
            'いました', 'いました。', 'いませんでした', 'いませんでした。',
            'おります', 'おります。', 'おりません', 'おりません。',
            'おりました', 'おりました。', 'おりませんでした', 'おりませんでした。',
            
            # その他よく使う表現
            'ください', 'ください。',
            'でしょう', 'でしょう。',
            'だろう', 'だろう。',
        ]
        
        self.verb_fragments = ['ます', 'ました', 'ません', 'ませんでした', 'です', 'でした', 'ください']
    
    def split_by_punctuation(self, text):
        """句読点で文章を分割"""
        # 改行を削除
        text = text.replace('\n', '').replace('\r', '')
        
        # 句読点で分割（。と、のみ）
        lines = []
        parts = []
        current = ""
        
        for char in text:
            current += char
            if char in ['。', '、']:
                parts.append(current)
                current = ""
        
        # 最後の部分を追加
        if current:
            parts.append(current)
        
        # 空の部分を除去
        lines = [part.strip() for part in parts if part.strip()]
        
        # 動詞の分割を修正
        lines = self.fix_verb_splits(lines)
        
        return lines
    
    def fix_verb_splits(self, lines):
        """動詞の分割を修正"""
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            current_line = lines[i]
            
            # 次の行をチェック
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                
                # 次の行が2文字以下の場合は前の行に結合
                if len(next_line) <= 2:
                    fixed_lines.append(current_line + next_line)
                    i += 2
                    continue
                
                # 次の行が短い丁寧語表現の場合は前の行に結合
                if next_line in self.short_expressions:
                    fixed_lines.append(current_line + next_line)
                    i += 2
                    continue
                
                # 次の行が括弧で始まる場合は前の行に結合
                if next_line and (next_line[0] in '（(' or next_line.startswith('（') or next_line.startswith('(')):
                    fixed_lines.append(current_line + next_line)
                    i += 2
                    continue
                
                # 次の行が3文字以下で句点で終わっている場合
                if len(next_line) <= 3 and next_line.endswith('。'):
                    fixed_lines.append(current_line + next_line)
                    i += 2
                    continue
                
                # 次の行が句点で始まっている場合
                if next_line.startswith('。'):
                    fixed_lines.append(current_line + '。')
                    # 残りの部分を次の行として処理
                    remaining = next_line[1:].strip()
                    if remaining:
                        lines[i + 1] = remaining
                    else:
                        i += 1
                    i += 1
                    continue
                
                # 次の行が動詞の断片で始まっている場合
                if any(next_line == frag or next_line.startswith(frag + '。') for frag in self.verb_fragments):
                    fixed_lines.append(current_line + next_line)
                    i += 2
                    continue
                
                # 現在の行が特定の文字で終わっている場合
                if current_line and current_line[-1] in ['し', 'せ', 'で', 'い', 'っ']:
                    if next_line and any(next_line.startswith(s) for s in ['ます', 'ました', 'ません', 'す', 'た', 'です', 'でした']):
                        fixed_lines.append(current_line + next_line)
                        i += 2
                        continue
                
                # 現在の行が「まし」で終わっている場合
                if current_line.endswith('まし'):
                    if next_line and any(next_line.startswith(s) for s in ['た', 'た。', 'ます', 'ません']):
                        fixed_lines.append(current_line + next_line)
                        i += 2
                        continue
            
            fixed_lines.append(current_line)
            i += 1
        
        return fixed_lines