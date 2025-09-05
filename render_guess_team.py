
import os, json, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip

W, H = 1080, 1920
SAFE = 48
PAD  = 20

def _font(size):
    for cand in [
        "assets/fonts/Inter-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(cand):
            try: return ImageFont.truetype(cand, size)
            except Exception: pass
    return ImageFont.load_default()

def _lh(draw, font):
    try: a, d = font.getmetrics(); return a + d
    except Exception:
        b = draw.textbbox((0,0), "Ag", font=font); return max(40, b[3]-b[1])

def _shadow(img, radius=22, alpha=140, expand=24, r=28):
    w, h = img.size
    sh = Image.new("RGBA", (w+expand*2, h+expand*2), (0,0,0,0))
    d  = ImageDraw.Draw(sh)
    d.rounded_rectangle((expand,expand, w+expand, h+expand), radius=r, fill=(0,0,0,alpha))
    return sh.filter(ImageFilter.GaussianBlur(radius))

def _pill(text, font, color=(10,35,70), txt=(255,255,255)):
    dmy = Image.new("RGB",(10,10)); draw = ImageDraw.Draw(dmy)
    tw = int(draw.textlength(text, font=font))
    h  = int(font.size*1.1) + 26
    w  = max(160, tw + 38)
    pill = Image.new("RGBA", (w,h), (0,0,0,0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle((0,0,w,h), radius=16,
                         fill=(color[0],color[1],color[2],235))
    pd.text((19, (h - int(font.size*1.1))//2 + 6), text, font=font, fill=txt)
    return pill

def _slug(s):
    s = s.strip().lower()
    import re
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "x"

def _stack_with_logo(center_xy, label_img, logo_img=None, gap=10):
    if logo_img is None:
        return label_img, (center_xy[0] - label_img.size[0]//2,
                           center_xy[1] - label_img.size[1]//2)
    w = max(label_img.size[0], logo_img.size[0])
    h = logo_img.size[1] + gap + label_img.size[1]
    comp = Image.new("RGBA", (w, h), (0,0,0,0))
    comp.paste(logo_img, ((w - logo_img.size[0])//2, 0), logo_img)
    comp.paste(label_img, ((w - label_img.size[0])//2, logo_img.size[1]+gap), label_img)
    return comp, (center_xy[0] - w//2, center_xy[1] - h//2)

def render_guess_team(json_path, out_path=None, music_path=None):
    data = json.load(open(json_path, "r", encoding="utf-8"))
    mode = data.get("mode","basketball").lower()
    bg_path = data.get("background", "assets/backgrounds/basketball.png")
    bg = Image.open(bg_path).convert("RGB").resize((W,H))
    draw = ImageDraw.Draw(bg)

    title = data.get("title", "Guess The Team")
    f_title = _font(84)
    chip_w = int(draw.textlength(title, font=f_title) + 48)
    chip_h = int(f_title.size*1.2) + 24
    chip = Image.new("RGBA", (chip_w, chip_h), (0,0,0,0))
    cd = ImageDraw.Draw(chip)
    cd.rounded_rectangle((0,0,chip_w,chip_h), radius=22, fill=(255,160,0,235))
    cd.text((24, 12), title, font=f_title, fill=(15,18,24))
    bg.paste(chip, (SAFE, SAFE), chip)

    f_lab = _font(46)
    max_y = 0

    if mode == "basketball":
        pos_map = {
            "PG": (W//2, 540),
            "SG": (W//2 + 240, 620),
            "SF": (W//2 - 240, 620),
            "PF": (W//2 - 180, 840),
            "C" : (W//2 + 180, 840),
        }
        color = (10,35,70)
        logo_root = Path("assets/college_logos")
        for p in data["players"]:
            college = p.get("college","")
            pos = pos_map.get(p["pos"], (W//2, H//2))
            pill = _pill(college, f_lab, color=color)
            logo_path = None
            if college:
                slug = _slug(college)
                for folder in [logo_root, Path("assets/logos/colleges")]:
                    cand = folder / f"{slug}.png"
                    if cand.exists(): logo_path = cand; break
            logo_img = None
            if logo_path:
                lg = Image.open(logo_path).convert("RGBA")
                r = min(96/lg.width, 96/lg.height)
                lg = lg.resize((int(lg.width*r), int(lg.height*r)))
                frame = Image.new("RGBA", (lg.width+18, lg.height+18), (255,255,255,230))
                frame.paste(lg, (9,9), lg)
                logo_img = frame

            stack, (sx, sy) = _stack_with_logo(pos, pill, logo_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            max_y = max(max_y, sy + stack.size[1])

    elif mode == "football":
        pos_map = {
            "LT": (200, 540), "LG": (320, 540), "C": (540, 540),
            "RG": (760, 540), "RT": (880, 540),
            "QB": (540, 690), "RB": (540, 840),
            "TE": (870, 690),
            "WR1": (160, 690), "WR2": (920, 690), "WR3": (160, 900),
        }
        color = (15,45,18)
        logo_root = Path("assets/college_logos")
        for p in data["players"]:
            college = p.get("college","")
            pos = pos_map.get(p["pos"], (W//2, H//2))
            pill = _pill(college, f_lab, color=color)
            logo_path = None
            if college:
                slug = _slug(college)
                for folder in [logo_root, Path("assets/logos/colleges")]:
                    cand = folder / f"{slug}.png"
                    if cand.exists(): logo_path = cand; break
            logo_img = None
            if logo_path:
                lg = Image.open(logo_path).convert("RGBA")
                r = min(96/lg.width, 96/lg.height)
                lg = lg.resize((int(lg.width*r), int(lg.height*r)))
                frame = Image.new("RGBA", (lg.width+18, lg.height+18), (255,255,255,230))
                frame.paste(lg, (9,9), lg)
                logo_img = frame

            stack, (sx, sy) = _stack_with_logo(pos, pill, logo_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            max_y = max(max_y, sy + stack.size[1])

    else:  # soccer
        pos_map = {
            "GK": (W//2, 1560),
            "LB": (200, 1320), "LCB": (420, 1320), "RCB": (660, 1320), "RB": (880, 1320),
            "DM": (W//2, 1120), "LCM": (340, 1080), "RCM": (740, 1080),
            "LW": (260, 840), "ST": (W//2, 780), "RW": (820, 840),
        }
        color = (18,80,24)
        for p in data["players"]:
            iso = (p.get("flag") or "").upper()
            country = p.get("country","")
            pos = pos_map.get(p["pos"], (W//2, H//2))
            label = iso or country or "—"
            pill = _pill(label, f_lab, color=color)

            flag_path = None
            if iso:
                for folder in [Path("assets/flags"), Path("assets/logos/flags")]:
                    cand = folder / f"{iso}.png"
                    if cand.exists(): flag_path = cand; break

            flag_img = None
            if flag_path and flag_path.exists():
                fl = Image.open(flag_path).convert("RGBA")
                r = min(130/fl.width, 90/fl.height)
                fl = fl.resize((int(fl.width*r), int(fl.height*r)))
                frame = Image.new("RGBA", (fl.width+18, fl.height+18), (255,255,255,230))
                frame.paste(fl, (9,9), fl)
                flag_img = frame

            stack, (sx, sy) = _stack_with_logo(pos, pill, flag_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            max_y = max(max_y, sy + stack.size[1])

    year = str(data.get("year","")).strip()
    if year:
        f_year = _font(64)
        yr = _pill(year, f_year, color=(0,160,255), txt=(16,18,24))
        y_candidate = min(max_y + 40, H - SAFE - yr.size[1])
        x = (W - yr.size[0]) // 2
        sh = _shadow(yr, expand=12, radius=12, alpha=120, r=20)
        bg.paste(sh, (x-12, y_candidate-12), sh)
        bg.paste(yr, (x, y_candidate), yr)

    handle = data.get("handle","@YourHandle • #Shorts")
    f_meta = _font(42)
    draw.text((SAFE, H - SAFE - _lh(draw, f_meta)),
              handle, font=f_meta, fill=(245,245,245))

    arr = np.array(bg)
    clip = ImageClip(arr).set_duration(18)
    music_path = music_path or data.get("music")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 0:
        try:
            music = AudioFileClip(music_path).volumex(0.12)
            clip = clip.set_audio(music)
        except Exception:
            pass

    if not out_path:
        stem = Path(json_path).with_suffix("")
        out_path = str(stem) + "_guess_team.mp4"
    clip.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac",
                         preset="medium", threads=4)
    clip.close()
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    import sys
    render_guess_team(sys.argv[1],
                      sys.argv[2] if len(sys.argv) > 2 else None,
                      sys.argv[3] if len(sys.argv) > 3 else None)
