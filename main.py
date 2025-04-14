#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コエモジ - 音声・動画文字起こしアプリケーション
OpenAI Whisperを使用して動画ファイルから音声を抽出し、自動的に文字起こしを行うデスクトップアプリケーション
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
import ctypes

# 自作モジュールのインポート
from transcriber import VideoTranscriber
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from utils.config_manager import ConfigManager

# モダンなカラーパレット定義
COLORS = {
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

def find_app_icon():
    """アプリケーションアイコンを探す"""
    # 優先順位: 256x256 -> 48x48 -> 動的生成
    
    # 大きい方のアイコンを優先
    icon_path_large = os.path.join("resources", "koemoji-logo256x256.ico")
    if os.path.exists(icon_path_large):
        print(f"大きいアイコンファイルを使用します: {icon_path_large}")
        return icon_path_large
    
    # 小さい方のアイコン
    icon_path_small = os.path.join("resources", "koemoji-logo48x48.ico")
    if os.path.exists(icon_path_small):
        print(f"小さいアイコンファイルを使用します: {icon_path_small}")
        return icon_path_small
    
    # 既存のアイコンが見つからない場合は動的に生成
    return create_app_icon()

def create_app_icon():
    """アプリケーションアイコンを作成"""
    try:
        # アイコンファイルの保存先
        icon_path = os.path.join("resources", "app_icon.ico")
        
        # アイコンがすでに存在する場合でも、高品質なアイコンを確保するために再作成する
        
        # ロゴ画像の候補
        logo_paths = [
            os.path.join("resources", "koemoji-logo256x256"),  # 高解像度を優先
            os.path.join("resources", "koemoji-logo48x48.png")
        ]
        
        # 使用可能なロゴを探す
        logo_path = None
        for path in logo_paths:
            if os.path.exists(path):
                logo_path = path
                break
        
        if not logo_path:
            print("ロゴ画像が見つかりませんでした")
            return None
            
        # PNGからICOを作成
        from PIL import Image, ImageEnhance
        img = Image.open(logo_path)
        
        # 背景が透明でない場合は透明な背景を作成
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # コントラストとシャープネスを少し上げて鮮明にする
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)  # コントラストを20%上げる
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)  # シャープネスを50%上げる
        
        # 複数サイズのアイコンを作成（Windows推奨サイズ）
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icon_images = []
        
        for size in sizes:
            # アイコン用の新しい正方形画像を作成 (透明背景)
            square_img = Image.new('RGBA', size, (0, 0, 0, 0))
            
            # 小さいサイズほどアンチエイリアスを調整
            if size[0] <= 32:
                # 元画像を一度大きめにリサイズしてからシャープネスを上げる (小さいアイコン向け)
                temp_size = (size[0] * 3, size[1] * 3)
                temp_img = img.resize(temp_size, Image.LANCZOS)
                
                # シャープネスを上げる
                enhancer = ImageEnhance.Sharpness(temp_img)
                temp_img = enhancer.enhance(2.0)  # 小さいアイコンは特にシャープに
                
                # 最終サイズにリサイズ
                resized_img = temp_img.resize(size, Image.LANCZOS)
            else:
                # 大きめのアイコンは直接リサイズ
                resized_img = img.resize(size, Image.LANCZOS)
            
            # 中央に配置
            paste_x = (size[0] - resized_img.width) // 2
            paste_y = (size[1] - resized_img.height) // 2
            square_img.paste(resized_img, (paste_x, paste_y), resized_img)
            
            # 透明度をさらに確実にする
            r, g, b, a = square_img.split()
            square_img = Image.merge("RGBA", (r, g, b, a))
            
            icon_images.append(square_img)
        
        # 複数サイズを含むICOとして保存
        icon_images[0].save(icon_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in icon_images], quality=100)
        print(f"超高品質アプリケーションアイコンを作成しました: {icon_path}")
        
        return icon_path
    except Exception as e:
        print(f"アイコン作成エラー: {e}")
        return None

def set_taskbar_icon():
    """Windows10/11のタスクバーアイコンを設定"""
    try:
        # アプリケーションIDを設定（これがタスクバーアイコン関連付けの鍵）
        app_id = 'com.koemoji.app'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        
        # アイコンファイルも設定
        icon_path = find_app_icon()
        if icon_path and os.path.exists(icon_path):
            # WinAPIを使用してアイコンを設定
            try:
                import win32gui
                import win32con
                import win32api
                
                # アイコンをロード
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                h_icon = win32gui.LoadImage(
                    None, 
                    icon_path, 
                    win32con.IMAGE_ICON,
                    0, 0,
                    icon_flags
                )
                
                # アプリケーションアイコンを設定
                win32gui.SendMessage(
                    win32gui.GetForegroundWindow(), 
                    win32con.WM_SETICON, 
                    win32con.ICON_SMALL, 
                    h_icon
                )
                win32gui.SendMessage(
                    win32gui.GetForegroundWindow(),
                    win32con.WM_SETICON,
                    win32con.ICON_BIG,
                    h_icon
                )
                
                print("Windows APIを使用してアイコンを設定しました")
            except Exception as e:
                print(f"Windows APIでのアイコン設定エラー: {e}")
        
    except Exception as e:
        print(f"タスクバーアイコン設定エラー: {e}")

def main():
    """アプリケーションのメインエントリーポイント"""
    # 事前にアイコンを取得
    icon_path = find_app_icon()
    
    # 設定の読み込み
    config_manager = ConfigManager()
    
    # メインウィンドウの作成
    root = tk.Tk()
    
    # ウィンドウの設定
    root.title("コエモジ")
    root.geometry("950x800")  # 横幅を広げ、縦幅をさらに増加
    root.configure(bg=COLORS["bg_primary"])
    
    # ウィンドウを画面中央に配置
    # ウィンドウサイズを取得
    window_width = 950  # 横幅を広げる
    window_height = 800  # 縦幅をさらに増加
    # 画面サイズを取得
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # 中央の座標を計算
    center_x = int((screen_width - window_width) / 2)
    center_y = int((screen_height - window_height) / 2)
    # ウィンドウの位置を設定
    root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    
    # フォントサイズを調整
    font_size = 12
    
    # フォントの設定
    default_font = ("游ゴシック", font_size)
    root.option_add("*Font", default_font)
    
    print(f"フォントサイズ: 大 ({font_size}px)")
    
    # Windows固有のタスクバーアイコン設定
    set_taskbar_icon()
    
    # アプリケーションのアイコン設定（複数の方法を試みる）
    try:
        # 方法1: 生成済みのICOファイルを直接使用
        if icon_path and os.path.exists(icon_path):
            # iconbitmapメソッドを試す
            try:
                root.iconbitmap(icon_path)
                print(f"iconbitmapでアイコンを設定しました: {icon_path}")
            except Exception as e:
                print(f"iconbitmapエラー: {e}")
        
        # 方法2: Tkinterの標準的な方法
        logo_path = "resources/koemoji-logo-48x48 px.png"
        if os.path.exists(logo_path):
            try:
                icon_img = Image.open(logo_path)
                icon_photo = ImageTk.PhotoImage(icon_img)
                root.iconphoto(True, icon_photo)
                # サブウィンドウでアイコンを再利用するためにプロパティとして保存
                root.iconphoto_master = icon_photo
                print(f"iconphotoでアイコンを設定しました: {logo_path}")
            except Exception as e:
                print(f"iconphotoエラー: {e}")
                
                # ファイル名にスペースがある場合の代替処理
                try:
                    # 代替ロゴを使用
                    alt_logo_path = "resources/koemoji-logo256x256.png"
                    if os.path.exists(alt_logo_path):
                        icon_img = Image.open(alt_logo_path)
                        # 適切なサイズにリサイズ
                        icon_img = icon_img.resize((48, 48), Image.LANCZOS)
                        icon_photo = ImageTk.PhotoImage(icon_img)
                        root.iconphoto(True, icon_photo)
                        root.iconphoto_master = icon_photo
                        print(f"代替アイコンを設定しました: {alt_logo_path}")
                except Exception as e2:
                    print(f"代替ロゴの読み込みにも失敗しました: {e2}")
    except Exception as e:
        print(f"アイコンの読み込みに失敗しました: {e}")
    
    # メインアプリケーションの作成
    app = MainWindow(root, config_manager)
    
    # アプリケーションの実行
    root.mainloop()

if __name__ == "__main__":
    main()