#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Koemoji - シンプル文字起こしツール
音声や動画ファイルから文字起こしを簡単に行うためのデスクトップアプリケーション。
FasterWhisperモデルを活用して、オフラインで文字起こしを行います。

MIT License
Copyright (c) 2025 Koemoji Project Authors
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional, Dict, Any, List, Tuple
import queue

# サードパーティライブラリ
try:
    from faster_whisper import WhisperModel
except ImportError:
    messagebox.showerror("エラー", "faster_whisperモジュールがインストールされていません。\n"
                        "pip install faster-whisper を実行してインストールしてください。")
    sys.exit(1)

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("koemoji")

# 定数
DEFAULT_CONFIG = {
    "model_size": "large",  # tiny, base, small, medium, large
    "language": "ja",  # ja, en, auto
    "output_dir": str(Path.home() / "Documents"),
    "compute_type": "int8"  # float16, float32, int8
}

MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]
LANGUAGES = {
    "自動検出": "auto",
    "日本語": "ja",
    "英語": "en",
}

CONFIG_PATH = Path(__file__).parent / "config.json"


class KoemojiApp:
    """Koemojiアプリケーションのメインクラス"""

    def __init__(self, root: tk.Tk):
        """アプリケーションの初期化"""
        self.root = root
        self.root.title("Koemoji - シンプル文字起こしツール")
        self.root.geometry("1000x750")
        
        # ウィンドウを画面中央に配置
        self.center_window()
        
        # アイコンの設定（存在する場合）
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))
        
        # 設定の読み込み
        self.config = self.load_config()
        
        # モデル
        self.model: Optional[WhisperModel] = None
        
        # ファイルキュー
        self.file_queue = queue.Queue()
        self.processing_files = False
        self.cancel_flag = False
        
        # 処理スレッド
        self.transcription_thread = None
        
        # UI構築
        self.build_ui()
        
    def center_window(self):
        """ウィンドウを画面中央に配置"""
        # 画面サイズ取得
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # ウィンドウサイズ取得
        window_width = 1000
        window_height = 750
        
        # 中央位置を計算
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
            
        # 位置を設定
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def load_config(self) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 必要なキーが存在するか確認し、存在しない場合はデフォルト値を使用
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"設定ファイルの読み込みエラー: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        """設定ファイルの保存"""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def build_ui(self):
        """UIの構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ファイル選択セクション
        file_frame = ttk.LabelFrame(main_frame, text="ファイル選択", padding="10")
        file_frame.pack(fill=tk.X, pady=5)

        # ファイルリストフレーム
        file_list_frame = ttk.Frame(file_frame)
        file_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # ファイルリスト
        file_list_frame_inner = ttk.Frame(file_list_frame)
        file_list_frame_inner.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # リストボックスとスクロールバー
        self.file_listbox = tk.Listbox(file_list_frame_inner, height=5, selectmode=tk.EXTENDED)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        file_scrollbar = ttk.Scrollbar(file_list_frame_inner, orient=tk.VERTICAL, command=self.file_listbox.yview)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)

        # ファイル操作ボタン
        file_buttons_frame = ttk.Frame(file_list_frame)
        file_buttons_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=5)
        
        ttk.Button(file_buttons_frame, text="📂 ファイル追加", command=self.browse_files).pack(pady=2)
        ttk.Button(file_buttons_frame, text="📁 フォルダから追加", command=self.browse_folder).pack(pady=2)
        ttk.Button(file_buttons_frame, text="🗑️ 選択削除", command=self.remove_selected_files).pack(pady=2)
        ttk.Button(file_buttons_frame, text="🧹 全削除", command=self.clear_files).pack(pady=2)

        # 設定セクション
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)

        # モデルサイズ選択
        ttk.Label(settings_frame, text="モデルサイズ:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_size_var = tk.StringVar(value=self.config["model_size"])
        model_combo = ttk.Combobox(settings_frame, textvariable=self.model_size_var, values=MODEL_SIZES, state="readonly", width=15)
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        model_combo.bind("<<ComboboxSelected>>", lambda e: self.update_config("model_size", self.model_size_var.get()))

        # 言語選択
        ttk.Label(settings_frame, text="言語:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.language_var = tk.StringVar()
        # 設定から言語コードを表示用テキストに変換
        for display_name, code in LANGUAGES.items():
            if code == self.config["language"]:
                self.language_var.set(display_name)
                break
        else:
            self.language_var.set("自動検出")  # デフォルト値
            
        language_combo = ttk.Combobox(settings_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly", width=15)
        language_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        language_combo.bind("<<ComboboxSelected>>", self.on_language_changed)

        # 出力ディレクトリ選択
        ttk.Label(settings_frame, text="出力先:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir_var = tk.StringVar(value=self.config["output_dir"])
        ttk.Entry(settings_frame, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(settings_frame, text="📂 変更...", command=self.browse_output_dir).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 出力先が変更されたときに設定を更新するバインド
        self.output_dir_var.trace_add("write", lambda name, index, mode: self.update_config("output_dir", self.output_dir_var.get()))

        # ステータス表示
        status_frame = ttk.LabelFrame(main_frame, text="状態", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # ステータステキスト
        self.status_text = tk.Text(status_frame, height=10, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # スクロールバー
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)

        # 進捗表示
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        # ファイル進捗
        ttk.Label(progress_frame, text="ファイル進捗:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_progress_var = tk.StringVar(value="0/0")
        ttk.Label(progress_frame, textvariable=self.file_progress_var).pack(side=tk.LEFT, padx=(0, 10))
        
        # 現在のファイル進捗（パルスモードで表示）
        ttk.Label(progress_frame, text="現在の処理:").pack(side=tk.LEFT, padx=(0, 5))
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=280)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_percent_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.progress_percent_var, width=8).pack(side=tk.LEFT, padx=5)

        # 実行ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="🎙️ 文字起こし開始", command=self.start_transcription).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⛔ キャンセル", command=self.cancel_transcription).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🚪 終了", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)

        # 初期メッセージ
        self.update_status("🎵 ファイルを選択して「文字起こし開始」ボタンをクリックしてください。")

    def update_status(self, message: str):
        """ステータスメッセージの更新"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M')}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def browse_files(self):
        """複数の音声/動画ファイルを選択するダイアログを表示"""
        filetypes = [
            ("メディアファイル", "*.mp3 *.mp4 *.wav *.m4a *.avi *.mov *.wmv *.flac"),
            ("すべてのファイル", "*.*")
        ]
        filepaths = filedialog.askopenfilenames(filetypes=filetypes)
        if filepaths:
            for filepath in filepaths:
                if filepath not in self.get_all_files():
                    self.file_listbox.insert(tk.END, filepath)
            self.update_status(f"📥 {len(filepaths)}個のファイルを追加しました。")

    def browse_folder(self):
        """フォルダ内の音声/動画ファイルを追加"""
        folder = filedialog.askdirectory()
        if not folder:
            return
            
        # サポートする拡張子
        extensions = [".mp3", ".mp4", ".wav", ".m4a", ".avi", ".mov", ".wmv", ".flac"]
        
        count = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    if filepath not in self.get_all_files():
                        self.file_listbox.insert(tk.END, filepath)
                        count += 1
        
        if count > 0:
            self.update_status(f"📁 フォルダから{count}個のメディアファイルを追加しました。")
        else:
            self.update_status("❓ フォルダ内にサポートされているメディアファイルが見つかりませんでした。")

    def get_all_files(self) -> List[str]:
        """リストボックス内のすべてのファイルを取得"""
        return [self.file_listbox.get(i) for i in range(self.file_listbox.size())]

    def remove_selected_files(self):
        """選択されたファイルをリストから削除"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
            
        # 後ろから削除（インデックスがずれないように）
        for i in sorted(selected_indices, reverse=True):
            self.file_listbox.delete(i)
        
        self.update_status(f"🗑️ {len(selected_indices)}個のファイルをリストから削除しました。")

    def clear_files(self):
        """ファイルリストを全てクリア"""
        if self.file_listbox.size() > 0:
            self.file_listbox.delete(0, tk.END)
            self.update_status("🧹 ファイルリストをクリアしました。")

    def browse_output_dir(self):
        """出力先ディレクトリを選択するダイアログを表示"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
            self.update_config("output_dir", directory)

    def on_language_changed(self, event):
        """言語選択が変更されたときの処理"""
        selected_display = self.language_var.get()
        selected_code = LANGUAGES.get(selected_display, "auto")
        self.update_config("language", selected_code)

    def update_config(self, key: str, value: Any):
        """設定を更新して保存"""
        self.config[key] = value
        self.save_config()

    def check_ffmpeg(self) -> bool:
        """FFmpegがインストールされているか確認"""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def load_model(self):
        """WhisperModelをロード"""
        try:
            # モデルサイズが変更された場合、または初回ロード時に新しくロードする
            current_model_size = getattr(self.model, "_model_size", None) if self.model else None
            
            if self.model is None or current_model_size != self.config["model_size"]:
                self.update_status(f"🔄 モデル '{self.config['model_size']}' をロード中...")
                
                # CPUの場合はint8、CUDAが利用可能ならfloat16を使用
                compute_type = self.config["compute_type"]
                device = "cuda" if self.is_cuda_available() else "cpu"
                
                # CPUでfloat16を指定された場合はint8に自動変換
                if device == "cpu" and compute_type == "float16":
                    compute_type = "int8"
                    self.update_status("ℹ️ CPUでの実行のため、計算タイプをint8に自動変更しました。")
                
                self.model = WhisperModel(
                    model_size_or_path=self.config["model_size"],
                    device=device,
                    compute_type=compute_type
                )
                self.update_status(f"✅ モデル '{self.config['model_size']}' のロードが完了しました。({device}、{compute_type})")
            return True
        except Exception as e:
            self.update_status(f"モデルのロードエラー: {e}")
            messagebox.showerror("エラー", f"モデルのロードに失敗しました: {e}")
            return False

    def is_cuda_available(self) -> bool:
        """CUDAが利用可能かどうかを確認"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def start_transcription(self):
        """文字起こし処理を開始"""
        files = self.get_all_files()
        output_dir = self.output_dir_var.get()

        # 入力チェック
        if not files:
            messagebox.showerror("エラー", "ファイルを選択してください。")
            return

        if not output_dir:
            messagebox.showerror("エラー", "出力先ディレクトリを指定してください。")
            return

        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("エラー", f"出力先ディレクトリの作成に失敗しました: {e}")
                return

        # FFmpegのチェック
        if not self.check_ffmpeg():
            messagebox.showerror("エラー", "FFmpegがインストールされていないか、PATHに設定されていません。\n"
                               "FFmpegをインストールして、PATHに追加してください。")
            return

        # 処理中の場合は警告
        if self.transcription_thread and self.transcription_thread.is_alive():
            messagebox.showwarning("警告", "すでに文字起こし処理が実行中です。")
            return
            
        # 以前のスレッドが終了している場合はNoneに設定（メモリリーク防止）
        if self.transcription_thread and not self.transcription_thread.is_alive():
            self.transcription_thread = None

        # キャンセルフラグのリセット
        self.cancel_flag = False
        
        # 前の処理が完全に終了していることを確認
        if self.processing_files:
            messagebox.showwarning("警告", "前回の処理がまだ完了していません。")
            return
            
        # キャンセルフラグをリセット
        self.cancel_flag = False
        
        # ファイルキューをクリアして追加
        with self.file_queue.mutex:
            self.file_queue.queue.clear()
        
        file_count = 0
        for file in files:
            if os.path.exists(file):
                self.file_queue.put(file)
                file_count += 1
            else:
                self.update_status(f"⚠️ 警告: ファイルが見つかりません: {file}")
                
        if file_count == 0:
            messagebox.showinfo("情報", "処理するファイルがありません。")
            return
        
        self.file_progress_var.set(f"0/{file_count}")
        self.update_status(f"🚀 {file_count}個のファイルの処理を開始します。")

        # 処理スレッドの開始
        self.transcription_thread = threading.Thread(
            target=self.process_file_queue,
            args=(output_dir,),
            daemon=True
        )
        self.transcription_thread.start()

    def process_file_queue(self, output_dir: str):
        """ファイルキューの処理"""
        try:
            # 処理中フラグを設定
            self.processing_files = True
            
            # モデルのロード
            if not self.load_model():
                self.processing_files = False
                return
                
            total_files = self.file_queue.qsize()
            processed_files = 0
            
            while not self.file_queue.empty() and not self.cancel_flag:
                input_file = self.file_queue.get()
                processed_files += 1
                
                # ファイル進捗の更新
                self.file_progress_var.set(f"{processed_files}/{total_files}")
                
                try:
                    # プログレスバーのパルスを開始
                    self.progress_bar.start()
                    self.progress_percent_var.set("処理中")
                    
                    self.transcribe_file(input_file, output_dir)
                except Exception as e:
                    self.update_status(f"❌ ファイル処理中にエラーが発生しました: {os.path.basename(input_file)} - {e}")
                    logger.exception(f"ファイル処理中にエラー: {input_file}")
                
                # ファイルキューのタスク完了を通知
                self.file_queue.task_done()
            
            if self.cancel_flag:
                self.update_status("🛑 処理がキャンセルされました。")
            else:
                self.update_status("🎉 すべてのファイルの処理が完了しました。")
                messagebox.showinfo("✅ 完了", "🎉 すべてのファイルの文字起こしが完了しました。")
        
        except Exception as e:
            self.update_status(f"❌ 処理中にエラーが発生しました: {e}")
            logger.exception("ファイルキュー処理中にエラーが発生しました")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {e}")
        
        finally:
            self.processing_files = False
            # パルスを停止
            self.progress_bar.stop()
            self.progress_percent_var.set("停止")

    def transcribe_file(self, input_file: str, output_dir: str):
        """単一ファイルの文字起こし処理"""
        # 出力ファイルパスの生成
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        timestamp = datetime.now().strftime("%Y-%m%d-%H%M")
        # Windowsのパス区切り文字を統一
        output_file = os.path.normpath(os.path.join(output_dir, f"{base_name}_{timestamp}.txt"))

        self.update_status(f"🎙️ 文字起こし開始: {os.path.basename(input_file)}")
        self.update_status(f"📄 出力先: {output_file}")

        # 言語設定の取得
        language = self.config["language"]
        if language == "auto":
            language = None  # Whisperの自動検出を使用
            self.update_status("🔍 言語は自動検出を使用します。")
        else:
            self.update_status(f"🗣️ 言語設定: {language}")

        # 文字起こしの実行
        segments, info = self.model.transcribe(
            input_file,
            language=language,
            beam_size=5,
            task="transcribe"
        )

        # 進捗計算のために合計セグメント数を推定
        # infoの型によって処理を分ける
        if hasattr(info, "get") and callable(info.get):
            estimated_segments = info.get("segment_count", 100)  # 辞書の場合
        else:
            # オブジェクトの場合はsegemnt_countの属性があるか確認
            estimated_segments = getattr(info, "segment_count", 100) if hasattr(info, "segment_count") else 100
        
        # テキストファイルに書き込み
        with open(output_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                if self.cancel_flag:
                    self.update_status(f"🛑 ファイル {os.path.basename(input_file)} の処理がキャンセルされました。")
                    return

                # セグメント情報の書き込み
                text = segment.text.strip()
                
                # 空のテキストはスキップ
                if text:
                    f.write(f"{text}\n")
                
                # 進捗表示は行わない（パルスモードで常に処理中表示）
                
                # 定期的にステータス更新（セグメント数の比率表示をやめて単純化）
                if (i + 1) % 10 == 0 or i == 0:
                    self.update_status(f"⏳ ファイル: {os.path.basename(input_file)} - 処理中: セグメント {i + 1}")

        # 処理完了時にパルスを停止
        self.progress_bar.stop()
        self.progress_percent_var.set("完了")
        
        self.update_status(f"✅ ファイル {os.path.basename(input_file)} の文字起こしが完了しました。(合計 {i + 1} セグメント処理)")
        # 最後のファイルなら完了メッセージを表示するだけ（自動で開く機能は削除）

    def format_time(self, seconds: float) -> str:
        """秒数を[HH:MM:SS.mmm]形式に変換"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def cancel_transcription(self):
        """文字起こし処理をキャンセル"""
        if self.transcription_thread and self.transcription_thread.is_alive():
            self.cancel_flag = True
            self.update_status("⏳ キャンセル中...（現在の処理が完了するまでお待ちください）")
            
            # パルスを停止
            self.progress_bar.stop()
            self.progress_percent_var.set("")
            
            # キューをクリア
            with self.file_queue.mutex:
                self.file_queue.queue.clear()
        else:
            self.update_status("ℹ️ キャンセルする処理がありません。")

    # open_fileメソッドを削除


def main():
    """アプリケーションのエントリーポイント"""
    root = tk.Tk()
    app = KoemojiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
