#!/usr/bin/env python3
"""
AI自動カット編集＆テロップ生成システム - GUIアプリケーション
"""
import os
import sys
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QLineEdit, QDoubleSpinBox,
    QSpinBox, QTextEdit, QGroupBox, QFormLayout, QMessageBox,
    QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

# 設定をインポート
from config import OPENAI_API_KEY as DEFAULT_API_KEY, DEFAULT_SETTINGS

# 処理関数をインポート
from process_video import process_video

class WorkerSignals(QObject):
    """ワーカースレッドからのシグナルを定義するクラス"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    result = pyqtSignal(str)

class Worker(threading.Thread):
    """バックグラウンドでの処理を行うワーカークラス"""
    def __init__(self, video_path, silence_threshold, margin, max_chars_per_line, api_key, output_format, output_folder):
        super().__init__()
        self.video_path = video_path
        self.silence_threshold = silence_threshold
        self.margin = margin
        self.max_chars_per_line = max_chars_per_line
        self.api_key = api_key
        self.output_format = output_format
        self.output_folder = output_folder
        self.signals = WorkerSignals()
        self.daemon = True  # メインスレッドが終了したら一緒に終了

    def run(self):
        """スレッドの実行"""
        try:
            # APIキーを設定
            os.environ["OPENAI_API_KEY"] = self.api_key
            
            # ログ出力をキャプチャするためのリダイレクト
            from io import StringIO
            import sys
            old_stdout = sys.stdout
            redirected_output = StringIO()
            sys.stdout = redirected_output
            
            # 動画処理を実行
            output_file = process_video(
                self.video_path,
                silence_threshold=self.silence_threshold,
                margin=self.margin,
                max_chars_per_line=self.max_chars_per_line,
                output_format=self.output_format,
                output_dir=self.output_folder
            )
            
            # 標準出力を元に戻す
            sys.stdout = old_stdout
            
            # 完了シグナルを発行
            self.signals.result.emit(output_file)
            self.signals.finished.emit()
            
        except Exception as e:
            # エラー発生時のシグナル
            self.signals.error.emit(str(e))
            self.signals.finished.emit()

class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("AI自動カット編集＆テロップ生成システム")
        self.setMinimumSize(800, 600)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # ファイル選択部分
        file_group = QGroupBox("入力ファイル")
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.file_path_label.setStyleSheet("padding: 5px; background-color: white; color: black; border: 1px solid #cccccc; border-radius: 3px;")
        
        select_file_button = QPushButton("ファイルを選択")
        select_file_button.clicked.connect(self.select_file)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(select_file_button)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # パラメータ設定部分
        params_group = QGroupBox("処理パラメータ")
        params_layout = QFormLayout()
        
        # 無音閾値
        self.silence_threshold = QDoubleSpinBox()
        self.silence_threshold.setRange(0.1, 10.0)
        self.silence_threshold.setValue(DEFAULT_SETTINGS.get('silence_threshold', 1.0))
        self.silence_threshold.setSingleStep(0.1)
        self.silence_threshold.setDecimals(1)
        self.silence_threshold.setSuffix(" 秒")
        params_layout.addRow("無音閾値（秒）:", self.silence_threshold)
        
        # マージン
        self.margin = QDoubleSpinBox()
        self.margin.setRange(0.0, 1.0)
        self.margin.setValue(0.5)  # デフォルト値を0.5秒に変更
        self.margin.setSingleStep(0.1)
        self.margin.setDecimals(1)
        self.margin.setSuffix(" 秒")
        params_layout.addRow("マージン（秒）:", self.margin)
        
        # テロップ1行の最大文字数
        self.max_chars_per_line = QSpinBox()
        self.max_chars_per_line.setRange(5, 30)
        self.max_chars_per_line.setValue(DEFAULT_SETTINGS.get('max_chars_per_line', 15))
        self.max_chars_per_line.setSuffix(" 文字")
        params_layout.addRow("テロップ1行の最大文字数:", self.max_chars_per_line)
        
        # APIキー
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("OpenAI APIキーを入力")
        self.api_key.setText(DEFAULT_API_KEY or "")
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)  # APIキーを隠す
        params_layout.addRow("OpenAI APIキー:", self.api_key)
        
        # 出力フォーマット
        self.output_format = QComboBox()
        self.output_format.addItems([
            "Premiere Pro XML (推奨)",
            "Pure FCP7 XML",
            "EDL",
            "全フォーマット"
        ])
        self.output_format.setCurrentIndex(0)  # デフォルトはPremiere Pro XML
        params_layout.addRow("出力フォーマット:", self.output_format)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # 出力フォルダ設定部分
        output_group = QGroupBox("出力設定")
        output_layout = QHBoxLayout()
        
        self.output_folder_label = QLabel(DEFAULT_SETTINGS.get('output_dir', 'output'))
        self.output_folder_label.setStyleSheet("QLabel { padding: 5px; border: 1px solid gray; border-radius: 3px; }")
        
        select_output_button = QPushButton("出力フォルダを選択")
        select_output_button.clicked.connect(self.select_output_folder)
        
        output_layout.addWidget(QLabel("出力フォルダ:"))
        output_layout.addWidget(self.output_folder_label, 1)
        output_layout.addWidget(select_output_button)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # ログ表示部分
        log_group = QGroupBox("処理ログ")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不定進行表示
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 実行ボタン
        process_button = QPushButton("処理開始")
        process_button.setMinimumHeight(50)
        process_button.clicked.connect(self.start_processing)
        main_layout.addWidget(process_button)
        
        # 状態初期化
        self.video_path = None
        self.worker = None
        self.output_file = None
    
    def select_file(self):
        """ファイル選択ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "動画ファイルを選択", 
            str(Path.home()),
            "動画ファイル (*.mp4 *.mov *.avi *.mkv);;音声ファイル (*.wav *.mp3 *.aac *.m4a);;すべてのファイル (*.*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.file_path_label.setText(file_path)
            self.log_text.append(f"ファイルを選択しました: {file_path}")
    
    def select_output_folder(self):
        """出力フォルダ選択ダイアログを表示"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "出力フォルダを選択",
            self.output_folder_label.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            self.output_folder_label.setText(folder_path)
            self.log_text.append(f"出力フォルダを選択しました: {folder_path}")
    
    def start_processing(self):
        """処理を開始"""
        if not self.video_path:
            QMessageBox.warning(self, "エラー", "ファイルが選択されていません")
            return
        
        api_key = self.api_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "エラー", "OpenAI APIキーが入力されていません")
            return
        
        # パラメータを取得
        silence_threshold = self.silence_threshold.value()
        margin = self.margin.value()
        max_chars_per_line = self.max_chars_per_line.value()
        
        # フォーマットを取得（インデックスをフォーマット文字列に変換）
        format_map = {
            0: "xml",         # Premiere Pro XML (推奨)
            1: "pure-fcp7",   # Pure FCP7 XML
            2: "edl",         # EDL
            3: "all"          # 全フォーマット
        }
        output_format = format_map[self.output_format.currentIndex()]
        
        # ログにパラメータを表示
        self.log_text.append("---- 処理開始 ----")
        self.log_text.append(f"無音閾値: {silence_threshold}秒")
        self.log_text.append(f"マージン: {margin}秒")
        self.log_text.append(f"テロップ1行の最大文字数: {max_chars_per_line}文字")
        self.log_text.append(f"出力フォーマット: {self.output_format.currentText()}")
        self.log_text.append("処理中...")
        
        # 進捗バーを表示
        self.progress_bar.setVisible(True)
        
        # 出力フォルダを取得
        output_folder = self.output_folder_label.text()
        
        # ワーカーを作成して処理開始
        self.worker = Worker(
            self.video_path,
            silence_threshold,
            margin,
            max_chars_per_line,
            api_key,
            output_format,
            output_folder
        )
        
        # シグナル接続
        self.worker.signals.finished.connect(self.on_worker_finished)
        self.worker.signals.error.connect(self.on_worker_error)
        self.worker.signals.result.connect(self.on_worker_result)
        
        # スレッド開始
        self.worker.start()
    
    def on_worker_finished(self):
        """ワーカー終了時の処理"""
        self.progress_bar.setVisible(False)
        if self.output_file:
            self.log_text.append("---- 処理完了 ----")
            
            # 結果の表示
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("処理が完了しました")
            msg.setInformativeText(f"出力ファイル: {self.output_file}")
            msg.setWindowTitle("処理完了")
            
            # ファイルを開くボタンを追加
            open_button = msg.addButton("出力フォルダを開く", QMessageBox.ButtonRole.ActionRole)
            msg.addButton("閉じる", QMessageBox.ButtonRole.RejectRole)
            
            result = msg.exec()
            
            # 出力フォルダを開く
            if msg.clickedButton() == open_button:
                import subprocess
                subprocess.Popen(['open', os.path.dirname(self.output_file)])
    
    def on_worker_error(self, error_msg):
        """エラー発生時の処理"""
        self.log_text.append(f"エラー: {error_msg}")
        QMessageBox.critical(self, "エラー", f"処理中にエラーが発生しました:\n{error_msg}")
    
    def on_worker_result(self, output_file):
        """結果受信時の処理"""
        self.output_file = output_file
        if output_file:
            self.log_text.append(f"出力ファイル: {output_file}")
            # フォーマットが"全フォーマット"の場合、他のファイルも表示
            if self.output_format.currentIndex() == 3:  # 全フォーマット
                output_dir = os.path.dirname(output_file)
                base_name = Path(self.video_path).stem
                # 他の生成されたファイルも表示
                for ext in ['.xml', '_fcp7.xml', '.edl', '.srt']:
                    file_path = os.path.join(output_dir, f"{base_name}_edited{ext}")
                    if os.path.exists(file_path) and file_path != output_file:
                        self.log_text.append(f"追加出力ファイル: {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 