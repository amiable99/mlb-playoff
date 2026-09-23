"""MLB 30개 팀의 한글 이름과 표시 색(공식 로고가 아니라 팀 컬러 원 + 약칭으로 표현한다)."""

TEAM_INFO = {
    "BAL": {"ko": "볼티모어 오리올스", "short": "오리올스", "color": "#df4601"},
    "BOS": {"ko": "보스턴 레드삭스", "short": "레드삭스", "color": "#bd3039"},
    "NYY": {"ko": "뉴욕 양키스", "short": "양키스", "color": "#0c2340"},
    "TB":  {"ko": "탬파베이 레이스", "short": "레이스", "color": "#092c5c"},
    "TOR": {"ko": "토론토 블루제이스", "short": "블루제이스", "color": "#134a8e"},
    "CWS": {"ko": "시카고 화이트삭스", "short": "화이트삭스", "color": "#27251f"},
    "CLE": {"ko": "클리블랜드 가디언스", "short": "가디언스", "color": "#00385d"},
    "DET": {"ko": "디트로이트 타이거스", "short": "타이거스", "color": "#0c2340"},
    "KC":  {"ko": "캔자스시티 로열스", "short": "로열스", "color": "#004687"},
    "MIN": {"ko": "미네소타 트윈스", "short": "트윈스", "color": "#002b5c"},
    "HOU": {"ko": "휴스턴 애스트로스", "short": "애스트로스", "color": "#eb6e1f"},
    "LAA": {"ko": "LA 에인절스", "short": "에인절스", "color": "#ba0021"},
    "ATH": {"ko": "애슬레틱스", "short": "애슬레틱스", "color": "#003831"},
    "SEA": {"ko": "시애틀 매리너스", "short": "매리너스", "color": "#005c5c"},
    "TEX": {"ko": "텍사스 레인저스", "short": "레인저스", "color": "#003278"},
    "ATL": {"ko": "애틀랜타 브레이브스", "short": "브레이브스", "color": "#ce1141"},
    "MIA": {"ko": "마이애미 말린스", "short": "말린스", "color": "#00a3e0"},
    "NYM": {"ko": "뉴욕 메츠", "short": "메츠", "color": "#ff5910"},
    "PHI": {"ko": "필라델피아 필리스", "short": "필리스", "color": "#e81828"},
    "WSH": {"ko": "워싱턴 내셔널스", "short": "내셔널스", "color": "#ab0003"},
    "CHC": {"ko": "시카고 컵스", "short": "컵스", "color": "#0e3386"},
    "CIN": {"ko": "신시내티 레즈", "short": "레즈", "color": "#c6011f"},
    "MIL": {"ko": "밀워키 브루어스", "short": "브루어스", "color": "#12284b"},
    "PIT": {"ko": "피츠버그 파이리츠", "short": "파이리츠", "color": "#fdb827", "fg": "#111111"},
    "STL": {"ko": "세인트루이스 카디널스", "short": "카디널스", "color": "#c41e3a"},
    "AZ":  {"ko": "애리조나 다이아몬드백스", "short": "다이아몬드백스", "color": "#a71930"},
    "COL": {"ko": "콜로라도 로키스", "short": "로키스", "color": "#33006f"},
    "LAD": {"ko": "LA 다저스", "short": "다저스", "color": "#005a9c"},
    "SD":  {"ko": "샌디에이고 파드리스", "short": "파드리스", "color": "#2f241d"},
    "SF":  {"ko": "샌프란시스코 자이언츠", "short": "자이언츠", "color": "#fd5a1e"},
}

DIVISION_KO = {"E": "동부", "C": "중부", "W": "서부"}
LEAGUE_KO = {"AL": "아메리칸리그", "NL": "내셔널리그"}

# 한국 출신(MLB API의 birthCountry == "Republic of Korea") 선수의 정확한 한글 이름.
# 확인되지 않은 선수의 한글 이름을 추측해서 붙이지 않도록, 여기 없는 선수는 로마자 이름만 보여준다.
# key는 MLB API의 fullName과 정확히 같아야 한다.
KOREAN_PLAYERS_KO = {
    "Hyeseong Kim": "김혜성",
    "Ha-Seong Kim": "김하성",
    "Sung-Mun Song": "송성문",
    "Jung Hoo Lee": "이정후",
    "Jihwan Bae": "배지환",
    "Hyun-Seok Jang": "장현석",
    "Chan-Min Park": "박찬민",
}

# MLB API의 로스터 상태(status.description) → 한글 표시. 실제 포스트시즌 출전 가능성을 가늠하는 데 참고가 된다.
ROSTER_STATUS_KO = {
    "Active": "1군 활성",
    "Injured 60-Day": "60일 부상자 명단",
    "Injured 15-Day": "15일 부상자 명단",
    "Injured 10-Day": "10일 부상자 명단",
    "Reassigned to Minors": "마이너리그 재배정",
    "Restricted List": "제한 명단(아직 활동 전)",
    "Paternity List": "출산 휴가",
    "Bereavement List": "상(喪) 휴가",
    "Suspended List": "출전 정지",
}
