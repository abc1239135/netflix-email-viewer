from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import json
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """建立 Gmail API 服務，從 base64 的 token.json 解碼"""
    token_base64 = os.getenv("TOKEN_JSON_BASE64")
    if not token_base64:
        raise Exception("❌ 環境變數 TOKEN_JSON_BASE64 未設定")

    try:
        token_data = base64.b64decode(token_base64).decode("utf-8")
        creds_dict = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(info=creds_dict, scopes=SCOPES)
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise Exception(f"❌ token.json 解碼或建立 Credentials 失敗：{e}")

def extract_email_html(payload):
    """從 payload 中取出 text/html 的內容"""
    if payload.get("mimeType") == "text/html" and "data" in payload["body"]:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    elif payload.get("mimeType", "").startswith("multipart"):
        for part in payload.get("parts", []):
            html = extract_email_html(part)
            if html:
                return html
    return None

def get_latest_netflix_emails(limit=3):
    """抓取 Netflix 最新信件（HTML格式），回傳最新 limit 封"""
    service = get_gmail_service()

    results = service.users().messages().list(userId="me", q="from:info@account.netflix.com", maxResults=limit).execute()
    messages = results.get("messages", [])

    if not messages:
        return ["❌ 找不到 Netflix 的郵件"]

    email_html_list = []

    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"]).execute()
        html_content = extract_email_html(message["payload"])
        email_html_list.append(html_content or "⚠️ 無法解析 HTML 內容")

    return email_html_list
