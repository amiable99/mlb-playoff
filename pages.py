"""MLB 포스트시즌 대진표 - 서버 렌더링 페이지."""
import datetime
import html
import json
import re

from teams import DIVISION_KO, KOREAN_PLAYERS_KO, LEAGUE_KO, ROSTER_STATUS_KO, TEAM_INFO

SITE_NAME = "MLB 포스트시즌 대진표"

# 경기 날짜를 보여줄 시간대. 이 사이트(한글판)는 한국 시간(KST) 기준이다.
# 나중에 영문판을 만들 때는 이 값을 미국 동부시간(America/New_York, 서머타임에 따라 -4/-5시간)으로 바꾼다.
SITE_TZ = datetime.timezone(datetime.timedelta(hours=9))
ADS_SCRIPT = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
              '?client=ca-pub-5559949155901841" crossorigin="anonymous"></script>')

ROUND_LABEL = {"wc": "와일드카드 시리즈 (3전 2선승제)", "ds": "디비전시리즈에서 만날 수 있는 상대 (5전 3선승제)"}

NAV = [("/", "대진표"), ("/tournament/", "토너먼트"), ("/al/", "아메리칸리그"), ("/nl/", "내셔널리그"),
       ("/korean-players/", "한국인 선수"), ("/guide/", "가이드"), ("/about/", "소개")]

# 가이드 글 모음. 슬러그: (제목, 설명, 본문 HTML). 나중에 더 추가할 수 있도록 목록 형태로 둔다.
GUIDES = {
    "round-format": {
        "title": "MLB 포스트시즌 라운드별 경기 방식",
        "desc": "와일드카드 시리즈부터 월드시리즈까지 몇 전 몇 선승제인지, 홈구장은 어떻게 배정되는지 MLB 공식 일정을 바탕으로 정리했어요.",
        "html": """
<section class="prose">
  <h2>라운드마다 선승제가 달라요</h2>
  <table class="standings-table">
    <thead><tr><th>라운드</th><th>방식</th><th>홈구장 배정</th></tr></thead>
    <tbody>
      <tr><td>와일드카드 시리즈</td><td>3전 2선승제</td><td>전 경기 상위 시드 홈구장</td></tr>
      <tr><td>디비전시리즈</td><td>5전 3선승제</td><td>2-2-1 (상위 시드 홈이 3경기)</td></tr>
      <tr><td>챔피언십시리즈</td><td>7전 4선승제</td><td>2-3-2 (상위 시드 홈이 4경기)</td></tr>
      <tr><td>월드시리즈</td><td>7전 4선승제</td><td>2-3-2 (정규시즌 승률 높은 팀이 상위)</td></tr>
    </tbody>
  </table>
  <p class="note">MLB 공식 일정에 등록된 실제 홈/원정 배정을 직접 확인해서 정리했어요. 규정은 시즌마다 바뀔 수 있어요.</p>
</section>
<section class="prose">
  <h2>와일드카드 시리즈: 이동 없이 3연전</h2>
  <p>4~6시드는 3~6시드를 상대로 와일드카드 시리즈를 치러요. 최대 3경기를 먼저 2승 하는 팀이 이기고,
     <strong>세 경기 모두 상위 시드(4위 또는 3위)의 홈구장</strong>에서 열려요. 하위 시드는 이동 부담이 있고,
     상위 시드는 자기 구장에서만 싸운다는 점에서 확실한 이점이에요.</p>
</section>
<section class="prose">
  <h2>디비전시리즈: 2-2-1 방식</h2>
  <p>와일드카드 시리즈 승자가 1·2시드와 맞붙어요. 5전 3선승제이고, 1·2차전과(필요하면) 5차전은 상위 시드 홈구장,
     3·4차전은 하위 시드 홈구장에서 열려요. 상위 시드는 최대 5경기 중 3경기를 홈에서 치를 수 있어요.</p>
</section>
<section class="prose">
  <h2>챔피언십시리즈·월드시리즈: 2-3-2 방식</h2>
  <p>리그 챔피언십 시리즈(ALCS·NLCS)와 월드시리즈는 둘 다 7전 4선승제이고, 1·2차전과 6·7차전은 상위 시드 홈구장,
     3·4·5차전은 하위 시드 홈구장에서 열려요. 월드시리즈에서는 지구·와일드카드 순위가 아니라
     <strong>정규시즌 승률이 더 높은 팀</strong>이 상위 시드가 돼요.</p>
</section>
<section>
  <h2>자주 묻는 질문</h2>
  <div class="faq">
    <details><summary>왜 상위 시드가 유리한가요?</summary><p>라운드마다 홈경기 비율이 더 높기 때문이에요. 와일드카드 시리즈는 아예 이동 없이 자기 구장에서만 치르고, 디비전시리즈부터는 최대 경기 수 중 절반 이상을 홈에서 치를 수 있어요.</p></details>
    <details><summary>월드시리즈의 홈 어드밴티지는 어떻게 정해지나요?</summary><p>과거에는 올스타전 승리 리그가 가졌지만, 지금은 양 리그 챔피언 중 정규시즌 승률이 더 높은 팀이 홈 어드밴티지를 가져요.</p></details>
    <details><summary>시리즈 도중 원정팀이 유리해지는 경우도 있나요?</summary><p>이동일이 있는 라운드(디비전시리즈 이상)는 원정팀도 하루 쉬고 경기할 수 있어서 절대적인 약점은 아니지만, 전체 경기 수 기준으로는 상위 시드가 여전히 유리해요.</p></details>
  </div>
</section>
""",
    },
}


def esc(s):
    return html.escape(str(s), quote=True)


def josa(word, with_batchim, without_batchim):
    """한글 낱말 마지막 글자의 받침 유무에 따라 조사를 고른다."""
    ch = word.strip()[-1] if word.strip() else ""
    if "가" <= ch <= "힣":
        return with_batchim if (ord(ch) - 0xAC00) % 28 != 0 else without_batchim
    return without_batchim


def team_info(abbr):
    return TEAM_INFO.get(abbr, {"ko": abbr, "short": abbr, "color": "#64748b"})


def logo(abbr, size=""):
    info = team_info(abbr)
    return (f'<span class="team-logo {size}" style="--team:{info["color"]};--fg:{info.get("fg", "#fff")}" '
            f'aria-hidden="true">{esc(abbr)}</span>')


def team_url(abbr):
    return f"/team/{abbr.lower()}/"


def kst(iso):
    try:
        d = datetime.datetime.fromisoformat(iso).astimezone(SITE_TZ)
        return d.strftime("%Y년 %m월 %d일 %H:%M")
    except (TypeError, ValueError):
        return ""


def _to_site_tz(iso):
    """MLB API의 'Z'로 끝나는 UTC 시각 문자열을 이 사이트의 시간대로 바꾼다."""
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(SITE_TZ)


def _kr_time(dt):
    ampm = "오전" if dt.hour < 12 else "오후"
    h12 = dt.hour % 12 or 12
    return f"{ampm} {h12}시" if dt.minute == 0 else f"{ampm} {h12}시 {dt.minute}분"


def date_range_text(rng):
    """{"start":iso,"end":iso,"game1Time":iso|None} → '9월 29일~10월 1일' 같은 짧은 날짜 범위.
    MLB이 1차전 시작 시각을 공개하면(game1Time) '· 1차전 오후 8시'를 자동으로 덧붙인다. 데이터가 없으면 빈 문자열."""
    if not rng:
        return ""
    s, e = _to_site_tz(rng["start"]), _to_site_tz(rng["end"])
    if s.date() == e.date():
        text = f"{s.month}월 {s.day}일"
    elif s.month == e.month:
        text = f"{s.month}월 {s.day}일~{e.day}일"
    else:
        text = f"{s.month}월 {s.day}일~{e.month}월 {e.day}일"
    if rng.get("game1Time"):
        text += f" · 1차전 {_kr_time(_to_site_tz(rng['game1Time']))}"
    return text


def layout(title, desc, body, path, base_url, active="", hero_title="", hero_sub="", updated="", alt_en=None):
    canonical = f'<link rel="canonical" href="{esc(base_url + path)}">' if base_url else ""
    og_url = f'<meta property="og:url" content="{esc(base_url + path)}">' if base_url else ""
    hreflang = ""
    if base_url and alt_en:
        hreflang = (f'<link rel="alternate" hreflang="ko" href="{esc(base_url + path)}">'
                    f'<link rel="alternate" hreflang="en" href="{esc(base_url + alt_en)}">'
                    f'<link rel="alternate" hreflang="x-default" href="{esc(base_url + path)}">')
    nav = "".join(f'<a href="{href}"{" class=on" if href == active else ""}>{esc(label)}</a>' for href, label in NAV)
    upd = f'<p class="updated">기준 시각 <span>{esc(updated)}</span></p>' if updated else ""
    json_ld = ""
    if base_url:
        json_ld = "<script type=\"application/ld+json\">" + json.dumps({
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE_NAME,
            "alternateName": "MLB 포스트시즌 토너먼트",
            "url": base_url + "/",
            "inLanguage": "ko",
        }, ensure_ascii=False) + "</script>"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="sEMkgaO-KtKsTvs7tXRVVFQNi7uJSD09_yrNQtG3M_0">
    <meta name="naver-site-verification" content="7b6d8a31c3d791a66f8b7a96e3855f8667157eb2">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    {canonical}
    {hreflang}
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ko_KR">
    <meta property="og:site_name" content="{esc(SITE_NAME)}">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    {og_url}
    {json_ld}
    <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
    <link rel="stylesheet" href="/static/style.css">
    {ADS_SCRIPT}
</head>
<body>
    <div class="container">
        <header>
            <a class="brand-link" href="/">⚾ {esc(SITE_NAME)}</a>
            <h1>{hero_title}</h1>
            <p class="subtitle">{esc(hero_sub)}</p>
            {upd}
        </header>
        <nav class="site-nav" aria-label="주요 메뉴">{nav}</nav>
        {body}
        <footer>
            <p>© 2026 {esc(SITE_NAME)} | 시즌 순위를 바탕으로 만든 포스트시즌 대진 예상 도구</p>
            <p>순위·경기 데이터 출처: MLB Stats API (조회 결과를 30분 동안 재사용) · <a href="/about/">사이트 소개</a> · <a href="/privacy.html">개인정보처리방침</a></p>
            <p>본 사이트는 MLB 및 각 구단과 관련이 없는 비공식 사이트입니다. <a href="/en/">English</a></p>
        </footer>
    </div>
</body>
</html>
"""


def team_row(team, extra=""):
    return (f'<a class="team-row" href="{team_url(team["abbr"])}">'
            f'{logo(team["abbr"])}<span class="tr-name">{esc(team_info(team["abbr"])["ko"])}'
            f'<small>{team["wins"]}승 {team["losses"]}패 · {esc(team["pctText"])}</small></span>{extra}</a>')


def h2h_line(a_abbr, h2h):
    w, l = h2h["w"], h2h["l"]
    if w == l:
        return f'<span class="h2h-line even">이번 시즌 상대전적 {w}승 {l}패 · 동률</span>'
    verdict = "우세" if w > l else "열세"
    cls = "win" if w > l else "lose"
    return f'<span class="h2h-line {cls}">이번 시즌 상대전적 {w}승 {l}패 · {esc(team_info(a_abbr)["ko"])} {verdict}</span>'


def matchup_box(m):
    if m["kind"] == "wc":
        return f"""<div class="matchup wc">
            <div class="mu-seed">{m["aSeed"]}시드 <span class="mu-vs">vs</span> {m["bSeed"]}시드</div>
            {team_row(m["a"])}
            <div class="mu-mid">{h2h_line(m["a"]["abbr"], m["h2h"])}</div>
            {team_row(m["b"])}
        </div>"""
    return f"""<div class="matchup ds">
        <div class="mu-seed">{m["aSeed"]}시드 <span class="mu-vs">vs</span> {m["bSeed"]}시드 승자</div>
        {team_row(m["a"])}
        <div class="mu-mid">{h2h_line(m["a"]["abbr"], m["h2h"])}</div>
        {team_row(m["b"])}
    </div>"""


def round_title(base_label, date_range):
    date_html = f'<span class="round-date">{esc(date_range)}</span>' if date_range else ""
    return f'<div class="round-title">{base_label}{date_html}</div>'


def league_bracket(lg, data, ps_dates=None):
    seeds = data["seeds"]
    wc = [m for m in data["matchups"] if m["kind"] == "wc"]
    ds = [m for m in data["matchups"] if m["kind"] == "ds"]
    bye_tag = "<span class='bye-tag'>디비전시리즈 직행</span>"
    byes = "".join(f'<div class="bye">{team_row(seeds[n], extra=bye_tag)}</div>' for n in (1, 2))
    ps_dates = ps_dates or {}
    wc_date = date_range_text((ps_dates.get("wc") or {}).get(lg))
    ds_date = date_range_text((ps_dates.get("ds") or {}).get(lg))
    return f"""
<section class="league-block">
  <h2>{esc(LEAGUE_KO[lg])} ({lg})</h2>
  <div class="bracket">
    <div class="bracket-round">
      {round_title(ROUND_LABEL["wc"], wc_date)}
      {"".join(matchup_box(m) for m in wc)}
      {byes}
    </div>
    <div class="bracket-round">
      {round_title(ROUND_LABEL["ds"], ds_date)}
      {"".join(matchup_box(m) for m in ds)}
    </div>
  </div>
</section>
"""


def home_page(payload, base_url):
    body = "".join(league_bracket(lg, payload["leagues"][lg], payload.get("postseasonDates")) for lg in ("AL", "NL"))
    body += """
<section class="prose">
  <h2>어떻게 읽나요?</h2>
  <p>현재 순위를 기준으로 지구 우승 3팀은 승률 순으로 1~3시드, 와일드카드 상위 3팀은 4~6시드를 받아요.
     3시드와 6시드, 4시드와 5시드가 와일드카드 시리즈에서 맞붙고, 1시드와 2시드는 그 결과를 기다렸다가 디비전시리즈에 나가요.
     실제 승자는 아직 정해지지 않았으니, 디비전시리즈 칸에는 만날 수 있는 두 팀을 함께 보여드려요.</p>
  <p>리그 챔피언십 시리즈와 월드시리즈 대진은 그 앞 라운드 결과에 따라 정해져서 아직 표에 넣지 않았어요.
     팀 이름을 누르면 그 팀이 만날 수 있는 상대와 상대전적을 자세히 볼 수 있어요.</p>
  <p>라운드별 날짜는 MLB이 시즌 전에 미리 정해둔 공식 일정이에요. 1차전 시작 시각은 보통 중계 일정이 정해진 뒤에 공개되는데,
     아직 정해지지 않았다면 날짜만 보여드리고, MLB이 시각을 공개하면 30분 안에 자동으로 함께 표시돼요.</p>
</section>
"""
    title = "MLB 포스트시즌 대진표 - 와일드카드부터 디비전시리즈까지 시드별 대진"
    desc = "MLB 아메리칸리그·내셔널리그 포스트시즌 대진을 현재 순위 기준으로 그려서 보여드려요. 와일드카드 시리즈 확정 대진과 디비전시리즈에서 만날 수 있는 상대의 상대전적까지 확인하세요."
    return layout(title, desc, body, "/", base_url, "/", "🏆 포스트시즌 대진표", "현재 순위 기준 대진과 상대전적",
                  kst(payload["fetchedAt"]), alt_en="/en/")


def standings_note(t):
    if t["leader"]:
        return "지구 " + esc(DIVISION_KO[t["division"]])
    if t["wildCardRank"]:
        return f'WC {t["wildCardRank"]}위'
    return "-"


def league_page(lg, payload, base_url):
    data = payload["leagues"][lg]
    rows = "".join(
        f'<tr class="{"in-zone" if i < 6 else ""}"><td>{i + 1}</td><td class="team-name">'
        f'<a href="{team_url(t["abbr"])}">{logo(t["abbr"], "sm")} {esc(team_info(t["abbr"])["ko"])}</a></td>'
        f'<td>{t["wins"]}-{t["losses"]}</td><td>{esc(t["pctText"])}</td>'
        f'<td>{standings_note(t)}</td></tr>'
        for i, t in enumerate(data["standings"]))
    body = f"""
{league_bracket(lg, data, payload.get("postseasonDates"))}
<section>
  <h2>{esc(LEAGUE_KO[lg])} 전체 순위</h2>
  <div class="table-scroll"><table class="standings-table">
    <thead><tr><th>#</th><th>팀</th><th>승-패</th><th>승률</th><th>비고</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
  <p class="note">상위 6팀(초록 표시)이 포스트시즌 진출권이에요.</p>
</section>
"""
    return layout(f"{LEAGUE_KO[lg]} 포스트시즌 대진 · 순위 | {SITE_NAME}",
                  f"{LEAGUE_KO[lg]} 포스트시즌 대진과 전체 순위를 확인하세요.",
                  body, f"/{lg.lower()}/", base_url, f"/{lg.lower()}/", f"🏆 {esc(LEAGUE_KO[lg])}", "포스트시즌 대진과 순위",
                  kst(payload["fetchedAt"]), alt_en=f"/en/{lg.lower()}/")


def roster_group_rows(players):
    rows = ""
    for p in sorted(players, key=lambda p: p["fullName"]):
        ko = KOREAN_PLAYERS_KO.get(p["fullName"])
        pos = POSITION_KO.get(p["position"], p["position"] or "-")
        year = (p.get("birthDate") or "")[:4]
        status = ROSTER_STATUS_KO.get(p.get("status", ""))
        name_html = f'{esc(ko)} <span class="muted">({esc(p["fullName"])})</span>' if ko else esc(p["fullName"])
        status_html = f' <span class="player-status">{esc(status)}</span>' if status and status != "1군 활성" else ""
        rows += (f'<div class="roster-row"><span class="roster-name">{name_html}{status_html}</span>'
                  f'<span class="player-meta">{esc(pos)}{f" · {year}년생" if year else ""}</span></div>')
    return rows


def roster_section(team):
    if not team.get("postseasonRosterSet"):
        # 아직 이 팀의 포스트시즌 26인 로스터가 발표되지 않았어요. 자리만 만들어두고,
        # 그 팀의 라운드 첫 경기가 열려서 실제 26인이 확인되면 자동으로 채워져요.
        return """<section>
  <h2>전체 로스터 <span class="chip-pending">26인 로스터 발표 전</span></h2>
  <p class="note">이 팀의 포스트시즌 첫 경기가 열리면 실제 26인 로스터가 여기 자동으로 표시돼요.</p>
</section>"""
    roster = team.get("roster", [])
    if not roster:
        return ""
    used = set()
    groups = []
    for label, codes in ROSTER_GROUPS:
        used |= codes
        members = [p for p in roster if p["position"] in codes]
        if members:
            groups.append((label, members))
    others = [p for p in roster if p["position"] not in used]
    if others:
        groups.append(("기타", others))
    body = "".join(
        f'<div class="roster-group"><h3>{esc(label)} <span class="roster-count">{len(members)}명</span></h3>'
        f'<div class="roster-rows">{roster_group_rows(members)}</div></div>'
        for label, members in groups)
    return f"""<section>
  <h2>전체 로스터 <span class="chip-set">26인 로스터 확정</span></h2>
  <div class="roster-wrap">{body}</div>
</section>"""


def team_page(abbr, lg, payload, base_url):
    data = payload["leagues"][lg]
    seed_no = next(n for n, t in data["seeds"].items() if t["abbr"] == abbr)
    team = data["seeds"][seed_no]
    info = team_info(abbr)
    matches = data["perTeam"][seed_no]

    cards = ""
    for m in matches:
        opp = m["opponent"]
        cards += f"""<div class="opp-card">
            <div class="opp-label">{esc(m["label"])}</div>
            <div class="opp-team">{team_row(opp)}</div>
            <div class="opp-h2h">{h2h_line(abbr, m["h2h"])}</div>
        </div>"""

    name = info["ko"]
    faqs = [(f'{name}{josa(name, "은", "는")} 포스트시즌에서 몇 시드인가요?',
             f'{esc(LEAGUE_KO[lg])} {seed_no}시드예요. {team["role"]}으로 진출했고, 현재 {team["wins"]}승 {team["losses"]}패(승률 {team["pctText"]})예요.')]
    if matches:
        opp0 = matches[0]["opponent"]
        opp0_name = team_info(opp0["abbr"])["ko"]
        faqs.append((f'{name}{josa(name, "이", "가")} 포스트시즌에서 처음 만나는 상대는 누구인가요?',
                     f'{matches[0]["label"]}에서 {opp0_name}{josa(opp0_name, "과", "와")} 만나요. '
                     f'이번 시즌 상대전적은 {matches[0]["h2h"]["w"]}승 {matches[0]["h2h"]["l"]}패예요.'))
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)

    body = f"""
<section>
  <h2>{esc(info["ko"])} 포스트시즌 위치</h2>
  <div class="scenario-stats">
    <div class="stat-item"><div class="stat-label">시드</div><div class="stat-value">{esc(LEAGUE_KO[lg])} {seed_no}시드</div><div class="stat-sub">{esc(team["role"])}</div></div>
    <div class="stat-item"><div class="stat-label">전적</div><div class="stat-value">{team["wins"]}승 {team["losses"]}패</div><div class="stat-sub">승률 {esc(team["pctText"])}</div></div>
  </div>
</section>
<section>
  <h2>만날 수 있는 상대</h2>
  <div class="opp-grid">{cards}</div>
</section>
{roster_section(team)}
<section>{faq_html and f'<h2>자주 묻는 질문</h2><div class="faq">{faq_html}</div>'}</section>
<section><h2>{esc(LEAGUE_KO[lg])} 대진표로 돌아가기</h2><p><a class="chip" href="/{lg.lower()}/">{esc(LEAGUE_KO[lg])} 전체 대진 보기</a> <a class="chip" href="/">전체 대진표</a></p></section>
"""
    title = f"{info['ko']} 포스트시즌 상대전적 - 만날 수 있는 팀 | {SITE_NAME}"
    desc = f'{info["ko"]}({esc(LEAGUE_KO[lg])} {seed_no}시드)이 포스트시즌에서 만날 수 있는 상대와 이번 시즌 상대전적을 확인하세요.'
    return layout(title, desc, body, team_url(abbr), base_url, f"/{lg.lower()}/",
                  f'{logo(abbr, "lg")} {esc(info["ko"])}', f'{esc(LEAGUE_KO[lg])} {seed_no}시드 · {team["wins"]}승 {team["losses"]}패',
                  kst(payload["fetchedAt"]), alt_en=f"/en/team/{abbr.lower()}/")


def t_slot(team=None, seed=None, tbd=None):
    if team:
        return (f'<a class="t-slot" href="{team_url(team["abbr"])}"><span class="seed-no">{seed}</span>'
                f'{logo(team["abbr"], "sm")} {esc(team_info(team["abbr"])["ko"])}</a>')
    return f'<div class="t-slot tbd"><span class="seed-no"></span>{esc(tbd)}</div>'


def t_pair(a_html, b_html, mirror=False):
    return f'<div class="t-pair{" mirror" if mirror else ""}">{a_html}{b_html}</div>'


def league_tourney_rounds(lg, data, mirror=False):
    seeds = data["seeds"]
    r1 = "".join(t_pair(t_slot(seeds[a], a), t_slot(seeds[b], b), mirror) for a, b in ((4, 5), (3, 6)))
    r2 = "".join(
        t_pair(t_slot(seeds[s], s), t_slot(tbd=f"{a}·{b}시드 승자"), mirror)
        for s, (a, b) in ((1, (4, 5)), (2, (3, 6))))
    r3 = t_pair(t_slot(tbd="1시드측 승자"), t_slot(tbd="2시드측 승자"), mirror)
    return r1, r2, r3


def t_col_title(label, date_range):
    date_html = f'<span class="round-date">{esc(date_range)}</span>' if date_range else ""
    return f'<div class="t-col-title">{esc(label)}{date_html}</div>'


def tournament_page(payload, base_url):
    al1, al2, al3 = league_tourney_rounds("AL", payload["leagues"]["AL"])
    nl1, nl2, nl3 = league_tourney_rounds("NL", payload["leagues"]["NL"], mirror=True)
    ws = (f'{t_slot(tbd=esc(LEAGUE_KO["AL"]) + " 챔피언")}{t_slot(tbd=esc(LEAGUE_KO["NL"]) + " 챔피언")}')

    d = payload.get("postseasonDates") or {}
    wc_d = d.get("wc") or {}
    ds_d = d.get("ds") or {}
    cs_d = d.get("cs") or {}
    ws_date = date_range_text(d.get("ws"))

    body = f"""
<section class="tourney-wrap">
  <div class="tourney">
    <div class="t-col t-round-1">{t_col_title("AL 와일드카드", date_range_text(wc_d.get("AL")))}{al1}</div>
    <div class="t-col t-round-2">{t_col_title("AL 디비전시리즈", date_range_text(ds_d.get("AL")))}{al2}</div>
    <div class="t-col t-round-3">{t_col_title("AL 챔피언십시리즈", date_range_text(cs_d.get("AL")))}{al3}</div>
    <div class="t-col t-final"><div class="t-final-box"><div class="trophy">🏆</div><div class="t-final-title">월드시리즈</div>
      {f'<span class="round-date">{esc(ws_date)}</span>' if ws_date else ""}{ws}</div></div>
    <div class="t-col t-round-3">{t_col_title("NL 챔피언십시리즈", date_range_text(cs_d.get("NL")))}{nl3}</div>
    <div class="t-col t-round-2">{t_col_title("NL 디비전시리즈", date_range_text(ds_d.get("NL")))}{nl2}</div>
    <div class="t-col t-round-1">{t_col_title("NL 와일드카드", date_range_text(wc_d.get("NL")))}{nl1}</div>
  </div>
</section>
<section class="prose">
  <h2>어떻게 읽나요?</h2>
  <p>현재 순위를 기준으로 이미 정해진 와일드카드 시리즈 대진은 실제 팀으로 채워 넣었고,
     아직 승자가 정해지지 않은 디비전시리즈·챔피언십시리즈·월드시리즈는 점선 칸으로 비워뒀어요.
     각 라운드가 끝나면 그 결과에 맞춰 다음 칸이 채워져요. 팀을 누르면 그 팀의 상세 페이지로 이동해요.</p>
  <p>각 칸 아래 날짜는 MLB이 미리 정해둔 라운드 일정이에요. 1차전 시작 시각은 아직 정해지지 않았다면 날짜만 보여드리고,
     MLB이 공개하면 자동으로 함께 표시돼요.</p>
</section>
"""
    title = "MLB 포스트시즌 토너먼트 대진표 - 와일드카드부터 월드시리즈까지"
    desc = "MLB 아메리칸리그·내셔널리그 포스트시즌 전체 토너먼트를 한 화면에서 확인하세요. 확정된 와일드카드 대진과 앞으로 채워질 자리를 함께 보여드려요."
    return layout(title, desc, body, "/tournament/", base_url, "/tournament/", "🎋 포스트시즌 토너먼트", "와일드카드부터 월드시리즈까지 한눈에",
                  kst(payload["fetchedAt"]), alt_en="/en/tournament/")


POSITION_KO = {
    "P": "투수", "C": "포수", "1B": "1루수", "2B": "2루수", "3B": "3루수", "SS": "유격수",
    "LF": "좌익수", "CF": "중견수", "RF": "우익수", "OF": "외야수", "DH": "지명타자", "TWP": "투타 겸업",
}

# 로스터를 화면에 보여줄 때 묶는 순서와 그룹명. 여기 없는 포지션은 "기타"로 묶인다.
ROSTER_GROUPS = [
    ("투수진", {"P", "TWP"}),
    ("포수", {"C"}),
    ("내야수", {"1B", "2B", "3B", "SS", "IF"}),
    ("외야수", {"LF", "CF", "RF", "OF"}),
    ("지명타자", {"DH"}),
]


def korean_players_page(payload, base_url):
    with_players, without_players = [], []
    for lg in ("AL", "NL"):
        for t in payload["leagues"][lg]["seeds"].values():
            (with_players if t.get("koreanPlayers") else without_players).append((lg, t))

    def player_card(t):
        rows = ""
        for p in t["koreanPlayers"]:
            ko = KOREAN_PLAYERS_KO.get(p["fullName"])
            pos = POSITION_KO.get(p["position"], p["position"])
            year = (p.get("birthDate") or "")[:4]
            status = ROSTER_STATUS_KO.get(p.get("status", ""))
            name_html = f'{esc(ko)} <span class="muted">({esc(p["fullName"])})</span>' if ko else esc(p["fullName"])
            meta = f"{esc(pos)}{f' · {year}년생' if year else ''}"
            status_html = f'<div class="player-status">{esc(status)}</div>' if status and status != "1군 활성" else ""
            rows += (f'<div class="player-row"><div><strong>{name_html}</strong>{status_html}</div>'
                     f'<span class="player-meta">{meta}</span></div>')
        badge = ('<span class="chip-set">26인 로스터 확정</span>' if t.get("postseasonRosterSet")
                  else '<span class="chip-pending">26인 발표 전 · 40인 로스터 후보</span>')
        return f"""<div class="kr-card">
            <div class="kr-card-head">{team_row(t)}{badge}</div>
            <div class="kr-players">{rows}</div>
        </div>"""

    featured = "".join(player_card(t) for _, t in with_players)
    others = "".join(
        f'<a class="chip" href="{team_url(t["abbr"])}">{esc(team_info(t["abbr"])["ko"])}</a>' for _, t in without_players)

    body = f"""
<section class="prose">
  <h2>포스트시즌에 오른 한국인 선수</h2>
  <p>포스트시즌에 진출한 12개 팀 중 한국 출신 선수가 있는 팀을 모았어요. 각 팀의 실제 26인 출전 명단은
     그 팀의 라운드 첫 경기가 열려야 공개되기 때문에, 그 전까지는 40인 로스터 후보를 보여주고
     ("26인 발표 전" 표시), 경기가 시작되면 자동으로 그 라운드의 실제 26인 로스터 기준으로 바뀌어요
     ("26인 로스터 확정" 표시) — 26인에 없는 선수는 이때 자동으로 목록에서 빠져요.</p>
</section>
<section><div class="kr-grid">{featured or "<p class='muted'>이번 포스트시즌 진출 팀 중에는 한국 출신 선수가 없어요.</p>"}</div></section>
{f'''<section class="prose">
  <h2>한국인 선수가 없는 팀</h2>
  <div class="chips">{others}</div>
</section>''' if others else ""}
<section>
  <h2>자주 묻는 질문</h2>
  <div class="faq">
    <details><summary>왜 여기 없는 유명한 한국 선수가 있나요?</summary><p>이 페이지는 포스트시즌에 진출한 12개 팀만 대상으로 해요. 소속팀이 포스트시즌에 오르지 못했다면 목록에 없어요.</p></details>
    <details><summary>이 선수들이 포스트시즌 경기에 실제로 나오나요?</summary><p>"26인 발표 전" 표시가 있는 팀은 아직 40인 로스터 후보 단계라 실제로 뛰는지 확실하지 않아요. 그 팀의 라운드 첫 경기가 시작되면 자동으로 실제 26인 출전 명단 기준으로 바뀌면서 "26인 로스터 확정" 표시로 바뀌고, 26인에 들지 못한 선수는 목록에서 빠져요.</p></details>
  </div>
</section>
"""
    return layout(f"MLB 포스트시즌 한국인 선수 | {SITE_NAME}",
                  "포스트시즌에 진출한 12개 팀 중 한국 출신 선수가 있는 팀을 모아서 보여드려요.",
                  body, "/korean-players/", base_url, "/korean-players/", "🇰🇷 한국인 선수",
                  "포스트시즌 진출팀의 한국 출신 선수", kst(payload["fetchedAt"]))


def guide_hub_page(base_url):
    cards = "".join(
        f'<a class="team-card" href="/guide/{slug}/"><strong>{esc(g["title"])}</strong>'
        f'<div class="tc-sub">{esc(g["desc"])}</div></a>' for slug, g in GUIDES.items())
    body = f"""
<section class="prose">
  <h2>포스트시즌 가이드</h2>
  <p>대진과 순위만으로는 알기 어려운 포스트시즌 규정을 쉽게 정리했어요.</p>
</section>
<section><div class="team-grid">{cards}</div></section>
"""
    return layout(f"MLB 포스트시즌 가이드 | {SITE_NAME}", "MLB 포스트시즌 경기 방식, 시드 규정을 쉽게 설명하는 가이드 모음.",
                  body, "/guide/", base_url, "/guide/", "📖 가이드", "포스트시즌 규정 쉽게 알아보기", alt_en="/en/guide/")


def guide_page(slug, base_url):
    g = GUIDES[slug]
    others = "".join(f'<a class="chip" href="/guide/{s}/">{esc(o["title"])}</a>' for s, o in GUIDES.items() if s != slug)
    body = g["html"] + (f'<section><h2>다른 가이드</h2><div class="chips">{others}</div></section>' if others else "")
    from pages_en import GUIDES_EN
    alt_en = f"/en/guide/{slug}/" if slug in GUIDES_EN else None
    return layout(f'{g["title"]} | {SITE_NAME}', g["desc"], body, f"/guide/{slug}/", base_url, "/guide/",
                  esc(g["title"]), "MLB 포스트시즌 가이드", alt_en=alt_en)


def about_page(base_url):
    body = """
<section class="prose">
  <h2>사이트 소개</h2>
  <p>MLB 포스트시즌 대진표는 아메리칸리그·내셔널리그의 현재 순위를 바탕으로 포스트시즌 대진이 어떻게 만들어질지 보여주는 사이트예요.
     와일드카드 시리즈는 확정된 대진이고, 디비전시리즈는 와일드카드 시리즈 결과에 따라 달라지는 만큼 만날 수 있는 상대를 함께 보여드려요.</p>
  <h2>시드는 이렇게 정해요</h2>
  <p>각 리그에서 지구 우승 3팀을 승률 순으로 1~3시드, 나머지 팀 중 와일드카드 순위 상위 3팀을 4~6시드로 정해요.
     3시드 대 6시드, 4시드 대 5시드가 와일드카드 시리즈(3전 2선승제)를 치르고, 승자가 1시드·2시드와 디비전시리즈(5전 3선승제)를 치러요.
     그 승자끼리 리그 챔피언십 시리즈, 마지막으로 양 리그 우승팀이 월드시리즈를 치르는데 이 두 라운드는 7전 4선승제예요.</p>
  <h2>상대전적은 어떻게 계산하나요</h2>
  <p>MLB Stats API에서 관련된 6개 팀의 이번 시즌 경기 일정을 가져와, 두 팀이 실제로 치른 경기의 승패를 세어 계산해요.
     리그 챔피언십 시리즈·월드시리즈처럼 아직 만날 팀이 정해지지 않은 단계는 보여드리지 않아요.</p>
  <h2>알려드려요</h2>
  <p>이 사이트는 MLB 및 각 구단과 관련이 없는 비공식 사이트이고, 제공하는 정보는 참고용이에요.
     순위 데이터는 MLB Stats API에서 30분마다 새로 가져와요. 실제 대진과 일정은 MLB 공식 사이트에서 확인하세요.</p>
</section>"""
    return layout(f"사이트 소개 | {SITE_NAME}", f"{SITE_NAME}의 대진 계산 방식과 데이터 출처를 소개해요.", body, "/about/", base_url,
                  "/about/", "ℹ️ 사이트 소개", "대진 계산 방식과 데이터 출처", alt_en="/en/about/")


PAGE_PREFIXES = ("/al", "/nl", "/team/", "/about", "/tournament", "/guide", "/korean-players")


def is_page(path):
    return path.startswith(PAGE_PREFIXES) or path == "/"


def render(path, base_url, payload):
    path = path.rstrip("/") + "/" if not path.endswith(".html") else path
    if path == "/":
        return 200, home_page(payload, base_url)
    if path == "/tournament/":
        return 200, tournament_page(payload, base_url)
    if path == "/korean-players/":
        return 200, korean_players_page(payload, base_url)
    if path in ("/al/", "/nl/"):
        return 200, league_page(path.strip("/").upper(), payload, base_url)
    if path.startswith("/team/"):
        abbr = path[len("/team/"):].strip("/").upper()
        for lg in ("AL", "NL"):
            if any(t["abbr"] == abbr for t in payload["leagues"][lg]["seeds"].values()):
                return 200, team_page(abbr, lg, payload, base_url)
        return 404, None
    if path == "/guide/":
        return 200, guide_hub_page(base_url)
    if path.startswith("/guide/"):
        slug = path[len("/guide/"):].strip("/")
        return (200, guide_page(slug, base_url)) if slug in GUIDES else (404, None)
    if path == "/about/":
        return 200, about_page(base_url)
    return None


def sitemap_urls(payload):
    urls = ["/", "/tournament/", "/korean-players/", "/al/", "/nl/", "/guide/", "/about/", "/privacy.html"]
    urls += [f"/guide/{s}/" for s in GUIDES]
    for lg in ("AL", "NL"):
        urls += [team_url(t["abbr"]) for t in payload["leagues"][lg]["seeds"].values()]
    return urls


def sitemap(base_url, payload, extra_urls=None):
    urls = sitemap_urls(payload) + (extra_urls or [])
    today = datetime.date.today().isoformat()
    body = "".join(f"<url><loc>{esc(base_url + u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
