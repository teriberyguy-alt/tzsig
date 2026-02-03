from flask import Flask
import requests
import re

app = Flask(__name__)

def get_tz():
    r = requests.get(
        "https://d2emu.com/tz",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10
    )
    r.raise_for_status()

    html = r.text

    # DEBUG — TEMPORARY
    print("---- HTML START ----")
    print(html[:1500])
    print("---- HTML END ----")

    html = html.upper()

    cur = re.search(r'CURRENT TERROR ZONE.*?<B>(.*?)</B>', html, re.S)
    nxt = re.search(r'NEXT TERROR ZONE.*?<B>(.*?)</B>', html, re.S)

    return (
        cur.group(1).strip() if cur else "UNKNOWN",
        nxt.group(1).strip() if nxt else "UNKNOWN"
    )


@app.route("/")
def index():
    cur, nxt = get_tz()
    return f"NOW: {cur}<br>NEXT: {nxt}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
