import io
import os
import requests
import textwrap
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response
from bs4 import BeautifulSoup

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ladder scrape function (for flex sig)
def scrape_ladder_stats(player_id='218121324'):
    url = f'https://d2emu.com/ladder/{player_id}'
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

        text = soup.get_text(separator=' ', strip=True)

        # Rank
        if "Rank" in text:
            rank_pos = text.find("Rank")
            rank_snippet = text[rank_pos:rank_pos + 50]
            rank = rank_snippet.split()[1] if len(rank_snippet.split()) > 1 else 'N/A'
            stats['rank'] = rank

        # Level/Class
        if "Level" in text:
            level_pos = text.find("Level")
            level_snippet = text[level_pos:level_pos + 50]
            level = level_snippet.split()[1] if len(level_snippet.split()) > 1 else 'N/A'
            class_name = level_snippet.split()[2] if len(level_snippet.split()) > 2 else 'N/A'
            stats['level'] = level
            stats['class'] = class_name

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

        # BattleTag
        if "GuyT#11983" in text:
            stats['battletag'] = "GuyT#11983"

        return stats
    except Exception as e:
        print(f"Scrape error: {str(e)}")
        return {'rank': 'Error', 'level': 'Error', 'class': 'Error', 'exp': 'Error', 'last_active': str(e)[:30], 'battletag': 'Error'}

# Signature route (your original TZ sig, updated with scrape if needed)
@app.route('/signature.png')
def generate_signature():
    now_lines = ["TZ data unavailable"]
    next_lines = []
    countdown_str = ""
    try:
        tz_url = 'https://d2runewizard.com/api/terror-zone'
       
        for attempt in range(2):
            try:
                response = requests.get(tz_url, timeout=15)
                response.raise_for_status()
                data = response.json()
               
                current_zone = data.get('currentTerrorZone', {}).get('zone', 'Unknown')
                next_zone = data.get('nextTerrorZone', {}).get('zone', 'Unknown')
               
                now_text = f"Now: {current_zone}"
                next_text = f"Next: {next_zone}"
               
                now_lines = textwrap.wrap(now_text, width=35)
                next_lines = textwrap.wrap(next_text, width=35)
               
                now_dt = datetime.utcnow()
                seconds_to_next = (60 - now_dt.minute) * 60 - now_dt.second
                if seconds_to_next < 0:
                    seconds_to_next = 0
                minutes = seconds_to_next // 60
                seconds = seconds_to_next % 60
               
                if minutes == 0:
                    countdown_str = f"{seconds} seconds until"
                else:
                    countdown_str = f"{minutes} min, {seconds:02d} sec until"
               
                break
            except requests.exceptions.RequestException:
                if attempt == 1:
                    raise
                time.sleep(1)
    except Exception:
        now_lines = ["TZ Fetch Slow"]
        next_lines = ["Refresh in a few sec"]
    try:
        bg_path = os.path.join(BASE_DIR, 'bg.jpg')
        font_path = os.path.join(BASE_DIR, 'font.ttf')
       
        bg_image = Image.open(bg_path).convert('RGBA')
        draw = ImageDraw.Draw(bg_image)
        font = ImageFont.truetype(font_path, 12)
        timer_font = ImageFont.truetype(font_path, 13)
       
        x = 10
        y = 55 # Back to original starting y (no title room needed)
        line_spacing = 15
       
        # Shadow helper function
        def draw_with_shadow(text, px, py, fnt, color):
            draw.text((px+1, py+1), text, font=fnt, fill=(0, 0, 0)) # Shadow
            draw.text((px, py), text, font=fnt, fill=color) # Main
       
        # Draw "Now" lines with shadow
        for line in now_lines:
            draw_with_shadow(line, x, y, font, (255, 255, 255))
            y += line_spacing
       
        # Countdown with shadow + gold
        if countdown_str:
            y += 6
            draw_with_shadow(countdown_str, x + 5, y, timer_font, (255, 215, 0))
            y += line_spacing + 4
       
        # Draw "Next" lines with shadow
        for line in next_lines:
            draw_with_shadow(line, x, y, font, (255, 255, 255))
            y += line_spacing
       
        img_bytes = io.BytesIO()
        bg_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
       
        return Response(img_bytes, mimetype='image/png')
    except Exception as e:
        return Response(f"Image error: {str(e)}".encode(), mimetype='text/plain', status=500)

# Avatar route
@app.route('/avatar.gif')
def avatar():
    current_zone, next_zone = get_terror_zones()

    font_path = os.path.join(BASE_DIR, 'font.ttf')
    try:
        font = ImageFont.truetype(font_path, 8)
    except:
        font = ImageFont.load_default()

    wrapper = textwrap.TextWrapper(width=12)
    curr_lines = wrapper.wrap(current_zone)
    next_lines = wrapper.wrap(next_zone)

    frames = []
    bg_colors = [(0, 0, 0), (10, 0, 0), (20, 0, 0)]

    for i in range(3):
        img = Image.new('RGB', (64, 64), bg_colors[i])
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, 63, 63), outline=(200, 40, 0), width=1)

        y = 6

        if i == 0:
            draw.text((4, y), "NOW:", fill=(255, 165, 0), font=font)
            y += 10
            for line in curr_lines:
                draw.text((4, y), line, fill=(255, 255, 255), font=font)
                y += 9
        elif i == 1:
            mins = 60 - datetime.now().minute
            timer_text = f"{mins}M LEFT"
            draw.text((4, 12), timer_text, fill=(255, 215, 0), font=font)
            draw.text((4, 30), "TIME", fill=(220, 220, 150), font=font)
        else:
            draw.text((4, y), "NEXT:", fill=(200, 40, 0), font=font)
            y += 10
            for line in next_lines:
                draw.text((4, y), line, fill=(220, 220, 150), font=font)
                y += 9

        frames.append(img)

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1000,
        loop=0,
        optimize=True
    )
    buf.seek(0)

    res = Response(buf, mimetype='image/gif')
    res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return res

# Flex sig route (new ladder tracking)
@app.route('/flex-sig.png')
def flex_sig():
    player_id = '218121324'  # Your ID
    stats = scrape_ladder_stats(player_id)

    try:
        bg_path = os.path.join(BASE_DIR, 'bg.jpg')
        font_path = os.path.join(BASE_DIR, 'font.ttf')

        bg_image = Image.open(bg_path).convert('RGBA')
        draw = ImageDraw.Draw(bg_image)
        font = ImageFont.truetype(font_path, 12)

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

        draw_with_shadow("GUY_T", x + 200, y + 20, font, (150, 150, 150))

        img_bytes = io.BytesIO()
        bg_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return Response(img_bytes, mimetype='image/png')
    except Exception as e:
        return Response(f"Image error: {str(e)}".encode(), mimetype='text/plain', status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
