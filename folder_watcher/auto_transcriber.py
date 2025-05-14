#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動文字起こしツール
フォルダ監視モジュールを使用して、指定フォルダに追加された音声・動画ファイルを自動的に文字起こしします。
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, Optional

# フォルダ監視モジュールをインポート
from folder_watcher import FolderWatcher

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_transcriber.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("auto_transcriber")

# 設定ファイルのパス
CONFIG_PATH = "auto_transcriber_config.json"

def load_config() -> Dict[str, Any]:
    """設定ファイルの読み込み"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            return config_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")
        # デフォルト設定を返す
        return {
            "input_directory": "",
            "output_directory": "",
            "supported_extensions": [
                ".mp3", ".mp4", ".wav", ".m4a", ".avi", ".mov", ".wmv", ".flac"
            ]
        }

def save_config(config: Dict[str, Any]):
    """設定ファイルの保存"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.info("設定を保存しました。")
    except Exception as e:
        logger.error(f"設定ファイルの保存エラー: {e}")

def transcribe_file(file_path: str) -> Optional[str]:
    """ファイルの文字起こし処理
    
    Args:
        file_path: 文字起こしするファイルパス
        
    Returns:
        str: 文字起こし結果、または失敗時はNone
    """
    try:
        config = load_config()
        output_dir = config.get("output_directory", "")
        
        # 出力ディレクトリがなければ作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # ここで実際の文字起こし処理を行う
        # 例: 既存の文字起こしツールのコマンドを実行する
        logger.info(f"文字起こし開始: {file_path}")
        
        # このサンプルでは実際の文字起こしは行わず、ダミーの結果を生成
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_transcript.txt")
        
        # テスト用のダミー出力
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"これは {file_path} の文字起こし結果のサンプルです。\n")
            f.write("実際のアプリケーションでは、ここに本物の文字起こし結果が入ります。\n")
        
        logger.info(f"文字起こし完了: {file_path} -> {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"文字起こし処理エラー: {e}")
        return None

def process_media_file(file_path: str):
    """メディアファイル処理関数（フォルダ監視のコールバック）
    
    Args:
        file_path: 処理するファイルパス
    """
    logger.info(f"メディアファイル処理開始: {file_path}")
    
    # ファイルの文字起こし処理
    output_path = transcribe_file(file_path)
    
    if output_path:
        # 処理成功したら、ファイルを処理済みとしてマーク
        watcher.mark_file_as_processed(file_path, {
            "output_file": output_path,
            "status": "success"
        })
        logger.info(f"処理成功: {file_path}")
    else:
        # 処理失敗した場合でも、再処理を防ぐためにマーク
        watcher.mark_file_as_processed(file_path, {
            "status": "failed"
        })
        logger.error(f"処理失敗: {file_path}")

def main():
    """メインエントリーポイント"""
    global watcher
    
    print("自動文字起こしツール")
    print("====================")
    
    # 設定の読み込み
    config = load_config()
    
    # 初回起動時の設定
    if not config.get("input_directory"):
        print("\n初期設定が必要です。")
        input_dir = input("監視するディレクトリのパスを入力してください: ")
        output_dir = input("文字起こし結果の出力先ディレクトリを入力してください: ")
        
        config["input_directory"] = input_dir
        config["output_directory"] = output_dir
        save_config(config)
    
    # フォルダ監視インスタンスの作成
    watcher_config = {
        "input_directory": config["input_directory"],
        "supported_extensions": config["supported_extensions"]
    }
    
    with open("folder_watcher_config.json", "w", encoding="utf-8") as f:
        json.dump(watcher_config, f, ensure_ascii=False, indent=4)
    
    watcher = FolderWatcher("folder_watcher_config.json")
    
    # コールバック関数の設定
    watcher.set_callback(process_media_file)
    
    try:
        print("\n自動文字起こしサービスを開始しています...")
        if watcher.start():
            print(f"サービスが正常に開始されました。")
            print(f"フォルダ {config['input_directory']} を監視中です。")
            print(f"対応ファイル形式: {', '.join(config['supported_extensions'])}")
            print("Ctrl+Cで終了できます。\n")
            
            # メインスレッドを維持
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n自動文字起こしサービスを停止しています...")
                watcher.stop()
                print("サービスが停止しました。")
        else:
            print("サービスの開始に失敗しました。ログを確認してください。")
    
    except Exception as e:
        logger.exception(f"予期しない例外が発生しました: {e}")
        print(f"エラーが発生しました: {e}")
        watcher.stop()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())