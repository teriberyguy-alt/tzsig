import io
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'  # Your profile
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
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

        # Extract all text
        text = soup.get_text(separator=' ', strip=True)

        # Rank (usually first in table or text)
        if "Rank" in text:
            rank_pos = text.find("Rank")
            rank_snippet = text[rank_pos:rank_pos + 50]
            rank = rank_snippet.split()[1] if len(rank_snippet.split()) > 1 else 'N/A'
            stats['rank'] = rank

        # Level and Class (often "Level 99 Assassin")
        if "Level" in text:
            level_pos = text.find("Level")
            level_snippet = text[level_pos:level_pos + 50]
            parts = level_snippet.split()
            if len(parts) > 1:
                stats['level'] = parts[1]
            if len(parts) > 2:
                stats['class'] = parts[2]

        # Exp
        if "Experience" in text:
            exp_pos = text.find("Experience")
            exp_snippet = text[exp_pos:exp_pos + 50]
            exp = exp_snippet.split()[1] if len(exp_snippet.split()) > 1 else 'N/A'
            stats['exp'] = exp

        # Last Active
        if "Last Active" in text:
            active_pos = text.find("Last Active")
            active_snippet = text[active_pos:active_pos + 50]
            active = active_snippet.split(":", 1)[1].strip() if ":" in active_snippet else 'N/A'
            stats['last_active'] = active

        # BattleTag (hardcoded fallback or scrape from title/text)
        if "GuyT#11983" in text or "Its_Guy" in text:
            stats['battletag'] = "GuyT#11983"

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

        # Fallback if files missing
        if not os.path.exists(bg_path):
            bg_image = Image.new('RGBA', (300, 140), (20, 20, 20))
        else:
            bg_image = Image.open(bg_path).convert('RGBA')

        draw = ImageDraw.Draw(bg_image)

        font = ImageFont.load_default()
        try:
            font = ImageFont.truetype(font_path, 12)
        except:
            pass  # fallback to default

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

        # Footer
        draw_with_shadow("GUY_T", x + 200, y + 20, font, (150, 150, 150))

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
