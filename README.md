# 블로그 자동화 시스템
**돈·건강·AI 이야기** - 티스토리 + 블로그스팟 반자동 글 생성

## 사용법

### Windows
1. `시작.bat` 더블클릭
2. 주제 입력 → 글 생성 시작
3. 저장 폴더에서 파일 4개 확인
4. 각 블로그에 붙여넣기

### 커맨드라인
```bash
# 패키지 설치
pip install -r requirements.txt

# .env 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 실행
python run.py                        # topics.json 자동 처리
python run.py "ISA 계좌 2026"        # 주제 직접 지정
python run.py "ISA" "키워드" -o D:\  # 저장 경로 지정
python gui.py                        # GUI 실행
```

## 출력 파일 (4개)
| 파일 | 용도 |
|------|------|
| `tistory_32_주제.html` | 티스토리 HTML 에디터 붙여넣기 |
| `thumbnail_32_tistory.png` | 티스토리 썸네일 업로드 |
| `blogger_32_주제.html` | 블로그스팟 HTML 에디터 붙여넣기 |
| `thumbnail_32_blogger.png` | 블로그스팟 썸네일 업로드 |

## 구조
```
blog/
├── run.py           ← 메인 실행
├── gui.py           ← GUI
├── config.py        ← 설정
├── topics.json      ← 주제 큐 (32~45번)
├── requirements.txt
├── .env             ← API 키 (gitignore)
├── 시작.bat          ← Windows 실행
└── modules/
    ├── content_generator.py  ← Claude API 글 생성
    ├── image_generator.py    ← 이미지 생성
    └── utils.py
```
