#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
フォルダ監視モジュール
指定されたフォルダを監視し、新しいファイルが追加されたときにコールバック関数を実行します。
"""

import os
import time
import logging
import threading
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set
import queue

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
except ImportError:
    print("エラー: watchdogモジュールがインストールされていません。")
    print("pip install watchdog を実行してインストールしてください。")
    exit(1)

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("folder_watcher.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("folder_watcher")


class MediaFileHandler(FileSystemEventHandler):
    """監視フォルダ内のファイル作成イベントを処理するクラス"""
    
    def __init__(self, supported_extensions: List[str], file_queue: queue.Queue, processed_files: Set[str]):
        """初期化
        
        Args:
            supported_extensions: 監視対象のファイル拡張子リスト
            file_queue: 処理待ちファイルキュー
            processed_files: 処理済みファイルのセット
        """
        self.supported_extensions = supported_extensions
        self.file_queue = file_queue
        self.processed_files = processed_files
    
    def on_created(self, event):
        """ファイル作成イベントの処理"""
        if not event.is_directory:
            file_path = event.src_path
            ext = os.path.splitext(file_path)[-1].lower()
            
            if ext in self.supported_extensions:
                logger.info(f"新しいメディアファイルを検出: {file_path}")
                
                # ファイルのアクセスが可能になるまで少し待機（他プロセスによる書き込み完了待ち）
                time.sleep(1)
                
                # 処理済みかどうかをチェック
                file_hash = get_file_hash(file_path)
                if file_path in self.processed_files or file_hash in self.processed_files:
                    logger.info(f"ファイルは既に処理済みです: {file_path}")
                    return
                
                self.file_queue.put(file_path)


class FolderWatcher:
    """フォルダ監視クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初期化
        
        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルト設定を使用）
        """
        self.config_path = config_path or "folder_watcher_config.json"
        self.config = self.load_config()
        
        self.file_queue = queue.Queue()
        self.processed_files = set()
        self.observer = None
        self.processing_thread = None
        self.should_stop = False
        self.callback_function = None
    
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return config_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")
            # デフォルト設定を返す
            return {
                "input_directory": "",
                "supported_extensions": [
                    ".mp3", ".mp4", ".wav", ".m4a", ".avi", ".mov", ".wmv", ".flac"
                ],
                "processed_files": {}
            }
    
    def save_config(self):
        """設定ファイルの保存"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info("設定を保存しました。")
        except Exception as e:
            logger.error(f"設定ファイルの保存エラー: {e}")
    
    def mark_file_as_processed(self, file_path: str, result_info: Optional[Dict[str, Any]] = None):
        """ファイルを処理済みとしてマーク
        
        Args:
            file_path: 処理済みとしてマークするファイルパス
            result_info: 処理結果情報（省略可）
        """
        # ファイルハッシュを計算
        file_hash = get_file_hash(file_path)
        
        # 処理情報を記録
        processed_info = {
            "processed_at": datetime.now().isoformat(),
        }
        
        # 結果情報があれば追加
        if result_info:
            processed_info.update(result_info)
        
        # 設定ファイルに追加
        if "processed_files" not in self.config:
            self.config["processed_files"] = {}
        
        # ハッシュ値をキーとして保存
        self.config["processed_files"][file_hash] = processed_info
        self.processed_files.add(file_hash)
        
        # 設定を保存
        self.save_config()
        logger.info(f"ファイルを処理済みリストに追加しました: {file_path}")
    
    def set_callback(self, callback_function: Callable[[str], None]):
        """コールバック関数を設定
        
        Args:
            callback_function: ファイルパスを引数に取るコールバック関数
        """
        self.callback_function = callback_function
    
    def process_file_queue(self):
        """ファイルキューを処理"""
        logger.info("ファイル処理スレッドを開始しました。")
        
        while not self.should_stop:
            try:
                # キューからファイルを取得（タイムアウト付き）
                try:
                    file_path = self.file_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 処理済みかどうかの再チェック
                file_hash = get_file_hash(file_path)
                if file_path in self.processed_files or file_hash in self.processed_files:
                    logger.info(f"ファイルは既に処理済みです（キュー内再チェック）: {file_path}")
                    self.file_queue.task_done()
                    continue
                
                # コールバック関数を実行
                if self.callback_function:
                    try:
                        logger.info(f"ファイル処理開始: {file_path}")
                        self.callback_function(file_path)
                        # 注意: コールバック関数の中で mark_file_as_processed を呼び出すことを推奨
                    except Exception as e:
                        logger.error(f"コールバック関数の実行中にエラーが発生しました: {e}")
                else:
                    # コールバック関数が設定されていない場合は自動的に処理済みとしてマーク
                    self.mark_file_as_processed(file_path)
                
                # キューのタスク完了を通知
                self.file_queue.task_done()
            
            except Exception as e:
                logger.exception(f"ファイル処理中に例外が発生しました: {e}")
                try:
                    self.file_queue.task_done()
                except:
                    pass
        
        logger.info("ファイル処理スレッドを終了しました。")
    
    def start_file_watcher(self) -> bool:
        """ファイル監視を開始
        
        Returns:
            bool: 監視開始に成功したかどうか
        """
        input_dir = self.config.get("input_directory", "")
        
        if not input_dir:
            logger.error("入力ディレクトリが設定されていません。")
            return False
        
        if not os.path.exists(input_dir):
            try:
                os.makedirs(input_dir, exist_ok=True)
                logger.info(f"入力ディレクトリを作成しました: {input_dir}")
            except Exception as e:
                logger.error(f"入力ディレクトリの作成に失敗しました: {e}")
                return False
        
        try:
            supported_extensions = self.config.get("supported_extensions", [])
            # 処理済みファイルのセットを更新
            self.processed_files = set(self.config.get("processed_files", {}).keys())
            
            event_handler = MediaFileHandler(supported_extensions, self.file_queue, self.processed_files)
            self.observer = Observer()
            self.observer.schedule(event_handler, input_dir, recursive=False)
            self.observer.start()
            logger.info(f"ディレクトリ監視を開始しました: {input_dir}")
            return True
        
        except Exception as e:
            logger.error(f"ファイル監視の開始に失敗しました: {e}")
            return False
    
    def check_existing_files(self):
        """監視ディレクトリ内の既存ファイルを確認しキューに追加"""
        input_dir = self.config.get("input_directory", "")
        if not input_dir or not os.path.exists(input_dir):
            return
        
        extensions = self.config.get("supported_extensions", [])
        count = 0
        processed_count = 0
        
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[-1].lower()
                if ext in extensions:
                    # 処理済みかどうかチェック
                    file_hash = get_file_hash(file_path)
                    if file_path in self.processed_files or file_hash in self.processed_files:
                        processed_count += 1
                        continue
                        
                    self.file_queue.put(file_path)
                    count += 1
        
        if count > 0:
            logger.info(f"ディレクトリ内の未処理メディアファイル {count}個 をキューに追加しました。")
        if processed_count > 0:
            logger.info(f"ディレクトリ内の処理済みメディアファイル {processed_count}個 をスキップしました。")
    
    def clean_old_processed_files(self, max_entries: int = 1000):
        """古い処理済みファイル情報をクリーンアップ
        
        Args:
            max_entries: 保持する最大エントリ数
        """
        processed_files = self.config.get("processed_files", {})
        if not processed_files:
            return
        
        # エントリ数が上限を超えている場合にクリーンアップ
        if len(processed_files) > max_entries:
            logger.info(f"処理済みファイルリストのクリーンアップを実行します (現在: {len(processed_files)} エントリ)")
            
            # 日付でソート
            sorted_entries = sorted(
                processed_files.items(),
                key=lambda x: x[1].get("processed_at", ""),
                reverse=True
            )
            
            # 上限数まで削減
            self.config["processed_files"] = dict(sorted_entries[:max_entries])
            self.save_config()
            
            # 処理済みファイルセットを更新
            self.processed_files = set(self.config.get("processed_files", {}).keys())
            
            logger.info(f"処理済みファイルリストを {len(processed_files)} から {len(self.config['processed_files'])} エントリに削減しました")
    
    def start(self) -> bool:
        """監視サービスの開始
        
        Returns:
            bool: 監視開始に成功したかどうか
        """
        # 処理済みファイルリストのクリーンアップ
        self.clean_old_processed_files()
        
        # ファイル処理スレッドの開始
        self.should_stop = False
        self.processing_thread = threading.Thread(target=self.process_file_queue, daemon=True)
        self.processing_thread.start()
        
        # ファイル監視の開始
        if not self.start_file_watcher():
            self.stop()
            return False
        
        # 既存ファイルのチェック
        self.check_existing_files()
        
        logger.info("🚀 フォルダ監視サービスが開始されました。")
        return True
    
    def stop(self):
        """監視サービスの停止"""
        # 停止フラグの設定
        self.should_stop = True
        
        # ファイル監視の停止
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        # 処理スレッドの待機
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
            self.processing_thread = None
        
        logger.info("🛑 フォルダ監視サービスが停止されました。")
    
    def set_input_directory(self, directory: str) -> bool:
        """入力ディレクトリの設定
        
        Args:
            directory: 設定する入力ディレクトリパス
            
        Returns:
            bool: 設定に成功したかどうか
        """
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                logger.error(f"入力ディレクトリの作成に失敗しました: {e}")
                return False
        
        self.config["input_directory"] = directory
        self.save_config()
        logger.info(f"入力ディレクトリを設定しました: {directory}")
        return True
    
    def set_supported_extensions(self, extensions: List[str]):
        """監視対象のファイル拡張子を設定
        
        Args:
            extensions: 拡張子のリスト
        """
        self.config["supported_extensions"] = extensions
        self.save_config()
        logger.info(f"対応ファイル拡張子を設定しました: {extensions}")


def get_file_hash(file_path: str) -> str:
    """ファイルのハッシュ値を計算（ファイルサイズとパスの組み合わせ）
    
    Args:
        file_path: ハッシュを生成するファイルパス
        
    Returns:
        str: 生成されたハッシュ値
    """
    # 高速化のためにファイルサイズとパスの組み合わせをハッシュ
    try:
        file_size = os.path.getsize(file_path)
        hash_input = f"{file_path}:{file_size}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    except Exception as e:
        logger.error(f"ファイルハッシュ計算エラー: {e}")
        # エラーが発生した場合はパスのみからハッシュを生成
        return hashlib.md5(file_path.encode()).hexdigest()


# 使用サンプル
if __name__ == "__main__":
    def process_file(file_path: str):
        """サンプルの処理関数"""
        print(f"ファイル {file_path} を処理します...")
        # ここで実際のファイル処理を行う
        
        # 処理が終わったらファイルを処理済みとしてマーク
        watcher.mark_file_as_processed(file_path, {"result": "success"})
    
    # フォルダ監視インスタンスの作成
    watcher = FolderWatcher()
    
    # 入力ディレクトリの設定
    input_dir = input("監視するディレクトリパスを入力してください: ")
    watcher.set_input_directory(input_dir)
    
    # コールバック関数の設定
    watcher.set_callback(process_file)
    
    # 監視開始
    if watcher.start():
        print("フォルダ監視を開始しました。Ctrl+Cで終了できます。")
        
        try:
            # メインスレッドを維持
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nフォルダ監視を停止しています...")
            watcher.stop()
            print("監視を停止しました。")