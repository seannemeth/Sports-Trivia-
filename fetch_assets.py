
# fetch_assets.py
# - Downloads soccer flags (PNG) for ISO3 codes in data/*.json
# - Creates placeholder monogram logos for colleges when no PNG exists

import json, os, hashlib, io, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DATA = Path("data")
FLAGS_DIR = Path("assets/flags"); FLAGS_DIR.mkdir(parents=True, exist_ok=True)
COLLEGE_DIR = Path("assets/college_logos"); COLLEGE_DIR.mkdir(parents=True, exist_ok=True)

ISO3_TO_2 = {
    "USA":"us","BRA":"br","ARG":"ar","FRA":"fr","ENG":"gb","GER":"de","ESP":"es","POR":"pt",
    "NED":"nl","ITA":"it","BEL":"be","URU":"uy","MEX":"mx","POL":"pl","JPN":"jp","KOR":"kr"
}

def slug(s: str) -> str:
    import re
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"

def download_flag(iso3: str):
    iso3 = (iso3 or "").upper()
    if not iso3: return
    target = FLAGS_DIR / f"{iso3}.png"
    if target.exists(): return
    a2 = ISO3_TO_2.get(iso3)
    if not a2:
        print(f"[flags] No ISO2 map for {iso3}; skipping (will render text).")
        return
    url = f"https://flagcdn.com/w160/{a2}.png"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = r.read()
        Image.open(io.BytesIO(data)).convert("RGBA").save(target, "PNG")
        print(f"[flags] Saved {target}")
    except Exception as e:
        print(f"[flags] Failed {iso3} -> {url}: {e}")

def mono_color(name: str):
    h = hashlib.md5(name.encode("utf-8")).hexdigest()
    r = (int(h[0:2],16)//2)+60; g = (int(h[2:4],16)//2)+60; b = (int(h[4:6],16)//2)+60
    return (r,g,b)

def ensure_college_logo(college: str):
    if not college: return
    fn = COLLEGE_DIR / f"{slug(college)}.png"
    if fn.exists(): return
    initials = "".join([w[0] for w in college.split() if w][:2]).upper()
    size = 120
    img = Image.new("RGBA",(size,size),(0,0,0,0))
    d = ImageDraw.Draw(img)
    bg = mono_color(college)
    d.ellipse((0,0,size,size), fill=bg+(255,))
    for fp in ["assets/fonts/Inter-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            fnt = ImageFont.truetype(fp, 58); break
        except Exception: fnt = None
    if fnt is None: fnt = ImageFont.load_default()
    tw = int(d.textlength(initials, font=fnt)); th = int(fnt.size*1.1)
    d.text(((size-tw)//2, (size-th)//2), initials, font=fnt, fill=(255,255,255))
    img.save(fn, "PNG")
    print(f"[college] Placeholder {fn} created")

def collect_from_json(jpath: Path):
    try:
        j = json.load(open(jpath,"r",encoding="utf-8"))
    except Exception as e:
        print(f"[json] skip {jpath}: {e}"); return
    mode = (j.get("mode","")).lower()
    if mode == "soccer":
        for p in j.get("players", []):
            download_flag(p.get("flag") or p.get("country") or "")
    elif mode in ("basketball","football"):
        for p in j.get("players", []):
            ensure_college_logo(p.get("college",""))

def main():
    for p in DATA.glob("*.json"):
        collect_from_json(p)
    print("Done.")

if __name__ == "__main__":
    main()
