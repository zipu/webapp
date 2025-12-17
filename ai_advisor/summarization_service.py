"""
Summarization Service
대화 내역을 요약하여 컨텍스트 크기를 관리합니다.
"""

import anthropic
from typing import Optional
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .models import Conversation, Message, ContextCache


class SummarizationService:
    """대화 요약 생성 및 관리 서비스"""

    def __init__(self):
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY가 settings.py에 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"

    def needs_summary(self, conversation: Conversation) -> bool:
        """
        대화가 요약이 필요한지 판단

        Args:
            conversation: 대화 객체

        Returns:
            요약 필요 여부
        """
        ai_config = getattr(settings, 'AI_ADVISOR', {})
        retention_days = ai_config.get('MESSAGE_RETENTION_DAYS', 30)

        # 30일 이상 된 메시지가 있는지 확인
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        old_messages_exist = conversation.messages.filter(
            created_at__lt=cutoff_date,
            is_archived=False
        ).exists()

        if not old_messages_exist:
            return False

        # 요약이 없거나 오래된 경우
        if not conversation.history_summary:
            return True

        # 요약이 7일 이상 지난 경우 (새 메시지가 있을 수 있음)
        if conversation.summary_generated_at:
            summary_age = timezone.now() - conversation.summary_generated_at
            if summary_age > timedelta(days=7):
                return True

        return False

    def generate_summary(self, conversation: Conversation) -> str:
        """
        30일 이상 된 메시지를 요약 생성

        Args:
            conversation: 대화 객체

        Returns:
            생성된 요약 텍스트
        """
        ai_config = getattr(settings, 'AI_ADVISOR', {})
        retention_days = ai_config.get('MESSAGE_RETENTION_DAYS', 30)
        max_tokens = ai_config.get('SUMMARY_MAX_TOKENS', 500)

        # 30일+ 이전 메시지 가져오기
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        old_messages = conversation.messages.filter(
            created_at__lt=cutoff_date,
            is_archived=False
        ).order_by('created_at')

        if not old_messages.exists():
            return ""

        # 메시지를 텍스트로 변환
        messages_text = "\n\n".join([
            f"[{msg.created_at.strftime('%Y-%m-%d')}] [{msg.get_role_display()}]\n{msg.content}"
            for msg in old_messages
        ])

        # 요약 프롬프트
        summary_prompt = f"""다음은 트레이딩 AI 어드바이저와 사용자의 과거 대화 내역입니다.
이 대화를 {max_tokens} 토큰 이하로 간결하게 요약해주세요.

**중요: 사용자 중심으로 요약하세요**
- 사용자가 언급한 거래 내역, 전략, 고민에 집중
- AI의 조언이나 설명은 간략히만 언급
- 사용자의 거래 성과, 습관 변화, 심리 상태 변화에 주목

**요약에 포함할 내용:**
1. 사용자가 논의한 주요 거래 전략과 패턴
2. 사용자가 겪은 주요 문제와 시도한 해결 방법
3. 사용자의 중요한 인사이트나 발견
4. 사용자의 거래 성과나 습관의 시간 흐름에 따른 변화

**제외할 내용:**
- 불필요한 인사말
- 반복적인 AI 조언
- 일반적인 트레이딩 이론

대화 내역:
{messages_text}

요약:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": summary_prompt
                }]
            )

            summary = response.content[0].text.strip()

            # DB에 저장
            conversation.history_summary = summary
            conversation.summary_generated_at = timezone.now()
            conversation.save()

            return summary

        except Exception as e:
            print(f"요약 생성 실패: {str(e)}")
            return ""

    def get_summary(self, conversation: Conversation) -> str:
        """
        요약 조회 (없으면 생성)

        Args:
            conversation: 대화 객체

        Returns:
            요약 텍스트
        """
        # 캐시 확인
        cache_key = f"summary_{conversation.id}"
        cached = ContextCache.get_cached(cache_key)
        if cached:
            return cached.get('summary', '')

        # 요약이 필요한지 확인
        if self.needs_summary(conversation):
            summary = self.generate_summary(conversation)
        else:
            summary = conversation.history_summary or ""

        # 캐싱 (1시간)
        if summary:
            ContextCache.set_cache(cache_key, {'summary': summary}, hours=1)

        return summary

    def invalidate_cache(self, conversation: Conversation):
        """
        요약 캐시 무효화

        Args:
            conversation: 대화 객체
        """
        cache_key = f"summary_{conversation.id}"
        try:
            cache = ContextCache.objects.get(cache_key=cache_key)
            cache.delete()
        except ContextCache.DoesNotExist:
            pass

    def get_summary_stats(self, conversation: Conversation) -> dict:
        """
        요약 관련 통계 정보

        Args:
            conversation: 대화 객체

        Returns:
            통계 딕셔너리
        """
        ai_config = getattr(settings, 'AI_ADVISOR', {})
        retention_days = ai_config.get('MESSAGE_RETENTION_DAYS', 30)

        cutoff_date = timezone.now() - timedelta(days=retention_days)

        total_messages = conversation.messages.filter(is_archived=False).count()
        old_messages = conversation.messages.filter(
            created_at__lt=cutoff_date,
            is_archived=False
        ).count()
        recent_messages = total_messages - old_messages

        return {
            'total_messages': total_messages,
            'old_messages': old_messages,
            'recent_messages': recent_messages,
            'has_summary': bool(conversation.history_summary),
            'summary_generated_at': conversation.summary_generated_at,
            'needs_summary': self.needs_summary(conversation)
        }
