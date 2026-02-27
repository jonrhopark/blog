"""
PIL을 사용한 이미지 생성 - 클린 라이트 디자인
흰 배경 / 소프트 컬러 / 충분한 여백
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import IMG_CONTENT_SIZE, THUMB_TISTORY_SIZE, THUMB_BLOGGER_SIZE


# ── 색상 팔레트 (라이트·소프트) ──────────────────────────────────────────────
C = {
    # 배경
    "white":       (255, 255, 255),
    "bg":          (248, 250, 252),   # 거의 흰색
    "bg2":         (241, 245, 249),   # 연한 회청
    # 텍스트
    "text":        (15,  23,  42),    # 거의 검정
    "text2":       (51,  65,  85),    # 중간 슬레이트
    "text3":       (100, 116, 139),   # 연한 슬레이트
    # 경계선
    "line":        (226, 232, 240),   # 매우 연한 회색
    "line2":       (203, 213, 225),
    # 소프트 액센트 (배지 배경용)
    "blue_s":      (219, 234, 254),   # #dbeafe
    "indigo_s":    (224, 231, 255),   # #e0e7ff
    "emerald_s":   (209, 250, 229),   # #d1fae5
    "amber_s":     (254, 243, 199),   # #fef3c7
    "violet_s":    (237, 233, 254),   # #ede9fe
    "rose_s":      (255, 228, 230),   # #ffe4e6
    # 진한 액센트 (텍스트·아이콘용)
    "blue":        (37,  99,  235),   # #2563eb
    "indigo":      (79,  70,  229),   # #4f46e5
    "emerald":     (5,   150, 105),   # #059669
    "amber":       (180, 103, 4),     # dark amber
    "amber_b":     (245, 158, 11),    # bright amber
    "violet":      (109, 40,  217),   # #6d28d9
    "rose":        (190, 18,  60),    # #be123c
    # 썸네일용
    "thumb_bg":    (15,  23,  42),    # 다크 네이비
    "thumb_card":  (30,  41,  59),    # 슬레이트 카드
    "thumb_line":  (51,  65,  85),    # 구분선
}

BADGE_SOFT = [C["blue_s"], C["emerald_s"], C["violet_s"], C["amber_s"]]
BADGE_DARK = [C["blue"],   C["emerald"],   C["violet"],   C["amber"]]


# ── 폰트 ─────────────────────────────────────────────────────────────────────
def _find_korean_font():
    candidates = [
        ("C:/Windows/Fonts/malgunbd.ttf", 0),
        ("C:/Windows/Fonts/malgun.ttf",   0),
        ("C:/Windows/Fonts/gulim.ttc",    0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",    1),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 1),
        ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",    0),
        ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf",        0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        0),
    ]
    for path, index in candidates:
        if os.path.exists(path):
            return path, index
    return None, 0


_FONT_PATH, _FONT_IDX = _find_korean_font()


def _f(size: int) -> ImageFont.FreeTypeFont:
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
    n = max((y2 - y1) if vertical else (x2 - x1), 1)
    for i in range(n):
        t = i / n
        col = tuple(int(c1[j] + (c2[j] - c1[j]) * t) for j in range(3))
        if vertical:
            draw.line([(x1, y1 + i), (x2, y1 + i)], fill=col)
        else:
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=col)


def _rrect(draw, x1, y1, x2, y2, r, fill, outline=None, ow=1):
    r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)
    for cx, cy in [(x1, y1), (x2 - 2*r, y1), (x1, y2 - 2*r), (x2 - 2*r, y2 - 2*r)]:
        draw.ellipse([cx, cy, cx + 2*r, cy + 2*r], fill=fill)
    if outline:
        corners = [(x1, y1, 180, 270), (x2-2*r, y1, 270, 360),
                   (x1, y2-2*r, 90, 180), (x2-2*r, y2-2*r, 0, 90)]
        for bx, by, s, e in corners:
            draw.arc([bx, by, bx+2*r, by+2*r], s, e, fill=outline, width=ow)
        draw.line([x1+r, y1, x2-r, y1], fill=outline, width=ow)
        draw.line([x1+r, y2, x2-r, y2], fill=outline, width=ow)
        draw.line([x1, y1+r, x1, y2-r], fill=outline, width=ow)
        draw.line([x2, y1+r, x2, y2-r], fill=outline, width=ow)


def _wrap_words(draw, text: str, font, max_width: int) -> list:
    lines, current = [], ""
    for word in text.split() or [text]:
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
                current = word
            else:
                for ch in word:
                    t2 = current + ch
                    if draw.textbbox((0, 0), t2, font=font)[2] <= max_width:
                        current = t2
                    else:
                        if current:
                            lines.append(current)
                        current = ch
    if current:
        lines.append(current)
    return lines or [text[:20]]


def _cx(draw, cx, y, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (bb[2] - bb[0]) // 2, y), text, font=font, fill=fill)


def _cxy(draw, cx, cy, text, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2),
              text, font=font, fill=fill)


# ── 콘텐츠 이미지 1: 핵심 포인트 (800×450) ───────────────────────────────────
def make_content_img1(topic: str, subtitle: str, points: list, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["bg"])
    draw = ImageDraw.Draw(img)

    # 상단 헤더 영역 (흰 배경 + 하단 얇은 선)
    draw.rectangle([0, 0, w, 90], fill=C["white"])
    draw.rectangle([0, 89, w, 91], fill=C["line"])

    # 상단 좌측 컬러 포인트 바
    draw.rectangle([0, 0, 5, 90], fill=C["blue"])

    # 제목
    draw.text((22, 16), topic[:28], font=_f(30), fill=C["text"])
    draw.text((22, 58), subtitle[:44], font=_f(16), fill=C["text3"])

    # 우측 배지
    tag_w = draw.textbbox((0, 0), "핵심 포인트", font=_f(14))[2] + 24
    _rrect(draw, w - tag_w - 16, 28, w - 16, 62, 20,
           C["blue_s"], outline=C["line"], ow=1)
    _cxy(draw, w - tag_w // 2 - 16, 45, "핵심 포인트", _f(14), C["blue"])

    # 카드 리스트
    card_h = 66
    gap = 6
    y = 106
    for i, point in enumerate(points[:4]):
        soft = BADGE_SOFT[i]
        dark = BADGE_DARK[i]

        # 카드 (흰 배경 + 연한 테두리)
        _rrect(draw, 16, y, w - 16, y + card_h, 10,
               C["white"], outline=C["line"], ow=1)

        # 번호 배지 (소프트 배경 원형)
        bx, by = 50, y + card_h // 2
        draw.ellipse([bx - 19, by - 19, bx + 19, by + 19], fill=soft)
        _cxy(draw, bx, by, str(i + 1), _f(17), dark)

        # 포인트 텍스트
        pt_lines = _wrap_words(draw, str(point), _f(19), w - 110)
        ty = y + (card_h - len(pt_lines[:2]) * 26) // 2
        for line in pt_lines[:2]:
            draw.text((80, ty), line, font=_f(19), fill=C["text2"])
            ty += 26

        y += card_h + gap

    # 하단 푸터
    draw.rectangle([0, h - 26, w, h], fill=C["bg2"])
    draw.text((20, h - 19), "2026년 최신 기준", font=_f(12), fill=C["text3"])

    img.save(save_path)


# ── 콘텐츠 이미지 2: 수치/표 (800×450) ───────────────────────────────────────
def make_content_img2(topic: str, table_data: list, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["bg"])
    draw = ImageDraw.Draw(img)

    # 헤더
    draw.rectangle([0, 0, w, 82], fill=C["white"])
    draw.rectangle([0, 81, w, 83], fill=C["line"])
    draw.rectangle([0, 0, 5, 82], fill=C["indigo"])
    draw.text((22, 16), topic[:32], font=_f(30), fill=C["text"])

    tag_w = draw.textbbox((0, 0), "데이터 비교", font=_f(14))[2] + 24
    _rrect(draw, w - tag_w - 16, 24, w - 16, 58, 20,
           C["indigo_s"], outline=C["line"], ow=1)
    _cxy(draw, w - tag_w // 2 - 16, 41, "데이터 비교", _f(14), C["indigo"])

    if table_data:
        col_w = (w - 32) // 3
        col_x = [16, 16 + col_w, 16 + col_w * 2]
        row_h = 50
        y = 96

        # 헤더 행
        _rrect(draw, 16, y, w - 16, y + row_h, 8, C["indigo_s"])
        for i, hdr in enumerate(table_data[0][:3]):
            _cxy(draw, col_x[i] + col_w // 2, y + row_h // 2,
                 str(hdr)[:14], _f(16), C["indigo"])
        y += row_h + 2

        # 데이터 행
        for idx, row in enumerate(table_data[1:6]):
            bg = C["white"] if idx % 2 == 0 else C["bg"]
            draw.rectangle([16, y, w - 16, y + row_h], fill=bg)
            draw.rectangle([16, y + row_h - 1, w - 16, y + row_h], fill=C["line"])
            for j, cell in enumerate(row[:3]):
                col = C["blue"] if j == 2 else C["text2"]
                font = _f(17) if j == 2 else _f(16)
                _cxy(draw, col_x[j] + col_w // 2, y + row_h // 2,
                     str(cell)[:18], font, col)
            # 세로 구분선
            for lx in col_x[1:]:
                draw.line([(lx, y + 8), (lx, y + row_h - 8)],
                          fill=C["line2"], width=1)
            y += row_h

    # 하단 푸터
    draw.rectangle([0, h - 26, w, h], fill=C["bg2"])
    draw.text((20, h - 19), "출처: 기획재정부 2026년 세제개편안", font=_f(12), fill=C["text3"])

    img.save(save_path)


# ── 콘텐츠 이미지 3: 실전 절차 (800×450) ─────────────────────────────────────
def make_content_img3(topic: str, steps: list, result: str, save_path: str):
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), C["bg"])
    draw = ImageDraw.Draw(img)

    # 헤더
    draw.rectangle([0, 0, w, 82], fill=C["white"])
    draw.rectangle([0, 81, w, 83], fill=C["line"])
    draw.rectangle([0, 0, 5, 82], fill=C["emerald"])
    draw.text((22, 16), topic[:32], font=_f(30), fill=C["text"])

    tag_w = draw.textbbox((0, 0), "실전 절차", font=_f(14))[2] + 24
    _rrect(draw, w - tag_w - 16, 24, w - 16, 58, 20,
           C["emerald_s"], outline=C["line"], ow=1)
    _cxy(draw, w - tag_w // 2 - 16, 41, "실전 절차", _f(14), C["emerald"])

    has_result = bool(result)
    content_h = h - 82 - (82 if has_result else 16) - 8
    step_count = min(len(steps), 4)
    step_h = content_h // max(step_count, 1)

    TL_X = 54
    y = 92
    for i, step in enumerate(steps[:4]):
        dark = BADGE_DARK[i]
        soft = BADGE_SOFT[i]

        # 타임라인 연결선
        if i < step_count - 1:
            draw.line([(TL_X, y + 22), (TL_X, y + step_h - 6)],
                      fill=C["line2"], width=2)

        # 번호 원 (소프트 배경)
        draw.ellipse([TL_X - 18, y - 18, TL_X + 18, y + 18], fill=soft)
        _cxy(draw, TL_X, y, str(i + 1), _f(16), dark)

        # 스텝 카드
        cy1 = y - 20
        cy2 = y + step_h - 14
        _rrect(draw, TL_X + 28, cy1, w - 16, cy2, 8,
               C["white"], outline=C["line"], ow=1)
        draw.rectangle([TL_X + 28, cy1, TL_X + 32, cy2], fill=dark)

        step_lines = _wrap_words(draw, str(step), _f(18), w - TL_X - 80)
        ty = cy1 + (cy2 - cy1 - len(step_lines[:2]) * 24) // 2
        for line in step_lines[:2]:
            draw.text((TL_X + 42, ty), line, font=_f(18), fill=C["text2"])
            ty += 24

        y += step_h

    # 결과 박스
    if has_result:
        ry = h - 76
        _rrect(draw, 16, ry, w - 16, ry + 60, 10, C["emerald_s"], outline=C["line"])
        draw.rectangle([16, ry, 20, ry + 60], fill=C["emerald"])
        draw.text((28, ry + 8), "결과", font=_f(13), fill=C["emerald"])
        res_lines = _wrap_words(draw, str(result), _f(16), w - 72)
        for j, line in enumerate(res_lines[:2]):
            draw.text((28, ry + 28 + j * 20), line, font=_f(16), fill=C["text2"])

    img.save(save_path)


# ── 썸네일: 티스토리 800×450 ─────────────────────────────────────────────────
def make_thumb_tistory(num: int, title: str, subtitle: str, amount: str, save_path: str):
    w, h = THUMB_TISTORY_SIZE
    img = Image.new('RGB', (w, h), C["thumb_bg"])
    draw = ImageDraw.Draw(img)

    # 배경 미세 그라데이션
    _grad(draw, 0, 0, w, h, C["thumb_bg"], (22, 33, 55))

    # 좌측 액센트 바
    draw.rectangle([0, 0, 5, h], fill=C["blue"])

    # 상단 배지들 (소프트 + 아웃라인)
    _rrect(draw, 20, 22, 106, 56, 6, (255, 255, 255, 0))
    draw.rectangle([20, 22, 106, 56], fill=(30, 41, 59))
    _rrect(draw, 20, 22, 106, 56, 6, (0, 0, 0, 0), outline=(70, 100, 160), ow=1)
    _cxy(draw, 63, 39, "2026", _f(20), (147, 197, 253))

    # 메인 제목
    title_font = _f(42)
    title_lines = _wrap_words(draw, title, title_font, w - 230)
    ty = 72
    for line in title_lines[:3]:
        draw.text((20, ty), line, font=title_font, fill=C["white"])
        ty += 54

    # 서브타이틀
    draw.text((20, ty + 6), subtitle[:38], font=_f(20), fill=(147, 197, 253))

    # 우측 금액 박스 (둥근 카드)
    bx1, by1, bx2, by2 = w - 196, h // 2 - 58, w - 20, h // 2 + 58
    _rrect(draw, bx1, by1, bx2, by2, 14, C["thumb_card"],
           outline=(70, 100, 160), ow=1)
    amt_lines = _wrap_words(draw, amount[:16], _f(22), bx2 - bx1 - 20)
    ay = (by1 + by2) // 2 - len(amt_lines) * 14
    for line in amt_lines[:2]:
        _cx(draw, (bx1 + bx2) // 2, ay, line, _f(22), C["amber_b"])
        ay += 32

    # 하단
    draw.line([(20, h - 32), (w - 220, h - 32)], fill=C["thumb_line"], width=1)
    draw.text((20, h - 24), f"#{num}  bbogil.com", font=_f(14), fill=(100, 116, 139))

    img.save(save_path)


# ── 썸네일: 블로그스팟 1200×628 ──────────────────────────────────────────────
def make_thumb_blogger(num: int, persona: str, title: str, amount: str,
                       emoji: str, save_path: str):
    w, h = THUMB_BLOGGER_SIZE

    img = Image.new('RGB', (w, h), C["thumb_bg"])
    draw = ImageDraw.Draw(img)

    # 배경 그라데이션
    _grad(draw, 0, 0, w, h, C["thumb_bg"], (22, 33, 55))

    # 우측 밝은 패널
    divide = w * 3 // 5
    draw.polygon([(divide, 0), (w, 0), (w, h), (divide - 50, h)],
                 fill=(20, 30, 52))

    # 좌측 액센트 바
    draw.rectangle([0, 0, 5, h], fill=C["indigo"])

    # 상단 배지
    _rrect(draw, 20, 24, 140, 58, 6, (0, 0, 0, 0), outline=(70, 90, 150), ow=1)
    _cxy(draw, 80, 41, "실전 후기", _f(19), (147, 179, 253))

    # 페르소나
    draw.text((20, 72), persona[:40], font=_f(18), fill=(100, 116, 139))

    # 메인 제목
    title_font = _f(44)
    title_lines = _wrap_words(draw, title, title_font, divide - 60)
    ty = 106
    for line in title_lines[:3]:
        draw.text((20, ty), line, font=title_font, fill=C["white"])
        ty += 58

    # 금액 박스
    amount_y = min(ty + 14, h - 110)
    amt_lines = _wrap_words(draw, amount[:28], _f(26), divide - 70)
    box_h = len(amt_lines[:2]) * 34 + 20
    _rrect(draw, 20, amount_y, divide - 40, amount_y + box_h, 10,
           C["thumb_card"], outline=(70, 100, 160), ow=1)
    ay = amount_y + 10
    for line in amt_lines[:2]:
        draw.text((34, ay), line, font=_f(26), fill=C["amber_b"])
        ay += 34

    # 우측 이모지 원형 (클린)
    cx = divide + (w - divide) // 2
    cy = h // 2
    r = 110
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=C["thumb_card"], outline=(70, 100, 160), width=2)
    try:
        ef = _emoji_font(80)
        eb = draw.textbbox((0, 0), emoji, font=ef)
        ew, eh = eb[2] - eb[0], eb[3] - eb[1]
        draw.text((cx - ew // 2, cy - eh // 2), emoji, font=ef, fill=C["white"])
    except Exception:
        _cxy(draw, cx, cy, emoji, _f(72), C["white"])

    # 하단
    draw.line([(20, h - 36), (divide - 60, h - 36)],
              fill=C["thumb_line"], width=1)
    draw.text((20, h - 28), f"2026.02  돈·건강·AI 이야기  #{num}",
              font=_f(16), fill=(100, 116, 139))

    img.save(save_path)


def BLOG_DOMAIN_SHORT():
    return "bbogil.com"
