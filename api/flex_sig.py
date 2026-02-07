from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont
import io

app = Flask(__name__)

@app.route('/flex-sig.png')
def flex_sig():
    try:
        img = Image.new('RGB', (300, 140), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        draw.text((10, 10), "LADDER FLEX TEST", fill=(255, 215, 0), font=font)
        draw.text((10, 40), "Rank: N/A", fill=(255, 255, 255), font=font)
        draw.text((10, 60), "Level: N/A", fill=(255, 255, 255), font=font)
        draw.text((10, 80), "Exp: N/A", fill=(255, 255, 255), font=font)
        draw.text((10, 100), "GUY_T", fill=(150, 150, 150), font=font)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return Response(img_bytes, mimetype='image/png')
    except Exception as e:
        return Response(f"Error: {str(e)}", mimetype='text/plain', status=500)

if __name__ == '__main__':
    app.run()
