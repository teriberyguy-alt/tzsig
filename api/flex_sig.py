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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"Status code: {response.status_code}")  # Log to Render
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11983'
        }

        # Extract all text
        text = soup.get_text(separator=' ', strip=True)

        # Rank - look for number near "Rank" or first #number
        rank_pos = text.find("Rank")
        if rank_pos != -1:
            snippet = text[rank_pos - 20:rank_pos + 80]
            parts = snippet.split()
            for p in parts:
                if p.isdigit() or p.startswith('#'):
                    stats['rank'] = p
                    break

        # Level and Class - look for "Level" followed by number and class
        level_pos = text.find("Level")
        if level_pos != -1:
            snippet = text[level_pos - 20:level_pos + 100]
            parts = snippet.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['level'] = parts[1]
            for p in parts:
                if p in ['Assassin', 'Sorceress', 'Barbarian', 'Paladin', 'Necromancer', 'Amazon', 'Druid']:
                    stats['class'] = p
                    break

        # Experience - look for large number near "Experience" or "Exp"
        exp_pos = text.find("Experience")
        if exp_pos != -1:
            snippet = text[exp_pos - 20:exp_pos + 100]
            parts = snippet.split()
            for p in parts:
                if p.replace(',', '').isdigit() and len(p) > 6:  # long number = exp
                    stats['exp'] = p
                    break

        # Last Active - look for date/time patterns near "Active"
        active_pos = text.find("Active")
        if active_pos != -1:
            snippet = text[active_pos - 20:active_pos + 100]
            # Simple date match (e.g. "Jan 15, 2026" or "2 hours ago")
            if any(char.isdigit() for char in snippet):
                stats['last_active'] = snippet.split("ago")[0].strip() if "ago" in snippet else snippet.strip()

        print(f"Scraped stats: {stats}")  # Log to Render for debug
        return stats
    except Exception as e:
        print(f"Scrape error: {str(e)}")
        return {'rank': 'Error', 'level': 'Error', 'class': 'Error', 'exp': 'Error', 'last_active': str(e)[:30], 'battletag': 'GuyT#11983'}

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
