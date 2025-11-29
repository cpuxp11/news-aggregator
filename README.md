# News Aggregator

매일 아침 GitHub Trending, X(Twitter) 등의 정보를 자동 수집하여 텔레그램으로 발송하는 도구

## Features

- **GitHub Trending**: 오늘의 인기 레포 + AI 한글 요약
- **X (Twitter)**: 특정 유저/키워드 트윗 수집 (예정)
- **Telegram 발송**: 매일 아침 자동 알림
- **무료**: Gemini 무료 티어 + GitHub Actions

## Quick Start

```bash
# 1. 설치
cd scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 입력

# 3. 실행
python -m collectors.github_trending
```

## 환경변수

```env
# Gemini (한글 요약용) - 무료
GEMINI_API_KEY=your_gemini_api_key

# Telegram 발송 (선택)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# X 수집 (선택)
X_USERNAME=your_username
X_EMAIL=your_email
X_PASSWORD=your_password
```

## 폴더 구조

```
scripts/
├── collectors/
│   ├── github_trending.py  # GitHub Trending 수집
│   └── x_collector.py      # X(Twitter) 수집
├── senders/
│   └── telegram_sender.py  # 텔레그램 발송
├── output/                 # 수집 결과 저장
└── requirements.txt
```

## GitHub Actions (자동 실행)

매일 아침 8시에 자동으로 수집 후 텔레그램 발송:

```yaml
# .github/workflows/daily-digest.yml
name: Daily Digest
on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = KST 08:00
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/main.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## License

MIT
