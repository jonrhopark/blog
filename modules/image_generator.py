"""
PIL을 사용한 이미지 생성 (콘텐츠 이미지 3개 + 썸네일 2개)
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COLOR, FONTS, IMG_CONTENT_SIZE, THUMB_TISTORY_SIZE, THUMB_BLOGGER_SIZE


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """한글 폰트 로드"""
    if FONTS is None:
        return ImageFont.load_default()
    key = "bold" if bold else "regular"
    path, index = FONTS[key]
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()


def _load_emoji_font(size: int) -> ImageFont.FreeTypeFont:
    if FONTS and os.path.exists(FONTS["emoji"][0]):
        try:
            return ImageFont.truetype(FONTS["emoji"][0], size)
        except Exception:
            pass
    return ImageFont.load_default()


def _hex(color: str):
    """#RRGGBB → (R, G, B)"""
    c = color.lstrip('#')
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    """텍스트 줄바꿈"""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + (" " if current else "") + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ── 콘텐츠 이미지 (800×450) ──────────────────────────────────────────────────

def make_content_img1(topic: str, subtitle: str, points: list, save_path: str):
    """이미지1: 핵심 개념 비교"""
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), _hex(COLOR["extra_light"]))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(36)
    sub_font = _load_font(26)
    body_font = _load_font(22, bold=False)

    # 헤더 배경
    draw.rectangle([0, 0, w, 80], fill=_hex(COLOR["primary"]))
    draw.text((30, 20), topic[:30], font=title_font, fill=(255, 255, 255))

    # 서브타이틀
    draw.text((30, 100), subtitle[:40], font=sub_font, fill=_hex(COLOR["text_dark"]))

    # 포인트 목록
    y = 155
    for i, point in enumerate(points[:4]):
        # 원형 번호
        draw.ellipse([28, y-2, 52, y+22], fill=_hex(COLOR["primary"]))
        draw.text((34, y), str(i+1), font=_load_font(16), fill=(255, 255, 255))
        # 텍스트
        draw.text((62, y), str(point)[:45], font=body_font, fill=_hex(COLOR["text_dark"]))
        y += 52

    img.save(save_path)


def make_content_img2(topic: str, table_data: list, save_path: str):
    """이미지2: 수치/표"""
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(32)
    header_font = _load_font(22)
    body_font = _load_font(20, bold=False)

    # 헤더
    draw.rectangle([0, 0, w, 70], fill=_hex(COLOR["primary"]))
    draw.text((30, 18), topic[:35], font=title_font, fill=(255, 255, 255))

    # 표 그리기
    col_x = [30, 280, 530]
    row_h = 52
    y = 90

    if table_data:
        # 헤더 행
        headers = table_data[0] if table_data else ["항목", "기존", "변경"]
        draw.rectangle([20, y, w-20, y+row_h], fill=_hex(COLOR["light_blue"]))
        for i, hdr in enumerate(headers[:3]):
            draw.text((col_x[i], y+12), str(hdr)[:18], font=header_font, fill=_hex(COLOR["text_dark"]))
        y += row_h

        # 데이터 행
        for j, row in enumerate(table_data[1:5]):
            bg = _hex(COLOR["extra_light"]) if j % 2 == 0 else (255, 255, 255)
            draw.rectangle([20, y, w-20, y+row_h], fill=bg)
            for i, cell in enumerate(row[:3]):
                draw.text((col_x[i], y+12), str(cell)[:18], font=body_font,
                          fill=_hex(COLOR["text_dark"]))
            y += row_h

    # 하단 라인
    draw.line([20, h-30, w-20, h-30], fill=_hex(COLOR["light_blue"]), width=2)
    draw.text((30, h-24), "출처: 기획재정부 2026년 세제개편안", font=_load_font(16, bold=False),
              fill=_hex(COLOR["text_medium"]))

    img.save(save_path)


def make_content_img3(topic: str, steps: list, result: str, save_path: str):
    """이미지3: 실전 적용/절차"""
    w, h = IMG_CONTENT_SIZE
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_font = _load_font(32)
    step_font = _load_font(22)
    body_font = _load_font(19, bold=False)

    # 헤더
    draw.rectangle([0, 0, w, 70], fill=_hex(COLOR["success"]))
    draw.text((30, 18), topic[:35], font=title_font, fill=(255, 255, 255))

    # 스텝
    y = 90
    for i, step in enumerate(steps[:4]):
        x = 30
        # 스텝 번호 원형
        draw.ellipse([x, y, x+34, y+34], fill=_hex(COLOR["success"]))
        draw.text((x+8, y+5), str(i+1), font=_load_font(18), fill=(255, 255, 255))
        # 스텝 텍스트
        draw.text((x+45, y+6), str(step)[:42], font=step_font, fill=_hex(COLOR["text_dark"]))
        y += 48

    # 결과 박스
    if result:
        draw.rectangle([20, h-90, w-20, h-20], fill=_hex(COLOR["extra_light"]),
                        outline=_hex(COLOR["primary"]), width=2)
        draw.text((32, h-78), "💡 " + str(result)[:50], font=body_font,
                  fill=_hex(COLOR["primary"]))

    img.save(save_path)


# ── 썸네일 이미지 ────────────────────────────────────────────────────────────

def make_thumb_tistory(num: int, title: str, subtitle: str, amount: str, save_path: str):
    """티스토리 썸네일 800×450"""
    w, h = THUMB_TISTORY_SIZE
    img = Image.new('RGB', (w, h), _hex(COLOR["extra_light"]))
    draw = ImageDraw.Draw(img)

    # 배경 그라데이션 효과 (오른쪽 밝게)
    for x in range(w):
        alpha = int(255 * (0.85 + 0.15 * x / w))
        draw.line([(x, 0), (x, h)], fill=(alpha, alpha, 255))

    # 왼쪽 강조 바
    draw.rectangle([0, 0, 8, h], fill=_hex(COLOR["primary"]))

    # 2026 레이블
    draw.rectangle([30, 25, 130, 60], fill=_hex(COLOR["primary"]))
    draw.text((42, 32), "2026", font=_load_font(24), fill=(255, 255, 255))

    # 메인 제목
    title_font = _load_font(38)
    lines = _wrap_text(draw, title, title_font, w - 200)
    y = 80
    for line in lines[:3]:
        draw.text((30, y), line, font=title_font, fill=_hex(COLOR["text_dark"]))
        y += 52

    # 서브 제목
    sub_font = _load_font(26)
    draw.text((30, y + 10), subtitle[:40], font=sub_font, fill=_hex(COLOR["primary"]))

    # 오른쪽 원형 강조 (금액)
    cx, cy, r = w - 110, h // 2, 90
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=_hex(COLOR["extra_light"]),
                 outline=_hex(COLOR["primary"]), width=3)
    amt_font = _load_font(28)
    draw.text((cx - 50, cy - 20), amount[:8], font=amt_font, fill=_hex(COLOR["primary"]))

    # 하단 정보
    draw.text((30, h - 40), f"#{num}  {BLOG_DOMAIN_SHORT()}",
              font=_load_font(18, bold=False), fill=_hex(COLOR["text_medium"]))

    img.save(save_path)


def make_thumb_blogger(num: int, persona: str, title: str, amount: str,
                       emoji: str, save_path: str):
    """블로그스팟 썸네일 1200×628"""
    w, h = THUMB_BLOGGER_SIZE
    # 따뜻한 그라데이션 배경
    img = Image.new('RGB', (w, h), (255, 251, 245))
    draw = ImageDraw.Draw(img)

    # 배경 (따뜻한 톤)
    for x in range(w):
        r = int(255 - 10 * x / w)
        draw.line([(x, 0), (x, h)], fill=(r, 248, 235))

    # 카드 영역
    card = [60, 40, w - 60, h - 40]
    draw.rectangle(card, fill=(255, 255, 255), outline=_hex(COLOR["primary"]), width=3)

    # 초록 레이블
    draw.rectangle([80, 55, 230, 90], fill=_hex(COLOR["success"]))
    draw.text((90, 60), "실제 후기", font=_load_font(22), fill=(255, 255, 255))

    # 페르소나
    draw.text((80, 105), persona[:40], font=_load_font(24, bold=False),
              fill=_hex(COLOR["text_medium"]))

    # 메인 제목
    title_font = _load_font(42)
    lines = _wrap_text(draw, title, title_font, w - 350)
    y = 150
    for line in lines[:3]:
        draw.text((80, y), line, font=title_font, fill=_hex(COLOR["text_dark"]))
        y += 56

    # 금액 강조 박스
    draw.rectangle([80, y + 20, 480, y + 80], fill=_hex(COLOR["extra_light"]),
                   outline=_hex(COLOR["primary"]), width=2)
    draw.text((95, y + 30), amount[:30], font=_load_font(30), fill=_hex(COLOR["primary"]))

    # 이모지 원형 (우측)
    cx, cy, r = w - 180, h // 2, 110
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=_hex(COLOR["light_green"]),
                 outline=_hex(COLOR["success"]), width=3)
    emoji_font = _load_emoji_font(70)
    draw.text((cx - 35, cy - 40), emoji, font=emoji_font, fill=_hex(COLOR["success"]))

    # 하단 정보
    draw.text((80, h - 70), f"2026.02  돈·건강·AI 이야기",
              font=_load_font(20, bold=False), fill=_hex(COLOR["text_light"]))

    img.save(save_path)


def BLOG_DOMAIN_SHORT():
    return "bbogil.com"
