import os
import json
import logging
import hmac
import hashlib
import base64
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
)

# ロガーの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('danshari-bot')

from app.handlers import LineEventHandler

load_dotenv()

# LINE credentials
CHANNEL_SECRET = (os.getenv("LINE_CHANNEL_SECRET") or "").strip()
CHANNEL_ACCESS_TOKEN = (os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "").strip()

# デバッグ情報を表示
print("=== 環境変数確認 ===")
print(f"CHANNEL_SECRET: {CHANNEL_SECRET[:3] + '...' if CHANNEL_SECRET else 'None'}")
print(f"CHANNEL_ACCESS_TOKEN: {CHANNEL_ACCESS_TOKEN[:3] + '...' if CHANNEL_ACCESS_TOKEN else 'None'}")

# Allow local testing without setting real LINE credentials (YAGNI)
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    CHANNEL_SECRET = CHANNEL_SECRET or "DUMMY_SECRET"
    CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN or "DUMMY_TOKEN"
    print("警告: ダミーの認証情報を使用しています")
else:
    print("✅ 認証情報を正常に読み込みました")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = FastAPI(title="LINE 断捨離 Bot")

# Load fixed Flex template once at startup (YAGNI: 1種のみ)
_template_path = Path(__file__).resolve().parent.parent / "templates" / "comment_template.json"
FIXED_TEMPLATE = None
if _template_path.exists():
    FIXED_TEMPLATE = json.loads(_template_path.read_text(encoding="utf-8"))

# Create event handler with template
event_handler = LineEventHandler(line_bot_api, FIXED_TEMPLATE)


@app.get("/")
def health():
    """Health-check endpoint used by tests & monitoring."""
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    """LINE Messaging API webhook endpoint."""
    signature = request.headers.get("x-line-signature") or request.headers.get("X-Line-Signature")
    body = await request.body()
    body_text = body.decode("utf-8")

    # LINEの検証リクエストなど、events が空のケースを許容して 200 を返す
    try:
        payload = json.loads(body_text) if body_text else {}
    except ValueError:
        payload = {}

    if not payload.get("events"):
        logger.info("Received empty events payload – returning 200 for verification ping.")
        return JSONResponse(content={"status": "ok"})
    
    # 署名計算デバッグ
    expected_sig = base64.b64encode(hmac.new(CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()).decode()
    logger.info(f"Expected sig: {expected_sig}")
    logger.info(f"Header sig  : {signature}")
    if expected_sig != signature:
        logger.warning("Signature mismatch in debug calculation")

    # デバッグ情報の記録
    logger.debug(f"Webhook called with signature: {signature}")
    logger.info(f"Received body: {body_text}")
    logger.debug(f"Headers: {request.headers}")

    if not signature:
        logger.error("X-Line-Signature header is missing")
        raise HTTPException(status_code=400, detail="X-Line-Signature header is missing")

    try:
        # シグネチャ検証と処理
        logger.info("Handling webhook request with LINE SDK...")
        handler.handle(body_text, signature)
        logger.info("Webhook handling successful")
    except InvalidSignatureError:
        logger.error(f"Invalid signature: {signature}")
        logger.error(f"Using channel secret: {CHANNEL_SECRET[:5]}..." if CHANNEL_SECRET else "No channel secret")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except LineBotApiError as e:
        logger.error(f"LINE API error: {e}")
        raise HTTPException(status_code=500, detail=f"LINE API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return JSONResponse(content={"status": "ok"})


# --- Event handlers registration ---------------------------------------------

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    """Handle text messages."""
    event_handler.handle_text_message(event)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    """Handle image messages (screenshots)."""
    event_handler.handle_image_message(event)
