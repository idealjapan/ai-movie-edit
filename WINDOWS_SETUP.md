# Windows向けセットアップガイド

## 🚀 5分でセットアップ完了

### 1. Docker Desktop for Windowsのインストール

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)をダウンロード
2. インストーラーを実行
3. WSL2の有効化を選択（推奨）
4. PCを再起動

### 2. プロジェクトの取得

PowerShellを開いて以下を実行：

```powershell
# プロジェクトをダウンロード
git clone https://github.com/idealjapan/ai-movie-edit.git
cd ai-movie-edit

# 環境設定ファイルをコピー
copy .env.example .env
```

### 3. APIキーの設定

メモ帳で`.env`ファイルを開いて編集：
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 4. 起動

```powershell
docker-compose up
```

初回は数分かかります（Dockerイメージのダウンロード）。

### 5. アクセス

ブラウザで http://localhost:8501 を開く

## 📌 日常の使い方

### 起動
```powershell
cd ai-movie-edit
docker-compose up
```

### 停止
`Ctrl + C` を押してから：
```powershell
docker-compose down
```

## ⚡ Windows特有の注意点

### ファイアウォール警告
初回起動時に「Windowsファイアウォール」の警告が出たら「アクセスを許可」

### パス長制限
Windowsはパスが260文字を超えるとエラーになることがあります。
なるべくCドライブ直下など、短いパスに配置してください：
```
C:\ai-movie-edit
```

### 改行コード
Gitの設定で改行コードを自動変換：
```powershell
git config --global core.autocrlf true
```

## 🔧 トラブルシューティング

### Docker Desktopが起動しない
- Hyper-Vが有効か確認
- BIOSで仮想化が有効か確認
- Windows Updateを最新に

### "docker-compose"コマンドが見つからない
Docker Desktopを再インストール、またはPATHを確認

### メモリ不足
Docker Desktop設定 → Resources → Memory を増やす（推奨: 4GB以上）

## 🎯 便利な設定

### ショートカット作成

デスクトップにバッチファイルを作成：

`AI動画編集ツール.bat`:
```batch
@echo off
cd /d C:\ai-movie-edit
docker-compose up
pause
```

ダブルクリックで起動できます！

### スタートアップ登録

PC起動時に自動で立ち上げたい場合：
1. `docker-compose.yml`の`restart: always`を有効化
2. Docker Desktopの自動起動を有効化