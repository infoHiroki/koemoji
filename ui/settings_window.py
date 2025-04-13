#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
設定ウィンドウモジュール
アプリケーションの設定を構成するためのウィンドウを実装
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class SettingsWindow:
    """設定ウィンドウクラス"""
    
    def __init__(self, parent, config_manager):
        """
        初期化
        
        Args:
            parent (tk.Tk): 親ウィンドウ
            config_manager (ConfigManager): 設定管理オブジェクト
        """
        self.parent = parent
        self.config_manager = config_manager
        
        # 設定ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("設定")
        self.window.geometry("650x700")  # 縦幅をさらに増やす
        self.window.minsize(650, 700)  # 最小サイズを設定
        self.window.resizable(True, True)  # リサイズ可能にする
        self.window.transient(parent)  # 親ウィンドウに対するモーダルダイアログとして設定
        self.window.grab_set()  # モーダルにする
        
        # 親ウィンドウの中央に配置
        self._center_window()
        
        # 設定値を取得
        self.config = self.config_manager.get_config()
        
        # UIコンポーネントの初期化
        self._init_ui()
    
    def _center_window(self):
        """ウィンドウを親ウィンドウの中央に配置"""
        self.window.update_idletasks()
        
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _init_ui(self):
        """UIコンポーネントの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame,
            text="コエモジ 設定",
            font=("游ゴシック", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # スタイルの作成
        style = ttk.Style()
        
        # タブのフォントを大きくするスタイルを設定
        style.configure("TNotebook.Tab", font=("游ゴシック", 14), padding=[15, 5])  # タブのフォントサイズと内部余白を設定
        style.configure("TNotebook", tabmargins=[2, 5, 2, 0])  # タブのマージンを調整してクリック領域を広く
        
        # タブコントロールの作成
        tab_control = ttk.Notebook(main_frame)
        
        # タブ1: 文字起こし設定
        tab_transcription = ttk.Frame(tab_control)
        tab_control.add(tab_transcription, text="文字起こし設定")
        
        # タブ2: 出力設定
        tab_output = ttk.Frame(tab_control)
        tab_control.add(tab_output, text="出力設定")
        
        tab_control.pack(expand=True, fill=tk.BOTH)
        
        #---------- 文字起こし設定タブの内容 ----------
        # モデル選択
        model_frame = ttk.LabelFrame(tab_transcription, text="文字起こしモデル", padding=10)
        model_frame.pack(fill=tk.X, pady=5)
        
        # モデルの説明
        model_desc = ttk.Label(
            model_frame,
            text="モデルサイズの選択ガイド：\n・tiny：短い音声や速度優先の場合、低スペックPCでの利用に適しています\n・base：一般的な会話や講義に最適なバランス\n・large：専門用語や複数話者、重要な会議録など高い精度が必要な場合（推奨）",
            justify=tk.LEFT,
            wraplength=550,
            font=("游ゴシック", 12)  # フォントサイズをやや小さく調整
        )
        model_desc.pack(anchor=tk.W, pady=(0, 10))
        
        # ラジオボタン用のフォントスタイルを作成
        style.configure("LargeRadio.TRadiobutton", font=("游ゴシック", 14))
        
        # モデルサイズ選択
        self.model_var = tk.StringVar(value=self.config.get("model", "tiny"))
        
        model_sizes = [
            ("tiny", "tiny (処理速度優先)"),
            ("base", "base"),
            ("small", "small"),
            ("medium", "medium"),
            ("large", "large (推奨)")
        ]
        
        for i, (model_value, model_text) in enumerate(model_sizes):
            model_radio = ttk.Radiobutton(
                model_frame,
                text=model_text,
                value=model_value,
                variable=self.model_var,
                style="LargeRadio.TRadiobutton"  # 大きなフォントのスタイルを適用
            )
            model_radio.pack(anchor=tk.W, pady=4)  # 余白も少し大きく
        
        # 言語設定
        lang_frame = ttk.LabelFrame(tab_transcription, text="言語設定", padding=10)
        lang_frame.pack(fill=tk.X, pady=10)
        
        # 言語の説明
        lang_desc = ttk.Label(
            lang_frame,
            text="文字起こし対象の言語を指定します。特定の言語を指定すると精度が向上します。",
            justify=tk.LEFT,
            wraplength=550,
            font=("游ゴシック", 12)  # フォントサイズをやや小さく調整
        )
        lang_desc.pack(anchor=tk.W, pady=(0, 10))
        
        # 言語選択
        self.lang_var = tk.StringVar(value=self.config.get("language", "ja"))
        
        languages = [
            ("", "自動検出"),
            ("ja", "日本語"),
            ("en", "英語"),
            ("zh", "中国語"),
            ("ko", "韓国語"),
            ("es", "スペイン語"),
            ("fr", "フランス語"),
            ("de", "ドイツ語"),
            ("it", "イタリア語"),
            ("pt", "ポルトガル語"),
            ("ru", "ロシア語")
        ]
        
        language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=[lang_text for lang_value, lang_text in languages],
            state="readonly",
            font=("游ゴシック", 12)  # フォントサイズをやや小さく調整
        )
        language_combo.pack(fill=tk.X, pady=5)
        
        # 言語コードとテキスト表示のマッピング
        self.lang_mapping = {lang_text: lang_value for lang_value, lang_text in languages}
        self.lang_reverse_mapping = {lang_value: lang_text for lang_value, lang_text in languages}
        
        # 表示されている言語テキストを選択
        selected_lang = self.config.get("language", "ja")
        language_combo.set(self.lang_reverse_mapping.get(selected_lang, "自動検出"))
        
        # コンボボックス選択時のイベント
        def on_language_selected(event):
            selected_text = language_combo.get()
            selected_code = self.lang_mapping.get(selected_text, "")
            self.lang_var.set(selected_code)
        
        language_combo.bind("<<ComboboxSelected>>", on_language_selected)
        
        # この位置にはタブが減ったので、何もコードを入れません
        
        #---------- 出力設定タブの内容 ----------
        # 出力ディレクトリ
        dir_frame = ttk.LabelFrame(tab_output, text="出力ディレクトリ", padding=10)
        dir_frame.pack(fill=tk.X, pady=5)
        
        # 出力ディレクトリの説明
        dir_desc = ttk.Label(
            dir_frame,
            text="文字起こし結果の保存先を指定します。",
            justify=tk.LEFT,
            wraplength=550,
            font=("游ゴシック", 12)  # フォントサイズをやや小さく調整
        )
        dir_desc.pack(anchor=tk.W, pady=(0, 10))
        
        # 出力ディレクトリ設定
        dir_input_frame = ttk.Frame(dir_frame)
        dir_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dir_input_frame, text="ディレクトリ:", font=("游ゴシック", 12)).pack(side=tk.LEFT)
        
        self.output_dir_var = tk.StringVar(value=self.config.get("output_directory", ""))
        output_dir_entry = ttk.Entry(dir_input_frame, textvariable=self.output_dir_var, width=50, font=("游ゴシック", 12))
        output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(
            dir_input_frame,
            text="参照...",
            command=self._browse_output_dir,
            style="Settings.LargeButton.TButton",  # 大きなフォントのスタイルを適用
            padding=(8, 6)
        )
        browse_button.pack(side=tk.RIGHT)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # ボタンのフォントを設定
        button_font = ("游ゴシック", 14)  # ボタン用のフォントをやや小さく
        style.configure("Settings.LargeButton.TButton", font=button_font)
        
        # 保存ボタン
        save_button = ttk.Button(
            button_frame,
            text="保存",
            command=self._save_settings,
            width=15,
            padding=(10, 8),
            style="Settings.LargeButton.TButton"  # 大きなフォントのスタイルを適用
        )
        save_button.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # キャンセルボタン
        cancel_button = ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.window.destroy,
            width=15,
            padding=(10, 8),
            style="Settings.LargeButton.TButton"  # 大きなフォントのスタイルを適用
        )
        cancel_button.pack(side=tk.RIGHT, padx=10, pady=8)
    
    def _browse_output_dir(self):
        """出力ディレクトリを選択"""
        current_dir = self.output_dir_var.get()
        
        # カレントディレクトリが存在しない場合はデスクトップを選択
        if not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~/Desktop")
        
        # ディレクトリ選択ダイアログを表示
        directory = filedialog.askdirectory(
            title="出力ディレクトリを選択",
            initialdir=current_dir
        )
        
        # ディレクトリが選択された場合は設定を更新
        if directory:
            self.output_dir_var.set(directory)
    
    def _save_settings(self):
        """設定を保存"""
        # 設定値を取得
        model = self.model_var.get()
        language = self.lang_var.get()
        output_directory = self.output_dir_var.get()
        
        # 出力ディレクトリのチェック
        if not output_directory:
            messagebox.showerror("エラー", "出力ディレクトリを指定してください。")
            return
        
        # 出力ディレクトリが存在しない場合は確認
        if not os.path.exists(output_directory):
            if messagebox.askyesno("確認", f"指定された出力ディレクトリ「{output_directory}」が存在しません。\n作成しますか？"):
                try:
                    os.makedirs(output_directory)
                except Exception as e:
                    messagebox.showerror("エラー", f"ディレクトリの作成に失敗しました: {e}")
                    return
            else:
                return
        
        # 設定を更新
        self.config_manager.set_model(model)
        self.config_manager.set_language(language)
        self.config_manager.set_output_directory(output_directory)
        
        # 設定を保存
        self.config_manager.save_config()
        
        # 保存成功メッセージ
        messagebox.showinfo("設定を保存しました", "設定を保存しました。")
        
        # ウィンドウを閉じる
        self.window.destroy()
