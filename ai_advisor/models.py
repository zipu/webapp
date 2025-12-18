from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """채팅 대화 세션"""
    APP_TYPE_CHOICES = [
        ('trading', 'Trading Advisor'),
        ('echomind', 'Echomind Advisor'),
    ]

    app_type = models.CharField(
        max_length=20,
        choices=APP_TYPE_CHOICES,
        default='trading',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200, blank=True)
    context_snapshot = models.JSONField(default=dict)
    is_archived = models.BooleanField(default=False)
    tokens_used = models.IntegerField(default=0)

    # 대화 최적화 필드
    history_summary = models.TextField(
        blank=True,
        help_text="30일 이상 된 메시지들의 요약본"
    )
    summary_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="요약이 마지막으로 생성된 시점"
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '대화'
        verbose_name_plural = '대화들'

    def __str__(self):
        # 이모지 제거 (MySQL utf8 호환)
        import re
        title = self.title or f"대화 #{self.id} ({self.created_at.strftime('%Y-%m-%d')})"
        # 이모지 및 4바이트 문자 제거
        title = re.sub(r'[^\u0000-\uFFFF]', '', title)
        return title[:100]  # 길이 제한


class Message(models.Model):
    """개별 메시지"""
    ROLE_CHOICES = [
        ('user', '사용자'),
        ('assistant', 'AI'),
        ('system', '시스템'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tokens = models.IntegerField(default=0)  # 총 토큰 (입력 + 출력)
    input_tokens = models.IntegerField(default=0)  # 입력 토큰
    output_tokens = models.IntegerField(default=0)  # 출력 토큰
    tool_calls = models.JSONField(null=True, blank=True)  # Claude Tool use 기록

    # 아카이빙 필드
    is_archived = models.BooleanField(
        default=False,
        help_text="60일 이상 된 메시지는 아카이빙됨"
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = '메시지'
        verbose_name_plural = '메시지들'

    def __str__(self):
        # 이모지 제거 (MySQL utf8 호환)
        import re
        content = re.sub(r'[^\u0000-\uFFFF]', '', self.content[:50])
        return f"{self.get_role_display()}: {content}..."


class ContextCache(models.Model):
    """데이터 캐싱으로 API 비용 절감"""
    cache_key = models.CharField(max_length=100, unique=True, db_index=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = '캐시'
        verbose_name_plural = '캐시들'

    def __str__(self):
        return f"{self.cache_key} (만료: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"

    def is_expired(self):
        """캐시가 만료되었는지 확인"""
        return timezone.now() > self.expires_at

    @classmethod
    def get_cached(cls, cache_key):
        """캐시에서 데이터 가져오기 (만료된 경우 None 반환)"""
        try:
            cache = cls.objects.get(cache_key=cache_key)
            if cache.is_expired():
                cache.delete()
                return None
            return cache.data
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_cache(cls, cache_key, data, hours=1):
        """캐시 설정 (기본 1시간)"""
        expires_at = timezone.now() + timezone.timedelta(hours=hours)
        cache, created = cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={'data': data, 'expires_at': expires_at}
        )
        return cache


class ConversationMemory(models.Model):
    """장기 기억 저장 (중요한 트레이딩 인사이트, 규칙, 교훈 등)"""
    CATEGORY_CHOICES = [
        ('strategy', '거래 전략'),
        ('rule', '거래 규칙'),
        ('lesson', '배운 교훈'),
        ('psychology', '심리/감정 관리'),
        ('risk', '리스크 관리'),
        ('pattern', '발견한 패턴'),
        ('goal', '목표/제약사항'),
        ('other', '기타'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='memories'
    )
    content = models.TextField(help_text="기억할 내용")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    importance = models.IntegerField(
        default=5,
        help_text="중요도 (1-10)"
    )
    source_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="이 메모리가 추출된 원본 메시지"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="비활성화된 메모리는 AI에게 제공되지 않음"
    )

    class Meta:
        ordering = ['-importance', '-created_at']
        verbose_name = '대화 메모리'
        verbose_name_plural = '대화 메모리들'

    def __str__(self):
        # 이모지 제거 (MySQL utf8 호환)
        import re
        content = re.sub(r'[^\u0000-\uFFFF]', '', self.content[:50])
        return f"[{self.get_category_display()}] {content}..."


class AISettings(models.Model):
    """AI Advisor 설정 (전역 설정, 하나의 인스턴스만 존재)"""
    MODEL_CHOICES = [
        ('claude-sonnet-4-5', 'Claude Sonnet 4.5 (고품질, 느림)'),
        ('claude-haiku-4-5', 'Claude Haiku 4.5 (빠름, 저렴)'),
    ]

    # 장기 기억 설정
    enable_long_term_memory = models.BooleanField(
        default=True,
        verbose_name='장기 기억 활성화',
        help_text='대화에서 중요한 사실을 자동으로 기억합니다'
    )

    # 메시지 보관 기간
    message_retention_days = models.IntegerField(
        default=30,
        verbose_name='최근 메시지 보관 일수',
        help_text='이 기간 내의 메시지만 전체 로드합니다 (나머지는 요약)'
    )

    # AI 모델 선택
    ai_model = models.CharField(
        max_length=50,
        choices=MODEL_CHOICES,
        default='claude-sonnet-4-5',
        verbose_name='AI 모델'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI 설정'
        verbose_name_plural = 'AI 설정'

    def __str__(self):
        return f"AI 설정 (모델: {self.get_ai_model_display()})"

    @classmethod
    def get_settings(cls):
        """설정 가져오기 (없으면 기본값으로 생성)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
