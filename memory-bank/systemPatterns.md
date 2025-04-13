# コエモジ - システムパターン

## システムアーキテクチャ

コエモジは、モジュール化されたMVCに近い設計パターンを採用しています。主要なモジュールは以下の通りです：

```
アプリケーション（main.py）
  ↓
  ├── UI層（ui/）
  │   ├── メインウィンドウ（main_window.py）
  │   ├── 設定ウィンドウ（settings_window.py）
  │   └── 結果ウィンドウ（result_window.py）
  │
  ├── コア処理層（transcriber.py）
  │   ├── BaseTranscriber
  │   ├── VideoTranscriber
  │   └── AudioTranscriber
  │
  └── ユーティリティ層（utils/）
      └── 設定管理（config_manager.py）
```

### 主要コンポーネントの関係

1. **メインアプリケーション（main.py）**
   - アプリケーションの起動ポイント
   - Tkinterのルートウィンドウを初期化
   - 設定マネージャーの初期化
   - メインウィンドウの生成と表示

2. **UI層（ui/）**
   - メインウィンドウ（main_window.py）：ファイル選択と処理開始のメインインターフェイス
   - 設定ウィンドウ（settings_window.py）：アプリケーション設定の構成用インターフェイス
   - 結果ウィンドウ（result_window.py）：文字起こし結果の表示と操作用インターフェイス

3. **コア処理層（transcriber.py）**
   - BaseTranscriber：文字起こし基本機能を実装する抽象クラス
   - VideoTranscriber：動画ファイルから音声抽出と文字起こしを行うクラス
   - AudioTranscriber：音声ファイルの文字起こしを行うクラス

4. **ユーティリティ層（utils/）**
   - ConfigManager（config_manager.py）：アプリケーション設定の読み込みと保存

## 重要な設計パターン

### 1. クラス継承とポリモーフィズム
- BaseTranscriberを基底クラスとし、VideoTranscriberとAudioTranscriberが継承
- ファイル形式に依存しない共通インターフェイスを提供

```python
class BaseTranscriber:
    # 基本の文字起こし機能
    def transcribe_audio(self, audio_path): ...

class VideoTranscriber(BaseTranscriber):
    # 動画特有の処理を追加
    def extract_audio(self, video_path): ...
    def process_video(self, video_path): ...

class AudioTranscriber(BaseTranscriber):
    # 音声特有の処理を追加
    def preprocess_audio(self, audio_path): ...
    def process_audio(self, audio_path): ...
```

### 2. モデル-ビュー分離
- 設定データとUIの明確な分離（ConfigManagerとSettingsWindow）
- 処理ロジックとUIの分離（TranscriberクラスとMainWindow）

### 3. コールバックパターン
- 非同期処理中の進捗更新にコールバック関数を使用
- UIスレッドとバックグラウンド処理スレッド間の通信を実現

```python
# コールバック関数の定義
def update_progress(status, progress):
    # UIの更新処理
    self._update_progress_gui(status, progress)

# 処理時にコールバックを渡す
transcriber = VideoTranscriber(model_name=model, language=language, callback=update_progress)
```

### 4. スレッド処理
- 文字起こし処理を別スレッドで実行し、UIのフリーズを防止
- tkinterの`after`メソッドを使用してスレッド間の安全な通信を実現

```python
# 処理スレッドの起動
thread = threading.Thread(
    target=self._process_files,
    args=(self.files.copy(), model, language, output_dir)
)
thread.daemon = True
thread.start()

# UIスレッドでの安全な更新
self.root.after(0, lambda: self._update_progress_gui(status, progress))
```

### 5. 設定の永続化
- JSON形式での設定保存によるセッション間の設定維持
- デフォルト値とユーザー設定の適切なマージ

## データフロー

### 文字起こし処理のフロー
1. ユーザーがファイルを選択し、処理開始ボタンをクリック
2. MainWindowがファイルリストと設定パラメータを取得
3. バックグラウンドスレッドで処理を開始
4. 各ファイルに対して：
   - 動画ファイルの場合：VideoTranscriberを使用
     a. 音声を抽出（FFmpeg使用）
     b. 抽出した音声を文字起こし
   - 音声ファイルの場合：AudioTranscriberを使用
     a. 音声を前処理（必要に応じて）
     b. 文字起こしを実行
5. コールバック関数を通じて進捗を更新
6. 処理完了時に結果をファイルに保存
7. ResultWindowで結果を表示

### 設定管理のフロー
1. アプリケーション起動時にConfigManagerが設定ファイルを読み込み
2. ユーザーが設定ウィンドウで設定を変更
3. 設定変更時にConfigManagerが更新内容をメモリ上に保存
4. 設定ウィンドウ閉じる時に設定をファイルに保存

## 拡張性とモジュール性

システムは以下の点で拡張性を考慮しています：

1. **新しい処理エンジンの追加**
   - BaseTranscriberを継承する新しいクラスを作成するだけで対応可能

2. **UIの拡張**
   - 各ウィンドウクラスは独立しており、新しい機能画面の追加が容易

3. **設定オプションの追加**
   - ConfigManagerは汎用的に設計されており、新しい設定項目の追加が簡単

4. **サポートファイル形式の拡張**
   - ファイル形式のリストを更新するだけで新しい形式をサポート可能
