from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import json
import os
from datetime import datetime, timedelta

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
    senders = [
        ("Netflix", "no-reply@netflix.com"),
        ("Disney+", "account@disneyplus.com")
    ]
    
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=5)
    all_emails = []

    for platform, sender in senders:
        results = service.users().messages().list(
            userId="me", q=f"from:{sender}", maxResults=3
        ).execute()

        messages = results.get("messages", [])
        for msg in messages:
            full_msg = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            internal_date = int(full_msg.get("internalDate", 0)) / 1000
            msg_time = datetime.utcfromtimestamp(internal_date)

            if msg_time < cutoff:
                continue  # 跳過超過 5 分鐘的信件

            payload = full_msg["payload"]
            email_html = "⚠️ 無法讀取郵件內容"

            # 嘗試抓取 HTML 格式
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/html":
                        body_data = part["body"].get("data")
                        if body_data:
                            email_html = base64.urlsafe_b64decode(body_data).decode("utf-8")
            elif payload.get("mimeType") == "text/html":
                body_data = payload["body"].get("data")
                if body_data:
                    email_html = base64.urlsafe_b64decode(body_data).decode("utf-8")

            all_emails.append({
                "content": email_html,
                "timestamp": msg_time,
                "platform": platform
            })

    # 按照時間排序（新 → 舊）
    sorted_emails = sorted(all_emails, key=lambda e: e["timestamp"], reverse=True)
    return sorted_emails
