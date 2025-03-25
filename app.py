from flask import Flask, render_template
from get_email import get_latest_netflix_emails

app = Flask(__name__)

@app.route("/")
def index():
    emails = get_latest_netflix_emails()
    return render_template("index.html", emails=emails)
