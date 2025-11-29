# News Aggregator Skill

X(Twitter), Threads, RSS 등 다양한 소스에서 콘텐츠를 수집하고 텔레그램/이메일로 발송하는 스킬

## 트리거 키워드

- "트윗 가져와", "X 수집", "트위터 크롤링"
- "@유저명 트윗", "엘론머스크 트윗"
- "뉴스 수집", "피드 가져와"

## 사용 가능한 기능

### 1. X (Twitter) 수집

특정 유저의 트윗 또는 키워드 검색 결과 수집

```bash
cd .claude/skills/news-aggregator/scripts
source venv/bin/activate
python -m collectors.x_collector
```

### 2. 지원 예정
- Threads 수집
- RSS 피드 수집
- 텔레그램 발송
- 이메일 발송

## 설정

### 필수: X 계정 정보

`.claude/skills/news-aggregator/scripts/.env` 파일 생성:

```
X_USERNAME=your_username
X_EMAIL=your_email@example.com
X_PASSWORD=your_password
```

**주의:** 메인 계정 대신 버너 계정 사용 권장

### 선택: 텔레그램/이메일

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
RESEND_API_KEY=your_resend_key
```

## 실행 예시

```python
from collectors.x_collector import XCollector
import asyncio

async def main():
    collector = XCollector()
    await collector.login()

    # 특정 유저 트윗
    tweets = await collector.get_user_tweets('elonmusk', count=10)

    # 키워드 검색
    tweets = await collector.search_tweets('Claude AI', count=20)

asyncio.run(main())
```

## 출력

- 마크다운 형식으로 변환
- `output/` 폴더에 저장
- Obsidian에서 바로 확인 가능
