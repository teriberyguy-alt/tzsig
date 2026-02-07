import io
import os
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'

    try:
        # Headless Chrome setup for Render
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        time.sleep(5)  # Wait for JS to load stats

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11983'
        }

        # Extract from rendered page
        text = soup.get_text(separator=' ', strip=True)

        # Rank
        if "Rank" in text:
            pos = text.find("Rank")
            snippet = text[pos:pos + 60]
            parts = snippet.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['rank'] = parts[1]

        # Level and Class
        if "Level" in text:
            pos = text.find("Level")
            snippet = text[pos:pos + 80]
            parts = snippet.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['level'] = parts[1]
            if len(parts) > 2:
                class_name = parts[2]
                if class_name in ['Assassin', 'Sorceress', 'Barbarian', 'Paladin', 'Necromancer', 'Amazon', 'Druid']:
                    stats['class'] = class_name

        # Exp
        if "Experience" in text:
            pos = text.find("Experience")
            snippet = text[pos:pos + 80]
            parts = snippet.split()
            if len(parts) > 1:
                exp = parts[1].replace(',', '')
                if exp.isdigit():
                    stats['exp'] = exp

        # Last Active
        if "Last Active" in text:
            pos = text.find("Last Active")
            snippet = text[pos:pos + 80]
            active = snippet.split(":", 1)[1].strip() if ":" in snippet else 'N/A'
            stats['last_active'] = active

        driver.quit()
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
