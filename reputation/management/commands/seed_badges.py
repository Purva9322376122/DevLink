"""
Management command to seed the default Badge records.
Run once: python manage.py seed_badges
"""
from django.core.management.base import BaseCommand
from reputation.models import Badge

BADGES = [
    {
        'name': 'First Problem',
        'slug': 'first-problem',
        'description': 'Awarded for posting your first problem.',
        'icon': 'bi-question-circle',
        'trigger': 'first_problem',
    },
    {
        'name': 'First Accepted Solution',
        'slug': 'first-accepted',
        'description': 'Awarded when your first solution is accepted.',
        'icon': 'bi-check-circle',
        'trigger': 'first_accepted',
    },
    {
        'name': 'Top Contributor',
        'slug': 'top-contributor',
        'description': 'Recognised as a top contributor to the community.',
        'icon': 'bi-star',
        'trigger': 'top_contributor',
    },
    {
        'name': 'Mentor',
        'slug': 'mentor',
        'description': 'Helped many members by sharing knowledge.',
        'icon': 'bi-mortarboard',
        'trigger': 'mentor',
    },
    {
        'name': '100 Reputation',
        'slug': 'rep-100',
        'description': 'Reached 100 reputation points.',
        'icon': 'bi-award',
        'trigger': 'rep_100',
    },
    {
        'name': '1000 Reputation',
        'slug': 'rep-1000',
        'description': 'Reached 1000 reputation points.',
        'icon': 'bi-trophy',
        'trigger': 'rep_1000',
    },
    {
        'name': 'Connector',
        'slug': 'connector',
        'description': 'Made 10 or more connections on DevLink.',
        'icon': 'bi-people',
        'trigger': 'connector',
    },
]


class Command(BaseCommand):
    help = 'Seed default badge data'

    def handle(self, *args, **options):
        created_count = 0
        for badge_data in BADGES:
            _, created = Badge.objects.get_or_create(
                trigger=badge_data['trigger'],
                defaults={
                    'name': badge_data['name'],
                    'slug': badge_data['slug'],
                    'description': badge_data['description'],
                    'icon': badge_data['icon'],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created badge: {badge_data['name']}"))
            else:
                self.stdout.write(f"Badge already exists: {badge_data['name']}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_count} new badge(s) created."))
