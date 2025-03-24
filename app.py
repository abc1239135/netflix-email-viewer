from flask import Flask, render_template
from get_email import get_latest_netflix_email

app = Flask(__name__)

@app.route("/")
def index():
    email_content = get_latest_netflix_email()
    return render_template("index.html", email_content=email_content)

if __name__ == "__main__":
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
