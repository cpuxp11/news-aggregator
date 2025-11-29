#!/usr/bin/env python3
"""
GitHub Trending Collector
무료! API 키 필요 없음!
+ Gemini로 한글 요약 (무료)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# .env 로드 (Gemini API 키)
env_path = Path(__file__).parent.parent.parent.parent / 'web-crawler-ocr' / 'scripts' / '.env'
load_dotenv(env_path)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GitHubTrendingCollector:
    BASE_URL = "https://github.com/trending"

    def __init__(self, use_ai_summary: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.use_ai_summary = use_ai_summary
        self.model = None

        # Gemini 설정
        if use_ai_summary and GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Gemini 요약 활성화")
            else:
                print("⚠️ GEMINI_API_KEY 없음, 요약 비활성화")

    def summarize_korean(self, name: str, description: str) -> str:
        """Gemini로 한글 한줄 요약"""
        if not self.model or not description:
            return ""

        try:
            prompt = f"""다음 GitHub 프로젝트를 한국어로 한 줄(20자 이내)로 요약해줘.
이모지 없이, 핵심 기능만 간단히.

프로젝트명: {name}
설명: {description[:200]}

한줄요약:"""

            response = self.model.generate_content(prompt)
            result = response.text.strip()
            # 줄바꿈 제거
            return result.split('\n')[0]
        except Exception as e:
            print(f"  ⚠️ 요약 실패 ({name}): {e}")
            return ""

    def get_trending(self, language: str = None, since: str = "daily") -> list:
        """
        GitHub Trending 레포 가져오기

        Args:
            language: 프로그래밍 언어 (예: "python", "javascript", None=전체)
            since: "daily", "weekly", "monthly"

        Returns:
            list of trending repos
        """
        # URL 구성
        url = self.BASE_URL
        if language:
            url += f"/{language}"
        url += f"?since={since}"

        print(f"🔍 GitHub Trending 수집 중: {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        repos = []

        # 트렌딩 레포 파싱
        articles = soup.select('article.Box-row')

        for article in articles:
            try:
                # 레포 이름
                h2 = article.select_one('h2 a')
                if not h2:
                    continue

                full_name = h2.get('href', '').strip('/')
                owner, name = full_name.split('/') if '/' in full_name else ('', full_name)

                # 설명
                desc_elem = article.select_one('p')
                description = desc_elem.text.strip() if desc_elem else ''

                # 언어
                lang_elem = article.select_one('[itemprop="programmingLanguage"]')
                lang = lang_elem.text.strip() if lang_elem else 'Unknown'

                # 스타 수
                star_elem = article.select_one('a[href$="/stargazers"]')
                stars = star_elem.text.strip().replace(',', '') if star_elem else '0'

                # 오늘의 스타
                today_stars_elem = article.select_one('span.d-inline-block.float-sm-right')
                today_stars = today_stars_elem.text.strip() if today_stars_elem else ''

                # 포크 수
                fork_elem = article.select_one('a[href$="/forks"]')
                forks = fork_elem.text.strip().replace(',', '') if fork_elem else '0'

                repos.append({
                    'rank': len(repos) + 1,
                    'owner': owner,
                    'name': name,
                    'full_name': full_name,
                    'url': f"https://github.com/{full_name}",
                    'description': description,
                    'language': lang,
                    'stars': int(stars) if stars.isdigit() else 0,
                    'forks': int(forks) if forks.isdigit() else 0,
                    'today_stars': today_stars,
                })

            except Exception as e:
                print(f"⚠️ 파싱 오류: {e}")
                continue

        print(f"✅ {len(repos)}개 레포 수집 완료!")

        # 한글 요약 추가 (수집 후 일괄 처리)
        if self.use_ai_summary and self.model:
            print(f"🤖 한글 요약 생성 중...")
            for repo in repos[:10]:  # 상위 10개만 요약 (API 절약)
                summary = self.summarize_korean(repo['name'], repo['description'])
                repo['summary_kr'] = summary
                if summary:
                    print(f"  ✓ {repo['name']}: {summary}")

        return repos

    def format_markdown(self, repos: list, title: str = "GitHub Trending") -> str:
        """마크다운 형식으로 변환"""

        output = f"# {title}\n\n"
        output += f"> 수집 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        output += "---\n\n"

        for repo in repos:
            output += f"## {repo['rank']}. [{repo['full_name']}]({repo['url']})\n\n"

            # 한글 요약 먼저
            if repo.get('summary_kr'):
                output += f"> 📌 **{repo['summary_kr']}**\n\n"

            if repo['description']:
                output += f"{repo['description']}\n\n"

            output += f"- ⭐ **{repo['stars']:,}** stars"
            if repo['today_stars']:
                output += f" ({repo['today_stars']})"
            output += "\n"

            output += f"- 🍴 {repo['forks']:,} forks\n"
            output += f"- 💻 {repo['language']}\n\n"
            output += "---\n\n"

        return output


def main():
    """테스트 실행"""
    collector = GitHubTrendingCollector()

    # 오늘의 트렌딩 (전체)
    repos = collector.get_trending(since="daily")

    if repos:
        md = collector.format_markdown(repos, "GitHub Trending (오늘)")
        print("\n" + "="*60)
        print(md[:2000])  # 미리보기

        # 파일 저장
        output_path = Path(__file__).parent.parent / 'output' / 'github_trending.md'
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(md, encoding='utf-8')
        print(f"\n✅ 저장됨: {output_path}")


if __name__ == "__main__":
    main()
