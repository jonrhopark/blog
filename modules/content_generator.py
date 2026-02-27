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


# 티스토리 본문에 자동 삽입되는 인라인 CSS
_INLINE_CSS = """<style>
/* 도입부 파란 박스 */
.intro-box{background:#eff6ff;border-left:5px solid #2563eb;border-radius:0 10px 10px 0;padding:18px 22px;margin:24px 0;color:#1e3a8a;line-height:1.8}
/* 팁/포인트 초록 박스 */
.tip-box{background:#f0fdf4;border-left:5px solid #16a34a;border-radius:0 10px 10px 0;padding:18px 22px;margin:24px 0;color:#14532d;line-height:1.8}
/* 주의사항 빨간 박스 */
.warn-box{background:#fff1f2;border-left:5px solid #dc2626;border-radius:0 10px 10px 0;padding:18px 22px;margin:24px 0;color:#7f1d1d;line-height:1.8}
/* 금액 강조 박스 */
.money-box{background:#fffbeb;border:2px solid #f59e0b;border-radius:10px;padding:18px 22px;margin:24px 0;text-align:center}
.money-amount{font-size:2em;font-weight:700;color:#b45309;display:block;margin:6px 0}
/* 체크리스트 박스 */
.check-box{background:#f0fdf4;border:2px solid #16a34a;border-radius:10px;padding:18px 22px;margin:24px 0}
.check-box ul{list-style:none;padding:0;margin:0}
.check-box li{padding:5px 0;font-size:15px;color:#166534;line-height:1.7}
/* 편집자 코멘트 박스 */
.editor-box{background:#f8fafc;border-left:4px solid #64748b;border-radius:0 8px 8px 0;padding:12px 18px;margin:16px 0;font-size:14px;color:#475569;font-style:italic;line-height:1.7}
/* 목차 박스 */
.toc-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px 24px;margin:24px 0}
.toc-box p{font-weight:700;color:#1e293b;margin:0 0 8px 0;font-size:15px}
.toc-box ol{margin:0;padding-left:20px}
.toc-box li{padding:3px 0;font-size:14px;color:#374151;line-height:1.7}
/* 핵심 답변 스니펫 박스 (검색 미리보기 타겟) */
.snippet-box{background:#f0f9ff;border:2px solid #0ea5e9;border-radius:10px;padding:16px 22px;margin:20px 0;font-size:16px;font-weight:500;color:#0c4a6e;line-height:1.8}
</style>"""


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


def _strip_preamble(html: str) -> str:
    """HTML 태그 시작 전에 붙은 영어 설명 텍스트 제거"""
    idx = html.find('<')
    if idx == -1:
        return html
    # 태그 시작 이전에 두 줄 이상 들어온 영어 설명도 제거
    before = html[:idx]
    if before.strip():
        # 앞에 붙은 텍스트가 있으면 제거
        return html[idx:]
    return html[idx:]


def _strip_english_opener(html: str) -> str:
    """앞쪽 <p> 태그가 영어 위주면 제거 (최대 3개 검사)"""
    for _ in range(3):
        m = re.search(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
        if not m:
            break
        content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if not content:
            break
        letters = [c for c in content if c.isalpha()]
        if not letters:
            break
        english_ratio = sum(1 for c in letters if ord(c) < 128) / len(letters)
        # 첫 글자가 영어이거나 영어 비율 30% 초과면 제거
        first_is_english = content and ord(content[0]) < 128 and content[0].isalpha()
        if english_ratio > 0.30 or first_is_english:
            html = html[:m.start()] + html[m.end():]
        else:
            break  # 한글 단락이 나오면 중단
    return html


def _strip_all_images(html: str) -> str:
    """블로거용: img 태그 전체 제거 (base64·일반 URL 모두)"""
    html = re.sub(r'<img\b[^>]*/?\s*>', '', html, flags=re.IGNORECASE)
    # 태그 밖에 노출된 data:image/... 텍스트도 제거
    html = re.sub(r'data:image/[^\s"\'<>]{10,}', '', html)
    return html


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
4. 제목 규칙 - 글 번호 {num}을 6으로 나눈 나머지({num % 6})에 따라 아래 패턴 사용:
   - 0: 수치형  → "[대상] 기준 [정책명] 2026 - 월 OOO원 바뀐다"
   - 1: 의문형  → "2026 [정책명], [대상]은 얼마 받나? 실수령액 계산"
   - 2: 행동형  → "[정책명] 2026 신청 전 확인할 OO가지 - [핵심 조건]"
   - 3: 비교형  → "[이전 금액] → [이후 금액], 2026 [정책명] 변경사항"
   - 4: 대상형  → "[연봉/나이/조건]별 [정책명] 2026 실수령액 비교"
   - 5: 긴급형  → "[마감/기간] [정책명] 2026 - [대상] 지금 안 하면 손해"
   ※ 제목 금지 표현: 완벽정리, 총정리, 알아보겠습니다, 살펴보겠습니다,
     모든것, A to Z, 꿀팁, 핵심정리, ~에 대해, 총 정리해드립니다
5. 내부 링크 3개 필수: 글 하단에 아래 형식으로 "함께 보면 좋은 글" 섹션 구성
   <div style="margin-top:60px;padding-top:30px;border-top:2px solid #e5e7eb">
     <p style="font-size:16px;color:#1f2937;font-weight:600;margin-bottom:15px">📌 함께 보면 좋은 글</p>
     <ul style="list-style:none;padding:0">
       <li style="margin-bottom:10px"><a href="{TISTORY_DOMAIN}/..." style="color:#3b82f6">• [키워드 포함 앵커텍스트]</a></li>
       <li style="margin-bottom:10px"><a href="{TISTORY_DOMAIN}/..." style="color:#3b82f6">• [키워드 포함 앵커텍스트]</a></li>
       <li style="margin-bottom:10px"><a href="{TISTORY_DOMAIN}/..." style="color:#3b82f6">• [키워드 포함 앵커텍스트]</a></li>
     </ul>
   </div>
6. 본문 이미지 3개 위치에 다음 태그를 반드시 이 형식 그대로 삽입:
   <img src="CONTENT_IMG_1" style="width:100%;max-width:800px;display:block;margin:20px auto;" alt="[A] vs [B] 비교 - [A특징], [B특징], [차이 수치]" />
   <img src="CONTENT_IMG_2" style="width:100%;max-width:800px;display:block;margin:20px auto;" alt="[주제] 세율/금액표 - [구간1] [비율], [구간2] [비율]" />
   <img src="CONTENT_IMG_3" style="width:100%;max-width:800px;display:block;margin:20px auto;" alt="[나이/상황] [주제] 사례 - [금액/조건] 시 [결과]" />
   ※ alt 텍스트는 실제 이미지 내용에 맞게 채워서 삽입
7. Q&A 섹션 2~3개 (핵심적인 것만 엄선)
8. 롱테일 키워드 공략 (구체적 금액/대상 포함)

[다른 AI 글과의 차별화 요소 - 반드시 포함]
A. 흔한 실수 섹션 (H2 1개):
   - 제목 패턴: "XX할 때 독자들이 가장 많이 하는 실수 3가지"
   - 다른 블로그가 언급하지 않는 비직관적 주의사항 위주
   - warn-box 활용
B. 체크리스트 박스 (check-box 클래스, 본문 마지막에 1개):
   - "지금 바로 확인할 3가지 체크리스트" 형식
   - 독자가 읽고 즉시 행동할 수 있는 구체적 항목
   - ul 내 li 앞에 ✅ 이모지 사용
C. 편집자 한줄 코멘트 (editor-box 클래스):
   - H2 섹션 3~4개마다 1회 삽입
   - 형식: <div class="editor-box">📌 편집자 코멘트: [한 줄 핵심 의견]</div>
   - 단순 정보 요약이 아닌 독자 관점의 짧은 견해

[SEO 검색 노출 규칙 - 필수]
1. 목차(TOC): H1 바로 아래 toc-box 클래스 div 삽입
   형식: <div class="toc-box"><p>📋 목차</p><ol><li>...</li></ol></div>
   H2 제목 전체를 번호 목록으로 나열 (링크 불필요)
2. 핵심 답변 스니펫: 목차 바로 아래 snippet-box 클래스 div 삽입
   형식: <div class="snippet-box">❓ [메인 키워드]란? → [한 문장 직접 답변 + 핵심 수치]</div>
   (검색결과 미리보기 노출 타겟)
3. 키워드 배치:
   - 첫 번째 <p> 태그 50자 이내에 메인 키워드 자연스럽게 포함
   - H2 제목 절반 이상에 메인 키워드 또는 LSI 키워드 포함
4. LSI 키워드 (연관 검색어) 5개 이상 본문에 자연스럽게 분산 배치
   예: "육아휴직급여" 글이면 → 통상임금, 출산휴가, 고용보험, 육아기근로시간단축, 배우자출산휴가
5. 내부 링크 앵커텍스트: "여기", "이 글", "클릭" 금지
   반드시 키워드 포함 앵커텍스트 사용
   예: <a href="...">2026 육아휴직 신청 방법</a>
6. 메타 description 형식: [핵심 수치] + [대상/조건] + [행동 유도], 120자 이내
   예: "2026 육아휴직급여 월 최대 250만원으로 인상. 통상임금 80% 계산법, 신청 기간, 서류까지 한 번에 확인하세요."

[CSS 클래스 - <style> 태그 없이 클래스명만 사용, CSS는 자동 삽입됨]
- toc-box: 목차 박스
- snippet-box: 핵심 답변 스니펫 박스 (하늘색 테두리)
- intro-box: 도입부 파란 박스
- tip-box: 팁/포인트 초록 박스
- warn-box: 주의사항 빨간 박스
- money-box + money-amount: 금액 강조 박스
- check-box: 체크리스트 초록 테두리 박스
- editor-box: 편집자 코멘트 회색 배경 박스
(주의: HTML에 <style> 블록을 직접 작성하지 마세요. 클래스명만 사용하세요.)

[Alt 태그 규칙]
이미지 Alt 태그는 40~80자로 구체적으로 작성 (숫자/키워드 포함)

[메타 태그]
- description: 120자 이내, [핵심 수치] + [대상] + [행동 유도] 구조
- keywords: 메인 키워드 1개 + LSI 키워드 5개 + 롱테일 키워드 4개 = 총 10개

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
    # HTML 앞 영어 설명 텍스트 제거 후 CSS 자동 삽입
    data["html"] = _INLINE_CSS + "\n" + _strip_preamble(data.get("html", ""))
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
4. 제목 규칙 - 글 번호 {num}을 5로 나눈 나머지({num % 5})에 따라 아래 패턴 사용:
   - 0: 결과형  → "[정책명] 2026 신청했더니 OOO원 나왔어요"
   - 1: 비교형  → "작년이랑 다르다는 [정책명]... OOO원 차이 직접 계산해봤어요"
   - 2: 실수형  → "[정책명] 2026 신청하다 [실수] - OOO원 날릴 뻔했어요"
   - 3: 의문형  → "[정책명] 2026 나도 받을 수 있을까? [조건] 직접 알아봤어요"
   - 4: 공감형  → "[직업/나이] [페르소나], [정책명] 2026 후기 - [솔직 결과]"
   ※ 제목 금지 표현: 완벽정리, 총정리, 완벽가이드, 꿀팁, 핵심만 쏙,
     알아보겠습니다, 살펴볼게요, ~에 대해, 해봤습니다 (단순 나열식)
5. 페르소나 필수: 구체적인 나이, 직업, 금액 설정
   예: "저는 36세 직장맘이에요. 자녀 2명, 연봉 5,200만원..."
6. 실수/고민/감정 표현 포함
7. 구체적 금액과 계산 포함
8. ⚠️ 절대 금지: <img> 태그 사용 금지. base64, data:image, src= 속성 일절 사용 불가. 이미지 없이 텍스트만으로 작성할 것.

[주제별 페르소나 예시 - 나이·직업·금액 모두 명시]
- 재테크/절세: 36세 직장맘(자녀2명, 연봉5200만원), 42세 배당투자자(배당5000만원), 29세 사회초년생(월급350만원)
- 투자: 35세 직장인(ISA 3년째, 수익률 8%), 40세 배당주투자자(KB금융 30%, KT 25%)
- 청년: 28세 직장인(청년미래적금 가입), 26세 취업준비생
- 육아: 34세 워킹맘(쌍둥이 3세), 38세 맞벌이(자녀3명, 월 보육비 120만원)
※ 페르소나 필수 요소: 나이 + 직업/상황 + 구체적 금액 + 고민/실수 + 감정 표현

[SEO 검색 노출 규칙 - 필수]
1. 첫 번째 <p> 태그 안에 메인 키워드를 페르소나 소개와 함께 자연스럽게 포함
   예: "저는 36세 직장맘인데요, 2026 육아휴직급여 인상 소식 듣고 바로 계산해봤어요."
2. H2 제목의 절반 이상에 메인 키워드 또는 연관어 포함
3. LSI 키워드 3개 이상 본문에 자연스럽게 배치
4. 티스토리 글 연결: 본문 중간에 자연스러운 내부 링크 1개 필수
   형식: <a href="{TISTORY_DOMAIN}/...">관련 정보 키워드</a> (앵커텍스트에 키워드 포함)
5. 메타 description: [페르소나 상황] + [결과/금액] + [공감 유도], 120자 이내
   예: "36세 직장맘이 2026 육아휴직급여 직접 계산해보니 월 210만원. 통상임금 계산 실수 없이 신청하는 법 공유해요."

[출력 형식] JSON으로만 응답:
{{
  "title": "경험담형 제목",
  "html": "블로그 본문 HTML (<h1>부터 마지막 태그까지, DOCTYPE/html/head/body 태그 제외)",
  "labels": ["블로그스팟레이블1", "레이블2", ...],
  "persona": "설정한 페르소나 (예: 36세 직장맘, 연봉 5200만원)",
  "description": "메타 설명 120자 이내 - [페르소나 상황]+[결과]+[공감 유도]"
}}
"""
    result = _call_claude(prompt, api_key)
    data = _extract_json(result)
    html = _strip_preamble(data.get("html", ""))
    html = _strip_english_opener(html)   # 첫 p가 영어면 제거
    html = _strip_all_images(html)   # img 태그 전체 제거 (블로거는 이미지 없음)
    data["html"] = html
    return data


def generate_meta_tags(tistory_tags: list, blogger_labels: list) -> str:
    """메타 태그 출력 문자열 생성"""
    t_tags = " ".join(f"#{tag.replace(' ', '')}" for tag in tistory_tags[:10])
    b_labels = ", ".join(blogger_labels[:10])
    return f"\n🔵 티스토리 Tags:\n{t_tags}\n\n🟣 블로그스팟 Labels:\n{b_labels}"
