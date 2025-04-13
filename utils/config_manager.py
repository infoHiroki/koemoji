#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
設定管理モジュール
アプリケーションの設定を管理する
"""

import os
import json
import datetime
import logging

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_file="config.json"):
        """
        初期化
        
        Args:
            config_file (str): 設定ファイルのパス
        """
        # 設定ファイルのパスを絶対パスに変換
        if not os.path.isabs(config_file):
            # 相対パスの場合は、現在の作業ディレクトリからの絶対パスに変換
            config_file = os.path.abspath(config_file)
        
        self.config_file = config_file
        logger.debug(f"設定ファイルのパス: {self.config_file}")
        self.config = self._load_config()
        
    def _load_config(self):
        """
        設定ファイルを読み込む
        
        Returns:
            dict: 設定データ
        """
        # デフォルト設定
        default_config = {
            "model": "tiny",
            "language": "ja",  # 日本語
            "output_format": "txt",
            "history": [],
            "font_size": "標準",
            "output_directory": os.path.join(os.path.expanduser("~/Desktop"), "コエモジ_文字起こし結果")
        }
        
        # 設定ファイルのパスを確認
        config_path = os.path.abspath(self.config_file)
        logger.debug(f"設定ファイルを読み込んでいます: {config_path}")
        
        # 設定ファイルが存在する場合は読み込む
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    logger.debug("設定ファイルを読み込みました")
                    
                    # デフォルト設定とマージ
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    
                    return config
            except Exception as e:
                logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 読み込みに失敗した場合はデフォルト設定を使用
                logger.info("デフォルト設定を使用します")
        else:
            logger.info("設定ファイルが存在しません。デフォルト設定を使用します")
        
        # 設定ファイルが存在しない場合はデフォルト設定を使用
        return default_config
    
    def get_config(self):
        """
        設定全体を取得
        
        Returns:
            dict: 設定データ
        """
        return self.config
    
    def save_config(self):
        """設定ファイルを保存"""
        try:
            # 設定ファイルのパスを確認
            config_path = os.path.abspath(self.config_file)
            logger.debug(f"設定を保存しています: {config_path}")
            
            # ディレクトリが存在することを確認
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 設定ファイルを保存
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            logger.debug("設定の保存に成功しました")
            return True
        except Exception as e:
            logger.error(f"設定の保存に失敗しました: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_model(self):
        """
        モデル名を取得
        
        Returns:
            str: モデル名
        """
        return self.config.get("model", "tiny")
    
    def set_model(self, model):
        """
        モデル名を設定
        
        Args:
            model (str): モデル名
        """
        self.config["model"] = model
        self.save_config()
    
    def get_language(self):
        """
        言語設定を取得
        
        Returns:
            str: 言語コード (None=自動検出)
        """
        language = self.config.get("language", "ja")
        
        # 有効な言語コードのリスト
        valid_codes = ["", "ja", "en", "zh", "ko", "es", "fr", "de", "it", "pt", "ru"]
        
        # もし言語が有効なコードでなければ、"ja"を返す
        if language not in valid_codes:
            # 逆変換を試みる（"日本語" → "ja"）
            lang_mapping = {
                "日本語": "ja", "英語": "en", "中国語": "zh", "韓国語": "ko",
                "スペイン語": "es", "フランス語": "fr", "ドイツ語": "de",
                "イタリア語": "it", "ポルトガル語": "pt", "ロシア語": "ru",
                "自動検出": ""
            }
            language = lang_mapping.get(language, "ja")
        
        return language
    
    def set_language(self, language):
        """
        言語設定を設定
        
        Args:
            language (str): 言語コード (None=自動検出)
        """
        self.config["language"] = language
        self.save_config()
    
    def get_output_format(self):
        """
        出力形式を取得
        
        Returns:
            str: 出力形式
        """
        return self.config.get("output_format", "txt")
    
    def set_output_format(self, output_format):
        """
        出力形式を設定
        
        Args:
            output_format (str): 出力形式
        """
        self.config["output_format"] = output_format
        self.save_config()
    
    def get_output_directory(self):
        """
        出力ディレクトリを取得
        
        Returns:
            str: 出力ディレクトリのパス
        """
        output_dir = self.config.get("output_directory", os.path.join(os.path.expanduser("~/Desktop"), "コエモジ_文字起こし結果"))
        
        # ディレクトリが存在しない場合は作成
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception:
                # 作成に失敗した場合はカレントディレクトリを使用
                output_dir = "."
        
        return output_dir
    
    def set_output_directory(self, output_directory):
        """
        出力ディレクトリを設定
        
        Args:
            output_directory (str): 出力ディレクトリのパス
        """
        self.config["output_directory"] = output_directory
        self.save_config()
    
    def add_to_history(self, file_path, output_path):
        """
        履歴に追加
        
        Args:
            file_path (str): 処理したファイルのパス
            output_path (str): 出力ファイルのパス
        """
        history = self.config.get("history", [])
        
        # 履歴エントリを作成
        entry = {
            "file": file_path,
            "output": output_path,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # 履歴に追加
        history.append(entry)
        
        # 履歴が長すぎる場合は古いものを削除
        if len(history) > 100:
            history = history[-100:]
        
        self.config["history"] = history
        self.save_config()
    
    def get_history(self):
        """
        履歴を取得
        
        Returns:
            list: 履歴リスト
        """
        return self.config.get("history", [])
    
    def get_font_size(self):
        """
        フォントサイズを取得
        
        Returns:
            str: フォントサイズ設定 ("小", "標準", "大", "特大")
        """
        return self.config.get("font_size", "標準")
    
    def set_font_size(self, font_size):
        """
        フォントサイズを設定
        
        Args:
            font_size (str): フォントサイズ設定 ("小", "標準", "大", "特大")
        """
        self.config["font_size"] = font_size
        self.save_config()

    def update_config(self, new_config):
        """
        複数の設定を一括で更新
        
        Args:
            new_config (dict): 更新する設定のディクショナリ
        """
        # 既存の設定を更新
        for key, value in new_config.items():
            self.config[key] = value
        
        # 設定を保存
        self.save_config() 