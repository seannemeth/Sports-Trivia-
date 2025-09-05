import json, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
PAD = 72
ASSETS = Path(__file__).parent / "assets"

def _theme(league):
    cfg = {"bg_accent":[22,24,28],"ribbon":[80,80,80],"accent2":[140,140,140]}
    try:
        with open(ASSETS / "themes.json","r",encoding="utf-8") as f:
            T = json.load(f)
        return T.get(league, T.get("DEFAULT", cfg))
    except Exception:
        return cfg

def _pick_font(size):
    p = ASSETS / "fonts" / "Inter-Bold.ttf"
    if p.exists():
        try: return ImageFont.truetype(str(p), size)
        except Exception: pass
    for cand in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(cand): return ImageFont.truetype(cand, size)
    return ImageFont.load_default()

def _line_height(draw, font):
    try: a,d = font.getmetrics(); return a+d
    except Exception:
        bbox = draw.textbbox((0,0), "Ag", font=font)
        return max(48, bbox[3]-bbox[1])

def _gradient_bg(top, bottom):
    img = Image.new("RGB", (W, H), top)
    tr,tg,tb = top; br,bg,bb = bottom
    for y in range(H):
        t = y/(H-1)
        r = int(tr*(1-t)+br*t); g = int(tg*(1-t)+bg*t); b = int(tb*(1-t)+bb*t)
        img.putpixel((W//2, y), (r,g,b))
    return img.filter(ImageFilter.GaussianBlur(radius=600))

def _wrap(draw, text, font, max_width):
    words, line, lines = text.split(), "", []
    for w in words:
        test = (line+" "+w).strip()
        if draw.textlength(test, font=font) <= max_width: line = test
        else: lines.append(line); line = w
    if line: lines.append(line)
    return lines

def draw_card(question, idx, out_dir):
    league = (question.get("meta") or {}).get("league") or ((question.get("meta") or {}).get("leagues") or [""])[0] or "DEFAULT"
    T = _theme(league)

    bg = _gradient_bg(tuple(T["bg_accent"]), (8,10,14))
    draw = ImageDraw.Draw(bg)

    ribbon_h = 120
    draw.rectangle([0,0,W,ribbon_h], fill=tuple(T["ribbon"]))

    f_title = _pick_font(72)
    f_body  = _pick_font(54)
    f_small = _pick_font(44)

    draw.text((PAD, 32), f"Daily Sports Trivia • {league}", font=f_title, fill=(240,240,240))

    x, y = PAD+32, ribbon_h + 40
    maxw = W - 2*PAD - 64

    for line in _wrap(draw, question["question"], f_body, maxw):
        draw.text((x,y), line, font=f_body, fill=(255,255,255))
        y += _line_height(draw, f_body) + 6
    y += 10

    for i,opt in enumerate(question["options"], start=1):
        pill_h = _line_height(draw, f_small) + 28
        pill_w = max(320, int(draw.textlength(f"{i}. {opt}", font=f_small) + 48))
        pill = Image.new("RGBA", (pill_w, pill_h), (0,0,0,0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0,0,pill_w,pill_h), radius=22, fill=(T["accent2"][0], T["accent2"][1], T["accent2"][2], 230))
        pd.text((20, 14), f"{i}. {opt}", font=f_small, fill=(16,18,20))
        bg.paste(pill, (x, y), pill)
        y += pill_h + 14

    draw.text((PAD+32, H - PAD - 40), "@trivia • #Shorts", font=f_small, fill=(210,210,210))

    out_path = Path(out_dir) / f"q{idx:02d}.png"
    bg.save(out_path, format="PNG", optimize=True)
    return out_path

def render_cards(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_dir = Path(json_path).with_suffix("").as_posix() + "_cards"
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    paths = []
    for i, q in enumerate(data["questions"], start=1):
        p = draw_card(q, i, out_dir); paths.append(str(p))
    print("Wrote", len(paths), "cards to", out_dir)
    return out_dir

if __name__ == "__main__":
    import sys
    render_cards(sys.argv[1])
