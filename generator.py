import csv, random, json, datetime as dt
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_teams():
    leagues = defaultdict(list)
    for fname in ["nfl.csv", "nba.csv", "mlb.csv"]:
        with open(DATA_DIR / fname, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                leagues[r["league"]].append(r)
    flat = [t for v in leagues.values() for t in v]
    return leagues, flat

def city_to_leagues(leagues):
    m = defaultdict(set)
    for L, lst in leagues.items():
        for t in lst:
            m[t["city"]].add(L)
    return m

def q_which_not_in_division(leagues):
    L = random.choice(list(leagues.keys()))
    by_div = defaultdict(list)
    for t in leagues[L]: by_div[t["division"]].append(t)
    good_div = random.choice([d for d,v in by_div.items() if len(v) >= 3])
    corrects = random.sample(by_div[good_div], 3)
    other_div = random.choice([d for d in by_div if d != good_div])
    wrong = random.choice(by_div[other_div])
    options = [f'{t["city"]} {t["team"]}' for t in corrects] + [f'{wrong["city"]} {wrong["team"]}']
    random.shuffle(options)
    return {
        "type":"not_in_division",
        "question":f"Which team is NOT in the {good_div} ({L})?",
        "options":options,
        "answer":f'{wrong["city"]} {wrong["team"]}',
        "meta":{"league":L,"division":good_div}
    }

def q_pair_same_division(leagues):
    L = random.choice(list(leagues.keys()))
    by_div = defaultdict(list)
    for t in leagues[L]: by_div[t["division"]].append(t)
    target_div = random.choice([d for d,v in by_div.items() if len(v) >= 2])
    a,b = random.sample(by_div[target_div], 2)
    correct = f'{a["team"]} & {b["team"]}'
    teams = leagues[L]
    distractors = set()
    while len(distractors) < 3:
        x,y = random.sample(teams, 2)
        if x["division"] != y["division"]:
            distractors.add(f'{x["team"]} & {y["team"]}')
    options = list(distractors) + [correct]
    random.shuffle(options)
    return {
        "type":"pair_same_division",
        "question":f"Which pair plays in the SAME division ({L})?",
        "options":options,
        "answer":correct,
        "meta":{"league":L,"division":target_div}
    }

def q_city_cross_league(leagues):
    c2L = city_to_leagues(leagues)
    city, Ls = random.choice([(c, Ls) for c, Ls in c2L.items() if len(Ls) >= 2])
    L1, L2 = random.sample(list(Ls), 2)
    correct = city
    all_cities = {t["city"] for v in leagues.values() for t in v}
    distractors = [c for c in all_cities if not ({L1, L2} <= c2L.get(c, set()))]
    options = random.sample(distractors, 3) + [correct]
    random.shuffle(options)
    return {
        "type":"city_cross_league",
        "question":f"Which city has teams in BOTH the {L1} and the {L2}?",
        "options":options,
        "answer":correct,
        "meta":{"leagues":[L1, L2]}
    }

def q_fix_mismatch(leagues):
    L = random.choice(list(leagues.keys()))
    true = random.choice(leagues[L])
    correct = f'{true["city"]} {true["team"]}'
    cities = [t["city"] for t in leagues[L] if t["city"] != true["city"]]
    teams  = [t["team"] for t in leagues[L] if t["team"] != true["team"]]
    mismatches = set()
    while len(mismatches) < 3 and cities and teams:
        c = random.choice(cities); tm = random.choice(teams)
        if not (c == true["city"] and tm == true["team"]):
            mismatches.add(f"{c} {tm}")
    options = list(mismatches) + [correct]
    random.shuffle(options)
    return {
        "type":"fix_mismatch",
        "question":f"Which city–team pairing is CORRECT in the {L}?",
        "options":options,
        "answer":correct,
        "meta":{"league":L}
    }

def q_division_count(leagues):
    L = random.choice(list(leagues.keys()))
    by_div = defaultdict(list)
    for t in leagues[L]: by_div[t["division"]].append(t)
    div = random.choice(list(by_div))
    n = len(by_div[div])
    options = {n}
    while len(options) < 4:
        options.add(max(2, n + random.choice([-2,-1,1,2,3])))
    options = list(options); random.shuffle(options)
    return {
        "type":"division_count",
        "question":f"How many teams are in the {div} ({L})?",
        "options":[str(x) for x in options],
        "answer":str(n),
        "meta":{"league":L,"division":div,"true_count":n}
    }

QUESTION_BANK = [q_which_not_in_division, q_pair_same_division, q_city_cross_league, q_fix_mismatch, q_division_count]

def generate_daily(n_questions=10, seed=None):
    if seed is not None: random.seed(seed)
    leagues, _ = load_teams()
    qlist = [random.choice(QUESTION_BANK)(leagues) for _ in range(n_questions)]
    date_str = dt.datetime.utcnow().strftime("%Y-%m-%d")
    out = {"date": date_str, "questions": qlist}
    path = OUT_DIR / f"trivia_{date_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Wrote", path)
    return path

if __name__ == "__main__":
    generate_daily()
