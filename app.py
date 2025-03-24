from flask import Flask, render_template
from get_email import get_latest_netflix_emails
import os

app = Flask(__name__)

@app.route("/")
def index():
    emails = get_latest_netflix_emails()
    return render_template("index.html", emails=emails)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
