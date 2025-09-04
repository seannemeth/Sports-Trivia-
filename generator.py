
import csv, random, json, os, datetime as dt
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_teams():
    teams = []
    for fname in ["nfl.csv", "nba.csv", "mlb.csv"]:
        with open(DATA_DIR / fname, newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                teams.append(r)
    return teams

def mcq_city_for_team(teams):
    t = random.choice(teams)
    correct = t["city"]
    league = t["league"]
    teamname = t["team"]
    wrongs = set()
    same_league = [x for x in teams if x["league"] == league and x["city"] != correct]
    while len(wrongs) < 3 and same_league:
        wrongs.add(random.choice(same_league)["city"])
    options = list(wrongs) + [correct]
    random.shuffle(options)
    prompt = f"In which city do the {teamname} play ({league})?"
    answer = correct
    return {"type":"city_for_team","question":prompt,"options":options,"answer":answer,"meta":{"league":league,"team":teamname}}

def mcq_team_for_city(teams):
    t = random.choice(teams)
    correct = t["team"]
    league = t["league"]
    city = t["city"]
    same_league = [x for x in teams if x["league"] == league and x["team"] != correct and x["city"] != city]
    wrongs = set()
    while len(wrongs) < 3 and same_league:
        wrongs.add(random.choice(same_league)["team"])
    options = list(wrongs) + [correct]
    random.shuffle(options)
    prompt = f"Which {league} team plays in {city}?"
    answer = correct
    return {"type":"team_for_city","question":prompt,"options":options,"answer":answer,"meta":{"league":league,"city":city}}

def mcq_division_for_team(teams):
    t = random.choice(teams)
    correct = t["division"]
    league = t["league"]
    teamname = t["team"]
    all_divs = sorted({x["division"] for x in teams if x["league"] == league})
    distractors = [d for d in all_divs if d != correct]
    options = random.sample(distractors, k=3) + [correct]
    random.shuffle(options)
    prompt = f"In which division do the {teamname} play ({league})?"
    answer = correct
    return {"type":"division_for_team","question":prompt,"options":options,"answer":answer,"meta":{"league":league,"team":teamname}}

def generate_daily(n_questions=10, seed=None):
    if seed is not None:
        random.seed(seed)
    teams = load_teams()
    qlist = []
    generators = [mcq_city_for_team, mcq_team_for_city, mcq_division_for_team]
    for _ in range(n_questions):
        q = random.choice(generators)(teams)
        qlist.append(q)
    date_str = dt.datetime.utcnow().strftime("%Y-%m-%d")
    out = {"date": date_str, "questions": qlist}
    path = OUT_DIR / f"trivia_{date_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Wrote", path)
    return path

if __name__ == "__main__":
    generate_daily()
