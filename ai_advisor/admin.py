from django.contrib import admin
from .models import Conversation, Message, ContextCache, ConversationMemory, AISettings


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'app_type', 'created_at', 'updated_at', 'tokens_used', 'is_archived')
    list_filter = ('app_type', 'is_archived', 'created_at')
    search_fields = ('title', 'id')
    readonly_fields = ('created_at', 'updated_at', 'summary_generated_at')

    fieldsets = (
        ('기본 정보', {
            'fields': ('app_type', 'title', 'is_archived')
        }),
        ('토큰 및 컨텍스트', {
            'fields': ('tokens_used', 'context_snapshot')
        }),
        ('대화 최적화', {
            'fields': ('history_summary', 'summary_generated_at'),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'content_preview', 'created_at', 'tokens', 'is_archived')
    list_filter = ('role', 'is_archived', 'created_at')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at', 'archived_at')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용 미리보기'

    fieldsets = (
        ('메시지 정보', {
            'fields': ('conversation', 'role', 'content', 'tokens')
        }),
        ('Tool Calls', {
            'fields': ('tool_calls',),
            'classes': ('collapse',)
        }),
        ('아카이빙', {
            'fields': ('is_archived', 'archived_at'),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConversationMemory)
class ConversationMemoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'category', 'importance', 'content_preview', 'is_active', 'created_at')
    list_filter = ('category', 'importance', 'is_active', 'created_at')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_at', 'updated_at')

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용 미리보기'

    fieldsets = (
        ('메모리 정보', {
            'fields': ('conversation', 'content', 'category', 'importance', 'is_active')
        }),
        ('출처', {
            'fields': ('source_message',),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContextCache)
class ContextCacheAdmin(admin.ModelAdmin):
    list_display = ('cache_key', 'created_at', 'expires_at', 'is_expired_display')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('cache_key',)
    readonly_fields = ('created_at',)

    def is_expired_display(self, obj):
        return '만료됨' if obj.is_expired() else '유효함'
    is_expired_display.short_description = '상태'


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'ai_model', 'enable_long_term_memory', 'message_retention_days', 'updated_at')
    readonly_fields = ('updated_at',)

    fieldsets = (
        ('AI 모델 설정', {
            'fields': ('ai_model',)
        }),
        ('장기 기억 설정', {
            'fields': ('enable_long_term_memory',)
        }),
        ('메시지 관리', {
            'fields': ('message_retention_days',)
        }),
        ('타임스탬프', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
