import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status code: {response.status_code}")  # Debug to Render logs
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'N/A'
        }

        # h1 = name and battletag
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.text.strip()
            print(f"h1 text: {h1_text}")
            if '(' in h1_text and ')' in h1_text:
                name = h1_text.split(' (')[0].strip()
                battletag = h1_text.split(' (')[1].replace(')', '').strip()
                stats['battletag'] = battletag
            else:
                stats['battletag'] = h1_text

        # h2 = mode and level (e.g. "Softcore - Level 94")
        h2 = soup.find('h2')
        if h2:
            h2_text = h2.text.strip()
            print(f"h2 text: {h2_text}")
            if '-' in h2_text:
                mode = h2_text.split(' - ')[0].strip()
                level = h2_text.split(' - ')[1].strip().replace('Level', '').strip()
                stats['level'] = level
                stats['class'] = mode  # Softcore/Hardcore as "class" placeholder

        # Class (if explicitly listed)
        if "Assassin" in h2_text or "Assassin" in soup.get_text():
            stats['class'] = 'Assassin'

        # If rank/exp/last active appear later, add here
        # For now, they are not on the page

        print(f"Final scraped stats: {stats}")
        return stats
    except Exception as e:
        print(f"Scrape error: {str(e)}")
        return {'rank': 'Error', 'level': 'Error', 'class': 'Error', 'exp': 'Error', 'last_active': str(e)[:30], 'battletag': 'Error'}

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

        # Title
        draw_with_shadow("LADDER FLEX", x, y, font, (200, 40, 0))
        y += 30

        # Stats
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
