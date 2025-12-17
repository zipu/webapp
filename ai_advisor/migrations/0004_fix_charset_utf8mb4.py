# Generated migration to fix MySQL charset for emoji support

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_advisor', '0003_conversation_history_summary_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward migration - convert to utf8mb4
            sql=[
                "ALTER TABLE ai_advisor_conversation CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE ai_advisor_message CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE ai_advisor_conversationmemory CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                "ALTER TABLE ai_advisor_contextcache CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            ],
            # Reverse migration - convert back to utf8 (optional, for rollback)
            reverse_sql=[
                "ALTER TABLE ai_advisor_conversation CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;",
                "ALTER TABLE ai_advisor_message CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;",
                "ALTER TABLE ai_advisor_conversationmemory CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;",
                "ALTER TABLE ai_advisor_contextcache CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;",
            ],
        ),
    ]
