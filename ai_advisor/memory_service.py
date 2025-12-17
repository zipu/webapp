"""
Memory Service
대화에서 중요한 정보를 추출하고 관리합니다.
"""

import json
import anthropic
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone
from .models import Conversation, Message, ConversationMemory


class MemoryService:
    """장기 기억 추출 및 관리 서비스"""

    def __init__(self):
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY가 settings.py에 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"

    def extract_memories_from_conversation(
        self,
        conversation: Conversation,
        limit: int = 20
    ) -> List[ConversationMemory]:
        """
        대화에서 자동으로 중요한 메모리 추출

        Args:
            conversation: 대화 객체
            limit: 최근 메시지 분석 개수 (기본 20개)

        Returns:
            생성된 메모리 객체 리스트
        """
        # 자동 추출이 비활성화된 경우
        ai_config = getattr(settings, 'AI_ADVISOR', {})
        if not ai_config.get('AUTO_EXTRACT_MEMORIES', True):
            return []

        # 최근 메시지 가져오기
        recent_messages = conversation.messages.filter(
            is_archived=False
        ).order_by('-created_at')[:limit]

        if not recent_messages.exists():
            return []

        # 메시지를 시간순으로 정렬
        messages_text = "\n\n".join([
            f"[{msg.get_role_display()}] {msg.content}"
            for msg in reversed(recent_messages)
        ])

        # Claude에게 메모리 추출 요청
        extraction_prompt = f"""다음은 트레이딩 AI 어드바이저와 사용자의 대화입니다.
이 대화에서 **사용자에 대한 중요한 사실**만 추출하여 장기 기억으로 저장하세요.

대화 내용:
{messages_text}

**중요: 다음 규칙을 반드시 따르세요:**
1. **사용자에 대한 사실만** 추출 (AI의 조언이나 분석은 제외)
2. 사용자가 직접 언급하거나 암시한 내용만 포함
3. 사용자의 거래 습관, 전략, 목표, 심리 패턴, 제약사항에 집중

**추출할 정보 카테고리:**
- strategy: 사용자가 사용하는 거래 전략
- rule: 사용자가 설정한 거래 규칙
- lesson: 사용자가 배운 교훈 또는 경험
- psychology: 사용자의 심리/감정 패턴
- risk: 사용자의 리스크 관리 원칙
- pattern: 사용자가 관찰한 시장 패턴
- goal: 사용자의 목표나 제약사항

**출력 형식 (JSON 배열):**
[
  {{
    "content": "사용자에 대한 구체적인 사실",
    "category": "카테고리",
    "importance": 1-10
  }}
]

**예시:**
- ✅ "손절은 -2% 지점에서 실행한다는 규칙 설정"
- ✅ "연속 손실 후 감정적으로 복수 매매하는 경향"
- ✅ "아침 9-10시 거래 선호"
- ❌ "손절을 잘 지켜야 합니다" (AI의 조언)
- ❌ "변동성이 높을 때 주의하세요" (AI의 분석)

중요한 사실이 없다면 빈 배열 []을 반환하세요.
오직 JSON 배열만 반환하고 다른 설명은 하지 마세요."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": extraction_prompt
                }]
            )

            response_text = response.content[0].text.strip()

            # JSON 파싱 (마크다운 코드 블록 제거)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            memories_data = json.loads(response_text)

            # DB에 저장
            created_memories = []
            max_memories = ai_config.get('MEMORY_MAX_COUNT', 100)
            current_count = conversation.memories.filter(is_active=True).count()

            for mem_data in memories_data:
                # 최대 개수 체크
                if current_count >= max_memories:
                    break

                # 중복 체크 (유사한 내용이 이미 있는지)
                content = mem_data.get('content', '').strip()
                if not content:
                    continue

                # 같은 내용의 메모리가 이미 있는지 확인
                existing = conversation.memories.filter(
                    content__icontains=content[:50],  # 처음 50자로 체크
                    is_active=True
                ).exists()

                if existing:
                    continue

                # 메모리 생성
                memory = ConversationMemory.objects.create(
                    conversation=conversation,
                    content=content,
                    category=mem_data.get('category', 'other'),
                    importance=min(10, max(1, mem_data.get('importance', 5))),
                    source_message=recent_messages.first() if recent_messages else None
                )
                created_memories.append(memory)
                current_count += 1

            return created_memories

        except Exception as e:
            print(f"메모리 추출 실패: {str(e)}")
            return []

    def add_manual_memory(
        self,
        conversation: Conversation,
        content: str,
        category: str = 'other',
        importance: int = 5,
        source_message: Optional[Message] = None
    ) -> ConversationMemory:
        """
        수동으로 메모리 추가

        Args:
            conversation: 대화 객체
            content: 기억할 내용
            category: 카테고리
            importance: 중요도 (1-10)
            source_message: 출처 메시지

        Returns:
            생성된 메모리 객체
        """
        memory = ConversationMemory.objects.create(
            conversation=conversation,
            content=content,
            category=category,
            importance=min(10, max(1, importance)),
            source_message=source_message
        )
        return memory

    def get_active_memories(
        self,
        conversation: Conversation,
        max_count: Optional[int] = None
    ) -> List[ConversationMemory]:
        """
        활성 메모리 조회 (중요도 순)

        Args:
            conversation: 대화 객체
            max_count: 최대 개수 (None이면 모두)

        Returns:
            메모리 객체 리스트
        """
        memories = conversation.memories.filter(
            is_active=True
        ).order_by('-importance', '-created_at')

        if max_count:
            memories = memories[:max_count]

        return list(memories)

    def deactivate_memory(self, memory_id: int) -> bool:
        """
        메모리 비활성화

        Args:
            memory_id: 메모리 ID

        Returns:
            성공 여부
        """
        try:
            memory = ConversationMemory.objects.get(id=memory_id)
            memory.is_active = False
            memory.save()
            return True
        except ConversationMemory.DoesNotExist:
            return False

    def format_memories_for_context(
        self,
        conversation: Conversation,
        max_count: int = 50
    ) -> str:
        """
        메모리를 AI 컨텍스트용 텍스트로 포맷팅

        Args:
            conversation: 대화 객체
            max_count: 최대 메모리 개수

        Returns:
            포맷팅된 텍스트
        """
        memories = self.get_active_memories(conversation, max_count)

        if not memories:
            return ""

        # 카테고리별로 그룹화
        categorized = {}
        for memory in memories:
            category = memory.get_category_display()
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(memory)

        # 포맷팅
        lines = ["=== 장기 기억 (Long-term Memories) ===\n"]

        for category, mems in categorized.items():
            lines.append(f"\n[{category}]")
            for mem in mems:
                importance_stars = "⭐" * min(3, (mem.importance + 2) // 3)
                lines.append(f"  {importance_stars} {mem.content}")

        return "\n".join(lines)

    def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        category: Optional[str] = None,
        importance: Optional[int] = None
    ) -> bool:
        """
        메모리 업데이트

        Args:
            memory_id: 메모리 ID
            content: 새 내용 (선택)
            category: 새 카테고리 (선택)
            importance: 새 중요도 (선택)

        Returns:
            성공 여부
        """
        try:
            memory = ConversationMemory.objects.get(id=memory_id)

            if content is not None:
                memory.content = content
            if category is not None:
                memory.category = category
            if importance is not None:
                memory.importance = min(10, max(1, importance))

            memory.save()
            return True
        except ConversationMemory.DoesNotExist:
            return False
