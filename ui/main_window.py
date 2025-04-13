#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
メインウィンドウモジュール
アプリケーションのメインウィンドウを実装
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import json
import datetime
import tempfile

# 自作モジュールのインポート
from transcriber import VideoTranscriber, AudioTranscriber
from ui.settings_window import SettingsWindow
from ui.result_window import ResultWindow
from utils.config_manager import ConfigManager

class MainWindow:
    """メインウィンドウクラス"""
    
    def __init__(self, root, config_manager):
        """
        初期化
        
        Args:
            root (tk.Tk): Tkinterのルートウィンドウ
            config_manager (ConfigManager): 設定管理オブジェクト
        """
        self.root = root
        self.config_manager = config_manager
        self.files = []  # 処理対象ファイル一覧
        
        # UIの色定義
        self.colors = {
            "bg_primary": "#FAFAFA",        # 背景色（ほぼ白）
            "bg_secondary": "#FFFFFF",      # 白背景
            "accent": "#2196F3",            # アクセント色（青）
            "accent_hover": "#1976D2",      # ホバー時のアクセント色（濃い青）
            "success": "#4CAF50",           # 成功色（緑）
            "warning": "#FF9800",           # 警告色（オレンジ）
            "error": "#F44336",             # エラー色（赤）
            "text_primary": "#212121",      # 主要テキスト（黒に近いグレー）
            "text_secondary": "#757575",    # 副次テキスト（ミディアムグレー）
            "text_light": "#FFFFFF",        # 明るいテキスト（白）
            "border": "#E0E0E0",            # 標準ボーダー色（薄いグレー）
        }
        
        # 処理中フラグ
        self.processing = False
        self.processing_thread = None
        
        # UIの初期化
        self._init_ui()
        
        # 設定の読み込み
        self._load_settings()
    
    def _start_processing(self):
        """文字起こし処理を開始"""
        # ファイルが選択されていなければエラー
        if not self.files:
            messagebox.showerror("エラー", "文字起こしするファイルが選択されていません。")
            return
        
        # すでに処理中なら何もしない
        if self.processing:
            return
        
        # 処理状態を更新
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # 進捗表示を初期化
        self.progress_bar["value"] = 0
        self.status_label.config(text="処理を開始します...")
        
        # 設定を取得
        model = self.config_manager.get_model()
        language = self.config_manager.get_language()
        output_dir = self.config_manager.get_output_directory()
        
        # 出力ディレクトリが存在しない場合は作成
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("エラー", f"出力ディレクトリの作成に失敗しました: {e}")
                self._reset_processing_state()
                return
        
        # 処理スレッドを起動
        self.processing_thread = threading.Thread(
            target=self._process_files,
            args=(self.files.copy(), model, language, output_dir)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _cancel_processing(self):
        """処理をキャンセル"""
        if not self.processing:
            return
        
        # キャンセル確認
        if messagebox.askyesno("確認", "処理をキャンセルしますか？"):
            # 処理中フラグを解除
            self.processing = False
            self.status_label.config(text="キャンセルしています...")
            
            # UIの状態を更新
            self.start_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
    
    def _reset_processing_state(self):
        """処理状態をリセット"""
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.status_label.config(text="待機中...")
    
    def _process_files(self, files, model, language, output_dir):
        """
        ファイルを処理する（バックグラウンドスレッドで実行）
        
        Args:
            files (list): 処理対象ファイルのリスト
            model (str): Whisperモデル名
            language (str): 言語コード
            output_dir (str): 出力ディレクトリのパス
        """
        results = []
        total_files = len(files)
        
        # UIスレッドでのステータス更新
        self.root.after(0, lambda: self.status_label.config(text=f"処理開始: {total_files}ファイル"))
        
        # 各ファイルを処理
        for i, file_path in enumerate(files):
            # キャンセルされた場合は処理を中断
            if not self.processing:
                self.root.after(0, lambda: self.status_label.config(text="処理がキャンセルされました"))
                self.root.after(0, self._reset_processing_state)
                return
            
            # 進捗状況の更新
            file_name = os.path.basename(file_path)
            base_progress = (i / total_files) * 100
            
            # UIスレッドでの表示更新
            self.root.after(0, lambda p=base_progress, f=file_name: self._update_progress(p, f"処理中: {f}"))
            
            try:
                # ファイル拡張子を取得
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                
                # 進捗更新用コールバック関数
                def progress_callback(status, progress):
                    if not self.processing:
                        return
                    
                    # ファイルごとの進捗に基づいて全体の進捗を計算
                    if progress >= 0:
                        file_progress = progress / 100.0
                        overall_progress = base_progress + (file_progress * (100.0 / total_files))
                        self.root.after(0, lambda p=overall_progress, s=status: self._update_progress(p, s))
                    else:
                        # エラー時
                        self.root.after(0, lambda s=status: self.status_label.config(text=s))
                
                # ファイルタイプに応じたTranscriberを作成
                if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
                    # 動画ファイル
                    transcriber = VideoTranscriber(model_name=model, language=language, callback=progress_callback)
                    result = transcriber.process_video(file_path)
                else:
                    # 音声ファイル
                    transcriber = AudioTranscriber(model_name=model, language=language, callback=progress_callback)
                    result = transcriber.process_audio(file_path)
                
                # 結果を保存
                output_path = self._save_result(result, file_path, output_dir)
                
                # 履歴に追加
                if output_path:
                    self.config_manager.add_to_history(file_path, output_path)
                    results.append((file_path, output_path, result))
            
            except Exception as e:
                # エラー発生時
                error_message = f"エラー ({file_name}): {str(e)}"
                print(error_message)
                
                # UIスレッドでエラーメッセージを表示
                self.root.after(0, lambda msg=error_message: messagebox.showerror("処理エラー", msg))
                self.root.after(0, lambda msg=error_message: self.status_label.config(text=msg))
                
                # エラーが発生しても処理を続行
                continue
        
        # 処理完了時の処理
        if self.processing:
            # 結果ウィンドウを表示
            if results:
                self.root.after(0, lambda r=results: self._show_results(r))
            
            # 処理状態をリセット
            self.root.after(0, lambda: self._update_progress(100, "処理完了"))
            self.root.after(1000, self._reset_processing_state)
    
    def _update_progress(self, progress, status):
        """
        進捗状況を更新
        
        Args:
            progress (float): 進捗率 (0-100)
            status (str): ステータスメッセージ
        """
        # 進捗バーを更新
        self.progress_bar["value"] = progress
        
        # ステータスラベルを更新
        self.status_label.config(text=status)
    
    def _save_result(self, result, file_path, output_dir):
        """
        文字起こし結果を保存
        
        Args:
            result (dict): 文字起こし結果
            file_path (str): 元のファイルパス
            output_dir (str): 出力ディレクトリ
            
        Returns:
            str or None: 保存されたファイルのパス、保存に失敗した場合はNone
        """
        try:
            # ファイル名の生成
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            # 無効な文字を置換
            safe_name = "".join([c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in base_name])
            # 日時を付加して一意なファイル名にする
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"KOEMOJI-{safe_name}_{timestamp}.txt"
            output_path = os.path.join(output_dir, output_file)
            
            # ファイルに保存
            with open(output_path, "w", encoding="utf-8") as f:
                # ヘッダー情報を書き込み
                f.write(f"# 文字起こし結果: {base_name}\n")
                f.write(f"# 日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# モデル: {self.config_manager.get_model()}\n")
                lang = self.config_manager.get_language()
                lang_display = "日本語" if lang == "ja" else (lang if lang else "自動検出")
                f.write(f"# 言語: {lang_display}\n\n")
                
                # テキスト全体を書き込み
                f.write(result["text"])
                
                # セグメント情報がある場合は詳細も書き込み
                if "segments" in result and result["segments"]:
                    segments_count = len(result["segments"])
                    print(f"[INFO] 保存: {segments_count}個のセグメント情報を処理します")
                    
                    f.write("\n\n## 詳細タイムスタンプ\n\n")
                    for i, segment in enumerate(result["segments"]):
                        try:
                            # 必要なキーが存在するか確認
                            if "start" in segment and "end" in segment and "text" in segment:
                                start_time = self._format_time(segment["start"])
                                end_time = self._format_time(segment["end"])
                                f.write(f"[{start_time} --> {end_time}] {segment['text']}\n")
                            else:
                                # キーが存在しない場合のデバッグ情報
                                keys = list(segment.keys())
                                print(f"[WARNING] セグメント{i}に必要なキーがありません。利用可能なキー: {keys}")
                        except Exception as e:
                            print(f"[ERROR] セグメント{i}の処理中にエラー: {e}")
                else:
                    print("[WARNING] 保存: セグメント情報がありません")
            
            return output_path
        except Exception as e:
            print(f"結果の保存に失敗しました: {e}")
            return None
    
    def _format_time(self, seconds):
        """
        秒数を時:分:秒.ミリ秒の形式に変換
        
        Args:
            seconds (float): 秒数
            
        Returns:
            str: フォーマットされた時間文字列
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def _show_results(self, results):
        """
        結果ウィンドウを表示
        
        Args:
            results (list): (ファイルパス, 出力パス, 結果辞書)のタプルのリスト
        """
        # 結果ウィンドウを作成
        result_window = ResultWindow(self.root, results)
    
    def _init_ui(self):
        """UIコンポーネントの初期化"""
        self.root.title("コエモジ - 音声・動画文字起こし")
        self.root.configure(bg=self.colors["bg_primary"])
        
        # スタイルの設定
        style = ttk.Style()
        style.configure("Accent.TButton", foreground=self.colors["text_light"], background=self.colors["accent"])
        # 太い進捗バーのスタイルを定義
        style.configure("Thick.Horizontal.TProgressbar", thickness=25)  # 進捗バーを太く
        
        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダーフレーム（タイトル、ロゴ、説明を横に配置）
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 左側のフレーム（タイトルと説明用）
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # タイトルラベル
        title_font = ("游ゴシック", 16, "bold")
        self.title_label = ttk.Label(
            left_frame, 
            text="コエモジ - 音声・動画文字起こし",
            font=title_font
        )
        self.title_label.pack(anchor=tk.W)
        
        # 説明ラベル
        desc_font = ("游ゴシック", 12)  # フォントサイズを小さく調整
        self.desc_label = ttk.Label(
            left_frame,
            text="音声/動画ファイルから自動文字起こし - 対応: MP3, WAV, MP4, MOV, AVI など",
            font=desc_font,
            justify=tk.LEFT
        )
        self.desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        # ロゴ表示（リソースがある場合）
        logo_path = os.path.join("resources", "koemoji-logo.png")
        if os.path.exists(logo_path):
            try:
                # ロゴ画像を読み込み（サイズを小さくする）
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((80, 80), Image.LANCZOS)  # サイズを小さく
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                # ロゴラベル
                self.logo_label = ttk.Label(header_frame, image=self.logo_photo)
                self.logo_label.pack(side=tk.RIGHT, padx=10)
            except Exception as e:
                print(f"ロゴ画像読み込みエラー: {e}")
        
        # ファイル一覧フレーム - パディングを小さくして余白を節約
        self.files_frame = ttk.LabelFrame(self.main_frame, text="ファイル一覧", padding=5)
        self.files_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ファイルリストボックス
        self.files_listbox = tk.Listbox(
            self.files_frame,
            height=7,  # 高さを少し小さく調整
            selectmode=tk.EXTENDED,
            bg=self.colors["bg_secondary"],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=0,
            font=("游ゴシック", 13)  # フォントサイズをやや小さく調整
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # リストボックスの選択が変更されたときのイベントをバインド
        self.files_listbox.bind('<<ListboxSelect>>', self._on_files_select)
        
        # スクロールバー
        self.files_scrollbar = ttk.Scrollbar(self.files_frame, command=self.files_listbox.yview)
        self.files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_listbox.config(yscrollcommand=self.files_scrollbar.set)
        
        # ボタンフレーム - 余白を小さく
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        # スタイルを作成して、ボタンのフォントを設定
        style = ttk.Style()
        button_font = ("游ゴシック", 14)  # ボタン用のフォントをやや小さく
        style.configure("LargeButton.TButton", font=button_font)
        
        # ファイル追加ボタン
        self.add_button = ttk.Button(
            self.button_frame,
            text="ファイル追加",
            command=self._add_files,
            width=15,  # ボタン幅を大きく
            padding=(8, 6),  # 内部パディングを小さく
            style="LargeButton.TButton"  # 大きなフォントのスタイルを適用
        )
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # ファイル削除ボタン
        self.remove_button = ttk.Button(
            self.button_frame,
            text="削除",
            command=self._remove_files,
            width=10,  # ボタン幅を大きく
            padding=(8, 6),  # 内部パディングを小さく
            style="LargeButton.TButton",  # 大きなフォントのスタイルを適用
            state=tk.DISABLED  # 初期状態は無効
        )
        self.remove_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # すべて削除ボタン
        self.remove_all_button = ttk.Button(
            self.button_frame,
            text="すべて削除",
            command=self._remove_all_files,
            width=12,  # ボタン幅を大きく
            padding=(8, 6),  # 内部パディングを小さく
            style="LargeButton.TButton",  # 大きなフォントのスタイルを適用
            state=tk.DISABLED  # 初期状態は無効
        )
        self.remove_all_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 設定ボタン
        self.settings_button = ttk.Button(
            self.button_frame,
            text="設定",
            command=self._open_settings,
            width=10,  # ボタン幅を大きく
            padding=(8, 6),  # 内部パディングを小さく
            style="LargeButton.TButton"  # 大きなフォントのスタイルを適用
        )
        self.settings_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 処理ボタンフレーム - 余白を小さく
        self.process_frame = ttk.Frame(self.main_frame)
        self.process_frame.pack(fill=tk.X, pady=5)
        
        # アクセントボタン用のスタイル
        style.configure("LargeAccent.TButton", font=button_font, background=self.colors["accent"])
        
        # 文字起こし開始ボタン
        self.start_button = ttk.Button(
            self.process_frame,
            text="文字起こし開始",
            command=self._start_processing,
            style="LargeAccent.TButton",  # 大きなフォントのアクセントスタイルを適用
            padding=(12, 10)  # 内部パディングを少し小さく
        )
        self.start_button.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # キャンセルボタン（初期状態では無効）
        self.cancel_button = ttk.Button(
            self.process_frame,
            text="キャンセル",
            command=self._cancel_processing,
            state=tk.DISABLED,
            style="LargeButton.TButton",  # 大きなフォントのスタイルを適用
            padding=(12, 10)  # 内部パディングを少し小さく
        )
        self.cancel_button.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # 進捗表示フレーム - パディングを小さく
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="処理状況", padding=5)
        self.progress_frame.pack(fill=tk.X, pady=5)
        
        # 進捗ステータスラベル
        self.status_label = ttk.Label(
            self.progress_frame,
            text="待機中...",
            font=("游ゴシック", 13)  # フォントサイズをやや小さく調整
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 進捗バー - 高さを大きくして目立たせる
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode='determinate',
            style='Thick.Horizontal.TProgressbar'  # 太いスタイルを適用
        )
        self.progress_bar.pack(fill=tk.X)
        
        # ステータスバー
        self.status_bar = ttk.Label(
            self.root,
            text="準備完了",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("游ゴシック", 12)  # フォントサイズをやや小さく調整
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _load_settings(self):
        """設定を読み込む"""
        # 現在の設定を取得
        self.config = self.config_manager.get_config()
        
        # ステータスバーに設定状態を表示
        model = self.config.get("model", "tiny")
        language = self.config.get("language", "ja")
        
        # 言語表示を調整
        language_display = "日本語" if language == "ja" else (language if language else "自動検出")
        
        # モデル表示を調整
        model_display = {
            "tiny": "最小",
            "base": "小",
            "small": "標準",
            "medium": "高精度",
            "large": "最高精度"
        }.get(model, model)
        
        # ステータスバーに表示
        self.status_bar.config(text=f"設定: モデル: {model_display}, 言語: {language_display}")
    
    def _add_files(self):
        """ファイルを追加"""
        # サポートされているファイル形式
        filetypes = [
            ("対応ファイル", "*.mp3 *.wav *.ogg *.flac *.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("音声ファイル", "*.mp3 *.wav *.ogg *.flac"),
            ("動画ファイル", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("すべてのファイル", "*.*")
        ]
        
        # ファイル選択ダイアログを表示
        new_files = filedialog.askopenfilenames(
            title="文字起こしするファイルを選択",
            filetypes=filetypes
        )
        
        # 選択されたファイルがあれば追加
        if new_files:
            # 重複を避けつつ追加
            for file in new_files:
                if file not in self.files:
                    self.files.append(file)
                    filename = os.path.basename(file)
                    self.files_listbox.insert(tk.END, filename)
            
            # ボタンの状態を更新
            self._on_files_select()
    
    def _on_files_select(self, event=None):
        """ファイルの選択状態が変わったときに呼び出される"""
        # 選択されているファイルの数を取得
        selected_count = len(self.files_listbox.curselection())
        
        # 削除ボタンの状態を更新
        if selected_count > 0:
            self.remove_button.config(state=tk.NORMAL)
        else:
            self.remove_button.config(state=tk.DISABLED)
        
        # すべて削除ボタンの状態を更新（ファイルが1つ以上あれば有効）
        if len(self.files) > 0:
            self.remove_all_button.config(state=tk.NORMAL)
        else:
            self.remove_all_button.config(state=tk.DISABLED)
    
    def _remove_files(self):
        """選択されたファイルを削除"""
        # 選択されたインデックスを取得
        selected_indices = self.files_listbox.curselection()
        
        # 選択されたファイルがなければ何もしない
        if not selected_indices:
            return
        
        # 削除する件数
        count = len(selected_indices)
        
        # 確認ダイアログを表示
        confirm_message = f"選択された{count}件のファイルを削除しますか？"
        if not messagebox.askyesno("確認", confirm_message):
            return
        
        # 選択されたファイルを削除（インデックスが変わるため、逆順で削除）
        for i in sorted(selected_indices, reverse=True):
            del self.files[i]
            self.files_listbox.delete(i)
        
        # ボタンの状態を更新
        self._on_files_select()
    
    def _remove_all_files(self):
        """すべてのファイルを削除"""
        # ファイルがなければ何もしない
        if not self.files:
            return
        
        # 確認ダイアログを表示
        count = len(self.files)
        confirm_message = f"リスト内のすべてのファイル（{count}件）を削除しますか？"
        if not messagebox.askyesno("確認", confirm_message):
            return
        
        # すべてのファイルを削除
        self.files.clear()
        self.files_listbox.delete(0, tk.END)
        
        # ボタンの状態を更新
        self._on_files_select()
    
    def _open_settings(self):
        """設定画面を開く"""
        # 処理中は設定を変更できないようにする
        if self.processing:
            messagebox.showinfo("処理中", "文字起こし処理中は設定を変更できません。")
            return
        
        # 設定ウィンドウを作成
        settings_window = SettingsWindow(self.root, self.config_manager)
        
        # 設定画面が閉じられたら設定を再読み込み
        self.root.wait_window(settings_window.window)
        self._load_settings()
