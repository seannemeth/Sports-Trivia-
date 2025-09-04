# render_short.py — Pillow-only text (no ImageMagick), robust font+audio handling
import json, os, textwrap
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip

W, H = 1080, 1920

def _pick_font_path(custom="assets/fonts/Inter-Bold.ttf"):
    # Prefer your bundled font
    p = Path(custom)
    if p.exists():
        return str(p)
    # Fall back to a common system font on GitHub runners
    for cand in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(cand):
            return cand
    return None  # PIL will fallback to default bitmap font

def _load_font(size, custom="assets/fonts/Inter-Bold.ttf"):
    fp = _pick_font_path(custom)
    try:
        if fp:
            return ImageFont.truetype(fp, size)
    except Exception:
        pass
    return ImageFont.load_default()

def _line_height(draw, font):
    try:
        ascent, descent = font.getmetrics()
        return ascent + descent
    except Exception:
        bbox = draw.textbbox((0,0), "Ag", font=font)
        return max(48, bbox[3]-bbox[1])

def _draw_multiline(draw, text, x, y, font, fill, max_width, line_spacing=8):
    lh = _line_height(draw, font)
    line = ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            draw.text((x,y), line, font=font, fill=fill)
            y += lh + line_spacing
            line = word
    if line:
        draw.text((x,y), line, font=font, fill=fill)
        y += lh + line_spacing
    return y

def _compose_frame(bg_path, question, options, font_path="assets/fonts/Inter-Bold.ttf"):
    # Background
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
    else:
        bg = Image.new("RGB", (W,H), (24,26,32))
    bg = bg.resize((W,H))

    draw = ImageDraw.Draw(bg)
    pad = 80

    title_font = _load_font(72, font_path)
    body_font  = _load_font(60, font_path)

    # Title
    y = pad
    draw.text((pad, y), "Daily Sports Trivia", font=title_font, fill=(240,240,240))
    y += _line_height(draw, title_font) + 24

    # Question
    maxw = W - 2*pad
    q_text = "\n".join(textwrap.wrap(question, width=28))
    for line in q_text.split("\n"):
        y = _draw_multiline(draw, line, pad, y, body_font, (255,255,255), maxw, line_spacing=8)

    y += 16

    # Options
    opts = [f"{i+1}. {opt}" for i, opt in enumerate(options)]
    for line in opts:
        y = _draw_multiline(draw, line, pad, y, body_font, (220,220,220), maxw, line_spacing=6)
        y += 6

    return bg

def render_short(json_path, index=1, out_path=None, music_path=None, font="assets/fonts/Inter-Bold.ttf"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    q = data["questions"][index-1]
    question = q["question"]
    options = q["options"]

    frame = _compose_frame("assets/bg.jpg", question, options, font_path=font)
    arr = np.array(frame)

    duration = 18
    clip = ImageClip(arr).set_duration(duration)

    # Optional music (robust: skip if decode fails or file empty)
    if music_path and os.path.exists(music_path):
        try:
            if os.path.getsize(music_path) > 0:
                music = AudioFileClip(music_path).volumex(0.12)
                clip = clip.set_audio(music)
        except Exception:
            pass  # no audio if it fails

    if not out_path:
        out_path = Path(json_path).with_suffix("").as_posix() + f"_q{index:02d}.mp4"

    clip.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", preset="medium", threads=4)
    clip.close()
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    import sys
    render_short(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1, sys.argv[3] if len(sys.argv) > 3 else None, "assets/soft_loop.mp3")
