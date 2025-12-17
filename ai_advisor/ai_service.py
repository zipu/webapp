"""
Claude AI Service
Claude API와 통신하여 AI 응답을 생성합니다.
"""

import json
import anthropic
import time
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .prompts import get_system_prompt
from .tools import get_tools
from .context_builder import get_context_builder
from .memory_service import MemoryService
from .summarization_service import SummarizationService

class AIService:
    """Claude AI 서비스"""

    def __init__(self):
        """Claude 클라이언트 초기화"""
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY가 settings에 설정되지 않았습니다.")
        self.client = anthropic.Anthropic(api_key=api_key)

        # AI 설정 로드
        from .models import AISettings
        self.ai_settings = AISettings.get_settings()
        self.model = self.ai_settings.ai_model

    def chat(self, conversation, user_message):
        """
        대화 생성 (Tool use 지원)

        Args:
            conversation: Conversation 모델 인스턴스
            user_message: 사용자 메시지 텍스트

        Returns:
            AI 응답 텍스트
        """
        app_type = conversation.app_type

        # 시스템 프롬프트 가져오기
        system_prompt = get_system_prompt(app_type)

        # 도구 가져오기
        tools = get_tools(app_type)

        # 대화 히스토리 구성
        messages = self._build_messages(conversation)

        # 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Claude API 호출 (Tool use 포함)
        print(f"[AI Service] API 호출 시작... (모델: {self.model})")
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
            tools=tools,
            temperature=0.7
        )

        elapsed = time.time() - start_time
        print(f"[AI Service] API 호출 완료: {elapsed:.2f}초")

        # Tool use 처리
        final_response, tool_calls = self._handle_tool_use(
            response, messages, system_prompt, tools, app_type, conversation
        )

        # 토큰 사용량 계산
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        print(f"[AI Service] 토큰 사용: {total_tokens} (입력: {input_tokens}, 출력: {output_tokens})")

        return final_response, tool_calls, input_tokens, output_tokens

    def _build_messages(self, conversation):
        """
        대화 히스토리를 Claude 메시지 형식으로 변환
        3계층 구조: 장기 기억 + 요약 + 최근 메시지
        """
        messages = []

        # 1. 장기 기억 추가 (설정에 따라)
        if self.ai_settings.enable_long_term_memory:
            memory_service = MemoryService()
            memories_text = memory_service.format_memories_for_context(conversation)

            if memories_text:
                messages.append({
                    "role": "user",
                    "content": f"{memories_text}\n\n위 내용은 과거 대화에서 추출한 중요한 장기 기억입니다."
                })
                messages.append({
                    "role": "assistant",
                    "content": "장기 기억을 확인했습니다. 이 정보들을 기억하고 대화에 활용하겠습니다."
                })

        # 2. 30일+ 요약 추가
        summarization_service = SummarizationService()
        summary = summarization_service.get_summary(conversation)

        if summary:
            messages.append({
                "role": "user",
                "content": f"[과거 대화 요약]\n{summary}\n\n위 내용은 30일 이전 대화의 요약입니다."
            })
            messages.append({
                "role": "assistant",
                "content": "과거 대화 맥락을 이해했습니다."
            })

        # 3. 최근 메시지만 추가 (설정된 일수 기반)
        cutoff_date = timezone.now() - timedelta(days=self.ai_settings.message_retention_days)
        recent_messages = conversation.messages.filter(
            created_at__gte=cutoff_date,
            is_archived=False
        ).order_by('created_at')

        print(f"[AI Service] 로드된 메시지 수: {recent_messages.count()} (최근 {self.ai_settings.message_retention_days}일)")

        for msg in recent_messages:
            # 시스템 메시지는 제외
            if msg.role == 'system':
                continue

            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    def _handle_tool_use(self, response, messages, system_prompt, tools, app_type, conversation):
        """
        Tool use 처리
        Claude가 도구를 사용하면 실행하고 결과를 다시 전달
        """
        tool_calls = []
        max_iterations = 5  # 무한 루프 방지

        for iteration in range(max_iterations):
            # Tool use 확인
            if response.stop_reason != "tool_use":
                # 일반 응답
                text_content = next(
                    (block.text for block in response.content if hasattr(block, 'text')),
                    ""
                )
                return text_content, tool_calls

            # 모든 Tool use 블록 찾기
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

            if not tool_use_blocks:
                break

            # Assistant 응답 추가 (원본 content 그대로)
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # 모든 도구 실행 및 결과 수집
            tool_results = []
            for tool_use_block in tool_use_blocks:
                tool_name = tool_use_block.name
                tool_input = tool_use_block.input
                tool_use_id = tool_use_block.id

                print(f"[AI Service] Tool 실행: {tool_name} with {tool_input}")

                try:
                    result = self._execute_tool(tool_name, tool_input, app_type, conversation)
                    tool_calls.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                except Exception as e:
                    error_result = {"error": str(e)}
                    print(f"[AI Service] Tool 실행 오류: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(error_result, ensure_ascii=False)
                    })

            # Tool 결과 추가 (한 번에 모든 결과)
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # 다시 Claude 호출
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=messages,
                tools=tools,
                temperature=0.7
            )

        # 최종 응답
        text_content = next(
            (block.text for block in response.content if hasattr(block, 'text')),
            "죄송합니다. 응답을 생성하는 데 문제가 발생했습니다."
        )

        return text_content, tool_calls

    def _execute_tool(self, tool_name, tool_input, app_type, conversation):
        """
        도구 실행 라우터
        """
        context_builder = get_context_builder(app_type)

        # Memory tool
        if tool_name == "save_memory":
            from .memory_service import MemoryService

            memory_service = MemoryService()
            memory = memory_service.add_manual_memory(
                conversation=conversation,
                content=tool_input.get('content'),
                category=tool_input.get('category', 'other'),
                importance=tool_input.get('importance', 5)
            )

            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"메모리가 저장되었습니다. (카테고리: {memory.get_category_display()}, 중요도: {memory.importance})"
            }

        # Trading tools
        elif tool_name == "get_recent_trades":
            return context_builder.get_recent_trades(**tool_input)
        elif tool_name == "get_independence_test":
            return context_builder.get_independence_test()
        elif tool_name == "get_equity_curve":
            return context_builder.get_equity_curve(**tool_input)
        elif tool_name == "get_pattern_analysis":
            return context_builder.get_pattern_analysis(**tool_input)
        elif tool_name == "get_economic_news":
            # 뉴스 서비스 사용
            from .news_service import NewsService
            keyword = tool_input.get('keyword')
            max_articles = tool_input.get('max_articles', 8)
            return {
                "articles": NewsService.get_economic_news(keyword=keyword, max_articles=max_articles)
            }

        # Echomind tools (나중에 구현)
        elif tool_name == "get_recent_activities":
            return context_builder.get_recent_activities(**tool_input)

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def stream_chat(self, conversation, user_message):
        """
        스트리밍 채팅 응답 (나중에 구현)
        현재는 일반 chat() 사용
        """
        # TODO: Implement streaming with tool use
        return self.chat(conversation, user_message)
