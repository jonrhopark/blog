"""
Claude API를 사용해 티스토리/블로그스팟 HTML 생성
"""
import anthropic
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    TISTORY_DOMAIN, BLOGGER_DOMAIN, BLOG_NAME, BLOG_META,
    MIN_CHARS_TISTORY, MIN_CHARS_BLOGGER, CLAUDE_MODEL, CLAUDE_MAX_TOKENS
)


def _call_claude(prompt: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def _extract_json(text: str) -> dict:
    """응답에서 JSON 추출"""
    # 코드블록 제거
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    # JSON 찾기
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group())
    raise ValueError("JSON을 찾을 수 없습니다.")


def generate_tistory(num: int, topic: str, keyword: str, api_key: str,
                     progress_cb=None) -> dict:
    """티스토리 HTML 생성"""
    if progress_cb:
        progress_cb("티스토리 글 생성 중 (Claude API)...")

    prompt = f"""
당신은 SEO 최적화 블로그 전문가입니다.
아래 주제로 티스토리 블로그 글을 HTML로 작성해주세요.

[기본 정보]
- 글 번호: {num}번
- 주제: {topic}
- 메인 키워드: {keyword if keyword else topic}
- 블로그명: {BLOG_NAME}
- 도메인: {TISTORY_DOMAIN}

[티스토리 글 규칙]
1. 톤: 전문가 분석형, ~입니다/~됩니다 어조
2. 한글 글자수: 최소 2,500자 이상 (HTML 태그 제외)
3. H1 정확히 1개, H2 5~10개, H3 적절히, H4 이하 사용 금지
4. 제목 패턴: [정책명] 2026 [변경사항] - [구체적 수치/결과]
5. 내부 링크 3개 필수 (도메인: {TISTORY_DOMAIN})
6. 본문 이미지 3개 위치에 다음 placeholder 삽입:
   - CONTENT_IMG_1
   - CONTENT_IMG_2
   - CONTENT_IMG_3
7. Q&A 섹션 10~15개 포함
8. 롱테일 키워드 공략 (구체적 금액/대상 포함)

[CSS 박스 스타일 - 반드시 사용]
- intro-box: 도입부 파란 박스
- tip-box: 팁/포인트 초록 박스
- warn-box: 주의사항 빨간 박스
- money-box + money-amount: 금액 강조 박스

[Alt 태그 규칙]
이미지 Alt 태그는 40~80자로 구체적으로 작성 (숫자/키워드 포함)

[메타 태그]
- description: 150자 이내 요약
- keywords: 10개

[출력 형식] JSON으로만 응답:
{{
  "title": "글 제목 (SEO 최적화)",
  "html": "블로그 본문 HTML (<h1>부터 마지막 태그까지, DOCTYPE/html/head/body 태그 제외)",
  "tags": ["티스토리태그1", "태그2", ...],
  "description": "메타 설명 150자"
}}
"""
    result = _call_claude(prompt, api_key)
    data = _extract_json(result)
    return data


def generate_blogger(num: int, topic: str, keyword: str, tistory_title: str,
                     api_key: str, progress_cb=None) -> dict:
    """블로그스팟 HTML 생성"""
    if progress_cb:
        progress_cb("블로그스팟 글 생성 중 (Claude API)...")

    prompt = f"""
당신은 개인 블로그 경험담 전문 작가입니다.
아래 주제로 블로그스팟 경험담 글을 HTML로 작성해주세요.

[기본 정보]
- 글 번호: {num}번
- 주제: {topic}
- 메인 키워드: {keyword if keyword else topic}
- 블로그명: {BLOG_NAME}
- 도메인: {BLOGGER_DOMAIN}
- 관련 티스토리 글: {tistory_title}

[블로그스팟 글 규칙]
1. 톤: 개인 경험담, ~해요/~했어요 어조
2. 한글 글자수: 최소 2,200자 이상 (HTML 태그 제외)
3. H1 정확히 1개, H2 5~10개, H3 적절히, H4 이하 사용 금지
4. 제목 패턴: [정책명] 2026 - [구체적 금액/결과] [감정/후기]
5. 페르소나 필수: 구체적인 나이, 직업, 금액 설정
   예: "저는 36세 직장맘이에요. 자녀 2명, 연봉 5,200만원..."
6. 블로그스팟 썸네일 위치에 다음 placeholder 삽입 (body 첫 줄):
   BLOGGER_THUMBNAIL
7. 실수/고민/감정 표현 포함
8. 구체적 금액과 계산 포함

[주제별 페르소나 예시]
- 재테크: 36세 직장맘, 42세 배당투자자, 29세 사회초년생
- 청년: 28세 직장인, 26세 취업준비생
- 육아: 34세 워킹맘, 38세 맞벌이

[출력 형식] JSON으로만 응답:
{{
  "title": "경험담형 제목",
  "html": "블로그 본문 HTML (<h1>부터 마지막 태그까지, DOCTYPE/html/head/body 태그 제외)",
  "labels": ["블로그스팟레이블1", "레이블2", ...],
  "persona": "설정한 페르소나 (예: 36세 직장맘, 연봉 5200만원)"
}}
"""
    result = _call_claude(prompt, api_key)
    data = _extract_json(result)
    return data


def generate_meta_tags(tistory_tags: list, blogger_labels: list) -> str:
    """메타 태그 출력 문자열 생성"""
    t_tags = " ".join(f"#{tag.replace(' ', '')}" for tag in tistory_tags[:10])
    b_labels = ", ".join(blogger_labels[:10])
    return f"\n🔵 티스토리 Tags:\n{t_tags}\n\n🟣 블로그스팟 Labels:\n{b_labels}"
