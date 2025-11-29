#!/usr/bin/env python3
"""
RSS Feed Collector
다양한 Tech 뉴스 소스에서 RSS 피드 수집
- fastfeedparser 사용 (feedparser보다 10배 빠름)
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# .env 로드
load_dotenv(Path(__file__).parent.parent / '.env')

try:
    import fastfeedparser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("⚠️ fastfeedparser 미설치: pip install fastfeedparser")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# 피드 소스 정의
RSS_FEEDS = {
    # 한국어 (우선)
    "GeekNews": {
        "url": "https://news.hada.io/rss",
        "lang": "ko",
        "category": "general"
    },

    # 영문 주요 뉴스
    "TechCrunch": {
        "url": "https://techcrunch.com/feed/",
        "lang": "en",
        "category": "general"
    },
    "The Verge": {
        "url": "https://www.theverge.com/rss/index.xml",
        "lang": "en",
        "category": "general"
    },
    "Ars Technica": {
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "lang": "en",
        "category": "general"
    },
    "Wired": {
        "url": "https://www.wired.com/feed/rss",
        "lang": "en",
        "category": "general"
    },

    # 개발자 특화
    "Hacker News": {
        "url": "https://hnrss.org/frontpage",  # 비공식 RSS
        "lang": "en",
        "category": "dev"
    },

    # 추가 소스
    "MIT Tech Review": {
        "url": "https://www.technologyreview.com/feed/",
        "lang": "en",
        "category": "research"
    },
    "CNET": {
        "url": "https://www.cnet.com/rss/news/",
        "lang": "en",
        "category": "general"
    },
    "Engadget": {
        "url": "https://www.engadget.com/rss.xml",
        "lang": "en",
        "category": "general"
    },
}


class RSSCollector:
    def __init__(self, use_ai_summary: bool = True, max_per_source: int = 5):
        """
        Args:
            use_ai_summary: Gemini로 한글 요약 생성
            max_per_source: 소스당 최대 기사 수
        """
        if not PARSER_AVAILABLE:
            raise ImportError("fastfeedparser가 필요합니다: pip install fastfeedparser")

        self.use_ai_summary = use_ai_summary
        self.max_per_source = max_per_source
        self.model = None

        # Gemini 설정
        if use_ai_summary and GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Gemini 요약 활성화")

    def summarize_korean(self, title: str, description: str = "") -> str:
        """Gemini로 한글 한줄 요약"""
        if not self.model:
            return ""

        try:
            text = f"{title}. {description[:300]}" if description else title
            prompt = f"""다음 뉴스 제목/내용을 한국어로 한 줄(25자 이내)로 요약해줘.
이모지 없이, 핵심만 간단히.

내용: {text}

한줄요약:"""

            response = self.model.generate_content(prompt)
            result = response.text.strip()
            return result.split('\n')[0]
        except Exception as e:
            print(f"  ⚠️ 요약 실패: {e}")
            return ""

    def fetch_feed(self, name: str, feed_info: dict) -> list:
        """단일 피드 수집"""
        url = feed_info["url"]
        print(f"  📡 {name} 수집 중...")

        try:
            feed = fastfeedparser.parse(url)

            if not feed or not feed.get('entries'):
                print(f"  ⚠️ {name}: 항목 없음")
                return []

            articles = []
            entries = feed['entries'][:self.max_per_source]

            for entry in entries:
                # 기본 정보 추출
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')

                # 설명 (HTML 태그 제거는 선택)
                description = entry.get('summary', entry.get('description', ''))
                if description:
                    # 간단한 HTML 태그 제거
                    import re
                    description = re.sub(r'<[^>]+>', '', description)[:500]

                # 발행일
                published = entry.get('published', entry.get('updated', ''))

                articles.append({
                    'source': name,
                    'lang': feed_info['lang'],
                    'category': feed_info['category'],
                    'title': title,
                    'link': link,
                    'description': description,
                    'published': published,
                })

            print(f"  ✅ {name}: {len(articles)}개 수집")
            return articles

        except Exception as e:
            print(f"  ❌ {name} 오류: {e}")
            return []

    def collect_all(self, sources: list = None, categories: list = None) -> dict:
        """
        모든 RSS 피드 수집

        Args:
            sources: 특정 소스만 수집 (예: ["GeekNews", "TechCrunch"])
            categories: 특정 카테고리만 (예: ["dev", "general"])

        Returns:
            dict: {source_name: [articles]}
        """
        print(f"🚀 RSS 피드 수집 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        results = {}
        total_count = 0

        for name, feed_info in RSS_FEEDS.items():
            # 필터링
            if sources and name not in sources:
                continue
            if categories and feed_info['category'] not in categories:
                continue

            articles = self.fetch_feed(name, feed_info)
            if articles:
                results[name] = articles
                total_count += len(articles)

        print(f"\n📊 총 {len(results)}개 소스에서 {total_count}개 기사 수집")

        # 한글 요약 추가 (영문 기사만)
        if self.use_ai_summary and self.model:
            print("\n🤖 영문 기사 한글 요약 생성 중...")
            summary_count = 0

            for source, articles in results.items():
                for article in articles:
                    # 영문만 요약 (한글은 이미 읽기 쉬움)
                    if article['lang'] == 'en' and summary_count < 20:  # API 절약
                        summary = self.summarize_korean(article['title'], article['description'])
                        article['summary_kr'] = summary
                        if summary:
                            summary_count += 1
                            print(f"  ✓ {article['title'][:30]}... → {summary}")

        return results

    def format_markdown(self, results: dict, title: str = "Tech News Digest") -> str:
        """마크다운 형식으로 변환"""

        output = f"# {title}\n\n"
        output += f"> 수집 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        output += "---\n\n"

        for source, articles in results.items():
            output += f"## 📰 {source}\n\n"

            for i, article in enumerate(articles, 1):
                output += f"### {i}. [{article['title']}]({article['link']})\n\n"

                # 한글 요약 먼저
                if article.get('summary_kr'):
                    output += f"> 📌 **{article['summary_kr']}**\n\n"

                if article['description']:
                    output += f"{article['description'][:200]}...\n\n"

                if article['published']:
                    output += f"🕐 {article['published']}\n\n"

            output += "---\n\n"

        return output

    def format_telegram(self, results: dict, max_items: int = 10) -> str:
        """텔레그램용 포맷 (간결하게)"""

        message = "📰 *Tech News Digest*\n\n"
        count = 0

        # 한국어 소스 먼저
        for source in ["GeekNews"]:
            if source in results:
                message += f"*🇰🇷 {source}*\n"
                for article in results[source][:3]:
                    message += f"• [{article['title'][:40]}...]({article['link']})\n"
                    count += 1
                message += "\n"

        # 영문 소스
        for source, articles in results.items():
            if source == "GeekNews" or count >= max_items:
                continue

            message += f"*🌐 {source}*\n"
            for article in articles[:2]:
                title = article['title'][:35]
                if article.get('summary_kr'):
                    message += f"• [{title}...]({article['link']})\n"
                    message += f"  └ {article['summary_kr']}\n"
                else:
                    message += f"• [{title}...]({article['link']})\n"
                count += 1
                if count >= max_items:
                    break
            message += "\n"

        return message


def main():
    """테스트 실행"""
    collector = RSSCollector(use_ai_summary=True, max_per_source=3)

    # 모든 피드 수집
    results = collector.collect_all()

    if results:
        # 마크다운 출력
        md = collector.format_markdown(results)
        print("\n" + "=" * 60)
        print(md[:3000])

        # 파일 저장
        output_path = Path(__file__).parent.parent / 'output' / 'rss_news.md'
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(md, encoding='utf-8')
        print(f"\n✅ 저장됨: {output_path}")

        # 텔레그램 포맷 미리보기
        print("\n📱 텔레그램 미리보기:")
        print(collector.format_telegram(results))


if __name__ == "__main__":
    main()
