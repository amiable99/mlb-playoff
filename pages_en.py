"""MLB Postseason Bracket - English pages (server-rendered).

Shares the same data layer as pages.py (bracket.py's payload), but renders its own
English HTML. Team "role"/matchup "label" strings baked into bracket.py's payload are
Korean, so this module deliberately ignores those two fields and re-derives the same
facts from language-neutral data (team["leader"], team["wildCardRank"], matchup["kind"])
instead of touching bracket.py.
"""
import datetime
from zoneinfo import ZoneInfo

from pages import esc, logo, round_title, t_pair, t_col_title, ROSTER_STATUS_KO  # noqa: F401 (ROSTER_STATUS_KO unused, kept for parity)
from teams import DIVISION_EN, LEAGUE_EN, TEAM_INFO

SITE_NAME_EN = "MLB Postseason Bracket"

# US Eastern time, with automatic DST handling (unlike the Korean site's fixed KST offset,
# the postseason spans the early-November DST changeover, so a fixed offset would be wrong).
EN_SITE_TZ = ZoneInfo("America/New_York")
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ROUND_LABEL_EN = {"wc": "Wild Card Series (Best-of-3)", "ds": "Possible Division Series matchup (Best-of-5)"}

NAV_EN = [("/en/", "Bracket"), ("/en/tournament/", "Tournament"), ("/en/al/", "American League"),
          ("/en/nl/", "National League"), ("/en/guide/", "Guide"), ("/en/about/", "About")]

POSITION_EN = {
    "P": "Pitcher", "C": "Catcher", "1B": "First Base", "2B": "Second Base", "3B": "Third Base",
    "SS": "Shortstop", "LF": "Left Field", "CF": "Center Field", "RF": "Right Field",
    "OF": "Outfield", "DH": "Designated Hitter", "TWP": "Two-Way Player",
}

ROSTER_STATUS_EN = {
    "Active": "Active",
    "Injured 60-Day": "60-Day IL",
    "Injured 15-Day": "15-Day IL",
    "Injured 10-Day": "10-Day IL",
    "Reassigned to Minors": "Optioned to Minors",
    "Restricted List": "Restricted List",
    "Paternity List": "Paternity List",
    "Bereavement List": "Bereavement List",
    "Suspended List": "Suspended List",
}

ROSTER_GROUPS_EN = [
    ("Pitchers", {"P", "TWP"}),
    ("Catchers", {"C"}),
    ("Infielders", {"1B", "2B", "3B", "SS", "IF"}),
    ("Outfielders", {"LF", "CF", "RF", "OF"}),
    ("Designated Hitter", {"DH"}),
]

GUIDES_EN = {
    "round-format": {
        "title": "MLB Postseason Round-by-Round Format",
        "desc": "How many games each postseason round is (best-of-3/5/7) and how home-field advantage is assigned, based on MLB's official schedule.",
        "html": """
<section class="prose">
  <h2>Every round has a different format</h2>
  <table class="standings-table">
    <thead><tr><th>Round</th><th>Format</th><th>Home field</th></tr></thead>
    <tbody>
      <tr><td>Wild Card Series</td><td>Best-of-3</td><td>All games at the higher seed's park</td></tr>
      <tr><td>Division Series</td><td>Best-of-5</td><td>2-2-1 (higher seed hosts 3 games)</td></tr>
      <tr><td>Championship Series</td><td>Best-of-7</td><td>2-3-2 (higher seed hosts 4 games)</td></tr>
      <tr><td>World Series</td><td>Best-of-7</td><td>2-3-2 (better regular-season record hosts)</td></tr>
    </tbody>
  </table>
  <p class="note">Compiled directly from the actual home/away assignments in MLB's official schedule. Rules can change season to season.</p>
</section>
<section class="prose">
  <h2>Wild Card Series: three games, no travel</h2>
  <p>Seeds 4-6 face seeds 3-6 in a best-of-3 series, and <strong>all three games are played at the higher seed's
     (3 or 4) home park</strong>. The lower seed carries the full travel burden while the higher seed never leaves home
     — a real advantage.</p>
</section>
<section class="prose">
  <h2>Division Series: 2-2-1</h2>
  <p>The Wild Card Series winner faces the 1 or 2 seed. It's best-of-5, with Games 1-2 (and Game 5, if needed) at the
     higher seed's park and Games 3-4 at the lower seed's park — the higher seed can host up to 3 of 5 games.</p>
</section>
<section class="prose">
  <h2>Championship Series &amp; World Series: 2-3-2</h2>
  <p>Both the ALCS/NLCS and the World Series are best-of-7, with Games 1-2 and 6-7 at the higher seed's park and
     Games 3-4-5 at the lower seed's park. In the World Series, the "higher seed" isn't decided by division/wild-card
     rank — it's whichever pennant winner had the <strong>better regular-season record</strong>.</p>
</section>
<section>
  <h2>FAQ</h2>
  <div class="faq">
    <details><summary>Why does the higher seed have an advantage?</summary><p>Every round gives the higher seed a bigger share of home games. The Wild Card Series is played entirely at their park with zero travel, and from the Division Series on they can host more than half the possible games.</p></details>
    <details><summary>How is World Series home-field decided?</summary><p>It used to go to whichever league won the All-Star Game. Now it simply goes to whichever pennant winner has the better regular-season record.</p></details>
    <details><summary>Does the road team ever get an edge mid-series?</summary><p>Rounds with a travel day (Division Series and up) let the road team rest before playing too, so it's not a pure disadvantage — but across the full series, the higher seed still comes out ahead on home games.</p></details>
  </div>
</section>
""",
    },
}


def team_info(abbr):
    return TEAM_INFO.get(abbr, {"en": abbr, "color": "#64748b"})


def team_url(abbr):
    return f"/en/team/{abbr.lower()}/"


def _to_en_tz(iso):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(EN_SITE_TZ)


def _en_time(dt):
    ampm = "AM" if dt.hour < 12 else "PM"
    h12 = dt.hour % 12 or 12
    return f"{h12}:{dt.minute:02d} {ampm}" if dt.minute else f"{h12} {ampm}"


def updated_en(iso):
    try:
        d = datetime.datetime.fromisoformat(iso).astimezone(EN_SITE_TZ)
        return f"{MONTHS_EN[d.month - 1]} {d.day}, {d.year}, {_en_time(d)} ET"
    except (TypeError, ValueError):
        return ""


def date_range_text_en(rng):
    """Mirrors pages.date_range_text() but in US Eastern time with English month names,
    and appends the Game 1 time only once MLB has actually published it."""
    if not rng:
        return ""
    s, e = _to_en_tz(rng["start"]), _to_en_tz(rng["end"])
    if s.date() == e.date():
        text = f"{MONTHS_EN[s.month - 1]} {s.day}"
    elif s.month == e.month:
        text = f"{MONTHS_EN[s.month - 1]} {s.day}-{e.day}"
    else:
        text = f"{MONTHS_EN[s.month - 1]} {s.day} - {MONTHS_EN[e.month - 1]} {e.day}"
    if rng.get("game1Time"):
        text += f" · Game 1 {_en_time(_to_en_tz(rng['game1Time']))} ET"
    return text


def role_text(team):
    """Derives the English seed-role phrase from neutral data (leader/wildCardRank),
    instead of reading team["role"], which bracket.py stores pre-baked in Korean."""
    return "Division Winner" if team["leader"] else f'Wild Card #{team["wildCardRank"]}'


def layout_en(title, desc, body, path, base_url, alt_ko, active="", hero_title="", hero_sub="", updated=""):
    canonical = f'<link rel="canonical" href="{esc(base_url + path)}">' if base_url else ""
    og_url = f'<meta property="og:url" content="{esc(base_url + path)}">' if base_url else ""
    hreflang = ""
    if base_url:
        hreflang = (f'<link rel="alternate" hreflang="en" href="{esc(base_url + path)}">'
                    f'<link rel="alternate" hreflang="ko" href="{esc(base_url + alt_ko)}">'
                    f'<link rel="alternate" hreflang="x-default" href="{esc(base_url + alt_ko)}">')
    nav = "".join(f'<a href="{href}"{" class=on" if href == active else ""}>{esc(label)}</a>' for href, label in NAV_EN)
    upd = f'<p class="updated">As of <span>{esc(updated)}</span></p>' if updated else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    {canonical}
    {hreflang}
    <meta property="og:type" content="website">
    <meta property="og:locale" content="en_US">
    <meta property="og:site_name" content="{esc(SITE_NAME_EN)}">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    {og_url}
    <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
    <link rel="stylesheet" href="/static/style.css">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5559949155901841" crossorigin="anonymous"></script>
</head>
<body>
    <div class="container">
        <header>
            <a class="brand-link" href="/en/">⚾ {esc(SITE_NAME_EN)}</a>
            <h1>{hero_title}</h1>
            <p class="subtitle">{esc(hero_sub)}</p>
            {upd}
        </header>
        <nav class="site-nav" aria-label="Main menu">{nav}</nav>
        {body}
        <footer>
            <p>© 2026 {esc(SITE_NAME_EN)} | A postseason bracket projection built from current standings</p>
            <p>Standings/schedule data: MLB Stats API (refreshed every 30 minutes) · <a href="/en/about/">About</a> · <a href="/privacy.html">Privacy Policy</a></p>
            <p>This is an unofficial site with no affiliation to MLB or any club. <a href="/">한국어</a></p>
        </footer>
    </div>
</body>
</html>
"""


def team_row(team, extra=""):
    return (f'<a class="team-row" href="{team_url(team["abbr"])}">'
            f'{logo(team["abbr"])}<span class="tr-name">{esc(team_info(team["abbr"])["en"])}'
            f'<small>{team["wins"]}-{team["losses"]} · {esc(team["pctText"])}</small></span>{extra}</a>')


def h2h_line(a_abbr, h2h):
    w, l = h2h["w"], h2h["l"]
    if w == l:
        return f'<span class="h2h-line even">Season series {w}-{l} · Even</span>'
    verdict = "leads" if w > l else "trails"
    cls = "win" if w > l else "lose"
    return f'<span class="h2h-line {cls}">Season series {w}-{l} · {esc(team_info(a_abbr)["en"])} {verdict}</span>'


def matchup_box(m):
    if m["kind"] == "wc":
        return f"""<div class="matchup wc">
            <div class="mu-seed">Seed {m["aSeed"]} <span class="mu-vs">vs</span> Seed {m["bSeed"]}</div>
            {team_row(m["a"])}
            <div class="mu-mid">{h2h_line(m["a"]["abbr"], m["h2h"])}</div>
            {team_row(m["b"])}
        </div>"""
    return f"""<div class="matchup ds">
        <div class="mu-seed">Seed {m["aSeed"]} <span class="mu-vs">vs</span> Seed {m["bSeed"]} winner</div>
        {team_row(m["a"])}
        <div class="mu-mid">{h2h_line(m["a"]["abbr"], m["h2h"])}</div>
        {team_row(m["b"])}
    </div>"""


def league_bracket(lg, data, ps_dates=None):
    seeds = data["seeds"]
    wc = [m for m in data["matchups"] if m["kind"] == "wc"]
    ds = [m for m in data["matchups"] if m["kind"] == "ds"]
    bye_tag = "<span class='bye-tag'>Bye to Division Series</span>"
    byes = "".join(f'<div class="bye">{team_row(seeds[n], extra=bye_tag)}</div>' for n in (1, 2))
    ps_dates = ps_dates or {}
    wc_date = date_range_text_en((ps_dates.get("wc") or {}).get(lg))
    ds_date = date_range_text_en((ps_dates.get("ds") or {}).get(lg))
    return f"""
<section class="league-block">
  <h2>{esc(LEAGUE_EN[lg])} ({lg})</h2>
  <div class="bracket">
    <div class="bracket-round">
      {round_title(ROUND_LABEL_EN["wc"], wc_date)}
      {"".join(matchup_box(m) for m in wc)}
      {byes}
    </div>
    <div class="bracket-round">
      {round_title(ROUND_LABEL_EN["ds"], ds_date)}
      {"".join(matchup_box(m) for m in ds)}
    </div>
  </div>
</section>
"""


def home_page_en(payload, base_url):
    body = "".join(league_bracket(lg, payload["leagues"][lg], payload.get("postseasonDates")) for lg in ("AL", "NL"))
    body += """
<section class="prose">
  <h2>How to read this</h2>
  <p>Based on current standings, the 3 division winners are seeded 1-3 by winning percentage, and the top 3 wild-card
     teams are seeded 4-6. Seeds 3-6 and 4-5 face off in the Wild Card Series, and seeds 1-2 wait for that result before
     starting the Division Series. Since the actual winners aren't determined yet, the Division Series slots show both
     possible opponents.</p>
  <p>The Championship Series and World Series matchups depend on earlier rounds, so they aren't shown here yet. Click
     any team name for a detailed look at who they could face and the season series record.</p>
  <p>Round dates come from MLB's official pre-season schedule. Game 1 start times are usually announced once broadcast
     scheduling is finalized — until then only the date is shown, and the time appears automatically (within 30
     minutes) once MLB publishes it.</p>
</section>
"""
    title = "MLB Postseason Bracket - Wild Card Through Division Series by Seed"
    desc = "See how the MLB American League and National League postseason bracket shapes up based on current standings, including the confirmed Wild Card Series matchups and season series records for possible Division Series opponents."
    return layout_en(title, desc, body, "/en/", base_url, "/", "/en/", "🏆 Postseason Bracket", "Bracket and season series by current standings", updated_en(payload["fetchedAt"]))


def standings_note(t):
    if t["leader"]:
        return "Div " + esc(DIVISION_EN[t["division"]])
    if t["wildCardRank"]:
        return f'WC {t["wildCardRank"]}'
    return "-"


def league_page_en(lg, payload, base_url):
    data = payload["leagues"][lg]
    rows = "".join(
        f'<tr class="{"in-zone" if i < 6 else ""}"><td>{i + 1}</td><td class="team-name">'
        f'<a href="{team_url(t["abbr"])}">{logo(t["abbr"], "sm")} {esc(team_info(t["abbr"])["en"])}</a></td>'
        f'<td>{t["wins"]}-{t["losses"]}</td><td>{esc(t["pctText"])}</td>'
        f'<td>{standings_note(t)}</td></tr>'
        for i, t in enumerate(data["standings"]))
    body = f"""
{league_bracket(lg, data, payload.get("postseasonDates"))}
<section>
  <h2>{esc(LEAGUE_EN[lg])} Full Standings</h2>
  <div class="table-scroll"><table class="standings-table">
    <thead><tr><th>#</th><th>Team</th><th>W-L</th><th>PCT</th><th>Note</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
  <p class="note">The top 6 teams (highlighted) make the postseason.</p>
</section>
"""
    return layout_en(f"{LEAGUE_EN[lg]} Postseason Bracket & Standings | {SITE_NAME_EN}",
                      f"See the {LEAGUE_EN[lg]} postseason bracket and full standings.",
                      body, f"/en/{lg.lower()}/", base_url, f"/{lg.lower()}/", f"/en/{lg.lower()}/",
                      f"🏆 {esc(LEAGUE_EN[lg])}", "Bracket and standings", updated_en(payload["fetchedAt"]))


def roster_group_rows(players):
    rows = ""
    for p in sorted(players, key=lambda p: p["fullName"]):
        pos = POSITION_EN.get(p["position"], p["position"] or "-")
        year = (p.get("birthDate") or "")[:4]
        status = ROSTER_STATUS_EN.get(p.get("status", ""), p.get("status") or "")
        status_html = f' <span class="player-status">{esc(status)}</span>' if status and status != "Active" else ""
        rows += (f'<div class="roster-row"><span class="roster-name">{esc(p["fullName"])}{status_html}</span>'
                  f'<span class="player-meta">{esc(pos)}{f" · b. {year}" if year else ""}</span></div>')
    return rows


def roster_section_en(team):
    if not team.get("postseasonRosterSet"):
        return """<section>
  <h2>Full Roster <span class="chip-pending">26-man roster not yet announced</span></h2>
  <p class="note">The actual 26-man postseason roster will appear here automatically once this team's first game of the round begins.</p>
</section>"""
    roster = team.get("roster", [])
    if not roster:
        return ""
    used = set()
    groups = []
    for label, codes in ROSTER_GROUPS_EN:
        used |= codes
        members = [p for p in roster if p["position"] in codes]
        if members:
            groups.append((label, members))
    others = [p for p in roster if p["position"] not in used]
    if others:
        groups.append(("Other", others))
    body = "".join(
        f'<div class="roster-group"><h3>{esc(label)} <span class="roster-count">{len(members)}</span></h3>'
        f'<div class="roster-rows">{roster_group_rows(members)}</div></div>'
        for label, members in groups)
    return f"""<section>
  <h2>Full Roster <span class="chip-set">26-Man Roster Confirmed</span></h2>
  <div class="roster-wrap">{body}</div>
</section>"""


def team_page_en(abbr, lg, payload, base_url):
    data = payload["leagues"][lg]
    seed_no = next(n for n, t in data["seeds"].items() if t["abbr"] == abbr)
    team = data["seeds"][seed_no]
    info = team_info(abbr)
    matches = data["perTeam"][seed_no]

    cards = ""
    for m in matches:
        opp = m["opponent"]
        label = "Wild Card Series" if m["kind"] == "wc" else "Possible Division Series opponent (if this round is reached)"
        cards += f"""<div class="opp-card">
            <div class="opp-label">{esc(label)}</div>
            <div class="opp-team">{team_row(opp)}</div>
            <div class="opp-h2h">{h2h_line(abbr, m["h2h"])}</div>
        </div>"""

    name = info["en"]
    faqs = [(f"What seed are the {name} in the postseason?",
             f'They are the {esc(LEAGUE_EN[lg])} #{seed_no} seed ({role_text(team)}), currently {team["wins"]}-{team["losses"]} (PCT {team["pctText"]}).')]
    if matches:
        opp0 = matches[0]["opponent"]
        opp0_name = team_info(opp0["abbr"])["en"]
        opp0_label = "the Wild Card Series" if matches[0]["kind"] == "wc" else "a possible Division Series matchup"
        faqs.append((f"Who do the {name} play first in the postseason?",
                     f'They face the {opp0_name} in {opp0_label}. The season series is {matches[0]["h2h"]["w"]}-{matches[0]["h2h"]["l"]}.'))
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)

    body = f"""
<section>
  <h2>{esc(info["en"])} Postseason Position</h2>
  <div class="scenario-stats">
    <div class="stat-item"><div class="stat-label">Seed</div><div class="stat-value">{esc(LEAGUE_EN[lg])} #{seed_no}</div><div class="stat-sub">{esc(role_text(team))}</div></div>
    <div class="stat-item"><div class="stat-label">Record</div><div class="stat-value">{team["wins"]}-{team["losses"]}</div><div class="stat-sub">PCT {esc(team["pctText"])}</div></div>
  </div>
</section>
<section>
  <h2>Possible Opponents</h2>
  <div class="opp-grid">{cards}</div>
</section>
{roster_section_en(team)}
<section>{faq_html and f'<h2>FAQ</h2><div class="faq">{faq_html}</div>'}</section>
<section><h2>Back to {esc(LEAGUE_EN[lg])} Bracket</h2><p><a class="chip" href="/en/{lg.lower()}/">Full {esc(LEAGUE_EN[lg])} Bracket</a> <a class="chip" href="/en/">Full Bracket</a></p></section>
"""
    title = f"{info['en']} Postseason Opponents & Roster | {SITE_NAME_EN}"
    desc = f'See who the {info["en"]} ({esc(LEAGUE_EN[lg])} #{seed_no} seed) could face in the postseason, the season series record, and their full roster.'
    return layout_en(title, desc, body, team_url(abbr), base_url, f"/team/{abbr.lower()}/", f"/en/{lg.lower()}/",
                      f'{logo(abbr, "lg")} {esc(info["en"])}', f'{esc(LEAGUE_EN[lg])} #{seed_no} seed · {team["wins"]}-{team["losses"]}',
                      updated_en(payload["fetchedAt"]))


def t_slot_en(team=None, seed=None, tbd=None):
    if team:
        return (f'<a class="t-slot" href="{team_url(team["abbr"])}"><span class="seed-no">{seed}</span>'
                f'{logo(team["abbr"], "sm")} {esc(team_info(team["abbr"])["en"])}</a>')
    return f'<div class="t-slot tbd"><span class="seed-no"></span>{esc(tbd)}</div>'


def league_tourney_rounds(lg, data, mirror=False):
    seeds = data["seeds"]
    r1 = "".join(t_pair(t_slot_en(seeds[a], a), t_slot_en(seeds[b], b), mirror) for a, b in ((4, 5), (3, 6)))
    r2 = "".join(
        t_pair(t_slot_en(seeds[s], s), t_slot_en(tbd=f"Seed {a}/{b} winner"), mirror)
        for s, (a, b) in ((1, (4, 5)), (2, (3, 6))))
    r3 = t_pair(t_slot_en(tbd="Seed 1 side winner"), t_slot_en(tbd="Seed 2 side winner"), mirror)
    return r1, r2, r3


def tournament_page_en(payload, base_url):
    al1, al2, al3 = league_tourney_rounds("AL", payload["leagues"]["AL"])
    nl1, nl2, nl3 = league_tourney_rounds("NL", payload["leagues"]["NL"], mirror=True)
    ws = f'{t_slot_en(tbd=esc(LEAGUE_EN["AL"]) + " Champion")}{t_slot_en(tbd=esc(LEAGUE_EN["NL"]) + " Champion")}'

    d = payload.get("postseasonDates") or {}
    wc_d = d.get("wc") or {}
    ds_d = d.get("ds") or {}
    cs_d = d.get("cs") or {}
    ws_date = date_range_text_en(d.get("ws"))

    body = f"""
<section class="tourney-wrap">
  <div class="tourney">
    <div class="t-col t-round-1">{t_col_title("AL Wild Card", date_range_text_en(wc_d.get("AL")))}{al1}</div>
    <div class="t-col t-round-2">{t_col_title("AL Division Series", date_range_text_en(ds_d.get("AL")))}{al2}</div>
    <div class="t-col t-round-3">{t_col_title("AL Championship Series", date_range_text_en(cs_d.get("AL")))}{al3}</div>
    <div class="t-col t-final"><div class="t-final-box"><div class="trophy">🏆</div><div class="t-final-title">World Series</div>
      {f'<span class="round-date">{esc(ws_date)}</span>' if ws_date else ""}{ws}</div></div>
    <div class="t-col t-round-3">{t_col_title("NL Championship Series", date_range_text_en(cs_d.get("NL")))}{nl3}</div>
    <div class="t-col t-round-2">{t_col_title("NL Division Series", date_range_text_en(ds_d.get("NL")))}{nl2}</div>
    <div class="t-col t-round-1">{t_col_title("NL Wild Card", date_range_text_en(wc_d.get("NL")))}{nl1}</div>
  </div>
</section>
<section class="prose">
  <h2>How to read this</h2>
  <p>Based on current standings, the Wild Card Series matchups are already set and shown with real teams, while the
     Division Series, Championship Series and World Series — none of which have a winner yet — are shown as dashed
     placeholder slots. Each slot fills in automatically once that round's result is known. Click a team to see its
     detail page.</p>
  <p>Dates under each slot come from MLB's pre-set round schedule. Game 1 start times appear once MLB publishes them;
     until then, only the date is shown.</p>
</section>
"""
    title = "MLB Postseason Tournament Bracket - Wild Card Through World Series"
    desc = "See the full MLB American League and National League postseason tournament on one screen, with the confirmed Wild Card matchups and the rounds still to be filled in."
    return layout_en(title, desc, body, "/en/tournament/", base_url, "/tournament/", "/en/tournament/",
                      "🎋 Postseason Tournament", "Wild Card through World Series at a glance", updated_en(payload["fetchedAt"]))


def guide_hub_page_en(base_url):
    cards = "".join(
        f'<a class="team-card" href="/en/guide/{slug}/"><strong>{esc(g["title"])}</strong>'
        f'<div class="tc-sub">{esc(g["desc"])}</div></a>' for slug, g in GUIDES_EN.items())
    body = f"""
<section class="prose">
  <h2>Postseason Guide</h2>
  <p>Plain explanations of postseason rules that the bracket and standings alone don't make obvious.</p>
</section>
<section><div class="team-grid">{cards}</div></section>
"""
    return layout_en(f"MLB Postseason Guide | {SITE_NAME_EN}", "Easy explanations of MLB postseason format and seeding rules.",
                      body, "/en/guide/", base_url, "/guide/", "/en/guide/", "📖 Guide", "Postseason rules made simple")


def guide_page_en(slug, base_url):
    g = GUIDES_EN[slug]
    others = "".join(f'<a class="chip" href="/en/guide/{s}/">{esc(o["title"])}</a>' for s, o in GUIDES_EN.items() if s != slug)
    body = g["html"] + (f'<section><h2>More Guides</h2><div class="chips">{others}</div></section>' if others else "")
    return layout_en(f'{g["title"]} | {SITE_NAME_EN}', g["desc"], body, f"/en/guide/{slug}/", base_url, f"/guide/{slug}/",
                      "/en/guide/", esc(g["title"]), "MLB Postseason Guide")


def about_page_en(base_url):
    body = """
<section class="prose">
  <h2>About this site</h2>
  <p>MLB Postseason Bracket shows how the American League and National League postseason bracket would shape up based
     on current standings. The Wild Card Series matchups are confirmed; the Division Series depends on those results,
     so we show both possible opponents.</p>
  <h2>How seeding works</h2>
  <p>In each league, the 3 division winners are seeded 1-3 by winning percentage, and the top 3 wild-card teams by
     wild-card rank are seeded 4-6. Seed 3 vs. 6 and 4 vs. 5 play the Wild Card Series (best-of-3); the winners face
     seeds 1 and 2 in the Division Series (best-of-5). Those winners meet in the Championship Series, and the two
     league champions play the World Series — both of those rounds are best-of-7.</p>
  <h2>How the season series is calculated</h2>
  <p>We pull this season's full schedule for the 6 relevant teams in each league from the MLB Stats API and count the
     actual results between each pair. We don't show a season series for rounds (like the Championship Series or World
     Series) where the participants aren't determined yet.</p>
  <h2>Disclaimer</h2>
  <p>This is an unofficial site with no affiliation to MLB or any club; the information here is for reference only.
     Standings data refreshes from the MLB Stats API every 30 minutes. Check MLB's official site for the actual
     bracket and schedule.</p>
</section>"""
    return layout_en(f"About | {SITE_NAME_EN}", f"How {SITE_NAME_EN} calculates the bracket, and where the data comes from.",
                      body, "/en/about/", base_url, "/about/", "/en/about/", "ℹ️ About", "How the bracket is calculated")


PAGE_PREFIXES = ("/en/al", "/en/nl", "/en/team/", "/en/about", "/en/tournament", "/en/guide")


def is_page(path):
    return path.startswith(PAGE_PREFIXES) or path in ("/en", "/en/")


def render(path, base_url, payload):
    path = path.rstrip("/") + "/" if not path.endswith(".html") else path
    if path == "/en/":
        return 200, home_page_en(payload, base_url)
    if path == "/en/tournament/":
        return 200, tournament_page_en(payload, base_url)
    if path in ("/en/al/", "/en/nl/"):
        return 200, league_page_en(path.strip("/").split("/")[-1].upper(), payload, base_url)
    if path.startswith("/en/team/"):
        abbr = path[len("/en/team/"):].strip("/").upper()
        for lg in ("AL", "NL"):
            if any(t["abbr"] == abbr for t in payload["leagues"][lg]["seeds"].values()):
                return 200, team_page_en(abbr, lg, payload, base_url)
        return 404, None
    if path == "/en/guide/":
        return 200, guide_hub_page_en(base_url)
    if path.startswith("/en/guide/"):
        slug = path[len("/en/guide/"):].strip("/")
        return (200, guide_page_en(slug, base_url)) if slug in GUIDES_EN else (404, None)
    if path == "/en/about/":
        return 200, about_page_en(base_url)
    return None


def sitemap_urls(payload):
    urls = ["/en/", "/en/tournament/", "/en/al/", "/en/nl/", "/en/guide/", "/en/about/"]
    urls += [f"/en/guide/{s}/" for s in GUIDES_EN]
    for lg in ("AL", "NL"):
        urls += [team_url(t["abbr"]) for t in payload["leagues"][lg]["seeds"].values()]
    return urls
