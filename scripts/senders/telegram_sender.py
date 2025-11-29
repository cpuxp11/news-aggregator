#!/usr/bin/env python3
"""
Telegram Sender
수집된 정보를 텔레그램으로 발송
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
load_dotenv(Path(__file__).parent.parent / '.env')


class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            print("⚠️ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Telegram 발송 준비 완료")

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """텔레그램 메시지 발송"""
        if not self.enabled:
            print("❌ Telegram이 설정되지 않았습니다.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        # 메시지 길이 제한 (4096자)
        if len(text) > 4096:
            text = text[:4000] + "\n\n... (더보기: 전체 내용은 GitHub에서 확인)"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ 텔레그램 발송 성공!")
                return True
            else:
                print(f"❌ 발송 실패: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 발송 오류: {e}")
            return False

    def send_daily_digest(self, github_trending: str = None, x_digest: str = None) -> bool:
        """일일 다이제스트 발송"""
        from datetime import datetime

        message = f"🌅 *Daily Digest* - {datetime.now().strftime('%Y-%m-%d')}\n\n"

        if github_trending:
            message += "📊 *GitHub Trending*\n"
            message += github_trending[:2000]  # 길이 제한
            message += "\n\n"

        if x_digest:
            message += "🐦 *X Highlights*\n"
            message += x_digest[:1500]

        return self.send_message(message)


def main():
    """테스트 실행"""
    sender = TelegramSender()

    if sender.enabled:
        # 테스트 메시지
        sender.send_message("🔔 News Aggregator 테스트 메시지입니다!")
    else:
        print("\n📝 텔레그램 설정 방법:")
        print("1. @BotFather에서 봇 생성 → 토큰 받기")
        print("2. @userinfobot에서 chat_id 확인")
        print("3. .env 파일에 추가:")
        print("   TELEGRAM_BOT_TOKEN=your_token")
        print("   TELEGRAM_CHAT_ID=your_chat_id")


if __name__ == "__main__":
    main()
