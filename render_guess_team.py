
import os, json, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

W, H = 1080, 1920
SAFE = 48
DURATION = 18.0  # seconds

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

def _wrap_lines(text, draw, font, max_w):
    if max_w is None: return [text]
    words = (text or "").split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if int(draw.textlength(t, font=font)) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]

def _pill(text, font, color=(10,35,70), txt=(255,255,255), max_w=None, line_gap=6):
    dmy = Image.new("RGBA",(10,10)); draw = ImageDraw.Draw(dmy)
    inner_max = None if max_w is None else max(100, max_w - 38)
    lines = _wrap_lines(text, draw, font, inner_max)
    tw = max(int(draw.textlength(line, font=font)) for line in lines) if lines else 0
    lh = int(font.size*1.05)
    h  = lh*len(lines) + 26 + (max(0, len(lines)-1))*line_gap
    w  = max(160, tw + 38)
    pill = Image.new("RGBA", (w,h), (0,0,0,0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle((0,0,w,h), radius=16, fill=(color[0],color[1],color[2],235))
    y = (h - (lh*len(lines) + (len(lines)-1)*line_gap))//2
    for line in lines:
        lx = (w - int(pd.textlength(line, font=font)))//2
        pd.text((lx, y), line, font=font, fill=txt)
        y += lh + line_gap
    return pill

def _pos_badge(text, bg=(0,0,0), fg=(255,255,255), *, font_size=32, max_w=200):
    f = _font(font_size)
    dmy = Image.new("RGBA",(10,10)); dr = ImageDraw.Draw(dmy)
    t = (text or "").upper()
    while int(dr.textlength(t, font=f)) > max_w - 26 and len(t) > 3:
        t = t[:-2] + "…"
    tw = int(dr.textlength(t, font=f))
    h  = int(f.size*1.05) + 16
    w  = max(56, min(max_w, tw + 26))
    badge = Image.new("RGBA",(w,h),(0,0,0,0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle((0,0,w,h), radius=12, fill=(bg[0],bg[1],bg[2],220))
    bd.text(((w - tw)//2, (h - int(f.size*1.05))//2 + 4), t, font=f, fill=fg)
    return badge

def _slug(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"

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

def _avoid_overlap(xy, size, placed, step=18, top=SAFE, bottom=H-SAFE):
    x, y = xy; w, h = size
    def inter(a, b):
        ax, ay, aw, ah = a; bx, by, bw, bh = b
        return not (ax+aw <= bx or bx+bw <= ax or ay+ah <= by or by+bh <= ay)
    rect = [x,y,w,h]
    for _ in range(100):
        if any(inter(rect, r) for r in placed):
            ny = y - step if y - step >= top else min(bottom-h, y + step)
            if ny == y: break
            y = ny; rect[1] = y
        else:
            break
    placed.append(tuple(rect))
    return (x,y)

def _reveal_overlay(text, w=W, h=H):
    # Build a transparent overlay with centered reveal pill
    ov = Image.new("RGBA", (w,h), (0,0,0,0))
    draw = ImageDraw.Draw(ov)
    # subtle dim behind
    draw.rectangle((0,0,w,h), fill=(0,0,0,110))
    f = _font(64)
    pill = _pill(text, f, color=(0,160,255), txt=(16,18,24))
    sh = _shadow(pill, expand=12, radius=12, alpha=130, r=22)
    x = (w - pill.size[0])//2
    y = int(h*0.78)  # near bottom-center
    ov.paste(sh, (x-12, y-12), sh)
    ov.paste(pill, (x, y), pill)
    return ov

def render_guess_team(json_path, out_path=None, music_path=None):
    data = json.load(open(json_path, "r", encoding="utf-8"))
    mode = data.get("mode","basketball").lower()
    bg_path = data.get("background", "assets/backgrounds/basketball.png")
    bg = Image.open(bg_path).convert("RGB").resize((W,H))
    draw = ImageDraw.Draw(bg)

    title = (data.get("title") or "").strip()
    if title:
        f_title = _font(46)
        tw = int(draw.textlength(title, font=f_title))
        w  = min(tw + 32, 520)
        h  = int(f_title.size*1.1) + 18
        badge = Image.new("RGBA", (w, h), (0,0,0,0))
        bd = ImageDraw.Draw(badge)
        bd.rounded_rectangle((0,0,w,h), radius=14, fill=(0,0,0,140))
        bd.text((16, 8), title, font=f_title, fill=(255,255,255))
        bg.paste(badge, (SAFE, SAFE), badge)

    f_lab = _font(46)
    max_y = 0
    placed_rects = []

    if mode == "basketball":
        pos_map = {
            "PG": (W//2, 520),
            "SG": (W//2 + 260, 660),
            "SF": (W//2 - 260, 660),
            "PF": (W//2 - 200, 900),
            "C" : (W//2 + 200, 900),
        }
        color = (10,35,70)
        logo_root = Path("assets/college_logos")
        for p in data["players"]:
            college = p.get("college","")
            pos = pos_map.get((p.get("pos","")).upper(), (W//2, H//2))
            pill = _pill(college, f_lab, color=color, max_w=360)
            logo_img = None
            if college:
                slug = re.sub(r"[^a-z0-9]+","-",college.lower()).strip("-")
                for folder in [logo_root, Path("assets/logos/colleges")]:
                    cand = folder / f"{slug}.png"
                    if cand.exists():
                        logo_img = Image.open(cand).convert("RGBA"); break

            stack, (sx, sy) = _stack_with_logo(pos, pill, logo_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            placed_rects.append((sx, sy, stack.size[0], stack.size[1]))

            name = (p.get("pos","")).upper()
            pb = _pos_badge(name, bg=(20,40,85), font_size=32, max_w=200)
            bx = sx + (stack.size[0] - pb.size[0]) // 2
            by = sy - pb.size[1] - 10
            bx, by = _avoid_overlap((bx, by), pb.size, placed_rects, top=SAFE)
            bg.paste(pb, (bx, by), pb)
            max_y = max(max_y, sy + stack.size[1])

    elif mode == "football":
        pos_map = {
            "LT": (220, 620), "LG": (360, 620), "C": (540, 620),
            "RG": (720, 620), "RT": (860, 620),
            "QB": (540, 760), "RB": (540, 900),
            "TE": (860, 760),
            "WR1": (140, 780), "WR2": (940, 780), "WR3": (220, 980),
        }
        color = (15,45,18)
        logo_root = Path("assets/college_logos")
        for p in data["players"]:
            college = p.get("college","")
            pos = pos_map.get((p.get("pos","")).upper(), (W//2, H//2))
            pill = _pill(college, f_lab, color=color, max_w=360)
            logo_img = None
            if college:
                slug = re.sub(r"[^a-z0-9]+","-",college.lower()).strip("-")
                for folder in [logo_root, Path("assets/logos/colleges")]:
                    cand = folder / f"{slug}.png"
                    if cand.exists():
                        logo_img = Image.open(cand).convert("RGBA"); break

            stack, (sx, sy) = _stack_with_logo(pos, pill, logo_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            placed_rects.append((sx, sy, stack.size[0], stack.size[1]))

            name = (p.get("pos","")).upper()
            pb = _pos_badge(name, bg=(25,80,30), font_size=32, max_w=200)
            bx = sx + (stack.size[0] - pb.size[0]) // 2
            by = sy - pb.size[1] - 10
            bx, by = _avoid_overlap((bx, by), pb.size, placed_rects, top=SAFE)
            bg.paste(pb, (bx, by), pb)
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
            pos = pos_map.get((p.get("pos","")).upper(), (W//2, H//2))
            label = iso or country or "—"
            pill = _pill(label, f_lab, color=color, max_w=320)

            flag_img = None
            if iso:
                for folder in [Path("assets/flags"), Path("assets/logos/flags")]:
                    cand = folder / f"{iso}.png"
                    if cand.exists():
                        flag_img = Image.open(cand).convert("RGBA"); break

            stack, (sx, sy) = _stack_with_logo(pos, pill, flag_img, gap=8)
            sh = _shadow(stack, alpha=110, r=24)
            bg.paste(sh, (sx-18, sy-18), sh)
            bg.paste(stack, (sx, sy), stack)
            placed_rects.append((sx, sy, stack.size[0], stack.size[1]))

            name = (p.get("pos","")).upper()
            pb = _pos_badge(name, bg=(25,95,35), font_size=32, max_w=200)
            bx = sx + (stack.size[0] - pb.size[0]) // 2
            by = sy - pb.size[1] - 10
            bx, by = _avoid_overlap((bx, by), pb.size, placed_rects, top=SAFE)
            bg.paste(pb, (bx, by), pb)
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
    draw.text((SAFE, H - SAFE - _lh(draw, f_meta)), handle, font=f_meta, fill=(245,245,245))

    # Base clip
    arr = np.array(bg)
    base = ImageClip(arr).set_duration(DURATION)

    # Optional music
    music_path = music_path or data.get("music")
    if music_path and os.path.exists(music_path) and os.path.getsize(music_path) > 0:
        try:
            music = AudioFileClip(music_path).volumex(0.12)
            base = base.set_audio(music)
        except Exception:
            pass

    # On-screen reveal
    reveal = (data.get("reveal_on_screen") in [True, "true", "yes", "1"])
    answer = (data.get("answer") or "").strip()
    if reveal and answer:
        ov = _reveal_overlay(answer)
        ov_arr = np.array(ov)
        overlay = ImageClip(ov_arr).set_duration(max(1.8, float(data.get("reveal_seconds", 2.2))))
        overlay = overlay.set_start(DURATION - overlay.duration).crossfadein(0.35)
        clip = CompositeVideoClip([base, overlay])
    else:
        clip = base

    if not out_path:
        stem = Path(json_path).with_suffix("")
        out_path = str(stem) + "_guess_team.mp4"
    clip.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", preset="medium", threads=4)
    clip.close()
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    import sys
    render_guess_team(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
