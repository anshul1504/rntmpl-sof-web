from django.core.management.base import BaseCommand

from apps.accounts.saas import process_notification_outbox


class Command(BaseCommand):
    help = 'Process pending notification outbox rows.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=25)

    def handle(self, *args, **options):
        processed = process_notification_outbox(limit=options['limit'])
        sent = sum(1 for notification in processed if notification.status == notification.Status.SENT)
        failed = sum(1 for notification in processed if notification.status == notification.Status.FAILED)
        self.stdout.write(
            self.style.SUCCESS(
                f'Processed {len(processed)} notifications: {sent} sent, {failed} failed.'
            )
        )
