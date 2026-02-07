import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'  # Your current profile
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status code: {response.status_code}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11341'  # Fallback
        }

        text = soup.get_text(separator=' ', strip=True)
        print(f"Page text length: {len(text)}")  # Debug

        # h1: name and battletag
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.text.strip()
            print(f"h1: {h1_text}")
            if '(' in h1_text and ')' in h1_text:
                name = h1_text.split(' (')[0].strip()
                battletag = h1_text.split(' (')[1].replace(')', '').strip()
                stats['battletag'] = battletag
            else:
                stats['battletag'] = h1_text

        # h2: level and mode/class
        h2 = soup.find('h2')
        if h2:
            h2_text = h2.text.strip()
            print(f"h2: {h2_text}")
            if '-' in h2_text:
                mode = h2_text.split(' - ')[0].strip()
                level = h2_text.split(' - ')[1].strip().replace('Level', '').strip()
                stats['level'] = level
                stats['class'] = mode

        # Class if explicitly mentioned
        if "Assassin" in text:
            stats['class'] = 'Assassin'

        # Rank - look for number near "Rank" or first #number
        if "Rank" in text:
            pos = text.find("Rank")
            snippet = text[pos - 20:pos + 80]
            print(f"Rank snippet: {snippet}")
            parts = snippet.split()
            for p in parts:
                if p.isdigit() or p.startswith('#'):
                    stats['rank'] = p
                    break

        # Exp - look for large number near "Experience" or "Exp"
        if "Experience" in text:
            pos = text.find("Experience")
            snippet = text[pos - 20:pos + 100]
            print(f"Exp snippet: {snippet}")
            parts = snippet.split()
            for p in parts:
                if p.replace(',', '').isdigit() and len(p) > 6:
                    stats['exp'] = p
                    break

        # Last Active - look for date/time patterns
        if "Last Active" in text:
            pos = text.find("Last Active")
            snippet = text[pos - 20:pos + 100]
            print(f"Last Active snippet: {snippet}")
            active = snippet.split(":", 1)[1].strip() if ":" in snippet else 'N/A'
            stats['last_active'] = active

        print(f"Final stats: {stats}")
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
