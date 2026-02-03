from flask import Flask
import requests
import re

app = Flask(__name__)

def get_tz():
    url = "https://d2emu.com/tz"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()

    html = r.text.upper()

    cur = re.search(r'CURRENT TERROR ZONE.*?<B>(.*?)</B>', html, re.S)
    nxt = re.search(r'NEXT TERROR ZONE.*?<B>(.*?)</B>', html, re.S)

    current_zone = cur.group(1).strip() if cur else "UNKNOWN"
    next_zone = nxt.group(1).strip() if nxt else "UNKNOWN"

    return current_zone, next_zone

@app.route("/")
def index():
    cur, nxt = get_tz()
    return f"NOW: {cur}<br>NEXT: {nxt}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
