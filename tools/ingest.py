# -*- coding: utf-8 -*-
"""여행 중 현장 수집 — 디스코드로 들어온 사진·메모를 trips/<여행>/현장/ 에 저장한다.

사용:
  python tools/ingest.py --slug 오사카성 --at "2026-09-22 16:20" --memo "천수각 줄 20분" --photo a.jpg b.jpg
  python tools/ingest.py --memo "뭔지 모르겠는 골목"            # slug 생략 → 미분류
  python tools/ingest.py --slug 고베 --photo c.jpg              # 메모 없이 사진만

원칙: 버리는 것보다 잘못 분류하는 게 낫고, 잘못 분류하는 것보다 미분류가 낫다.
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIP = ROOT / "trips" / "2026-09_osaka-kobe"
FIELD = TRIP / "현장"
PHOTO_DIR = FIELD / "사진"
LOG = FIELD / "기록.md"

# site/build.py 의 CHAPTERS 와 반드시 동일 (슬러그 12종)
SLUGS = [
    "오사카", "고베", "기타노-이진칸", "메리켄파크", "하버랜드", "아리마온천",
    "오사카성", "스미요시타이샤", "신세카이-츠텐카쿠", "천진바시스지",
    "나카노시마-도서관", "도톤보리-우라난바",
]
UNSORTED = "미분류"

MAX_EDGE = 1600
JPEG_Q = 80


def parse_at(s: str | None) -> datetime:
    if not s:
        return datetime.now()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%m-%d %H:%M"):
        try:
            d = datetime.strptime(s, fmt)
            return d.replace(year=datetime.now().year) if fmt == "%m-%d %H:%M" else d
        except ValueError:
            continue
    raise SystemExit(f"[ingest] --at 형식을 못 읽었다: {s!r} (예: 2026-09-22 16:20)")


def save_photo(src: Path, slug: str, at: datetime) -> str:
    from PIL import Image, ImageOps

    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{at:%m%d-%H%M}_{slug}"
    n = 1
    while (PHOTO_DIR / f"{stem}_{n:02d}.jpg").exists():
        n += 1
    dst = PHOTO_DIR / f"{stem}_{n:02d}.jpg"

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # 폰 회전 정보 반영
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > MAX_EDGE:
            r = MAX_EDGE / max(w, h)
            im = im.resize((max(1, round(w * r)), max(1, round(h * r))), Image.LANCZOS)
        im.save(dst, "JPEG", quality=JPEG_Q, optimize=True)
    return dst.name


def append_log(slug: str, at: datetime, memo: str, photos: list[str]) -> None:
    FIELD.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text("# 현장 기록\n\n> 여행 중 디스코드 #travelog 로 들어온 메모·사진. "
                       "`tools/ingest.py` 가 append 한다 (덮어쓰기 금지).\n", encoding="utf-8")
    block = [f"\n## {at:%m/%d %H:%M} · {slug}\n"]
    if memo:
        block.append(memo.strip() + "\n")
    if photos:
        block.append("사진: " + ", ".join(photos) + "\n")
    with LOG.open("a", encoding="utf-8") as f:
        f.write("".join(block))


def main() -> None:
    ap = argparse.ArgumentParser(description="현장 사진·메모 저장")
    ap.add_argument("--slug", default=UNSORTED, help=f"포인트 슬러그 12종 중 하나. 애매하면 생략({UNSORTED})")
    ap.add_argument("--at", help="YYYY-MM-DD HH:MM (KST). 생략 시 현재 시각")
    ap.add_argument("--memo", default="", help="메모 원문")
    ap.add_argument("--photo", nargs="*", default=[], help="사진 파일 경로 (여러 개 가능)")
    a = ap.parse_args()

    slug = a.slug.strip() or UNSORTED
    if slug not in SLUGS and slug != UNSORTED:
        print(f"[ingest] 알 수 없는 슬러그 {slug!r} → {UNSORTED} 로 저장한다. "
              f"(허용: {', '.join(SLUGS)})", file=sys.stderr)
        slug = UNSORTED
    if re.search(r'[\\/:*?"<>|_]', slug):
        raise SystemExit(f"[ingest] 슬러그에 파일명 금지문자가 있다: {slug!r}")

    at = parse_at(a.at)
    if not a.memo and not a.photo:
        raise SystemExit("[ingest] --memo 나 --photo 중 하나는 있어야 한다")

    saved = []
    for p in a.photo:
        src = Path(p)
        if not src.exists():
            print(f"[ingest] 사진 없음, 건너뜀: {src}", file=sys.stderr)
            continue
        saved.append(save_photo(src, slug, at))

    append_log(slug, at, a.memo, saved)

    bits = []
    if a.memo:
        bits.append("메모 1건")
    if saved:
        bits.append(f"사진 {len(saved)}장")
    print(f"📥 {slug} · {' · '.join(bits)} 저장")


if __name__ == "__main__":
    main()
