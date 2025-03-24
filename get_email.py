from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
import json
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    """建立 Gmail API 服務，從環境變數讀取 credentials.json"""
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    
    if not credentials_json:
        raise Exception("❌ 找不到環境變數 GOOGLE_CREDENTIALS，請確認已設定！")

    creds_dict = json.loads(credentials_json)
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
    
    return build("gmail", "v1", credentials=creds)

def get_latest_netflix_email():
    """抓取 Netflix 最新信件的完整內容"""
    service = get_gmail_service()

    # 搜尋 Netflix 寄來的郵件
    results = service.users().messages().list(userId="me", q="from:no-reply@netflix.com", maxResults=1).execute()
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
            if part["mimeType"] == "text/plain":  # 取得純文字版本
                body_data = part["body"]["data"]
                email_text = base64.urlsafe_b64decode(body_data).decode("utf-8")

    return email_text
