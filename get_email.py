from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import json
import os
import time
from datetime import datetime, timezone

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
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

def get_latest_netflix_emails():
    """抓取 Netflix 與 Disney+ 最近 3 封且在 5 分鐘內的信件（HTML 格式）"""
    service = get_gmail_service()
    query = (
        'from:info@account.netflix.com OR '
        'from:disneyplus@trx.mail2.disneyplus.com'
    )
    results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    messages = results.get("messages", [])

    if not messages:
        return []

    valid_emails = []
    now = time.time()

    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        internal_date = int(message.get("internalDate", 0)) / 1000  # 轉成秒
        if now - internal_date > 300:
            continue  # 超過 5 分鐘就跳過

        payload = message["payload"]
        html_content = "⚠️ 無法讀取郵件內容"

        def extract_html(part):
            body_data = part.get("body", {}).get("data")
            if body_data:
                return base64.urlsafe_b64decode(body_data).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html":
                    html = extract_html(part)
                    if html:
                        html_content = html
                        break
        elif payload.get("mimeType") == "text/html":
            html = extract_html(payload)
            if html:
                html_content = html

        valid_emails.append(html_content)
        if len(valid_emails) >= 3:
            break

    return valid_emails
