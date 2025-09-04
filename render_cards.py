
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
PAD = 64
ASSETS = Path(__file__).parent / "assets"
FONT_PATH = ASSETS / "fonts" / "Inter-Bold.ttf"

def draw_multiline(draw, text, xy, font, fill, max_width, line_spacing=8):
    x, y = xy
    words = text.split()
    line = ""
    for w in words:
        test = line + (" " if line else "") + w
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            draw.text((x, y), line, font=font, fill=fill)
            y += font.size + line_spacing
            line = w
    if line:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_spacing
    return y

def draw_card(question, idx, out_dir):
    img = Image.new("RGB", (W, H), (20, 22, 26))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype(str(FONT_PATH), 72)
        font_body  = ImageFont.truetype(str(FONT_PATH), 52)
    except Exception:
        font_title = ImageFont.load_default()
        font_body  = ImageFont.load_default()

    y = PAD + 20
    draw.text((PAD, y), "Daily Sports Trivia", fill=(240,240,240), font=font_title)
    y += 120

    q_text = question["question"]
    y = draw_multiline(draw, q_text, (PAD, y), font_body, fill=(255,255,255), max_width=W-2*PAD, line_spacing=10)
    y += 40

    for i, opt in enumerate(question["options"], start=1):
        bullet = f"{i}. {opt}"
        y = draw_multiline(draw, bullet, (PAD, y), font_body, fill=(220,220,220), max_width=W-2*PAD, line_spacing=8)
        y += 12

    footer = "@trivia • #Shorts"
    draw.text((PAD, H - PAD - 40), footer, fill=(200,200,200), font=font_body)

    out_path = Path(out_dir) / f"q{idx:02d}.png"
    img.save(out_path, format="PNG", optimize=True)
    return out_path

def render_cards(json_path):
    import json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_dir = Path(json_path).with_suffix("").as_posix() + "_cards"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    paths = []
    for i, q in enumerate(data["questions"], start=1):
        p = draw_card(q, i, out_dir)
        paths.append(str(p))
    print("Wrote", len(paths), "cards to", out_dir)
    return out_dir

if __name__ == "__main__":
    import sys
    render_cards(sys.argv[1])
