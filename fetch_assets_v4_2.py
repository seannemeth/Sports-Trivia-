
#!/usr/bin/env python3
"""
fetch_assets_v4_2.py
- Smarter college logo queries (nickname/athletics/university variants)
- ISO3 flag mapping (e.g., BRA->Brazil) and fallback
- Optional alias files to override names:
    assets/aliases.colleges.json  ({"Iowa":"Iowa Hawkeyes", ...})
    assets/aliases.flags.json     ({"BRA":"Brazil", "ENG":"England", ...})
- Writes sources to assets/_sources.csv
Usage:
  python fetch_assets_v4_2.py data/lineup_*.json ...
Requires: requests, pillow
"""
import os, re, sys, csv, json, time, io
from pathlib import Path
from urllib.parse import urlencode
import requests
from PIL import Image, ImageOps, ImageFilter, ImageDraw

HEADERS = {"User-Agent": "CoachClicks-AssetsFetcher/1.1"}
API = "https://commons.wikimedia.org/w/api.php"

COL_DIR = Path("assets/college_logos"); COL_DIR.mkdir(parents=True, exist_ok=True)
FLG_DIR = Path("assets/flags"); FLG_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = Path("assets/_sources.csv")
ALIASES_COL = Path("assets/aliases.colleges.json")
ALIASES_FLG = Path("assets/aliases.flags.json")

ISO3 = {
  "ARG":"Argentina","AUT":"Austria","BEL":"Belgium","BRA":"Brazil","DEU":"Germany","ENG":"England","ESP":"Spain","FRA":"France",
  "GER":"Germany","ITA":"Italy","NED":"Netherlands","NOR":"Norway","POL":"Poland","POR":"Portugal","PRT":"Portugal","URU":"Uruguay","USA":"United States"
}

# Common college nickname aliases (extendable via assets/aliases.colleges.json)
COLLEGE_ALIASES = {
  "Arizona":"Arizona Wildcats",
  "Arizona State":"Arizona State Sun Devils",
  "Baylor":"Baylor Bears",
  "Gonzaga":"Gonzaga Bulldogs",
  "Iowa":"Iowa Hawkeyes",
  "Iowa State":"Iowa State Cyclones",
  "Kentucky":"Kentucky Wildcats",
  "McKendree":"McKendree Bearcats",
  "Missouri":"Missouri Tigers",
  "Notre Dame":"Notre Dame Fighting Irish",
  "South Carolina":"South Carolina Gamecocks",
  "Stanford":"Stanford Cardinal",
  "UTEP":"UTEP Miners",
  "West Virginia":"West Virginia Mountaineers",
  "Texas A&M":"Texas A&M Aggies",
  "Ohio State":"Ohio State Buckeyes",
  "LSU":"LSU Tigers",
  "USC":"USC Trojans",
  "UCLA":"UCLA Bruins",
  "Alabama":"Alabama Crimson Tide",
  "Duke":"Duke Blue Devils",
  "Georgia":"Georgia Bulldogs",
  "Murray State":"Murray State Racers",
  "Texas Tech":"Texas Tech Red Raiders",
  "Clemson":"Clemson Tigers",
  "Oklahoma":"Oklahoma Sooners",
  "Oklahoma State":"Oklahoma State Cowboys",
  "Pitt":"Pittsburgh Panthers",
}

def load_aliases():
    if ALIASES_COL.exists():
        try:
            COLLEGE_ALIASES.update(json.load(open(ALIASES_COL, "r", encoding="utf-8")))
        except Exception as e:
            print("[warn] aliases.colleges load:", e)
    if ALIASES_FLG.exists():
        try:
            ISO3.update(json.load(open(ALIASES_FLG, "r", encoding="utf-8")))
        except Exception as e:
            print("[warn] aliases.flags load:", e)

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

def search_commons(query:str, limit=10):
    params = {
        "action":"query","format":"json","prop":"imageinfo",
        "generator":"search","gsrsearch": query + " filetype:(svg|png)",
        "gsrnamespace":"6","gsrlimit": str(limit),
        "iiprop":"url|size|mime|extmetadata|canonicaltitle",
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
        mime=c.get("mime","")
        if mime.endswith("svg"): s+=5
        if mime.endswith("png"): s+=3
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
    arr = img.getdata()
    r=g=b=n=0
    for px in arr:
        if len(px)==4 and px[3]==0: continue
        rr,gg,bb = px[:3]
        r+=rr; g+=gg; b+=bb; n+=1
    if n==0: return (200,200,200)
    return (r//n, g//n, b//n)

def frameify(img, pad=9, radius=14):
    w,h = img.size
    card = Image.new("RGBA",(w+pad*2, h+pad*2),(255,255,255,235))
    # rounded corners
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

def college_query_variants(name:str):
    uni = name
    nick = COLLEGE_ALIASES.get(name, name)
    variants = []
    variants += [
        f"{nick} logo",
        f"{nick} athletics logo",
        f"{uni} {nick.split()[-1]} logo" if nick!=uni else f"{uni} athletics logo",
        f"{uni} logo athletics",
        f"{uni} logo",
        f"{uni} wordmark logo",
    ]
    seen=set(); out=[]
    for q in variants:
        if q not in seen:
            seen.add(q); out.append(q)
    return out

def fetch_logo(school:str):
    # Handle country mistakenly in college slot (e.g., "Serbia")
    if school in ISO3.values():
        img = fetch_flag_by_name(school)
        if img: return img
    slug = slugify(school)
    out = COL_DIR/f"{slug}.png"
    if out.exists() and out.stat().st_size>0: return out
    for q in college_query_variants(school):
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

def fetch_flag_by_name(name:str):
    slug = slugify(name)
    out = FLG_DIR/f"{slug.upper()}.png"
    if out.exists() and out.stat().st_size>0: return out
    for q in [f"Flag of {name}", f"{name} flag emblem", f"{name} flag"]:
        try:
            best = choose_best(search_commons(q))
            if not best: continue
            img = download_image(best["url"])
            img = normalize_logo(img, max_wh=130)
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, "PNG")
            write_manifest_row("flag", name, out.as_posix(), best["source"], best["license"], best["url"])
            time.sleep(0.3)
            return out
        except Exception as e:
            print("[warn] flag", name, e)
    print("[miss] flag", name)
    return None

def flag_name_from_code(code:str):
    code = code.strip().upper()
    return ISO3.get(code)

def fetch_flag(code_or_name:str):
    code_or_name = (code_or_name or "").strip()
    name = flag_name_from_code(code_or_name) or code_or_name
    return fetch_flag_by_name(name)

def extract_targets(json_paths):
    colleges=set(); flags=set()
    for p in json_paths:
        try:
            d=json.load(open(p,"r",encoding="utf-8"))
            for pl in d.get("players",[]):
                if pl.get("college"): colleges.add(pl["college"])
                if pl.get("flag"): flags.add(pl["flag"])
        except Exception as e:
            print("[warn] reading", p, e)
    return sorted(colleges), sorted(flags)

def main(argv):
    if not argv:
        print("Pass JSON paths like data/lineup_basketball.json ..."); return 0
    load_aliases()
    cols, flgs = extract_targets(argv)
    print(f"Colleges: {len(cols)} Flags: {len(flgs)}")
    for c in cols: fetch_logo(c)
    for f in flgs: fetch_flag(f)
    print("Done.")
    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
