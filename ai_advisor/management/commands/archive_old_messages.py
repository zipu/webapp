"""
Archive Old Messages Management Command
60일 이상 된 메시지를 아카이빙합니다.
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from ai_advisor.models import Message


class Command(BaseCommand):
    help = '60일 이상 된 메시지를 아카이빙합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='아카이빙할 메시지 기준 일수 (기본값: settings.AI_ADVISOR.MESSAGE_ARCHIVE_DAYS 또는 60일)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 아카이빙하지 않고 대상 메시지만 확인'
        )

    def handle(self, *args, **options):
        # 설정에서 아카이빙 기준 일수 가져오기
        ai_config = getattr(settings, 'AI_ADVISOR', {})
        archive_days = options['days'] or ai_config.get('MESSAGE_ARCHIVE_DAYS', 60)
        dry_run = options['dry_run']

        # 아카이빙 대상 메시지 계산
        cutoff_date = timezone.now() - timedelta(days=archive_days)

        # 아카이빙 대상 메시지 조회
        target_messages = Message.objects.filter(
            created_at__lt=cutoff_date,
            is_archived=False
        )

        count = target_messages.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'아카이빙할 메시지가 없습니다.')
            )
            return

        # Dry run 모드
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] {count}개의 메시지가 아카이빙 대상입니다.')
            )
            self.stdout.write(f'기준 날짜: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')

            # 샘플 메시지 표시
            sample_messages = target_messages[:5]
            self.stdout.write('\n샘플 메시지:')
            for msg in sample_messages:
                self.stdout.write(
                    f'  - ID: {msg.id}, 생성일: {msg.created_at.strftime("%Y-%m-%d")}, '
                    f'대화: {msg.conversation_id}'
                )

            if count > 5:
                self.stdout.write(f'  ... 외 {count - 5}개')

            return

        # 실제 아카이빙 실행
        self.stdout.write(f'{count}개의 메시지를 아카이빙 중...')

        updated = target_messages.update(
            is_archived=True,
            archived_at=timezone.now()
        )

        self.stdout.write(
            self.style.SUCCESS(f'✓ {updated}개의 메시지가 성공적으로 아카이빙되었습니다.')
        )
        self.stdout.write(f'기준 날짜: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
