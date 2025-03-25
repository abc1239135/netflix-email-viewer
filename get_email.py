from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import json
import os
from datetime import datetime, timedelta, timezone

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
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", q="from:info@account.netflix.com", maxResults=5).execute()
    messages = results.get("messages", [])

    emails = []
    now = datetime.now(timezone.utc)

    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        internal_date = int(message["internalDate"]) / 1000  # 轉成秒
        msg_time = datetime.fromtimestamp(internal_date, tz=timezone.utc)

        # 篩選：只保留 5 分鐘內的郵件
        if now - msg_time > timedelta(minutes=5):
            continue

        payload = message["payload"]
        html_content = None

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html":
                    data = part["body"].get("data")
                    if data:
                        html_content = base64.urlsafe_b64decode(data).decode("utf-8")
                        break

        if not html_content and "body" in payload:
            data = payload["body"].get("data")
            if data:
                html_content = base64.urlsafe_b64decode(data).decode("utf-8")

        if html_content:
            emails.append(html_content)

    return emails

