"""
AI Advisor Views
채팅 인터페이스와 API 엔드포인트를 제공합니다.
"""

import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from .models import Conversation, Message, ConversationMemory
from .ai_service import AIService
from .memory_service import MemoryService
from .summarization_service import SummarizationService


class ChatView(TemplateView):
    """채팅 메인 페이지"""
    template_name = 'ai_advisor/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # app_type 파라미터 (기본값: trading)
        app_type = self.request.GET.get('app_type', 'trading')
        context['app_type'] = app_type

        # 최근 대화 목록 (해당 앱 타입만)
        recent_conversations = Conversation.objects.filter(
            app_type=app_type,
            is_archived=False
        ).order_by('-updated_at')[:10]
        context['conversations'] = recent_conversations

        # conversation_id가 제공된 경우 해당 대화 로드
        conversation_id = self.request.GET.get('conversation_id')
        if conversation_id:
            try:
                context['active_conversation'] = Conversation.objects.get(
                    id=conversation_id,
                    app_type=app_type
                )
            except Conversation.DoesNotExist:
                pass
        else:
            # conversation_id가 없으면 최근 대화 자동 로드
            if recent_conversations.exists():
                context['active_conversation'] = recent_conversations.first()

        return context


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    사용자 메시지를 받아 AI 응답 생성

    POST /ai/send_message/
    Body: {
        "conversation_id": 123 (optional),
        "message": "안녕?",
        "app_type": "trading" (optional, default: trading)
    }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        app_type = data.get('app_type', 'trading')

        if not user_message:
            return JsonResponse({'error': '메시지가 비어있습니다.'}, status=400)

        # 대화 가져오기 또는 생성
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                app_type=app_type
            )
        else:
            conversation = Conversation.objects.create(app_type=app_type)

        # 사용자 메시지 저장
        user_msg = Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )

        # AI 응답 생성
        ai_service = AIService()
        try:
            ai_response, tool_calls, input_tokens, output_tokens = ai_service.chat(conversation, user_message)

            # AI 응답 저장 (토큰 수 포함)
            assistant_msg = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response,
                tokens=input_tokens + output_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tool_calls=tool_calls if tool_calls else None
            )

            # 대화 제목 자동 생성 (첫 메시지인 경우)
            if not conversation.title:
                conversation.title = user_message[:50]
                conversation.save()

            # 메모리 저장은 AI가 save_memory tool을 사용하여 자동으로 처리함
            # 별도의 메모리 추출 API 호출 불필요 (Tool Use 방식)

            return JsonResponse({
                'success': True,
                'conversation_id': conversation.id,
                'message': {
                    'id': assistant_msg.id,
                    'role': 'assistant',
                    'content': ai_response,
                    'created_at': assistant_msg.created_at.isoformat(),
                    'tokens': assistant_msg.tokens,
                    'input_tokens': assistant_msg.input_tokens,
                    'output_tokens': assistant_msg.output_tokens
                },
                'tool_calls': tool_calls
            })

        except Exception as e:
            # AI 에러 메시지 저장
            error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=error_msg
            )

            return JsonResponse({
                'success': False,
                'error': error_msg,
                'conversation_id': conversation.id
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_conversation(request, conversation_id):
    """
    특정 대화의 전체 메시지 조회

    GET /ai/conversation/<id>/
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    messages = [{
        'id': msg.id,
        'role': msg.role,
        'content': msg.content,
        'created_at': msg.created_at.isoformat(),
        'tool_calls': msg.tool_calls
    } for msg in conversation.messages.all()]

    return JsonResponse({
        'conversation_id': conversation.id,
        'app_type': conversation.app_type,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'messages': messages
    })


@csrf_exempt
@require_http_methods(["POST"])
def new_conversation(request):
    """
    새 대화 시작

    POST /ai/new_conversation/
    Body: {
        "app_type": "trading" (optional)
    }
    """
    try:
        data = json.loads(request.body)
        app_type = data.get('app_type', 'trading')

        conversation = Conversation.objects.create(app_type=app_type)

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'app_type': app_type
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def conversation_list(request):
    """
    대화 목록 조회

    GET /ai/conversations/?app_type=trading
    """
    app_type = request.GET.get('app_type', 'trading')

    conversations = Conversation.objects.filter(
        app_type=app_type,
        is_archived=False
    ).order_by('-updated_at')[:20]

    data = [{
        'id': conv.id,
        'title': conv.title or f'대화 #{conv.id}',
        'created_at': conv.created_at.isoformat(),
        'updated_at': conv.updated_at.isoformat(),
        'message_count': conv.messages.count()
    } for conv in conversations]

    return JsonResponse({'conversations': data})


# ========================================
# 메모리 관리 API
# ========================================

@require_http_methods(["GET"])
def get_memories(request, conversation_id):
    """
    대화의 메모리 목록 조회

    GET /ai/conversation/<id>/memories/
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    memory_service = MemoryService()

    memories = memory_service.get_active_memories(conversation)

    data = [{
        'id': mem.id,
        'content': mem.content,
        'category': mem.category,
        'category_display': mem.get_category_display(),
        'importance': mem.importance,
        'created_at': mem.created_at.isoformat(),
        'source_message_id': mem.source_message.id if mem.source_message else None
    } for mem in memories]

    return JsonResponse({'memories': data})


@csrf_exempt
@require_http_methods(["POST"])
def create_memory(request, conversation_id):
    """
    수동으로 메모리 생성

    POST /ai/conversation/<id>/memories/
    Body: {
        "content": "기억할 내용",
        "category": "strategy",
        "importance": 7
    }
    """
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        data = json.loads(request.body)

        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({'error': '내용이 비어있습니다.'}, status=400)

        category = data.get('category', 'other')
        importance = data.get('importance', 5)

        memory_service = MemoryService()
        memory = memory_service.add_manual_memory(
            conversation=conversation,
            content=content,
            category=category,
            importance=importance
        )

        return JsonResponse({
            'success': True,
            'memory': {
                'id': memory.id,
                'content': memory.content,
                'category': memory.category,
                'importance': memory.importance,
                'created_at': memory.created_at.isoformat()
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_memory(request, memory_id):
    """
    메모리 삭제 (비활성화)

    DELETE /ai/memory/<id>/
    """
    memory_service = MemoryService()
    success = memory_service.deactivate_memory(memory_id)

    if success:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': '메모리를 찾을 수 없습니다.'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def save_message_as_memory(request, message_id):
    """
    메시지를 메모리로 저장

    POST /ai/message/<id>/save_memory/
    Body: {
        "category": "strategy",
        "importance": 8
    }
    """
    try:
        message = get_object_or_404(Message, id=message_id)
        data = json.loads(request.body)

        category = data.get('category', 'other')
        importance = data.get('importance', 5)

        memory_service = MemoryService()
        memory = memory_service.add_manual_memory(
            conversation=message.conversation,
            content=message.content,
            category=category,
            importance=importance,
            source_message=message
        )

        return JsonResponse({
            'success': True,
            'memory': {
                'id': memory.id,
                'content': memory.content,
                'category': memory.category,
                'importance': memory.importance
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def extract_memories(request, conversation_id):
    """
    대화에서 메모리 자동 추출 트리거

    POST /ai/conversation/<id>/extract_memories/
    """
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)

        memory_service = MemoryService()
        memories = memory_service.extract_memories_from_conversation(conversation)

        return JsonResponse({
            'success': True,
            'extracted_count': len(memories),
            'memories': [{
                'id': mem.id,
                'content': mem.content,
                'category': mem.category,
                'importance': mem.importance
            } for mem in memories]
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_summary_stats(request, conversation_id):
    """
    대화 요약 통계

    GET /ai/conversation/<id>/summary_stats/
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    summarization_service = SummarizationService()
    stats = summarization_service.get_summary_stats(conversation)

    return JsonResponse(stats)
