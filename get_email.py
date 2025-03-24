from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import json
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """建立 Gmail API 服務，從 base64 的 token.json 解碼"""
    token_base64 = os.getenv("TOKEN_JSON_BASE64")
    if not token_base64:
        raise Exception("❌ 環境變數 TOKEN_JSON_BASE64 未設定")

    try:
        token_data = base64.b64decode(token_base64 + '=' * (-len(token_base64) % 4)).decode("utf-8")
        creds_dict = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(info=creds_dict, scopes=SCOPES)
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise Exception(f"❌ token.json 解碼或建立 Credentials 失敗：{e}")

def get_latest_netflix_email():
    """抓取 Netflix 最新信件的完整內容"""
    service = get_gmail_service()

    # 搜尋任何 Netflix 寄來的郵件
    results = service.users().messages().list(userId="me", q="from:(netflix)", maxResults=1).execute()
    messages = results.get("messages", [])

    if not messages:
        return "❌ 找不到 Netflix 的郵件"

    # 取得郵件內容
    message = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
    payload = message["payload"]

    # 解碼郵件內容
    email_text = "⚠️ 無法讀取郵件內容"
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body_data = part["body"].get("data")
                if body_data:
                    email_text = base64.urlsafe_b64decode(body_data + '=' * (-len(body_data) % 4)).decode("utf-8")

    return email_text