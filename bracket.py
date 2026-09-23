"""MLB 포스트시즌 대진표 데이터 만들기.

MLB 공식 Stats API에서 순위와 각 팀의 시즌 일정을 가져와,
- 리그별 6개 시드(지구 우승 3 + 와일드카드 3)를 정하고
- 와일드카드 시리즈와 "맞붙을 수 있는" 디비전시리즈 상대를 정리하고
- 그 대진에서 실제로 만날 수 있는 팀끼리의 이번 시즌 상대전적을 계산한다.

MLB Stats API는 순위 페이지 안에 상대전적 표가 없어서, 관련된 팀(리그당 6팀)의
시즌 일정을 한 번씩 가져와 직접 계산한다. 캐시를 오래 유지해서 호출 횟수를 줄인다.
"""
import datetime
import os
import ssl
import urllib.request

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

STANDINGS_URL = (
    "https://statsapi.mlb.com/api/v1/standings"
    "?leagueId=103,104&season={season}&standingsTypes=regularSeason&hydrate=team,division,league"
)
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&season={season}&gameType=R"
POSTSEASON_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={season}&gameType=F,D,L,W"
POSTSEASON_TEAM_SCHEDULE_URL = (
    "https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={season}&gameType=F,D,L,W&teamId={team_id}"
)
BOXSCORE_URL = "https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
ROSTER_URL = "https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=40Man&hydrate=person(nationality)"

PLAYOFF_SEEDS = 6  # 리그당 진출 팀 수: 지구 우승 3 + 와일드카드 3

# (상위 시드, 하위 시드, 종류). 'wc'=와일드카드 시리즈(확정), 'ds'=디비전시리즈에서 맞붙을 수 있는 상대(가정)
BRACKET_PAIRS = [
    (3, 6, "wc"), (4, 5, "wc"),
    (1, 4, "ds"), (1, 5, "ds"), (2, 3, "ds"), (2, 6, "ds"),
]


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (mlb-postseason-bracket)"})
    with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as resp:
        import json
        return json.loads(resp.read().decode("utf-8"))


def fetch_standings(season):
    raw = _get_json(STANDINGS_URL.format(season=season))
    by_league = {"AL": [], "NL": []}
    for rec in raw["records"]:
        league = rec["league"]["abbreviation"]
        if league not in by_league:
            continue
        for t in rec["teamRecords"]:
            tm = t["team"]
            by_league[league].append({
                "id": tm["id"],
                "abbr": tm["abbreviation"],
                "name": tm["name"],
                "division": rec["division"]["abbreviation"][-1],
                "wins": t["wins"],
                "losses": t["losses"],
                "pct": float(t["winningPercentage"]),
                "pctText": t["winningPercentage"],
                "divisionRank": int(t["divisionRank"]),
                "wildCardRank": int(t["wildCardRank"]) if t.get("wildCardRank") else None,
                "leader": bool(t.get("divisionLeader")),
                "gamesBack": t.get("wildCardGamesBack") or t.get("divisionGamesBack") or "-",
            })
    return by_league


def compute_seeds(teams):
    """리그 팀 목록에서 1~6시드를 정한다. 지구 1위 3팀은 승률 순, 나머지는 와일드카드 순위 상위 3팀."""
    leaders = sorted((t for t in teams if t["leader"]), key=lambda t: -t["pct"])
    others = sorted((t for t in teams if not t["leader"] and t["wildCardRank"]), key=lambda t: t["wildCardRank"])
    ordered = leaders[:3] + others[:3]
    seeds = {}
    for i, t in enumerate(ordered):
        seeds[i + 1] = {**t, "seed": i + 1, "role": "지구 우승" if t["leader"] else f'와일드카드 {i - 2}위'}
    return seeds


def fetch_schedule_results(team_id, season):
    """이 팀의 정규시즌 중 이미 끝난 경기만, (상대팀ID, 이겼는지)로 정리한다."""
    raw = _get_json(SCHEDULE_URL.format(team_id=team_id, season=season))
    results = []
    for date in raw.get("dates", []):
        for g in date["games"]:
            if g["status"]["abstractGameState"] != "Final":
                continue
            home, away = g["teams"]["home"], g["teams"]["away"]
            mine, theirs = (home, away) if home["team"]["id"] == team_id else (away, home)
            results.append((theirs["team"]["id"], bool(mine.get("isWinner"))))
    return results


def head_to_head_from_schedule(schedule, opponent_id):
    w = sum(1 for opp, win in schedule if opp == opponent_id and win)
    l = sum(1 for opp, win in schedule if opp == opponent_id and not win)
    return {"w": w, "l": l}


def fetch_postseason_dates(season):
    """와일드카드부터 월드시리즈까지, 라운드(리그별)마다 실제 경기 날짜 범위를 가져온다.
    MLB은 참가팀이 정해지지 않은 라운드도 날짜는 시즌 전에 미리 정해 둔다.
    1차전 시작 시각은 대부분 나중에(중계 일정이 정해지면) 공개되므로,
    MLB이 아직 'TBD'로 표시했다면 시각 없이 날짜만 돌려주고, 정해진 뒤에는 자동으로 함께 돌려준다."""
    raw = _get_json(POSTSEASON_SCHEDULE_URL.format(season=season))
    buckets = {}
    for date in raw.get("dates", []):
        for g in date["games"]:
            gt = g["gameType"]
            desc = g.get("description", "")
            league = "AL" if desc.startswith("AL") else ("NL" if desc.startswith("NL") else None)
            buckets.setdefault((gt, league), []).append(g)

    def rng(gt, league=None):
        games = buckets.get((gt, league))
        if not games:
            return None
        dates = [g["gameDate"] for g in games]
        game1 = min(games, key=lambda g: (g.get("seriesGameNumber") or 1, g["gameDate"]))
        time_decided = not game1.get("status", {}).get("startTimeTBD", True)
        return {
            "start": min(dates), "end": max(dates),
            "game1Time": game1["gameDate"] if time_decided else None,
        }

    return {
        "wc": {"AL": rng("F", "AL"), "NL": rng("F", "NL")},
        "ds": {"AL": rng("D", "AL"), "NL": rng("D", "NL")},
        "cs": {"AL": rng("L", "AL"), "NL": rng("L", "NL")},
        "ws": rng("W"),
    }


def fetch_active_postseason_roster_ids(team_id, season):
    """이 팀이 이번 포스트시즌에 실제로 치른(또는 지금 치르고 있는) 가장 최근 경기의 박스스코어에서,
    그 경기에 실제로 출전 자격이 있었던 26인 로스터의 선수 ID 집합을 돌려준다.
    MLB API에는 라운드 시작 '전에' 26인 명단을 미리 보여주는 엔드포인트가 따로 없다(확인 결과
    rosterType=postseason은 40인 로스터와 동일하게 나온다). 대신 각 팀의 그 라운드 첫 경기가
    열리면 그 경기 박스스코어에 실제 26인이 정확히 나타나므로, 그 시점부터는 이 함수가 진짜
    26인 로스터를 돌려준다.
    주의: 아직 시작하지 않은(Preview) 미래 경기도 박스스코어의 players 목록이 미리 채워져 나오는데
    (그날 시점의 현재 로스터를 그냥 복사해둔 것뿐, 실제 확정된 26인이 아니다), 이걸 그대로 믿으면
    포스트시즌이 시작되기도 전에 "확정됨"으로 잘못 표시된다. 그래서 게임 상태가 실제로 시작됐거나
    (Live) 끝난(Final) 경기만 인정한다. 아직 이 팀의 포스트시즌 경기가 시작되지 않았다면 None을
    돌려준다(=아직 26인 로스터가 공개되지 않았다는 뜻)."""
    raw = _get_json(POSTSEASON_TEAM_SCHEDULE_URL.format(season=season, team_id=team_id))
    games = [g for date in raw.get("dates", []) for g in date["games"]
             if g.get("status", {}).get("abstractGameState") in ("Live", "Final")]
    if not games:
        return None
    games.sort(key=lambda g: g["gameDate"], reverse=True)  # 최신 라운드부터: 라운드가 바뀌면 자동으로 그 라운드 26인으로 갱신된다
    for g in games:
        box = _get_json(BOXSCORE_URL.format(game_pk=g["gamePk"]))
        teams = box.get("gameData", {}).get("teams", {})
        side = None
        if teams.get("home", {}).get("id") == team_id:
            side = box.get("liveData", {}).get("boxscore", {}).get("teams", {}).get("home")
        elif teams.get("away", {}).get("id") == team_id:
            side = box.get("liveData", {}).get("boxscore", {}).get("teams", {}).get("away")
        players = side.get("players") if side else None
        if players:
            return {int(pid.replace("ID", "")) for pid in players}
    return None


def fetch_roster(team_id, active_ids=None):
    """이 팀의 로스터 전체를 돌려준다(선수 카드 겸 한국인 선수 필터링에 함께 쓴다).
    active_ids가 주어지면(=이 팀의 실제 26인 포스트시즌 로스터가 이미 공개됐다는 뜻) 그 26인에
    들어있는 선수만 돌려주고, 없는 선수는 자동으로 빠진다. active_ids가 None이면(아직 이 팀의
    포스트시즌 경기가 없었다는 뜻) 40인 로스터 전체를 후보로 돌려준다 - 60일 부상자 명단이나
    마이너리그로 재배정된 선수는 40인 로스터에서 빠지므로 이 경우에도 자동으로 제외된다."""
    raw = _get_json(ROSTER_URL.format(team_id=team_id))
    players = []
    for p in raw.get("roster", []):
        person = p["person"]
        if active_ids is not None and person["id"] not in active_ids:
            continue
        players.append({
            "id": person["id"],
            "fullName": person["fullName"],
            "position": p.get("position", {}).get("abbreviation", person.get("primaryPosition", {}).get("abbreviation", "")),
            "birthDate": person.get("birthDate"),
            "status": p.get("status", {}).get("description", ""),
            "birthCountry": person.get("birthCountry"),
        })
    return players


def build_bracket(season=None):
    season = season or os.environ.get("MLB_SEASON") or str(datetime.date.today().year)
    standings = fetch_standings(season)
    leagues = {}
    for lg, teams in standings.items():
        seeds = compute_seeds(teams)
        schedules = {n: fetch_schedule_results(t["id"], season) for n, t in seeds.items()}
        for t in seeds.values():
            try:
                active_ids = fetch_active_postseason_roster_ids(t["id"], season)
            except Exception:  # noqa: BLE001 - 확인 못 하면 40인 로스터 기준으로 대신 보여준다
                active_ids = None
            try:
                roster = fetch_roster(t["id"], active_ids=active_ids)
                t["roster"] = roster
                t["koreanPlayers"] = [p for p in roster if p.get("birthCountry") == "Republic of Korea"]
                t["postseasonRosterSet"] = active_ids is not None
            except Exception:  # noqa: BLE001 - 로스터를 못 가져와도 대진표 자체는 보여준다
                t["roster"] = []
                t["koreanPlayers"] = []
                t["postseasonRosterSet"] = False

        matchups = []
        for a, b, kind in BRACKET_PAIRS:
            h2h = head_to_head_from_schedule(schedules[a], seeds[b]["id"])
            matchups.append({"kind": kind, "aSeed": a, "bSeed": b, "a": seeds[a], "b": seeds[b], "h2h": h2h})

        # 팀별로 "이 팀이 만날 수 있는 상대" 목록을 만든다 (팀 페이지에서 쓴다)
        per_team = {n: [] for n in seeds}
        for m in matchups:
            label = "와일드카드 시리즈" if m["kind"] == "wc" else "디비전시리즈 상대 (해당 라운드 진출 시)"
            per_team[m["aSeed"]].append({"opponent": m["b"], "h2h": m["h2h"], "label": label, "kind": m["kind"]})
            mirrored = {"w": m["h2h"]["l"], "l": m["h2h"]["w"]}
            per_team[m["bSeed"]].append({"opponent": m["a"], "h2h": mirrored, "label": label, "kind": m["kind"]})

        leagues[lg] = {
            "seeds": seeds,
            "matchups": matchups,
            "perTeam": per_team,
            "standings": sorted(teams, key=lambda t: (-t["pct"])),
        }

    try:
        postseason_dates = fetch_postseason_dates(season)
    except Exception:  # noqa: BLE001 - 날짜를 못 가져와도 대진표 자체는 보여준다
        postseason_dates = {"wc": {"AL": None, "NL": None}, "ds": {"AL": None, "NL": None},
                             "cs": {"AL": None, "NL": None}, "ws": None}

    return {
        "ok": True,
        "season": season,
        "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "leagues": leagues,
        "postseasonDates": postseason_dates,
    }
