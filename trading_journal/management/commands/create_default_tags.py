from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from trading_journal.models import Tag

class Command(BaseCommand):
    help = 'Creates default trading strategy tags'

    def handle(self, *args, **kwargs):
        # Get or create a system user for default tags
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        default_tags = [
            {
                'name': 'Breakout',
                'description': 'Price breaking out of a defined range or pattern'
            },
            {
                'name': 'Compression Break',
                'description': 'Price breaking out after a period of compression'
            },
            {
                'name': 'Trend Reversal',
                'description': 'Change in the prevailing trend direction'
            },
            {
                'name': 'VWAP Reclaim',
                'description': 'Price reclaiming the Volume Weighted Average Price'
            },
            {
                'name': 'Range Break',
                'description': 'Price breaking out of a trading range'
            },
            {
                'name': 'Momentum Continuation',
                'description': 'Trading in the direction of strong momentum'
            }
        ]

        for tag_data in default_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'description': tag_data['description'],
                    'is_default': True,
                    'created_by': system_user
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created tag "{tag.name}"')
                ) 