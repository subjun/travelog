# -*- coding: utf-8 -*-
"""travelog 웹페이지 빌드 — 해설집 md 12편을 변환해 template.html에 주입한다.
사용: python site/build.py  → site/index.html 생성
"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE_DIR = ROOT / "trips" / "2026-09_osaka-kobe" / "해설집"
SITE = ROOT / "site"

# (파일 슬러그, 앵커 id, 번호, 일정 칩)
CHAPTERS = [
    ("오사카", "g-osaka", "城市", "도시 해설"),
    ("고베", "g-kobe", "城市", "도시 해설"),
    ("기타노-이진칸", "g-kitano", "9/21", "9/21 15:50"),
    ("메리켄파크", "g-meriken", "9/21", "9/21 17:40"),
    ("하버랜드", "g-harbor", "9/21", "9/21 18:15"),
    ("아리마온천", "g-arima", "9/22", "9/22 오전"),
    ("오사카성", "g-castle", "9/22", "9/22 16:10"),
    ("스미요시타이샤", "g-sumiyoshi", "9/23", "9/23 오후"),
    ("신세카이-츠텐카쿠", "g-shinsekai", "9/23", "9/23 저녁"),
    ("천진바시스지", "g-tenjinbashi", "9/24", "9/24 오후"),
    ("나카노시마-도서관", "g-nakanoshima", "9/25", "9/24·25 러닝 · 9/25 오전"),
    ("도톤보리-우라난바", "g-dotonbori", "매일", "매일 · 9/24"),
]


# 챕터별 내장 사진: (파일명, 캡션, 작가·라이선스, 출처 파일페이지 URL)
FIGURES = {
    "오사카": [
        ("osaka-umeda.jpg", "우메다에서 본 오사카 도심", "Marek Ślusarczyk · CC BY 3.0", "https://commons.wikimedia.org/wiki/File:Osaka,_Japan_-_Umeda_district_-_city_view_of_Osaka,_Japan.jpg"),
        ("osaka-night.jpg", "우메다 스카이빌딩에서 본 야경", "Kaiza96 · CC BY-SA 3.0", "https://commons.wikimedia.org/wiki/File:Osaka_skyline_at_night_from_Umeda_Sky_Building.jpg"),
    ],
    "고베": [
        ("kobe-city.jpg", "포아이시오사이 공원에서 본 고베 — 산이 바다까지 바짝 붙은 띠 모양 도시", "663highland · CC BY 2.5", "https://commons.wikimedia.org/wiki/File:Kobe_City_view_from_Po-ai_Shiosai_Park01s3.jpg"),
    ],
    "기타노-이진칸": [
        ("kitano-thomas1.jpg", "풍향계의 집 — 이진칸 유일의 벽돌조", "663highland · CC BY 2.5", "https://commons.wikimedia.org/wiki/File:Kobe_kitano_thomas_house07_2816.jpg"),
        ("kitano-thomas2.jpg", "지붕 위 수탉 풍향계", "Soramimi · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Thomas_House_20150920.jpg"),
    ],
    "메리켄파크": [
        ("meriken.jpg", "포트타워와 메리켄파크 오리엔탈 호텔", "Zairon · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Kobe_Kobe_Port_Tower_Blick_auf_das_Kobe_Meriken_Park_Oriental_Hotel_1.jpg"),
    ],
    "하버랜드": [
        ("harborland.jpg", "umie 모자이크 — 2층 데크가 야경 포인트", "DVMG · CC BY 3.0", "https://commons.wikimedia.org/wiki/File:MOSAIC,_Kobe_Harborland_-_panoramio.jpg"),
    ],
    "아리마온천": [
        ("arima1.jpg", "킨노유 외관", "Wpcpey · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Kin-no-yu_Arima_Onsen_2013.jpg"),
        ("arima2.jpg", "킨노유 — 금탕 입구", "663highland · CC BY 2.5", "https://commons.wikimedia.org/wiki/File:Kin-no-yu_Arima_Onsen01s3200.jpg"),
    ],
    "오사카성": [
        ("castle1.jpg", "천수각 남측 — 돌담은 도쿠가와, 외형은 히데요시, 몸체는 1931년", "DXR · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Osaka_Castle,_Keep_tower,_South_view_20190415_1.jpg"),
        ("castle2.jpg", "해자 너머의 천수각", "663highland · CC BY 2.5", "https://commons.wikimedia.org/wiki/File:Osaka_Castle_02bs3200.jpg"),
    ],
    "스미요시타이샤": [
        ("sumiyoshi1.jpg", "소리하시(태고교) — 건너는 것 자체가 정화", "chiron3636 · CC BY 2.0", "https://commons.wikimedia.org/wiki/File:Sorihashi_Bridge,_Sumiyoshi-taisha_Shrine_-_Oct_15,_2015.jpg"),
        ("sumiyoshi2.jpg", "수면에 비치면 원이 되는 주홍 아치", "Soramimi · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Sorihashi_Bridge_in_Sumiyoshi_Grand_Shrine_8.jpg"),
    ],
    "신세카이-츠텐카쿠": [
        ("shinsekai1.jpg", "신세카이와 츠텐카쿠", "Sakai Yayoi · CC0", "https://commons.wikimedia.org/wiki/File:Shinsekai_and_Tsutenkaku_Tower.jpg"),
        ("shinsekai2.jpg", "1912년 초대 츠텐카쿠와 루나파크 — 에펠탑+개선문", "퍼블릭 도메인", "https://commons.wikimedia.org/wiki/File:Original_Tsutenkaku_and_Shinsekai_2.jpg"),
    ],
    "천진바시스지": [
        ("tenjinbashi.jpg", "일본 최장 2.6km 아케이드", "DVMG · CC BY 3.0", "https://commons.wikimedia.org/wiki/File:Tenjinbashisuji_shopping_street_-_panoramio.jpg"),
    ],
    "나카노시마-도서관": [
        ("nakanoshima1.jpg", "중앙공회당 — 주식중매인 한 사람의 기부", "Daniel Lu · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Osaka_City_Central_Public_Hall_main_facade_2026_dllu.jpg"),
        ("nakanoshima2.jpg", "나카노시마의 다이오사카 시대 진열장", "Sakai Yayoi · CC0", "https://commons.wikimedia.org/wiki/File:Osaka_Nakanoshima_Public_Hall.jpg"),
    ],
    "도톤보리-우라난바": [
        ("dotonbori1.jpg", "도톤보리 야경 — 극장 간판 문화의 후예들", "Martin Falbisoner · CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Dotonbori,_Osaka,_at_night,_November_2016.jpg"),
        ("dotonbori2.jpg", "글리코 러너 — 1935년 초대부터 6대째", "CC0", "https://commons.wikimedia.org/wiki/File:Glico_signs_in_Dotonbori_at_night,18th_August_2014.JPG"),
    ],
}


def figure_html(slug: str) -> str:
    figs = FIGURES.get(slug, [])
    if not figs:
        return ""
    items = []
    for fname, cap, credit, src in figs:
        p = SITE / "assets" / fname
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        items.append(
            f'<figure><img src="data:image/jpeg;base64,{b64}" alt="{cap}" loading="lazy">'
            f'<figcaption><span class="figtag">참고사진</span><b>{cap}</b> — {credit} · '
            f'<a href="{src}" target="_blank" rel="noopener">출처</a> · 여행 후 내 사진으로 교체</figcaption></figure>'
        )
    if not items:
        return ""
    single = " single" if len(items) == 1 else ""
    return f'<div class="figs{single}">' + "".join(items) + "</div>"


def inline(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"「([^」]*)」", r"「\1」", s)
    return s


def md_to_html(md: str) -> tuple[str, str]:
    """(title, body_html) — h1은 제목으로 뽑고 본문은 chbody 규격으로 변환."""
    title = ""
    out, buf, mode = [], [], None  # mode: p/ul/bq/table

    def flush():
        nonlocal buf, mode
        if not buf:
            mode = None
            return
        if mode == "p":
            out.append("<p>" + " ".join(buf) + "</p>")
        elif mode == "ul":
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in buf) + "</ul>")
        elif mode == "ol":
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in buf) + "</ol>")
        elif mode == "bq":
            out.append("<blockquote>" + "".join(f"<p>{x}</p>" for x in buf) + "</blockquote>")
        elif mode == "table":
            rows = [r for r in buf if not re.match(r"^[\s|:-]+$", r)]
            html = []
            for i, row in enumerate(rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if i == 0 else "td"
                html.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            if html:
                out.append('<div class="tblwrap"><table><thead>' + html[0] + "</thead><tbody>"
                           + "".join(html[1:]) + "</tbody></table></div>")
        buf, mode = [], None

    for raw in md.splitlines():
        line = raw.rstrip()
        if re.match(r"^<!--.*-->\s*$", line.strip()):
            continue
        if line.startswith("# "):
            title = inline(line[2:].strip())
            flush()
            continue
        if line.startswith("## "):
            flush()
            out.append(f"<h4>{inline(line[3:].strip())}</h4>")
            continue
        if not line.strip():
            flush()
            continue
        if line.startswith("> "):
            if mode != "bq":
                flush()
                mode = "bq"
            buf.append(inline(line[2:].strip()))
            continue
        if line.strip().startswith("|"):
            if mode != "table":
                flush()
                mode = "table"
            buf.append(line.strip())
            continue
        if re.match(r"^- ", line):
            if mode != "ul":
                flush()
                mode = "ul"
            buf.append(inline(line[2:].strip()))
            continue
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            if mode != "ol":
                flush()
                mode = "ol"
            buf.append(inline(m.group(1)))
            continue
        if mode not in ("p",):
            flush()
            mode = "p"
        buf.append(inline(line.strip()))
    flush()
    return title, "\n".join(out)


def build_guide() -> str:
    parts = []
    for i, (slug, anchor, _badge, day) in enumerate(CHAPTERS, 1):
        path = GUIDE_DIR / f"{slug}.md"
        title, body = md_to_html(path.read_text(encoding="utf-8"))
        open_attr = " open" if i == 1 else ""
        parts.append(
            f'<details class="chapter" id="{anchor}"{open_attr}>\n'
            f'<summary><span class="cno">{i:02d}</span>'
            f'<span class="ct">{title}</span>'
            f'<span class="cday">{day}</span></summary>\n'
            f'<div class="chbody">\n{figure_html(slug)}\n{body}\n</div>\n</details>'
        )
    return "\n".join(parts)


def main():
    tpl = (SITE / "template.html").read_text(encoding="utf-8")
    html = (tpl
            .replace("{{GUIDE}}", build_guide())
            .replace("{{MEALS}}", (SITE / "partials" / "meals.html").read_text(encoding="utf-8"))
            .replace("{{MONEY}}", (SITE / "partials" / "money.html").read_text(encoding="utf-8"))
            .replace("{{OPEN}}", (SITE / "partials" / "open.html").read_text(encoding="utf-8")))
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"built: {out} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
