import json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip

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

def _wrap(draw, text, font, max_width):
    words, line, lines = text.split(), "", []
    for w in words:
        test = (line+" "+w).strip()
        if draw.textlength(test, font=font) <= max_width: line = test
        else: lines.append(line); line = w
    if line: lines.append(line)
    return lines

def _gradient_bg(top, bottom):
    img = Image.new("RGB", (W, H), top)
    tr,tg,tb = top; br,bg,bb = bottom
    for y in range(H):
        t = y/(H-1)
        r = int(tr*(1-t)+br*t); g = int(tg*(1-t)+bg*t); b = int(tb*(1-t)+bb*t)
        img.putpixel((W//2, y), (r,g,b))
    return img.filter(ImageFilter.GaussianBlur(radius=600))

def render_short(json_path, index=1, out_path=None, music_path=None, font="assets/fonts/Inter-Bold.ttf"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    q = data["questions"][index-1]
    league = (q.get("meta") or {}).get("league") or ((q.get("meta") or {}).get("leagues") or [""])[0] or "DEFAULT"
    T = _theme(league)

    bg = _gradient_bg(tuple(T["bg_accent"]), (8,10,14))
    draw = ImageDraw.Draw(bg)

    ribbon_h = 120
    draw.rectangle([0,0,W,ribbon_h], fill=tuple(T["ribbon"]))

    f_title = _pick_font(72)
    f_body  = _pick_font(60)
    f_small = _pick_font(48)

    draw.text((PAD, 32), f"Daily Sports Trivia • {league}", font=f_title, fill=(240,240,240))

    x, y = PAD+32, ribbon_h + 40
    maxw = W - 2*PAD - 64

    for line in _wrap(draw, q["question"], f_body, maxw):
        draw.text((x,y), line, font=f_body, fill=(255,255,255))
        y += _line_height(draw, f_body) + 6
    y += 16

    for i,opt in enumerate(q["options"], start=1):
        pill_h = _line_height(draw, f_small) + 28
        pill_w = max(360, int(draw.textlength(f"{i}. {opt}", font=f_small) + 48))
        pill = Image.new("RGBA", (pill_w, pill_h), (0,0,0,0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle((0,0,pill_w,pill_h), radius=22, fill=(T["accent2"][0], T["accent2"][1], T["accent2"][2], 230))
        pd.text((20, 14), f"{i}. {opt}", font=f_small, fill=(16,18,20))
        bg.paste(pill, (x, y), pill)
        y += pill_h + 12

    arr = np.array(bg)
    duration = 18
    clip = ImageClip(arr).set_duration(duration)

    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 0:
        try:
            music = AudioFileClip(music_path).volumex(0.12)
            clip = clip.set_audio(music)
        except Exception:
            pass

    if not out_path:
        out_path = Path(json_path).with_suffix("").as_posix() + f"_q{index:02d}.mp4"

    clip.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", preset="medium", threads=4)
    clip.close()
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    import sys
    render_short(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1, sys.argv[3] if len(sys.argv) > 3 else None, "assets/soft_loop.mp3")
