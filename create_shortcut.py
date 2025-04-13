#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
デスクトップにショートカットを作成するスクリプト
"""

import os
import sys
import winshell
from win32com.client import Dispatch

def create_ico_from_png(png_path, ico_path):
    """PNGファイルからICOファイルを作成"""
    try:
        from PIL import Image, ImageEnhance
        img = Image.open(png_path)
        
        # 背景が透明でない場合は透明な背景を作成
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # コントラストとシャープネスを上げて鮮明にする
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
        icon_images[0].save(ico_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in icon_images], quality=100)
        print(f"超高品質ICOファイルを作成しました: {ico_path}")
        return True
    except Exception as e:
        print(f"ICOファイル作成エラー: {e}")
        return False

def create_shortcut():
    """デスクトップにショートカットを作成"""
    # 現在のディレクトリ
    current_dir = os.path.abspath(os.path.dirname(__file__))
    # VBScriptファイルのパス
    vbs_path = os.path.join(current_dir, "run_hidden.vbs")
    
    if not os.path.exists(vbs_path):
        print(f"エラー: {vbs_path} が見つかりません。")
        return False
    
    # デスクトップのパス
    desktop = winshell.desktop()
    
    # ショートカットの作成
    shortcut_path = os.path.join(desktop, "コエモジ.lnk")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = vbs_path
    shortcut.WorkingDirectory = current_dir
    shortcut.Description = "音声・動画の文字起こしアプリ"
    
    # アイコンの設定（ロゴファイルからICOを生成）
    logo_path = os.path.join(current_dir, "resources", "koemoji-infinity-logo.png")
    icon_path = os.path.join(current_dir, "resources", "icon.ico")
    
    if os.path.exists(logo_path):
        # PNGファイルからICOファイルを作成
        if create_ico_from_png(logo_path, icon_path):
            shortcut.IconLocation = icon_path
        else:
            # 直接PNGファイルを使用（一部環境では動作しない可能性あり）
            shortcut.IconLocation = logo_path
    else:
        # 代替のロゴファイルを試す
        alt_logo_path = os.path.join(current_dir, "resources", "koemoji-infinity-logo-48x48 px.png")
        if os.path.exists(alt_logo_path):
            # 代替PNGからICOを作成
            if create_ico_from_png(alt_logo_path, icon_path):
                shortcut.IconLocation = icon_path
            else:
                shortcut.IconLocation = alt_logo_path
    
    shortcut.save()
    
    print(f"ショートカットを作成しました: {shortcut_path}")
    return True

if __name__ == "__main__":
    try:
        # 必要なライブラリが入っているか確認
        import win32com
        import winshell
        
        # PILがインストールされているか確認（アイコン変換用）
        try:
            from PIL import Image
        except ImportError:
            print("PIL/Pillowをインストールしています...")
            os.system("pip install pillow")
            print("インストール完了。")
            
    except ImportError:
        print("必要なライブラリをインストールしています...")
        os.system("pip install pywin32 winshell pillow")
        print("インストール完了。再度スクリプトを実行してください。")
        sys.exit(0)
    
    result = create_shortcut()
    if result:
        print("ショートカットの作成に成功しました。")
    else:
        print("ショートカットの作成に失敗しました。")
    
    input("Enterキーを押すと終了します...") 