
#!/usr/bin/env python3
"""
Fetches missing college logos and country flags from Wikimedia Commons,
normalizes them (transparent PNG, framed), and records a sources manifest.
Usage:
  python fetch_assets_v4.py data/lineup_basketball.json data/lineup_football.json data/lineup_soccer.json
Requires: requests, pillow
"""
import os, re, sys, csv, json, time, io
from pathlib import Path
from urllib.parse import urlencode
import requests
from PIL import Image, ImageOps, ImageFilter

HEADERS = {"User-Agent": "CoachClicks-AssetsFetcher/1.0"}
API = "https://commons.wikimedia.org/w/api.php"

COL_DIR = Path("assets/college_logos"); COL_DIR.mkdir(parents=True, exist_ok=True)
FLG_DIR = Path("assets/flags"); FLG_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = Path("assets/_sources.csv")

def slugify(s:str)->str:
    s = re.sub(r"[^A-Za-z0-9]+","-",s.strip().lower())
    return re.sub(r"-+","-",s).strip("-") or "x"

def write_manifest_row(kind, name, file, source, license_name, url):
    exists = MANIFEST.exists()
    with MANIFEST.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["kind","name","file","source","license","download_url"])
        w.writerow([kind, name, file, source, license_name, url])

def search_commons(query:str, limit=8):
    params = {
        "action":"query","format":"json","prop":"imageinfo",
        "generator":"search","gsrsearch": query + " filetype:(svg|png)",
        "gsrnamespace":"6","gsrlimit": str(limit),
        "iiprop":"url|size|mime|extmetadata|canonicaltitle|mediatype|commonmetadata",
        "iiurlwidth":"512"
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    pages = r.json().get("query",{}).get("pages",{})
    out = []
    for _,p in pages.items():
        if "imageinfo" not in p: continue
        ii = p["imageinfo"][0]
        meta = ii.get("extmetadata",{})
        out.append({
            "title": p.get("title",""),
            "mime": ii.get("mime",""),
            "url": ii.get("thumburl") or ii.get("url"),
            "width": ii.get("thumbwidth") or ii.get("width"),
            "height": ii.get("thumbheight") or ii.get("height"),
            "license": meta.get("LicenseShortName",{}).get("value",""),
            "source": ii.get("descriptionshorturl") or ii.get("url","")
        })
    return out

def choose_best(cands):
    def score(c):
        s=0
        if c["mime"] and c["mime"].endswith("svg"): s+=5
        if c["mime"] and c["mime"].endswith("png"): s+=3
        if (c.get("width") or 0) >= 256: s+=2
        if "logo" in (c.get("title","").lower()): s+=2
        return s
    cands = sorted(cands, key=score, reverse=True)
    return cands[0] if cands else None

def download_image(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")

def average_color(img):
    # ignore transparent pixels
    arr = img.getdata()
    r=g=b=n=0
    for px in arr:
        if len(px)==4 and px[3]==0: continue
        rr,gg,bb = px[:3]
        r+=rr; g+=gg; b+=bb; n+=1
    if n==0: return (200,200,200)
    return (r//n, g//n, b//n)

def frameify(img, pad=9, radius=14):
    # pad and add rounded white card with slight border using avg color
    w,h = img.size
    card = Image.new("RGBA",(w+pad*2, h+pad*2),(255,255,255,235))
    # subtle outer stroke using avg color
    avg = average_color(img)
    stroke = Image.new("RGBA", (w+pad*2+6, h+pad*2+6), (0,0,0,0))
    from PIL import ImageDraw
    d=ImageDraw.Draw(stroke)
    d.rounded_rectangle((0,0,stroke.size[0]-1,stroke.size[1]-1), radius=radius+6, outline=avg+(220,), width=4, fill=(0,0,0,0))
    # rounded corners on card
    corner = Image.new('L', (radius, radius), 0)
    ImageDraw.Draw(corner).pieslice((0, 0, radius*2, radius*2), 180, 270, fill=255)
    alpha = Image.new('L', (card.size[0], card.size[1]), 255)
    alpha.paste(corner, (0,0))
    alpha.paste(corner.rotate(90), (0, card.size[1]-radius))
    alpha.paste(corner.rotate(180), (card.size[0]-radius, card.size[1]-radius))
    alpha.paste(corner.rotate(270), (card.size[0]-radius, 0))
    card.putalpha(alpha)
    card.paste(img, (pad,pad), img)
    return card

def normalize_logo(img, max_wh=110):
    w,h=img.size
    r = min(max_wh/w, max_wh/h, 1.0)
    img = img.resize((int(w*r), int(h*r)), Image.LANCZOS)
    return frameify(img)

def fetch_logo(school:str):
    slug = slugify(school)
    out = COL_DIR/f"{slug}.png"
    if out.exists() and out.stat().st_size>0: return out
    queries = [f"{school} athletics logo", f"{school} logo", f"{school} wordmark"]
    for q in queries:
        try:
            best = choose_best(search_commons(q))
            if not best: continue
            img = download_image(best["url"])
            img = normalize_logo(img, max_wh=110)
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, "PNG")
            write_manifest_row("college", school, out.as_posix(), best["source"], best["license"], best["url"])
            time.sleep(0.3)
            return out
        except Exception as e:
            print("[warn]", school, e)
    print("[miss]", school)
    return None

def fetch_flag(code:str):
    code = code.upper()
    out = FLG_DIR/f"{code}.png"
    if out.exists() and out.stat().st_size>0: return out
    # Commons stores flags as "Flag of USA.svg" type
    queries = [f"Flag of {code}", f"{code} flag"]
    for q in queries:
        try:
            best = choose_best(search_commons(q))
            if not best: continue
            img = download_image(best["url"])
            img = normalize_logo(img, max_wh=130)  # flags a bit wider
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, "PNG")
            write_manifest_row("flag", code, out.as_posix(), best["source"], best["license"], best["url"])
            time.sleep(0.3)
            return out
        except Exception as e:
            print("[warn] flag", code, e)
    print("[miss] flag", code)
    return None

def extract_targets(json_paths):
    colleges=set(); flags=set()
    for p in json_paths:
        try:
            d=json.load(open(p,"r",encoding="utf-8"))
            for pl in d.get("players",[]):
                if "college" in pl and pl["college"]: colleges.add(pl["college"])
                if "flag" in pl and pl["flag"]: flags.add(pl["flag"].upper())
        except Exception as e:
            print("[warn] reading", p, e)
    return sorted(colleges), sorted(flags)

def main(argv):
    if not argv:
        print("Pass JSON paths like data/lineup_basketball.json ..."); return 0
    cols, flgs = extract_targets(argv)
    print("Colleges:", len(cols), "Flags:", len(flgs))
    for c in cols: fetch_logo(c)
    for f in flgs: fetch_flag(f)
    print("Done.")
    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
