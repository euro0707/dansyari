# LINE 断捨離 Bot (MVP)

FastAPI + LINE Messaging API で動作するシンプルなボット。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

環境変数 `.env` に以下を定義してください。

```
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

## 起動

```bash
uvicorn app.main:app --reload --port 8000
```

`/webhook` エンドポイントを LINE Developer Console に設定してください。

## 機能 (v1)
1. 画像アップロード (スクショ)
2. Bot が固定コメント + 選択肢(FlexMessage) を送信
3. ユーザー選択は記録せず、リアクションのみ返す

テストは `pytest` で実行できます。
