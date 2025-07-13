import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, handler

client = TestClient(app)


@patch("linebot.WebhookHandler.handle")
def test_webhook_valid_request(mock_handle):
    """Test that the webhook calls the handler's handle method."""
    body = '{"events":[]}'
    signature = "a_valid_signature"

    # We mock the handle method so we don't need a real signature
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Line-Signature": signature}
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_handle.assert_called_once_with(body, signature)


def test_webhook_invalid_signature():
    """Test that an invalid signature raises a 400 error."""
    # To test the real signature validation, we need to bypass the mock
    # and provide a body that doesn't match the signature.
    with patch("linebot.WebhookHandler.handle", side_effect=handler.handle) as mock_real_handle:
        body = '{"events":[]}'
        # This signature is invalid for the given body and channel secret
        invalid_signature = "invalid_signature"
        response = client.post(
            "/webhook",
            content=body,
            headers={"X-Line-Signature": invalid_signature}
        )
        assert response.status_code == 400

