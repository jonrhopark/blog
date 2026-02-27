"""
작성 이력 관리 모듈
- 작성 완료된 글을 history.json에 기록
- 새 주제 입력 시 유사 주제 검색 (중복 경고용)
"""
import json
from pathlib import Path
from difflib import SequenceMatcher

HISTORY_FILE = Path(__file__).parent.parent / "history.json"
SIMILARITY_THRESHOLD = 0.65  # 65% 이상 유사하면 중복 경고


def load_history() -> list:
    """작성 이력 전체 로드 (최신순)"""
    # history.json이 없으면 빈 파일 생성 후 빈 목록 반환
    if not HISTORY_FILE.exists():
        try:
            HISTORY_FILE.write_text("[]", encoding="utf-8")
        except Exception:
            pass
        return []
    try:
        raw = HISTORY_FILE.read_text(encoding="utf-8-sig")  # Windows BOM 대응
        raw = raw.strip()
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return sorted(data, key=lambda x: (x.get("date", ""), x.get("num", 0)), reverse=True)
    except Exception:
        return []


def add_history(num: int, topic: str, keyword: str,
                t_title: str, b_title: str, date_str: str):
    """이력 추가 (같은 num이면 덮어쓰기)"""
    try:
        entries = load_history()
        # 기존 동일 num 제거
        entries = [e for e in entries if e.get("num") != num]
        entries.append({
            "num": num,
            "topic": topic,
            "keyword": keyword or "",
            "t_title": t_title or topic,
            "b_title": b_title or topic,
            "date": date_str,
        })
        _save(entries)
    except Exception:
        pass  # 이력 저장 실패는 무시


def _save(entries: list):
    HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def find_similar(topic: str) -> list:
    """새 주제와 유사한 기존 이력 반환 (유사도 내림차순)"""
    history = load_history()
    results = []
    t = topic.strip().lower()
    t_words = set(t.split())

    for entry in history:
        old = entry.get("topic", "").strip().lower()
        old_words = set(old.split())

        # 문자열 전체 유사도
        ratio = SequenceMatcher(None, t, old).ratio()

        # 단어 겹침 비율
        if t_words and old_words:
            overlap = len(t_words & old_words) / max(len(t_words), len(old_words))
        else:
            overlap = 0.0

        score = max(ratio, overlap)
        if score >= SIMILARITY_THRESHOLD:
            results.append({**entry, "score": round(score * 100)})

    return sorted(results, key=lambda x: -x["score"])
