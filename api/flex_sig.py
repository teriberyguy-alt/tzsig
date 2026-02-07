import io
import os
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scrape_ladder_stats():
    url = 'https://d2emu.com/ladder/218121324'

    try:
        print("Starting Selenium scrape...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        time.sleep(8)  # Wait for JS to load stats

        html = driver.page_source
        print(f"Page loaded - HTML length: {len(html)}")

        stats = {
            'rank': 'N/A',
            'level': 'N/A',
            'class': 'N/A',
            'exp': 'N/A',
            'last_active': 'N/A',
            'battletag': 'GuyT#11983'
        }

        # Find elements by class or text (d2emu uses divs with classes like "ladder-stat")
        rank_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'Rank')]")
        if rank_elem:
            rank_text = rank_elem.text.strip()
            print(f"Rank text found: {rank_text}")
            if "Rank" in rank_text:
                rank = rank_text.split("Rank")[-1].strip().split()[0]
                if rank.isdigit() or rank.startswith('#'):
                    stats['rank'] = rank

        # Level/Class - look for "Level" or "Assassin"
        level_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'Level')]")
        if level_elem:
            level_text = level_elem.text.strip()
            print(f"Level text found: {level_text}")
            parts = level_text.split()
            if len(parts) > 1 and parts[1].isdigit():
                stats['level'] = parts[1]
            if 'Assassin' in level_text or 'Sorceress' in level_text or 'Barbarian' in level_text or 'Paladin' in level_text or 'Necromancer' in level_text or 'Amazon' in level_text or 'Druid' in level_text:
                stats['class'] = level_text.split()[-1]

        # Exp
        exp_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'Experience')]")
        if exp_elem:
            exp_text = exp_elem.text.strip()
            print(f"Exp text found: {exp_text}")
            exp = exp_text.split()[-1].replace(',', '')
            if exp.isdigit():
                stats['exp'] = exp

        # Last Active
        active_elem = driver.find_element(By.XPATH, "//*[contains(text(), 'Last Active')]")
        if active_elem:
            active_text = active_elem.text.strip()
            print(f"Last Active text found: {active_text}")
            active = active_text.split(":", 1)[1].strip() if ":" in active_text else active_text
            stats['last_active'] = active

        driver.quit()
        print(f"Final stats: {stats}")
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
