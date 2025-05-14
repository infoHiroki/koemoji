# フォルダ監視モジュール

このモジュールは、特定のフォルダを監視し、新しいファイルが追加されたときに指定のコールバック関数を実行するシステムです。元々は音声・動画ファイルの自動文字起こしシステムの一部として開発されましたが、汎用的なフォルダ監視機能として分離されました。

## 機能

- 指定フォルダの監視
- 特定の拡張子を持つファイルの検出
- 新しいファイルに対する処理のキュー管理
- 処理済みファイルの管理と重複処理の防止
- カスタムコールバック関数による柔軟な処理

## ファイル構成

- `folder_watcher.py` - フォルダ監視の中核モジュール
- `auto_transcriber.py` - 使用例（自動文字起こしアプリケーション）
- `auto_transcriber_config.json` - 設定ファイル

## 使い方

### フォルダ監視モジュールの基本的な使い方

```python
from folder_watcher import FolderWatcher

# 処理関数の定義
def process_file(file_path):
    print(f"ファイル {file_path} を処理します...")
    # ここで実際のファイル処理を行う
    
    # 処理が終わったらファイルを処理済みとしてマーク
    watcher.mark_file_as_processed(file_path, {"result": "success"})

# フォルダ監視インスタンスの作成
watcher = FolderWatcher()

# 入力ディレクトリの設定
watcher.set_input_directory("/path/to/watch")

# コールバック関数の設定
watcher.set_callback(process_file)

# 監視開始
watcher.start()

try:
    # メインスレッドを維持
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # 監視終了
    watcher.stop()
```

### 自動文字起こしツールとしての使用例

自動文字起こしのサンプルアプリケーションも用意されています。このアプリケーションは、指定されたフォルダに追加された音声・動画ファイルを自動的に文字起こしします。

実行方法:
```
python auto_transcriber.py
```

初回実行時に入力・出力ディレクトリの設定が求められます。

## 独自アプリケーションへの統合方法

1. `folder_watcher.py`をプロジェクトにインポートします
2. コールバック関数を設定して、あなたのアプリケーションの処理を実行します
3. 必要に応じて設定ファイルをカスタマイズします

## 要件

- Python 3.6以上
- watchdogパッケージ

インストール:
```
pip install watchdog
```