import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://maxroll.gg/d2r/ladders'  # Faster source
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }

    # Add retries to avoid pool errors
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, headers=headers, timeout=20)
        print(f"Status code: {response.status_code}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'rank': 'Not Ranked',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11341'
        }

        # Find the ladder table
        table = soup.find('table')
        if not table:
            print("No ladder table found")
            return stats

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                name_cell = cells[1].text.strip() if len(cells) > 1 else ''
                if "GuyT#11341" in name_cell or "Its_Guy" in name_cell:
                    print(f"Found player row: {name_cell}")
                    stats['rank'] = cells[0].text.strip() if len(cells) > 0 else 'N/A'
                    stats['level'] = cells[2].text.strip() if len(cells) > 2 else 'N/A'
                    stats['class'] = cells[3].text.strip() if len(cells) > 3 else 'N/A'
                    stats['exp'] = cells[4].text.strip() if len(cells) > 4 else 'N/A'
                    stats['battletag'] = name_cell
                    # Last active might be in another cell or not present
                    if len(cells) > 5:
                        stats['last_active'] = cells[5].text.strip()
                    break

        return stats
    except Exception as e:
        print(f"Scrape error: {str(e)}")
        return {'rank': 'Error', 'level': 'Error', 'class': 'Error', 'exp': 'Error', 'last_active': str(e)[:30], 'battletag': 'GuyT#11341'}

@app.route('/flex-sig.png')
def flex_sig():
    stats = scrape_ladder_stats()

    try:
        bg_path = os.path.join(BASE_DIR, 'bg.jpg')
        font_path = os.path.join(BASE_DIR, 'font.ttf')

        bg_image = Image.open(bg_path).convert('RGBA')
        draw = ImageDraw.Draw(bg_image)

        font = ImageFont.load_default()
        try:
            font = ImageFont.truetype(font_path, 12)
        except:
            print("Font load failed - using default")

        x = 10
        y = 10
        line_spacing = 18

        def draw_with_shadow(text, px, py, fnt, color):
            draw.text((px+1, py+1), text, font=fnt, fill=(0, 0, 0))
            draw.text((px, py), text, font=fnt, fill=color)

        draw_with_shadow("LADDER FLEX", x, y, font, (200, 40, 0))
        y += 30

        draw_with_shadow(f"Rank: {stats['rank']}", x, y, font, (255, 255, 255))
        y += line_spacing
        draw_with_shadow(f"Level: {stats['level']} {stats['class']}", x, y, font, (255, 255, 255))
        y += line_spacing
        draw_with_shadow(f"Exp: {stats['exp']}", x, y, font, (255, 255, 255))
        y += line_spacing
        draw_with_shadow(f"Last Active: {stats['last_active']}", x, y, font, (255, 255, 255))
        y += line_spacing
        draw_with_shadow(f"{stats['battletag']}", x, y, font, (255, 215, 0))

        img_bytes = io.BytesIO()
        bg_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return Response(img_bytes, mimetype='image/png')
    except Exception as e:
        print(f"Image generation error: {str(e)}")
        return Response(f"Image error: {str(e)}".encode(), mimetype='text/plain', status=500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
