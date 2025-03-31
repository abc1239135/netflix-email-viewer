from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import json
import os
from datetime import datetime, timedelta

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 紀錄已讀信件的 cache（記憶體內，5 分鐘自動移除）
email_cache = {}


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
    query = 'from:(no-reply@netflix.com OR disneyplus@trx.mail2.disneyplus.com)'
    results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    messages = results.get("messages", [])

    # 移除超過 5 分鐘的快取信件
    now = datetime.utcnow()
    expired_ids = [msg_id for msg_id, timestamp in email_cache.items() if now - timestamp > timedelta(minutes=5)]
    for msg_id in expired_ids:
        del email_cache[msg_id]

    emails = []
    for message_meta in messages:
        msg_id = message_meta["id"]

        # 已經過期的快取信件不處理
        if msg_id in email_cache:
            continue

        try:
            message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            payload = message.get("payload", {})
            email_html = "⚠️ 無法讀取郵件內容"

            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/html":
                        body_data = part["body"].get("data")
                        if body_data:
                            email_html = base64.urlsafe_b64decode(body_data).decode("utf-8")
            elif payload.get("mimeType") == "text/html":
                body_data = payload["body"].get("data")
                if body_data:
                    email_html = base64.urlsafe_b64decode(body_data).decode("utf-8")

            emails.append(email_html)
            email_cache[msg_id] = now

        except Exception as e:
            print(f"❌ 無法讀取郵件 {msg_id}：{e}")

    return emails[:3] if emails else []
