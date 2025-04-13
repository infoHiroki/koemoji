# コエモジ セットアップガイド（開発・セットアップ担当者向け）

このガイドは、「コエモジ」アプリケーションをWindows環境でセットアップするための手順を説明します。
現在、本アプリケーションはWindows環境でのみ動作確認を行っており、インストーラーは未実装です。

## 目次

1. [開発状況](#開発状況)
2. [システム要件](#システム要件)
3. [セットアップ手順](#セットアップ手順)
4. [実行と設定](#実行と設定)
5. [配布準備](#配布準備)
6. [トラブルシューティング](#トラブルシューティング)

## 開発状況

- **動作確認環境**: Windows 10/11のみ
- **開発状態**: アルファ版（基本機能実装済み）
- **配布形態**: 現状はソースコードのみ（インストーラー未実装）
- **PyInstaller**: spec ファイルは準備済み（ビルド未実施）

## システム要件

### 開発・テスト環境
- **OS**: Windows 10/11
- **Python**: 3.8以上
- **FFmpeg**: 最新版
- **GPU**: NVIDIA CUDA対応（推奨だが必須ではない）

### エンドユーザー環境（想定）
- **OS**: Windows 10/11
- **CPU**: Intel Core i5/AMD Ryzen 5以上
- **メモリ**: 8GB RAM以上
- **ストレージ**: 2GB以上の空き容量
- **インターネット接続**: Whisperモデルのダウンロードに必要

## セットアップ手順

### 1. 開発環境の準備

#### Pythonのインストール
1. [Python公式サイト](https://www.python.org/downloads/windows/)から Python 3.8以上をダウンロード
2. インストール時に「Add Python to PATH」オプションを有効化
3. インストール完了後、コマンドプロンプトで確認:
   ```
   python --version
   ```

#### Gitのインストール（オプション）
1. [Gitの公式サイト](https://git-scm.com/download/win)からインストーラーをダウンロード
2. デフォルト設定でインストール
3. インストール完了後、確認:
   ```
   git --version
   ```

#### FFmpegのインストール
1. [FFmpegの公式サイト](https://ffmpeg.org/download.html)から「Windows Builds」をダウンロード
2. ダウンロードしたZIPファイルを解凍（例: `C:\ffmpeg`）
3. 環境変数PATHにFFmpegのbinディレクトリを追加:
   - システムのプロパティ → 詳細設定 → 環境変数
   - システム環境変数の「Path」を選択し「編集」
   - 「新規」をクリックし、FFmpegのbinディレクトリのパスを追加（例: `C:\ffmpeg\bin`）
4. コマンドプロンプトで確認:
   ```
   ffmpeg -version
   ```

### 2. コエモジ∞のセットアップ

#### ソースコードの取得
**方法1: Gitを使用**
```
git clone https://github.com/yourusername/koemoji-infinity.git
cd koemoji-infinity
```

**方法2: ZIPファイルをダウンロード**
1. GitHubリポジトリから最新のZIPファイルをダウンロード
2. 適切な場所に解凍（例: `C:\Users\Username\Documents\koemoji-infinity`）
3. コマンドプロンプトで解凍したディレクトリに移動

#### 依存パッケージのインストール
解凍またはクローンしたディレクトリで以下のコマンドを実行:
```
pip install -r requirements.txt
```

CUDA対応GPUを使用する場合、PyTorchのCUDAバージョンをインストール:
```
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
※ CUDAのバージョンは環境に合わせて調整（cu116, cu117, cu118など）

#### 動作確認
基本的な動作確認:
```
python main.py
```

## 実行と設定

### 実行方法

#### 開発者モード
コマンドプロンプトでアプリケーションディレクトリから:
```
python main.py
```

#### ユーザーモード
1. `run_app.bat`をダブルクリック
2. または`create_shortcut.py`を実行してデスクトップショートカットを作成:
   ```
   python create_shortcut.py
   ```

### 初回起動時の挙動
- 初回起動時、Whisperモデルが自動的にダウンロードされます（インターネット接続が必要）
- モデルのサイズによってはダウンロードに時間がかかります（largeモデルは約3GB）
- モデルは`~/.cache/whisper`に保存されます

### 設定項目

設定は内部的にJSON形式で保存され、以下の項目が含まれます:

```json
{
  "model": "small",
  "language": "ja",
  "output_directory": "C:/Users/Username/Desktop/コエモジ∞"
}
```

- **model**: Whisperモデルのサイズ（"tiny", "base", "small", "medium", "large"）
- **language**: 文字起こし言語（""は自動検出、"ja"は日本語）
- **output_directory**: 文字起こし結果の保存先（ファイル名の頭に'KOEMOJI-'が追加されます）

## 配布準備

### 実行ファイルのビルド（PyInstaller）
アプリケーションを単一の実行ファイルにビルドする場合:

```
pip install pyinstaller
pyinstaller transcriber.spec
```

ビルド後の実行ファイルは`dist`ディレクトリに生成されます。

### 将来的なインストーラー作成
インストーラーを作成する場合の推奨ツール:
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [NSIS](https://nsis.sourceforge.io/)

これらのツールを使用してインストーラーを作成する手順は現在未実装です。

## トラブルシューティング

### 一般的な問題と解決策

#### 環境変数関連のエラー
- **症状**: `'python'/'ffmpeg' は、内部コマンドまたは外部コマンドとして認識されていません`
- **解決策**:
  1. 環境変数Pathに正しくパスが追加されているか確認
  2. コマンドプロンプトを再起動
  3. 絶対パスで実行（例: `C:\Python38\python.exe main.py`）

#### Whisperモデルのダウンロード失敗
- **症状**: `モデルのロードに失敗しました`
- **解決策**:
  1. インターネット接続を確認
  2. ファイアウォール設定を確認
  3. 手動でモデルをダウンロードし、`~/.cache/whisper`に配置

#### CUDA関連のエラー
- **症状**: `CUDA error: no kernel image is available for execution on the device`
- **解決策**:
  1. 適切なCUDAバージョンのPyTorchをインストール
  2. NVIDIAドライバを最新版に更新
  3. CPUモードに切り替え（`device="cpu"`を使用）

#### メモリ不足エラー
- **症状**: `CUDA out of memory`や`RuntimeError: DefaultCPUAllocator: not enough memory`
- **解決策**:
  1. より小さいモデルサイズを使用
  2. バックグラウンドアプリケーションを終了
  3. システムのページファイルサイズを増加

### デバッグ情報の取得
問題発生時のデバッグ情報を収集:
```
python main.py > debug_log.txt 2>&1
```

詳細なエラーメッセージとともにGitHub Issuesに報告してください。

---

**注意**: 本ドキュメントはセットアップ担当者向けであり、一般ユーザー向けのセットアップガイドは別途作成することをお勧めします。現状ではWindows環境のみの動作確認を行っており、他のプラットフォームでの動作は保証されていません。 