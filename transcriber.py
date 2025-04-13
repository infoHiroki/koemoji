#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文字起こし処理モジュール
動画ファイルから音声を抽出し、Whisperモデルを使用して文字起こしを行う
また、音声ファイルから直接文字起こしを行う機能も提供する
"""

import os
import tempfile
import subprocess
import sys
import datetime

# Whisperモジュールのパスを追加
whisper_path = os.path.join(os.path.dirname(__file__), "whisper-main")
if whisper_path not in sys.path:
    sys.path.insert(0, whisper_path)

# FFmpegのパスを取得
def find_ffmpeg():
    """FFmpegの実行ファイルのパスを検索"""
    # アプリケーションディレクトリ内のffmpeg_binフォルダを確認
    app_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir_ffmpeg = os.path.join(app_dir, "ffmpeg_bin", "ffmpeg.exe")
    if os.path.exists(bin_dir_ffmpeg):
        print(f"同梱のFFmpegを使用します: {bin_dir_ffmpeg}")
        return bin_dir_ffmpeg
    
    # PATHから検索
    try:
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"システムのFFmpegを使用します: {ffmpeg_path}")
            return ffmpeg_path
    except Exception as e:
        print(f"FFmpeg検索エラー: {e}")
    
    # デフォルトのコマンド名を返す
    print("FFmpegが見つからないため、デフォルトのコマンド名を使用します")
    return "ffmpeg"

# FFmpegの絶対パスを指定
FFMPEG_PATH = find_ffmpeg()

import whisper
import torch
from tqdm import tqdm

class BaseTranscriber:
    """文字起こしの基本クラス"""
    
    def __init__(self, model_name="small", language=None, callback=None):
        """
        初期化
        
        Args:
            model_name (str): Whisperモデル名 (tiny, base, small, medium, large)
            language (str, optional): 言語コード (None=自動検出)
            callback (function, optional): 進捗報告用コールバック関数
        """
        self.model_name = model_name
        self.language = language
        self.callback = callback
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        """Whisperモデルをロード"""
        if self.callback:
            self.callback(status="モデルをロード中...", progress=0)
        
        try:
            self.model = whisper.load_model(self.model_name, device=self.device)
            
            if self.callback:
                self.callback(status="モデルのロード完了", progress=10)
        except Exception as e:
            raise Exception(f"モデルのロードに失敗しました: {e}")
    
    def transcribe_audio(self, audio_path):
        """
        音声ファイルを文字起こし
        
        Args:
            audio_path (str): 音声ファイルのパス
            
        Returns:
            dict: 文字起こし結果
        """
        if self.callback:
            self.callback(status=f"文字起こし中: {os.path.basename(audio_path)}", progress=40)
        
        # モデルがロードされていない場合はロード
        if self.model is None:
            self.load_model()
        
        # 文字起こしオプション
        options = {
            "verbose": False,  # 詳細出力を無効化（必要に応じて変更）
            "word_timestamps": False,  # 単語単位のタイムスタンプは必要ない（処理速度向上のため）
            "task": "transcribe",  # 文字起こしタスク
        }
        
        # 言語設定がある場合は追加
        if self.language:
            options["language"] = self.language
        
        try:
            # 文字起こし実行
            result = self.model.transcribe(audio_path, **options)
            
            # デバッグ情報：segmentsキーが存在するか確認
            if "segments" in result and result["segments"]:
                print(f"[INFO] Segments found: {len(result['segments'])} segments")
            else:
                print("[WARNING] No segments found in transcription result")
            
            if self.callback:
                self.callback(status="文字起こし完了", progress=90)
                
            return result
        except Exception as e:
            raise Exception(f"文字起こしに失敗しました: {e}")

class VideoTranscriber(BaseTranscriber):
    """動画ファイルから文字起こしを行うクラス"""
    
    def extract_audio(self, video_path):
        """
        動画ファイルから音声を抽出
        
        Args:
            video_path (str): 動画ファイルのパス
            
        Returns:
            str: 抽出した音声ファイルのパス
        """
        if self.callback:
            self.callback(status=f"音声を抽出中: {os.path.basename(video_path)}", progress=20)
        
        # 一時ファイルを作成
        temp_dir = tempfile.gettempdir()
        # ファイル名から無効な文字を削除し、安全なファイル名を生成
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        # 無効な文字を置換
        safe_name = "".join([c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in base_name])
        # 一意のファイル名を生成するために現在時刻を追加
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        audio_path = os.path.join(temp_dir, f"{safe_name}_{timestamp}.wav")
        
        # FFmpegを使用して音声を抽出
        try:
            # FFmpegコマンドを実行
            subprocess.run(
                [FFMPEG_PATH, "-i", video_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-y", audio_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"音声抽出に失敗しました: {e}")
        except FileNotFoundError:
            raise Exception("FFmpegが見つかりません。FFmpegをインストールして環境変数に追加してください。")
        
        if self.callback:
            self.callback(status="音声抽出完了", progress=30)
            
        return audio_path
    
    def process_video(self, video_path):
        """
        動画ファイルを処理して文字起こしを行う
        
        Args:
            video_path (str): 動画ファイルのパス
            
        Returns:
            dict: 文字起こし結果
        """
        try:
            # 音声抽出
            audio_path = self.extract_audio(video_path)
            
            # 文字起こし
            result = self.transcribe_audio(audio_path)
            
            # 一時ファイルを削除
            try:
                os.remove(audio_path)
            except:
                pass
            
            if self.callback:
                self.callback(status="処理完了", progress=100)
                
            return result
            
        except Exception as e:
            if self.callback:
                self.callback(status=f"エラー: {str(e)}", progress=-1)
            raise

class AudioTranscriber(BaseTranscriber):
    """音声ファイルから直接文字起こしを行うクラス"""
    
    def preprocess_audio(self, audio_path):
        """
        音声ファイルを前処理（必要に応じてフォーマット変換）
        
        Args:
            audio_path (str): 音声ファイルのパス
            
        Returns:
            str: 処理済み音声ファイルのパス
        """
        if self.callback:
            self.callback(status=f"音声ファイルを処理中: {os.path.basename(audio_path)}", progress=20)
        
        # 一時ファイルを作成
        temp_dir = tempfile.gettempdir()
        # ファイル名から無効な文字を削除し、安全なファイル名を生成
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        # 無効な文字を置換
        safe_name = "".join([c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in base_name])
        # 一意のファイル名を生成するために現在時刻を追加
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        processed_audio_path = os.path.join(temp_dir, f"{safe_name}_{timestamp}.wav")
        
        # FFmpegを使用して音声を変換（サンプリングレートとチャンネル数を調整）
        try:
            # FFmpegコマンドを実行
            subprocess.run(
                [FFMPEG_PATH, "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-y", processed_audio_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"音声処理に失敗しました: {e}")
        except FileNotFoundError:
            raise Exception("FFmpegが見つかりません。FFmpegをインストールして環境変数に追加してください。")
        
        if self.callback:
            self.callback(status="音声処理完了", progress=30)
            
        return processed_audio_path
    
    def process_audio(self, audio_path):
        """
        音声ファイルを処理して文字起こしを行う
        
        Args:
            audio_path (str): 音声ファイルのパス
            
        Returns:
            dict: 文字起こし結果
        """
        try:
            # 音声前処理
            processed_audio_path = self.preprocess_audio(audio_path)
            
            # 文字起こし
            result = self.transcribe_audio(processed_audio_path)
            
            # 一時ファイルを削除
            try:
                os.remove(processed_audio_path)
            except:
                pass
            
            if self.callback:
                self.callback(status="処理完了", progress=100)
                
            return result
            
        except Exception as e:
            if self.callback:
                self.callback(status=f"エラー: {str(e)}", progress=-1)
            raise