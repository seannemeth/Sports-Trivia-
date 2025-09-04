
import os, json
from pathlib import Path
from generator import generate_daily
from render_cards import render_cards
from render_short import render_short

def ensure_public_index(today_json, out_cards_dir, short_path):
    public = Path(__file__).parent / "public"
    public.mkdir(exist_ok=True)
    date_str = Path(today_json).stem.replace("trivia_", "")
    day_dir = public / date_str
    day_dir.mkdir(exist_ok=True)

    import shutil, glob
    for p in glob.glob(str(out_cards_dir) + "/*.png"):
        shutil.copy(p, day_dir / os.path.basename(p))
    if os.path.exists(short_path):
        shutil.copy(short_path, day_dir / os.path.basename(short_path))

    index = public / "index.html"
    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Daily Sports Trivia</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial,sans-serif; background:#0f1115; color:#eee; padding:24px}}
.grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(220px,1fr)); gap:16px;}}
.card{{background:#181a20; border-radius:16px; padding:12px}}
a{{color:#8dd0ff; text-decoration:none}}
img{{width:100%; border-radius:12px}}
</style>
</head><body>
<h1>Daily Sports Trivia</h1>
<p>Generated on {date_str}. Each day auto-updates.</p>
<div class="grid">
"""
    import glob
    for p in sorted(glob.glob(str(day_dir / "*.png"))):
        rel = p.split("public/")[1]
        html += f'<div class="card"><img src="{rel}" /></div>\n'

    html += "</div></body></html>"
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    json_path = generate_daily(n_questions=10)
    cards_dir = render_cards(json_path)
    short_path = render_short(json_path, index=1, out_path=None, music_path="assets/soft_loop.mp3")
    ensure_public_index(json_path, cards_dir, short_path)
    print("Done.")

if __name__ == "__main__":
    main()
