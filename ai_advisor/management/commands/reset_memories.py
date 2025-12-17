"""
Reset and Re-extract Memories
잘못 추출된 메모리를 삭제하고 재추출합니다.
"""

from django.core.management.base import BaseCommand
from ai_advisor.models import ConversationMemory, Conversation
from ai_advisor.memory_service import MemoryService


class Command(BaseCommand):
    help = '잘못 추출된 메모리를 삭제하고 올바르게 재추출합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--conversation-id',
            type=int,
            default=None,
            help='특정 대화만 재추출 (지정하지 않으면 전체)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 삭제/재추출하지 않고 확인만'
        )

    def handle(self, *args, **options):
        conversation_id = options['conversation_id']
        dry_run = options['dry_run']

        # 대상 대화 선택
        if conversation_id:
            conversations = Conversation.objects.filter(id=conversation_id)
        else:
            conversations = Conversation.objects.all()

        total_deleted = 0
        total_created = 0

        for conversation in conversations:
            old_memories = conversation.memories.filter(is_active=True)
            old_count = old_memories.count()

            self.stdout.write(f'\n대화 #{conversation.id}: {conversation.title or "(제목 없음)"}')
            self.stdout.write(f'  - 기존 메모리: {old_count}개')

            if dry_run:
                self.stdout.write(self.style.WARNING('  [DRY RUN] 삭제하지 않음'))
                continue

            # 기존 메모리 삭제
            deleted_count = old_memories.delete()[0]
            total_deleted += deleted_count
            self.stdout.write(f'  - 삭제됨: {deleted_count}개')

            # 새로 추출
            memory_service = MemoryService()
            try:
                new_memories = memory_service.extract_memories_from_conversation(conversation)
                new_count = len(new_memories)
                total_created += new_count
                self.stdout.write(self.style.SUCCESS(f'  - 재추출됨: {new_count}개'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  - 오류: {str(e)}'))

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n완료: {total_deleted}개 삭제, {total_created}개 재추출')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n[DRY RUN] 실제 실행 시: {conversations.count()}개 대화 처리 예정')
            )
