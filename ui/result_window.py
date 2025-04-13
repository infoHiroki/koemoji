#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
結果表示ウィンドウモジュール
文字起こし結果を表示するウィンドウを実装
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform

class ResultWindow:
    """結果表示ウィンドウクラス"""
    
    def __init__(self, parent, results):
        """
        初期化
        
        Args:
            parent (tk.Tk): 親ウィンドウ
            results (list): (ファイルパス, 出力パス, 結果辞書)のタプルのリスト
        """
        self.parent = parent
        self.results = results
        
        # 結果ウィンドウの作成
        self.window = tk.Toplevel(parent)
        self.window.title("文字起こし結果")
        self.window.geometry("700x500")
        self.window.minsize(600, 400)
        self.window.transient(parent)
        
        # 親ウィンドウの中央に配置
        self._center_window()
        
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
            text="文字起こし結果",
            font=("游ゴシック", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 結果一覧フレーム
        results_frame = ttk.LabelFrame(main_frame, text="処理結果一覧", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 結果リストビュー
        columns = ("ファイル名", "出力ファイル")
        self.result_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # ヘッダーの設定
        self.result_tree.heading("ファイル名", text="ファイル名")
        self.result_tree.heading("出力ファイル", text="出力ファイル")
        
        # 列の幅の設定
        self.result_tree.column("ファイル名", width=300)
        self.result_tree.column("出力ファイル", width=350)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # ウィジェットの配置
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 結果データの挿入
        for file_path, output_path, result in self.results:
            self.result_tree.insert("", tk.END, values=(
                os.path.basename(file_path),
                os.path.basename(output_path)
            ), tags=(output_path,))
        
        # 結果ファイルをダブルクリックで開く
        self.result_tree.bind("<Double-1>", self._open_result_file)
        
        # アクションフレーム
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # フォルダを開くボタン
        open_folder_button = ttk.Button(
            action_frame,
            text="出力フォルダを開く",
            command=self._open_output_folder
        )
        open_folder_button.pack(side=tk.LEFT, padx=5)
        
        # ファイルを開くボタン
        open_file_button = ttk.Button(
            action_frame,
            text="選択したファイルを開く",
            command=self._open_selected_file
        )
        open_file_button.pack(side=tk.LEFT, padx=5)
        
        # コピーボタン
        copy_button = ttk.Button(
            action_frame,
            text="テキストをコピー",
            command=self._copy_text
        )
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # 閉じるボタン
        close_button = ttk.Button(
            action_frame,
            text="閉じる",
            command=self.window.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def _open_result_file(self, event):
        """結果ファイルを開く（ダブルクリック時）"""
        # 選択された項目を取得
        selection = self.result_tree.selection()
        if not selection:
            return
        
        # 選択された項目に関連するファイルパスを取得
        item = selection[0]
        item_values = self.result_tree.item(item, "values")
        
        # ファイル名から対応する出力パスを検索
        output_filename = item_values[1]
        output_path = None
        
        for _, out_path, _ in self.results:
            if os.path.basename(out_path) == output_filename:
                output_path = out_path
                break
        
        if output_path and os.path.exists(output_path):
            self._open_file(output_path)
    
    def _open_selected_file(self):
        """選択したファイルを開く"""
        # 選択された項目を取得
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showinfo("情報", "ファイルを選択してください。")
            return
        
        # 選択された項目に関連するファイルパスを取得
        item = selection[0]
        item_values = self.result_tree.item(item, "values")
        
        # ファイル名から対応する出力パスを検索
        output_filename = item_values[1]
        output_path = None
        
        for _, out_path, _ in self.results:
            if os.path.basename(out_path) == output_filename:
                output_path = out_path
                break
        
        if output_path and os.path.exists(output_path):
            self._open_file(output_path)
        else:
            messagebox.showerror("エラー", "ファイルが見つかりません。")
    
    def _open_output_folder(self):
        """出力フォルダを開く"""
        if not self.results:
            return
        
        # 最初の結果の出力パスからフォルダを取得
        _, output_path, _ = self.results[0]
        output_dir = os.path.dirname(output_path)
        
        if os.path.exists(output_dir):
            # プラットフォームに応じたフォルダを開くコマンド
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", output_dir])
            else:  # Linux
                subprocess.Popen(["xdg-open", output_dir])
        else:
            messagebox.showerror("エラー", "フォルダが見つかりません。")
    
    def _copy_text(self):
        """選択したファイルのテキストをクリップボードにコピー"""
        # 選択された項目を取得
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showinfo("情報", "ファイルを選択してください。")
            return
        
        # 選択された項目に関連するファイルパスを取得
        item = selection[0]
        item_values = self.result_tree.item(item, "values")
        
        # ファイル名から対応する出力パスと結果を検索
        output_filename = item_values[1]
        result_text = None
        
        for _, out_path, result in self.results:
            if os.path.basename(out_path) == output_filename:
                result_text = result["text"]
                break
        
        if result_text:
            # クリップボードにコピー
            self.window.clipboard_clear()
            self.window.clipboard_append(result_text)
            messagebox.showinfo("コピー完了", "テキストをクリップボードにコピーしました。")
        else:
            messagebox.showerror("エラー", "テキストを取得できませんでした。")
    
    def _open_file(self, file_path):
        """ファイルを既定のアプリケーションで開く"""
        try:
            # プラットフォームに応じたファイルを開くコマンド
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", file_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした: {e}")
