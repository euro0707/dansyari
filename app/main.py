import os
import json
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
)

from app.handlers import LineEventHandler

load_dotenv()

# LINE credentials
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# Allow local testing without setting real LINE credentials (YAGNI)
if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    CHANNEL_SECRET = CHANNEL_SECRET or "DUMMY_SECRET"
    CHANNEL_ACCESS_TOKEN = CHANNEL_ACCESS_TOKEN or "DUMMY_TOKEN"

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
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

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
