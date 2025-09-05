
#!/usr/bin/env python3
"""
Selects 1 lineup per sport each day from pools, writes dated JSONs with
reveal_on_screen true, and prints their paths (one per line).
"""
import json, sys, datetime
from pathlib import Path
ROOT = Path(".")
POOLS = ROOT/"data/pools"
OUT = ROOT/"data/out"/datetime.date.today().isoformat()
OUT.mkdir(parents=True, exist_ok=True)

def choose(items, day):
    # deterministic by date: rotate through list
    return items[day % len(items)]

def write_file(mode, bg, obj):
    obj = dict(obj)  # shallow copy
    obj["mode"] = mode
    obj["background"] = bg
    obj["title"] = ""
    obj["handle"] = obj.get("handle","@CoachClicks • #Shorts")
    obj["reveal_on_screen"] = True
    p = OUT/f"lineup_{mode}.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(p.as_posix())

def main():
    today = datetime.date.today()
    doy = int(today.strftime("%j"))  # 1..366
    b = json.loads((POOLS/"basketball.json").read_text(encoding="utf-8"))
    f = json.loads((POOLS/"football.json").read_text(encoding="utf-8"))
    s = json.loads((POOLS/"soccer.json").read_text(encoding="utf-8"))
    write_file("basketball","assets/backgrounds/basketball.png", choose(b, doy))
    write_file("football","assets/backgrounds/football.png", choose(f, doy))
    write_file("soccer","assets/backgrounds/soccer.png", choose(s, doy))

if __name__ == "__main__":
    main()
