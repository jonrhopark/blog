#!/usr/bin/env python3
"""
블로그 자동화 - 반자동 실행 스크립트
사용법:
  python run.py                          # topics.json 다음 주제 처리
  python run.py "ISA 계좌 2026"          # 주제 직접 지정
  python run.py "ISA 계좌 2026" "키워드"  # 주제 + 키워드 지정
  python run.py --output C:/내폴더       # 저장 경로 지정
"""
import os
import sys
import json
import shutil
import argparse
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 경로 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from config import DEFAULT_OUTPUT_DIR
from modules.content_generator import generate_tistory, generate_blogger, generate_meta_tags
from modules.image_generator import (
    make_content_img1, make_content_img2, make_content_img3,
    make_thumb_tistory, make_thumb_blogger
)
from modules.utils import count_korean, embed_image_base64, make_filename
from modules.history import add_history


def load_next_topic(topics_file: Path) -> tuple:
    """topics.json에서 다음 주제 로드"""
    if not topics_file.exists():
        return None, None, None
    with open(topics_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    topics = data.get("topics", [])
    for item in topics:
        if not item.get("done", False):
            return item["num"], item["topic"], item.get("keyword", "")
    return None, None, None


def mark_done(topics_file: Path, num: int):
    """topics.json에서 해당 번호 done 처리"""
    if not topics_file.exists():
        return
    with open(topics_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data.get("topics", []):
        if item["num"] == num:
            item["done"] = True
    with open(topics_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def progress(msg: str):
    print(f"  ⏳ {msg}")


def run(topic: str = None, keyword: str = None, output_dir: str = None):
    # API 키 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(".env 파일에 ANTHROPIC_API_KEY가 없습니다. API 키를 입력해주세요.")

    # 출력 디렉토리 (오늘 날짜 하위 폴더 자동 생성)
    out_dir = Path(output_dir) if output_dir else Path(DEFAULT_OUTPUT_DIR)
    out_dir = out_dir / date.today().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 글 번호 / 주제 결정
    topics_file = BASE_DIR / "topics.json"
    auto_mode = (topic is None)  # auto_mode: topics.json에서 자동 처리

    if not auto_mode:
        # 수동 모드: 주제 직접 지정
        num = None
        if topics_file.exists():
            with open(topics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nums = [t["num"] for t in data.get("topics", [])]
            done = [t["num"] for t in data.get("topics", []) if t.get("done")]
            remaining = [n for n in nums if n not in done]
            num = remaining[0] if remaining else (max(nums) + 1 if nums else 32)
        else:
            num = 32
        kw = keyword or topic
    else:
        # 자동 모드: topics.json에서 로드
        num, topic, kw = load_next_topic(topics_file)
        if not topic:
            print("✅ topics.json의 모든 주제가 완료됐습니다!")
            print("   topics.json에 새 주제를 추가하거나, 직접 주제를 입력하세요.")
            return  # GUI에서 호출 시 sys.exit 대신 return

    print(f"\n{'='*55}")
    print(f"  {num}번 글 생성 시작: {topic}")
    print(f"{'='*55}")

    # 작업 디렉토리
    work_dir = BASE_DIR / f"post_{num}"
    work_dir.mkdir(exist_ok=True)

    try:
        # ── STEP 1: 티스토리 HTML 생성 ─────────────────────────────
        print("\n[1/5] 티스토리 글 생성...")
        t_data = generate_tistory(num, topic, kw, api_key, progress_cb=progress)
        t_html = t_data.get("html", "")
        t_title = t_data.get("title", topic)
        t_tags = t_data.get("tags", [])

        t_chars = count_korean(t_html)
        print(f"  ✅ 티스토리 완성: {t_chars:,}자", "✓" if t_chars >= 2500 else "⚠️ 부족")

        # ── STEP 2: 콘텐츠 이미지 3개 생성 ─────────────────────────
        print("\n[2/5] 콘텐츠 이미지 생성...")
        img1_path = work_dir / "img1_concept.png"
        img2_path = work_dir / "img2_table.png"
        img3_path = work_dir / "img3_steps.png"

        make_content_img1(
            topic=topic[:20],
            subtitle=f"{topic} 핵심 포인트",
            points=[f"2026년 주요 변경사항", f"대상 조건", f"신청 방법", f"주의사항"],
            save_path=str(img1_path)
        )
        make_content_img2(
            topic=topic[:20],
            table_data=[
                ["구분", "기존", "2026년"],
                ["한도", "-", "변경"],
                ["세율", "-", "변경"],
                ["대상", "-", "확대"],
            ],
            save_path=str(img2_path)
        )
        make_content_img3(
            topic=topic[:20],
            steps=["자격 조건 확인", "필요 서류 준비", "홈택스/신청", "환급 수령"],
            result=f"{topic} 적용 시 절세 효과",
            save_path=str(img3_path)
        )
        print("  ✅ 이미지 3개 생성 완료 (800×450px)")

        # ── STEP 3: 이미지 HTML에 삽입 ──────────────────────────────
        t_html = embed_image_base64(t_html, "CONTENT_IMG_1", str(img1_path))
        t_html = embed_image_base64(t_html, "CONTENT_IMG_2", str(img2_path))
        t_html = embed_image_base64(t_html, "CONTENT_IMG_3", str(img3_path))

        # ── STEP 4: 블로그스팟 HTML 생성 ────────────────────────────
        print("\n[3/5] 블로그스팟 글 생성...")
        b_data = generate_blogger(num, topic, kw, t_title, api_key, progress_cb=progress)
        b_html = b_data.get("html", "")
        b_title = b_data.get("title", topic)
        b_labels = b_data.get("labels", [])
        b_persona = b_data.get("persona", "")

        b_chars = count_korean(b_html)
        print(f"  ✅ 블로그스팟 완성: {b_chars:,}자", "✓" if b_chars >= 2200 else "⚠️ 부족")

        # ── STEP 5: 썸네일 생성 ─────────────────────────────────────
        print("\n[4/5] 썸네일 생성...")
        thumb_t_path = work_dir / "thumbnail_tistory.png"
        thumb_b_path = work_dir / "thumbnail_blogger.png"

        make_thumb_tistory(
            num=num,
            title=t_title[:25],
            subtitle=f"2026 완벽 가이드",
            amount="절세",
            save_path=str(thumb_t_path)
        )
        make_thumb_blogger(
            num=num,
            persona=b_persona[:30] if b_persona else "실제 경험",
            title=b_title[:25],
            amount="절세 성공!",
            emoji="💰",
            save_path=str(thumb_b_path)
        )

        # 블로그스팟 썸네일: 블로거는 base64 data URI를 필터링하므로 HTML에 삽입하지 않음
        # → 썸네일 PNG 파일을 별도 저장 후 블로거 "게시물 설정 > 검색 설명/이미지"에서 직접 업로드
        print("  ✅ 썸네일 2개 생성 완료")

        # ── STEP 6: 파일 저장 ────────────────────────────────────────
        print("\n[5/5] 파일 저장...")
        safe_topic = topic.replace(' ', '_').replace('/', '_')[:25]

        t_filename = f"tistory_{num}_{safe_topic}.html"
        b_filename = f"blogger_{num}_{safe_topic}.html"
        thumb_t_filename = f"thumbnail_{num}_tistory.png"
        thumb_b_filename = f"thumbnail_{num}_blogger.png"

        t_out = out_dir / t_filename
        b_out = out_dir / b_filename
        thumb_t_out = out_dir / thumb_t_filename
        thumb_b_out = out_dir / thumb_b_filename

        with open(t_out, 'w', encoding='utf-8') as f:
            f.write(t_html)
        with open(b_out, 'w', encoding='utf-8') as f:
            f.write(b_html)
        shutil.copy(thumb_t_path, thumb_t_out)
        shutil.copy(thumb_b_path, thumb_b_out)

        # 작성 이력 기록
        add_history(
            num=num,
            topic=topic,
            keyword=kw or "",
            t_title=t_title,
            b_title=b_title,
            date_str=date.today().isoformat(),
        )

        # topics.json done 처리 (auto mode만)
        if auto_mode:
            mark_done(topics_file, num)

        # ── 최종 결과 출력 ────────────────────────────────────────────
        print(f"\n{'='*55}")
        print(f"✅ {num}번 글 완성!")
        print(f"{'='*55}")
        print(f"\n📂 저장 위치: {out_dir}")
        print(f"  ① {t_filename}")
        print(f"     → 티스토리 HTML 에디터에 붙여넣기")
        print(f"  ② {thumb_t_filename}")
        print(f"     → 티스토리 썸네일 업로드")
        print(f"  ③ {b_filename}")
        print(f"     → 블로그스팟 HTML 에디터에 붙여넣기")
        print(f"  ④ {thumb_b_filename}")
        print(f"     → 블로그스팟: 게시물 작성 > 우측 '게시물 설정' > '검색 설명' 아래 이미지 업로드")

        meta = generate_meta_tags(t_tags, b_labels)
        print(meta)
        print()

        # 글자수 경고
        if t_chars < 2500:
            print(f"⚠️  티스토리 글자수 부족: {t_chars}자 (최소 2,500자)")
        if b_chars < 2200:
            print(f"⚠️  블로그스팟 글자수 부족: {b_chars}자 (최소 2,200자)")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise  # GUI worker가 잡아서 로그에 표시
    finally:
        # 작업 폴더 정리
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description='블로그 자동화 실행')
    parser.add_argument('topic', nargs='?', help='글 주제 (없으면 topics.json 자동 처리)')
    parser.add_argument('keyword', nargs='?', help='메인 키워드 (선택)')
    parser.add_argument('--output', '-o', help='저장 경로 (기본: ./outputs)')
    args = parser.parse_args()

    run(
        topic=args.topic,
        keyword=args.keyword,
        output_dir=args.output
    )


if __name__ == '__main__':
    main()
