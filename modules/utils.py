"""
유틸리티 함수
"""
import re
import base64


def count_korean(text: str) -> int:
    """HTML에서 한글만 추출하여 글자수 반환"""
    # HTML 태그 제거
    plain = re.sub(r'<[^>]+>', '', text)
    # 한글만 카운트
    korean = re.findall(r'[가-힣]', plain)
    return len(korean)


def img_to_base64(img_path: str) -> str:
    """이미지 파일을 base64 문자열로 변환"""
    with open(img_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode('utf-8')


def embed_image_base64(html: str, placeholder: str, img_path: str) -> str:
    """HTML의 placeholder를 base64 이미지로 교체"""
    b64 = img_to_base64(img_path)
    data_uri = f"data:image/png;base64,{b64}"
    return html.replace(placeholder, data_uri)


def make_filename(num: int, topic: str, platform: str, ext: str) -> str:
    """파일명 생성: tistory_32_ISA_계좌.html"""
    # 파일명에 쓸 수 없는 문자 제거
    safe_topic = re.sub(r'[\\/:*?"<>|]', '', topic)
    safe_topic = safe_topic.replace(' ', '_')[:30]
    if platform == "thumb_tistory":
        return f"thumbnail_{num}_tistory.{ext}"
    elif platform == "thumb_blogger":
        return f"thumbnail_{num}_blogger.{ext}"
    else:
        return f"{platform}_{num}_{safe_topic}.{ext}"
