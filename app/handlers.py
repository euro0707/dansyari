from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
    TextSendMessage,
    FlexSendMessage,
)


class LineEventHandler:
    """LINEイベント処理のハンドラクラス"""

    def __init__(self, line_bot_api, flex_template=None):
        """
        初期化
        
        Args:
            line_bot_api: LINEのBot APIクライアント
            flex_template: FlexMessageテンプレート(Optional)
        """
        self.line_bot_api = line_bot_api
        self.flex_template = flex_template

    def handle_text_message(self, event):
        """テキストメッセージ処理"""
        # ユーザー選択のレスポンスを簡易処理（v1ではセッション管理なし）
        text = event.message.text
        if text in ["削除候補", "非表示", "残す"]:
            reply_text = f"「{text}」を選択しました。お役に立てて良かったです！"
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
        else:
            # 通常のテキストメッセージには画像スクショを求める
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEトークのスクリーンショットを送っていただくと、整理方法をアドバイスします。")
            )

    def handle_image_message(self, event):
        """画像メッセージ処理"""
        if self.flex_template:
            # 固定FlexMessageテンプレート使用
            flex = FlexSendMessage(
                alt_text=self.flex_template["altText"],
                contents=self.flex_template["contents"],
            )
            self.line_bot_api.reply_message(event.reply_token, flex)
        else:
            # テキストフォールバック
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="スクリーンショットを確認しました。どうしますか？\n・削除候補\n・非表示\n・残す")
            )
