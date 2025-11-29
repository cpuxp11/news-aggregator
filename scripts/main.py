#!/usr/bin/env python3
"""
News Aggregator - Main Entry Point
GitHub Actions에서 실행되는 메인 스크립트
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from collectors.github_trending import GitHubTrendingCollector
from senders.telegram_sender import TelegramSender


def main():
    print(f"🚀 News Aggregator 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    # 1. GitHub Trending 수집
    print("\n📊 GitHub Trending 수집 중...")
    try:
        github_collector = GitHubTrendingCollector(use_ai_summary=True)
        repos = github_collector.get_trending(since="daily")

        if repos:
            # 마크다운 생성
            md = github_collector.format_markdown(repos, "GitHub Trending")

            # 텔레그램용 요약 (상위 5개만)
            summary = "🔥 *오늘의 GitHub Trending*\n\n"
            for repo in repos[:5]:
                summary += f"• [{repo['full_name']}]({repo['url']})\n"
                if repo.get('summary_kr'):
                    summary += f"  └ {repo['summary_kr']}\n"
                summary += f"  ⭐ {repo['stars']:,} | {repo['today_stars']}\n\n"

            results['github'] = summary
            print(f"✅ {len(repos)}개 레포 수집 완료")
        else:
            print("⚠️ GitHub Trending 수집 실패")
    except Exception as e:
        print(f"❌ GitHub 수집 오류: {e}")

    # 2. 텔레그램 발송
    print("\n📤 텔레그램 발송 중...")
    sender = TelegramSender()

    if sender.enabled and results.get('github'):
        message = f"🌅 *Daily Tech Digest*\n"
        message += f"📅 {datetime.now().strftime('%Y년 %m월 %d일')}\n\n"
        message += results['github']
        message += "\n---\n"
        message += "_🤖 Powered by News Aggregator_"

        sender.send_message(message)
    else:
        print("⚠️ 텔레그램 미설정 또는 수집 결과 없음")

    print("\n" + "=" * 60)
    print("✅ 완료!")


if __name__ == "__main__":
    main()
