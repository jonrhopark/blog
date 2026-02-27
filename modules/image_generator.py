"""
PIL을 사용한 이미지 생성 - 모던 리디자인
한글 네모박스 오류 수정 + 다크/모던 플랫 디자인
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import IMG_CONTENT_SIZE, THUMB_TISTORY_SIZE, THUMB_BLOGGER_SIZE


# ── 색상 팔레트 (모던 다크) ────────────────────────────────────────────────────
C = {
    "dark":       (15,  23,  42),   # #0f172a
    "navy":       (30,  64, 175),   # #1e40af
    "navy2":      (20,  30,  80),   # 어두운 네이비
    "blue":       (59, 130, 246),   # #3b82f6
    "light_blue": (219, 234, 254),  # #dbeafe
    "purple":     (124, 58, 237),   # #7c3aed
    "amber":      (245, 158,  11),  # #f59e0b
    "green":      ( 16, 185, 129),  # #10b981
    "dark_green": (  5,  46,  22),
    "white":      (255, 255, 255),
    "off_white":  (248, 250, 252),  # #f8fafc
    "gray_100":   (241, 245, 249),  # #f1f5f9
    "gray_300":   (203, 213, 225),  # #cbd5e1
    "gray_500":   (100, 116, 139),  # #64748b
    "gray_800":   ( 30,  41,  59),  # #1e293b
}


# ── 폰트 로드 (한글 지원 강화) ────────────────────────────────────────────────
def _find_korean_font():
    """시스템에서 한글 지원 폰트 탐색 (FONTS config 의존 제거)"""
    candidates = [
        ("C:/Windows/Fonts/malgunbd.ttf", 0),   # 맑은 고딕 Bold
        ("C:/Windows/Fonts/malgun.ttf",   0),   # 맑은 고딕
        ("C:/Windows/Fonts/gulim.ttc",    0),   # 굴림
        ("C:/Windows/Fonts/batang.ttc",   0),   # 바탕
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",    1),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 1),
        ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",    0),
        ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",        0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        0),
    ]
    for path, index in candidates:
        if os.path.exists(path):
            return path, index
    return None, 0


_FONT_PATH, _FONT_IDX = _find_korean_font()


def _f(size: int) -> ImageFont.FreeTypeFont:
    """한글 폰트 로드"""
    if _FONT_PATH:
        try:
            return ImageFont.truetype(_FONT_PATH, size, index=_FONT_IDX)
        except Exception:
            pass
    return ImageFont.load_default()


def _emoji_font(size: int) -> ImageFont.FreeTypeFont:
    for p in ["C:/Windows/Fonts/seguiemj.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return _f(size)


# ── 드로잉 헬퍼 ───────────────────────────────────────────────────────────────
def _grad(draw, x1, y1, x2, y2, c1, c2, vertical=True):
    """두 색상 직선 그라데이션"""
    n = max((y2 - y1) if vertical else (x2 - x1), 1)
    for i in range(n):
        t = i / n
        col = tuple(int(c1[j] + (c2[j] - c1[j]) * t) for j in range(3))
        if vertical:
            draw.line([(x1, y1 + i), (x2, y1 + i)], fill=col)
        else:
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=col)


def _rrect(draw, x1, y1, x2, y2, r, fill, outline=None, ow=1):
    """모서리 둥근 사각형"""
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)
    for cx, cy in [(x1, y1), (x2 - 2*r, y1), (x1, y2 - 2*r), (x2 - 2*r, y2 - 2*r)]:
        draw.ellipse([cx, cy, cx + 2*r, cy + 2*r], fill=fill)
    if outline:
        corners = [(x1, y1, 180, 270), (x2-2*r, y1, 270, 360),
                   (x1, y2-2*r, 90, 180), (x2-2*r, y2-2*r, 0, 90)]
        for cx, cy, s, e in corners:
            draw.arc([cx, cy, cx+2*r, cy+2*r], s, e, fill=outline, width=ow)
        draw.line([x1+r, y1, x2-r, y1], fill=outline, width=ow)
        draw.line([x1+r, y2, x2-r, y2], fill=outline, width=ow)
        draw.line([x1, y1+r, x1, y2-r], fill=outline, width=ow)
        draw.line([x2, y1+r, x2, y2-r], fill=outline, width=ow)


def _wrap(draw, text: str, font, max_width: int) -> list:
    """텍스트 줄바꿈"""
    lines, current = [], ""
    for word in (text.split() or [text]):
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text[:25]]


def _centered_text(draw, cx, cy, text, font, fill):
    """중앙 정렬 텍스트"""
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2),
              text, font=font, fill=fill)


# ── 콘텐츠 이미지 1: 핵심 포인트 (800×450) ───────────────────────────────────
def make_content_img1(topic: str, subtitle: str, points: list, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["off_white"])
    draw = ImageDraw.Draw(img)

    # 다크 그라데이션 헤더
    _grad(draw, 0, 0, w, 108, C["dark"], C["navy"])
    draw.rectangle([0, 0, 6, 108], fill=C["amber"])  # 왼쪽 액센트 바

    # 헤더 텍스트
    draw.text((24, 18), topic[:28],    font=_f(32), fill=C["white"])
    draw.text((24, 70), subtitle[:40], font=_f(18), fill=C["light_blue"])

    # 포인트 카드
    badge_colors = [C["blue"], C["purple"], C["green"], C["amber"]]
    y = 124
    for i, point in enumerate(points[:4]):
        color = badge_colors[i % 4]
        _rrect(draw, 18, y, w - 18, y + 56, 8, C["white"])
        draw.rectangle([18, y, 23, y + 56], fill=color)       # 왼쪽 색선
        draw.ellipse([30, y + 13, 56, y + 39], fill=color)    # 번호 배지
        _centered_text(draw, 43, y + 26, str(i + 1), _f(15), C["white"])
        draw.text((68, y + 16), str(point)[:44], font=_f(20), fill=C["gray_800"])
        y += 68

    img.save(save_path)


# ── 콘텐츠 이미지 2: 수치/표 (800×450) ───────────────────────────────────────
def make_content_img2(topic: str, table_data: list, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["white"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    _grad(draw, 0, 0, w, 78, C["navy"], C["blue"])
    draw.rectangle([0, 0, 6, 78], fill=C["amber"])
    draw.text((22, 20), topic[:32], font=_f(30), fill=C["white"])

    # 표 영역 배경
    draw.rectangle([14, 86, w - 14, h - 30], fill=C["off_white"])

    if table_data:
        col_x   = [26, 260, 510]
        row_h   = 48
        y       = 94

        # 표 헤더 행
        draw.rectangle([14, y, w - 14, y + row_h], fill=C["navy"])
        headers = table_data[0] if table_data else ["항목", "내용", "비고"]
        for i, hdr in enumerate(headers[:3]):
            draw.text((col_x[i], y + 12), str(hdr)[:14], font=_f(17), fill=C["white"])
        y += row_h

        # 데이터 행
        for idx, row in enumerate(table_data[1:6]):
            bg = C["gray_100"] if idx % 2 == 0 else C["white"]
            draw.rectangle([14, y, w - 14, y + row_h], fill=bg)
            for j, cell in enumerate(row[:3]):
                col = C["blue"] if j == 2 else C["gray_800"]
                draw.text((col_x[j], y + 12), str(cell)[:18], font=_f(17), fill=col)
            draw.line([14, y + row_h, w - 14, y + row_h], fill=C["gray_300"], width=1)
            y += row_h

    # 하단 출처
    draw.rectangle([0, h - 28, w, h], fill=C["gray_100"])
    draw.text((20, h - 21), "출처: 기획재정부 2026년 세제개편안",
              font=_f(13), fill=C["gray_500"])

    img.save(save_path)


# ── 콘텐츠 이미지 3: 실전 절차 (800×450) ─────────────────────────────────────
def make_content_img3(topic: str, steps: list, result: str, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["white"])
    draw = ImageDraw.Draw(img)

    # 헤더
    _grad(draw, 0, 0, w, 78, C["dark_green"], C["green"])
    draw.rectangle([0, 0, 6, 78], fill=C["amber"])
    draw.text((22, 20), topic[:32], font=_f(30), fill=C["white"])

    # 타임라인 세로선
    tx = 46
    draw.line([(tx, 96), (tx, h - 106)], fill=C["gray_300"], width=2)

    step_colors = [C["blue"], C["purple"], C["green"], C["amber"]]
    y = 98
    for i, step in enumerate(steps[:4]):
        color = step_colors[i % 4]
        # 타임라인 원형
        draw.ellipse([tx - 14, y - 2, tx + 14, y + 26],
                     fill=C["white"], outline=color, width=3)
        _centered_text(draw, tx, y + 12, str(i + 1), _f(14), color)
        # 스텝 카드
        _rrect(draw, 72, y - 6, w - 18, y + 34, 8, C["off_white"])
        draw.rectangle([72, y - 6, 77, y + 34], fill=color)
        draw.text((88, y + 5), str(step)[:42], font=_f(19), fill=C["gray_800"])
        y += 70

    # 결과 박스
    if result:
        _rrect(draw, 16, h - 90, w - 16, h - 12, 10, C["light_blue"])
        draw.rectangle([16, h - 90, 22, h - 12], fill=C["blue"])
        draw.text((32, h - 78), "결과", font=_f(14), fill=C["navy"])
        draw.text((32, h - 58), str(result)[:54], font=_f(17), fill=C["navy"])

    img.save(save_path)


# ── 썸네일: 티스토리 800×450 ─────────────────────────────────────────────────
def make_thumb_tistory(num: int, title: str, subtitle: str, amount: str, save_path: str):
    w, h = THUMB_TISTORY_SIZE
    img = Image.new('RGB', (w, h), C["dark"])
    draw = ImageDraw.Draw(img)

    # 배경 그라데이션
    _grad(draw, 0, 0, w, h, C["dark"], C["navy2"])

    # 오른쪽 장식 원형들 (subtle)
    for i, offset in enumerate(range(0, 130, 10)):
        brightness = max(25, 70 - offset)
        cx, cy = w - 70, h // 2
        r = 140 + offset
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(brightness, brightness + 15, brightness + 50), width=1)

    # 왼쪽 강조 바
    draw.rectangle([0, 0, 7, h], fill=C["amber"])

    # 연도 배지
    _rrect(draw, 24, 22, 120, 58, 6, C["amber"])
    _centered_text(draw, 72, 40, "2026", _f(22), C["dark"])

    # 메인 제목
    lines = _wrap(draw, title, _f(40), w - 250)
    y = 76
    for line in lines[:3]:
        draw.text((24, y), line, font=_f(40), fill=C["white"])
        y += 52

    # 서브타이틀
    draw.text((24, y + 6), subtitle[:38], font=_f(23), fill=C["light_blue"])

    # 금액 원형 배지
    cx, cy, r = w - 112, h // 2, 86
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=C["navy2"], outline=C["amber"], width=3)
    amt = amount[:8]
    amt_f = _f(26)
    _centered_text(draw, cx, cy, amt, amt_f, C["amber"])

    # 하단 라인 + 정보
    draw.line([(24, h - 36), (w - 24, h - 36)], fill=(60, 80, 120), width=1)
    draw.text((24, h - 28), f"#{num}  bbogil.com",
              font=_f(15), fill=C["gray_500"])

    img.save(save_path)


# ── 썸네일: 블로그스팟 1200×628 ──────────────────────────────────────────────
def make_thumb_blogger(num: int, persona: str, title: str, amount: str,
                       emoji: str, save_path: str):
    w, h = THUMB_BLOGGER_SIZE
    divide = w * 2 // 3  # 800

    img = Image.new('RGB', (w, h), C["dark"])
    draw = ImageDraw.Draw(img)

    # 좌측 다크 그라데이션
    _grad(draw, 0, 0, w, h, C["dark"], C["navy2"])

    # 우측 밝은 영역 (사선 분할)
    draw.polygon([(divide, 0), (w, 0), (w, h), (divide - 70, h)],
                 fill=C["gray_100"])

    # 왼쪽 강조 바
    draw.rectangle([0, 0, 8, h], fill=C["blue"])

    # 상단 배지
    _rrect(draw, 24, 28, 184, 66, 6, C["blue"])
    draw.text((38, 34), "실전 후기", font=_f(24), fill=C["white"])

    # 페르소나
    draw.text((24, 82), persona[:38], font=_f(21), fill=C["gray_500"])

    # 메인 제목
    lines = _wrap(draw, title, _f(44), divide - 90)
    y = 118
    for line in lines[:3]:
        draw.text((24, y), line, font=_f(44), fill=C["white"])
        y += 58

    # 금액 강조 박스
    y = min(y, h - 130)
    _rrect(draw, 24, y + 18, min(490, divide - 50), y + 82, 10,
           fill=C["navy2"], outline=C["amber"], ow=2)
    draw.text((40, y + 32), amount[:28], font=_f(28), fill=C["amber"])

    # 우측 이모지 원형
    cx = divide + (w - divide) // 2
    cy = h // 2
    r  = 108
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=C["white"], outline=C["blue"], width=3)
    try:
        ef = _emoji_font(68)
        eb = draw.textbbox((0, 0), emoji, font=ef)
        ew, eh = eb[2] - eb[0], eb[3] - eb[1]
        draw.text((cx - ew // 2, cy - eh // 2), emoji, font=ef, fill=C["navy"])
    except Exception:
        _centered_text(draw, cx, cy, emoji, _f(60), C["navy"])

    # 하단
    draw.line([(24, h - 38), (divide - 80, h - 38)], fill=(60, 80, 120), width=1)
    draw.text((24, h - 30), f"2026.02  돈·건강·AI 이야기  #{num}",
              font=_f(17), fill=C["gray_500"])

    img.save(save_path)


def BLOG_DOMAIN_SHORT():
    return "bbogil.com"
