from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger('devlink')


@receiver(post_save, sender='solutions.Solution')
def on_solution_accepted(sender, instance, created, **kwargs):
    if not created and instance.is_accepted:
        from .services import award_reputation
        try:
            award_reputation(
                instance.user,
                'solution_accepted',
                f'Solution accepted for "{instance.problem.title}"',
            )
        except Exception as e:
            logger.warning("Reputation signal failed: %s", e)


@receiver(post_save, sender='solutions.Vote')
def on_vote_cast(sender, instance, created, **kwargs):
    if created:
        from .services import award_reputation
        try:
            award_reputation(
                instance.solution.user,
                'solution_upvoted',
                f'Solution upvoted by {instance.user.username}',
            )
        except Exception as e:
            logger.warning("Reputation signal failed: %s", e)


@receiver(post_save, sender='opportunities.Invitation')
def on_connection_accepted(sender, instance, created, **kwargs):
    if not created and instance.status == 'accepted':
        from .services import award_reputation
        try:
            award_reputation(instance.sender, 'connection_accepted', 'Connection accepted')
            award_reputation(instance.receiver, 'connection_accepted', 'Connection accepted')
        except Exception as e:
            logger.warning("Reputation signal failed: %s", e)
