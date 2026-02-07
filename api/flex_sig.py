import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'  # Your character profile
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status code: {response.status_code}")  # Log for Render
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11983'  # Hardcoded fallback
        }

        # Get all text
        text = soup.get_text(separator=' ', strip=True)

        # Rank - look for "Rank" followed by number
        if "Rank" in text:
            rank_pos = text.find("Rank")
            rank_snippet = text[rank_pos:rank_pos + 50]
            parts = rank_snippet.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['rank'] = parts[1]
            else:
                # Try to find # followed by number
                hash_pos = text.find('#')
                if hash_pos != -1:
                    rank_snippet = text[hash_pos-10:hash_pos+20]
                    parts = rank_snippet.split()
                    for p in parts:
                        if p.isdigit():
                            stats['rank'] = p
                            break

        # Level and Class - look for "Level" followed by number and class
        if "Level" in text:
            level_pos = text.find("Level")
            level_snippet = text[level_pos:level_pos + 80]
            parts = level_snippet.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['level'] = parts[1]
            if len(parts) > 2 and parts[2] in ['Assassin', 'Sorceress', 'Barbarian', 'Paladin', 'Necromancer', 'Amazon', 'Druid']:
                stats['class'] = parts[2]

        # Exp
        if "Experience" in text:
            exp_pos = text.find("Experience")
            exp_snippet = text[exp_pos:exp_pos + 80]
            parts = exp_snippet.split()
            if len(parts) > 1:
                stats['exp'] = parts[1].replace(',', '')

        # Last Active
        if "Last Active" in text:
            active_pos = text.find("Last Active")
            active_snippet = text[active_pos:active_pos + 80]
            active = active_snippet.split(":", 1)[1].strip() if ":" in active_snippet else 'N/A'
            stats['last_active'] = active

        print(f"Scraped stats: {stats}")  # Log to Render for debug
        return stats
    except Exception as e:
        print(f"Scrape error: {str(e)}")  # Log to Render
        return {'rank': 'Error', 'level': 'Error', 'class': 'Error', 'exp': 'Error', 'last_active': str(e)[:30], 'battletag': 'Error'}

@app.route('/flex-sig.png')
def flex_sig():
    stats = scrape_ladder_stats()

    try:
        bg_path = os.path.join(BASE_DIR, 'bg.jpg')
        font_path = os.path.join(BASE_DIR, 'font.ttf')

        # Fallback if files missing
        if not os.path.exists(bg_path):
            bg_image = Image.new('RGBA', (300, 140), (20, 20, 20))
            print("Warning: bg.jpg not found - using plain background")
        else:
            bg_image = Image.open(bg_path).convert('RGBA')

        draw = ImageDraw.Draw(bg_image)

        font = ImageFont.load_default()
        try:
            font = ImageFont.truetype(font_path, 12)
        except Exception as e:
            print(f"Font load error: {str(e)} - using default")

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

        # No "GUY_T" text - it's in bg.jpg

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
