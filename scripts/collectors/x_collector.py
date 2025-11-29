#!/usr/bin/env python3
"""
X (Twitter) Collector using Twikit
2025년 작동 확인된 라이브러리 사용
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent / '.env')

# twikit import
try:
    from twikit import Client
except ImportError:
    print("twikit이 설치되지 않았습니다. pip install twikit 실행하세요.")
    exit(1)


class XCollector:
    def __init__(self):
        self.client = Client('ko')  # 한국어 설정
        self.cookies_path = Path(__file__).parent.parent / 'cookies.json'

    async def login(self):
        """X 계정 로그인 (쿠키 재사용)"""

        # 기존 쿠키가 있으면 재사용
        if self.cookies_path.exists():
            print("기존 쿠키로 로그인 시도...")
            self.client.load_cookies(str(self.cookies_path))
            return True

        # 새로 로그인
        username = os.getenv('X_USERNAME')
        email = os.getenv('X_EMAIL')
        password = os.getenv('X_PASSWORD')

        if not all([username, email, password]):
            print("X 계정 정보가 .env에 설정되지 않았습니다.")
            print("필요한 환경변수: X_USERNAME, X_EMAIL, X_PASSWORD")
            return False

        print(f"@{username}으로 로그인 중...")

        try:
            await self.client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password
            )
            # 쿠키 저장 (다음 로그인에 재사용)
            self.client.save_cookies(str(self.cookies_path))
            print("로그인 성공! 쿠키 저장됨.")
            return True
        except Exception as e:
            print(f"로그인 실패: {e}")
            return False

    async def get_user_tweets(self, username: str, count: int = 10):
        """특정 유저의 최근 트윗 가져오기"""

        print(f"\n@{username}의 트윗 수집 중...")

        try:
            # 유저 정보 가져오기
            user = await self.client.get_user_by_screen_name(username)
            print(f"유저: {user.name} (@{user.screen_name})")
            print(f"팔로워: {user.followers_count:,}")

            # 트윗 가져오기
            tweets = await user.get_tweets('Tweets', count=count)

            results = []
            for tweet in tweets:
                results.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': str(tweet.created_at) if tweet.created_at else None,
                    'likes': tweet.favorite_count,
                    'retweets': tweet.retweet_count,
                    'url': f"https://x.com/{username}/status/{tweet.id}"
                })

            print(f"{len(results)}개 트윗 수집 완료!")
            return results

        except Exception as e:
            print(f"트윗 수집 실패: {e}")
            return []

    async def search_tweets(self, query: str, count: int = 20):
        """키워드로 트윗 검색"""

        print(f"\n'{query}' 검색 중...")

        try:
            tweets = await self.client.search_tweet(query, 'Latest', count=count)

            results = []
            for tweet in tweets:
                results.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author': tweet.user.screen_name if tweet.user else 'unknown',
                    'created_at': str(tweet.created_at) if tweet.created_at else None,
                    'likes': tweet.favorite_count,
                    'retweets': tweet.retweet_count,
                    'url': f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}" if tweet.user else None
                })

            print(f"{len(results)}개 트윗 검색 완료!")
            return results

        except Exception as e:
            print(f"검색 실패: {e}")
            return []

    def format_tweets_markdown(self, tweets: list, title: str = "수집된 트윗") -> str:
        """트윗을 마크다운 형식으로 변환"""

        output = f"# {title}\n\n"
        output += f"> 수집 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        output += "---\n\n"

        for i, tweet in enumerate(tweets, 1):
            output += f"## {i}. @{tweet.get('author', 'unknown')}\n\n"
            output += f"{tweet['text']}\n\n"
            output += f"- Likes: {tweet.get('likes', 0):,} | "
            output += f"RT: {tweet.get('retweets', 0):,}\n"
            output += f"- [원문 보기]({tweet.get('url', '#')})\n\n"
            output += "---\n\n"

        return output


async def main():
    """테스트 실행"""
    collector = XCollector()

    # 로그인
    if not await collector.login():
        print("로그인 실패. .env 파일을 확인하세요.")
        return

    # 테스트: elonmusk 트윗 가져오기
    tweets = await collector.get_user_tweets('elonmusk', count=5)

    if tweets:
        # 마크다운으로 출력
        md = collector.format_tweets_markdown(tweets, "@elonmusk 최근 트윗")
        print("\n" + "="*60)
        print(md)

        # 파일로 저장
        output_path = Path(__file__).parent.parent / 'output' / 'x_tweets.md'
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(md, encoding='utf-8')
        print(f"\n저장됨: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
