"""
Economic News Service
미국 주요 경제지에서 RSS로 뉴스를 수집합니다.
"""

import feedparser
from datetime import datetime
from typing import List, Dict, Optional


class NewsService:
    """경제 뉴스 수집 서비스"""

    # 미국 주요 경제지 RSS 피드
    RSS_FEEDS = {
        'WSJ': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
        'Reuters': 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best',
        'CNBC': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
        'MarketWatch': 'https://www.marketwatch.com/rss/topstories',
        'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex',
        'Bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
    }

    @classmethod
    def get_economic_news(cls, keyword: Optional[str] = None, max_articles: int = 10) -> List[Dict]:
        """
        경제 뉴스 수집

        Args:
            keyword: 검색 키워드 (예: 'fed', 'inflation', 'S&P500')
            max_articles: 최대 기사 수

        Returns:
            뉴스 기사 리스트
        """
        all_articles = []

        # 각 RSS 피드에서 뉴스 수집
        for source_name, feed_url in cls.RSS_FEEDS.items():
            try:
                articles = cls._parse_feed(feed_url, source_name, keyword)
                all_articles.extend(articles)
            except Exception as e:
                print(f"[NewsService] {source_name} RSS 파싱 오류: {e}")
                continue

        # 최신순 정렬
        all_articles.sort(key=lambda x: x['published_timestamp'], reverse=True)

        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title_lower = article['title'].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_articles.append(article)

        return unique_articles[:max_articles]

    @classmethod
    def _parse_feed(cls, feed_url: str, source_name: str, keyword: Optional[str] = None) -> List[Dict]:
        """
        RSS 피드 파싱

        Args:
            feed_url: RSS 피드 URL
            source_name: 뉴스 소스 이름
            keyword: 필터링 키워드

        Returns:
            파싱된 기사 리스트
        """
        feed = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:20]:  # 각 피드에서 최대 20개
            try:
                title = entry.get('title', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                link = entry.get('link', '')
                published = entry.get('published', '') or entry.get('updated', '')

                # 키워드 필터링
                if keyword:
                    keyword_lower = keyword.lower()
                    if keyword_lower not in title.lower() and keyword_lower not in summary.lower():
                        continue

                # 발행 시간 파싱
                published_timestamp = cls._parse_published_date(published)

                # HTML 태그 제거
                summary_clean = cls._clean_html(summary)

                articles.append({
                    'source': source_name,
                    'title': title,
                    'summary': summary_clean[:300],  # 최대 300자
                    'link': link,
                    'published': published,
                    'published_timestamp': published_timestamp
                })

            except Exception as e:
                print(f"[NewsService] 기사 파싱 오류: {e}")
                continue

        return articles

    @staticmethod
    def _parse_published_date(date_string: str) -> float:
        """
        발행일자를 타임스탬프로 변환

        Args:
            date_string: 날짜 문자열

        Returns:
            Unix 타임스탬프
        """
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_string)
            return dt.timestamp()
        except:
            # 파싱 실패 시 현재 시간 반환
            return datetime.now().timestamp()

    @staticmethod
    def _clean_html(text: str) -> str:
        """
        HTML 태그 제거

        Args:
            text: HTML 포함 텍스트

        Returns:
            순수 텍스트
        """
        import re
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @classmethod
    def get_news_by_topic(cls, topic: str) -> List[Dict]:
        """
        주제별 뉴스 검색

        Args:
            topic: 주제 (예: 'fed', 'interest rate', 'stock market')

        Returns:
            뉴스 기사 리스트
        """
        return cls.get_economic_news(keyword=topic, max_articles=8)

    @classmethod
    def get_daily_brief(cls) -> Dict:
        """
        일일 경제 브리핑

        Returns:
            주요 뉴스 요약
        """
        # 키워드별로 주요 뉴스 수집
        topics = {
            'fed_rate': cls.get_news_by_topic('federal reserve'),
            'market': cls.get_news_by_topic('stock market'),
            'economy': cls.get_news_by_topic('economy'),
        }

        # 전체 최신 뉴스
        all_news = cls.get_economic_news(max_articles=10)

        return {
            'top_news': all_news[:5],
            'by_topic': topics,
            'total_count': len(all_news)
        }
