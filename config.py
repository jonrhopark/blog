"""
블로그 자동화 설정 파일
"""
import os
import platform

# ─── 블로그 정보 ───────────────────────────────────────────────────────────────
TISTORY_DOMAIN = "https://bbogil.com"
BLOGGER_DOMAIN = "https://jjongjjong1.blogspot.com"
BLOG_NAME = "돈·건강·AI 이야기"
BLOG_SUBTITLE = "실전 재테크와 생활정보"
BLOG_META = "2026년 세제혜택, 배당투자, 재테크 실전 정보를 검증된 자료로 쉽게 알려드립니다."

# ─── 색상 팔레트 (고정) ────────────────────────────────────────────────────────
COLOR = {
    "primary":      "#3b82f6",
    "light_blue":   "#dbeafe",
    "extra_light":  "#eff6ff",
    "success":      "#22c55e",
    "light_green":  "#f0fdf4",
    "warning":      "#f59e0b",
    "light_yellow": "#fef3c7",
    "error":        "#ef4444",
    "light_red":    "#fef2f2",
    "text_dark":    "#1f2937",
    "text_medium":  "#6b7280",
    "text_light":   "#94a3b8",
}

# ─── 폰트 설정 ────────────────────────────────────────────────────────────────
def get_fonts():
    system = platform.system()
    if system == "Windows":
        # Windows 폰트 경로
        win_fonts = [
            "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
            "C:/Windows/Fonts/malgunbd.ttf",    # 맑은 고딕 Bold
            "C:/Windows/Fonts/gulim.ttc",       # 굴림
        ]
        for f in win_fonts:
            if os.path.exists(f):
                return {
                    "bold": (f, 0),
                    "regular": (f, 0),
                    "emoji": ("C:/Windows/Fonts/seguiemj.ttf", 0),
                }
        # 폰트 없으면 None 반환 (기본 폰트 사용)
        return None
    else:
        # Linux 폰트 경로
        noto_bold = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
        noto_regular = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        dejavu = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(noto_bold):
            return {
                "bold": (noto_bold, 1),        # index=1 → KR
                "regular": (noto_regular, 1),  # index=1 → KR
                "emoji": (dejavu, 0),
            }
        return None

FONTS = get_fonts()

# ─── 이미지 크기 ───────────────────────────────────────────────────────────────
IMG_CONTENT_SIZE = (800, 450)      # 본문 콘텐츠 이미지
THUMB_TISTORY_SIZE = (800, 450)    # 티스토리 썸네일
THUMB_BLOGGER_SIZE = (1200, 628)   # 블로그스팟 썸네일

# ─── 글자수 기준 ───────────────────────────────────────────────────────────────
MIN_CHARS_TISTORY = 2500
MIN_CHARS_BLOGGER = 2200

# ─── Claude API ───────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-opus-4-6"
CLAUDE_MAX_TOKENS = 16000

# ─── 출력 경로 ────────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
