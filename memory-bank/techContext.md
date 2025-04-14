# コエモジ - 技術コンテキスト

## 技術スタック

### 1. コア言語とフレームワーク
- **Python 3.8+**: アプリケーションの基盤となるプログラミング言語
- **Tkinter**: GUIフレームワーク。Pythonに標準で付属しているため導入の手間が少ない
- **Pillow (PIL)**: 画像処理ライブラリ、アイコンやUIの視覚的要素の処理に使用

### 2. 文字起こしエンジン
- **OpenAI Whisper**: 音声認識と文字起こしのためのAIモデル
  - 複数のモデルサイズをサポート: tiny, base, small, medium, large
  - 多言語対応
- **PyTorch**: Whisperモデルの実行環境
  - GPU加速処理をサポート（CUDA対応）

### 3. メディア処理
- **FFmpeg**: 動画・音声ファイルの処理ライブラリ
  - 動画から音声の抽出
  - 音声ファイルのフォーマット変換
  - サンプリングレートの調整


### 4. ユーティリティ
- **threading**: 非同期処理のためのスレッド管理
- **json**: 設定データの保存と読み込み
- **os/sys**: ファイルシステム操作とシステム機能へのアクセス
- **datetime**: タイムスタンプ生成と時間フォーマット処理
- **tempfile**: 一時ファイルの管理
- **ctypes/win32gui**: Windowsシステムとの統合（タスクバーアイコンなど）

## 開発環境

### 1. 推奨開発環境
- **Python 3.8以上**: 基本開発環境
- **仮想環境**: venv または Anaconda/Miniconda
- **FFmpeg**: システムにインストールされていること

### 2. 外部依存関係
主要な依存パッケージは以下の通り（requirements.txtより）:
- torch
- numpy
- whisper
- pillow
- tqdm
- pywin32 (Windowsのみ)

## 技術的制約

### 1. 実行時の制約
- **FFmpeg同梱の対応**: アプリケーションディレクトリの`ffmpeg_bin`フォルダにFFmpegを同梱
- **メモリ使用量**: 特に大きなWhisperモデル使用時のメモリ消費
- **処理時間**: CPUのみの環境では処理時間が長くなる可能性がある
- **ディスク容量**: 一時ファイルと結果ファイルのためのディスク容量

### 2. 開発上の制約
- **Windows専用アプリケーション**: 現在はWindows環境に特化した開発方針を採用
- **Whisperモデルのダウンロード**: 初回実行時に自動ダウンロードが必要
- **UI設計の制限**: Tkinterの基本的な制約（高度なアニメーションやエフェクトの制限など）
- **バッチファイルの言語**: すべてのバッチファイル（.bat）は英語で作成する必要がある。配布ドキュメントは日本語だが、スクリプトは英語であること

## ツール使用パターン

### 1. FFmpegの使用パターン
```python
# FFmpegの検出と使用
def find_ffmpeg():
    """FFmpegの実行ファイルのパスを検索"""
    # アプリケーションディレクトリ内のffmpeg_binフォルダを確認
    app_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir_ffmpeg = os.path.join(app_dir, "ffmpeg_bin", "ffmpeg.exe")
    if os.path.exists(bin_dir_ffmpeg):
        return bin_dir_ffmpeg
    
    # PATHから検索
    try:
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
    except Exception:
        pass
    
    # デフォルトのコマンド名を返す
    return "ffmpeg"

# FFmpegの実行
subprocess.run(
    [FFMPEG_PATH, "-i", video_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-y", audio_path],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
```

### 2. Whisperモデルの使用パターン
```python
# モデルのロード
self.model = whisper.load_model(self.model_name, device=self.device)

# 文字起こし実行
options = {}
if self.language:
    options["language"] = self.language
result = self.model.transcribe(audio_path, **options)
```

### 3. バックグラウンド処理パターン
```python
# 処理スレッドの起動
thread = threading.Thread(
    target=self._process_files,
    args=(self.files.copy(), model, language, output_dir)
)
thread.daemon = True
thread.start()
```

### 4. UIアップデートパターン
```python
# UIの安全な更新（スレッド間通信）
self.root.after(0, lambda: self._update_progress_gui(status, progress))
```

### 5. 設定の保存と読み込みパターン
```python
# 設定の読み込み
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 設定の保存
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(self.config, f, ensure_ascii=False, indent=4)
```

## パフォーマンス最適化

### 1. GPU高速化
- CUDA対応GPUを自動検出し、利用可能な場合はGPU処理を有効化
```python
self.device = "cuda" if torch.cuda.is_available() else "cpu"
```

### 2. メモリ使用量の最適化
- 処理完了後の一時ファイルの削除
- 適切なモデルサイズの選択オプション（小さいモデルは少ないメモリで動作）

### 3. マルチスレッド
- UIスレッドとは別のスレッドでの処理実行
- 進捗状況の非同期更新

## セキュリティ考慮事項

### 1. ファイル操作の安全性
- 一時ディレクトリの適切な使用
- ファイル名の安全な処理（無効な文字の削除）
```python
safe_name = "".join([c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in base_name])
```

### 2. エラーハンドリング
- 外部プロセス実行時の例外処理
- ファイルI/O操作での例外キャッチ

### 3. ユーザーデータの保護
- 設定やファイルパスなどの個人情報の適切な管理
- ローカルでの処理によるプライバシー保護（データがサーバーに送信されない）
