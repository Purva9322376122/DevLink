"""
Notification signals — wire domain events to notification creation.

Events covered:
  - Invitation created           → connection_request to receiver
  - Invitation accepted          → connection_accepted to sender
  - Solution accepted            → solution_accepted to solution author
  - Vote created                 → solution_upvoted to solution author
  - Comment created              → solution_commented / comment_replied
  - Application created          → application_received to opportunity owner
  - Application status changed   → application_accepted / application_rejected to applicant
  - Message created              → new_message to receiver
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('devlink')


# ---------------------------------------------------------------------------
# Invitations → connection_request / connection_accepted
# ---------------------------------------------------------------------------

@receiver(post_save, sender='opportunities.Invitation')
def on_invitation_saved(sender, instance, created, **kwargs):
    from notifications.services import create_notification
    from django.urls import reverse

    if created:
        # New invitation → notify receiver
        create_notification(
            recipient=instance.receiver,
            actor=instance.sender,
            verb='connection_request',
            target=instance,
            target_url=reverse('invitation_list'),
            preview=f"{instance.sender.username} sent you a connection request.",
        )
    elif instance.status == 'accepted':
        # Accepted → notify sender
        create_notification(
            recipient=instance.sender,
            actor=instance.receiver,
            verb='connection_accepted',
            target=instance,
            target_url=reverse('invitation_list'),
            preview=f"{instance.receiver.username} accepted your connection request.",
        )


# ---------------------------------------------------------------------------
# Solutions → solution_accepted
# ---------------------------------------------------------------------------

@receiver(post_save, sender='solutions.Solution')
def on_solution_saved(sender, instance, created, **kwargs):
    if not created and instance.is_accepted:
        from notifications.services import create_notification
        from django.urls import reverse

        create_notification(
            recipient=instance.user,
            actor=instance.problem.user,
            verb='solution_accepted',
            target=instance,
            target_url=reverse('solution_list', kwargs={'problem_id': instance.problem_id}),
            preview=f"Your solution to \"{instance.problem.title}\" was accepted!",
        )


# ---------------------------------------------------------------------------
# Votes → solution_upvoted
# ---------------------------------------------------------------------------

@receiver(post_save, sender='solutions.Vote')
def on_vote_created(sender, instance, created, **kwargs):
    if created:
        from notifications.services import create_notification
        from django.urls import reverse

        create_notification(
            recipient=instance.solution.user,
            actor=instance.user,
            verb='solution_upvoted',
            target=instance.solution,
            target_url=reverse('solution_list', kwargs={'problem_id': instance.solution.problem_id}),
            preview=f"{instance.user.username} upvoted your solution.",
        )


# ---------------------------------------------------------------------------
# Comments → solution_commented / comment_replied
# ---------------------------------------------------------------------------

@receiver(post_save, sender='solutions.Comment')
def on_comment_created(sender, instance, created, **kwargs):
    if not created:
        return

    from notifications.services import create_notification
    from django.urls import reverse

    target_url = reverse('solution_list', kwargs={'problem_id': instance.solution.problem_id})

    if instance.parent:
        # Reply — notify the parent comment author
        create_notification(
            recipient=instance.parent.user,
            actor=instance.user,
            verb='comment_replied',
            target=instance,
            target_url=target_url,
            preview=f"{instance.user.username} replied to your comment.",
        )
    else:
        # Top-level comment — notify solution author
        create_notification(
            recipient=instance.solution.user,
            actor=instance.user,
            verb='solution_commented',
            target=instance,
            target_url=target_url,
            preview=f"{instance.user.username} commented on your solution.",
        )


# ---------------------------------------------------------------------------
# Applications → application_received / accepted / rejected
# ---------------------------------------------------------------------------

@receiver(post_save, sender='opportunities.Application')
def on_application_saved(sender, instance, created, **kwargs):
    from notifications.services import create_notification
    from django.urls import reverse

    if created:
        # Notify opportunity owner
        create_notification(
            recipient=instance.opportunity.user,
            actor=instance.user,
            verb='application_received',
            target=instance,
            target_url=reverse('application_list'),
            preview=f"{instance.user.username} applied to \"{instance.opportunity.title}\".",
        )
    else:
        # Notify applicant of status change
        if instance.status == 'accepted':
            create_notification(
                recipient=instance.user,
                actor=instance.opportunity.user,
                verb='application_accepted',
                target=instance,
                target_url=reverse('my_applications'),
                preview=f"Your application to \"{instance.opportunity.title}\" was accepted!",
            )
        elif instance.status == 'rejected':
            create_notification(
                recipient=instance.user,
                actor=instance.opportunity.user,
                verb='application_rejected',
                target=instance,
                target_url=reverse('my_applications'),
                preview=f"Your application to \"{instance.opportunity.title}\" was not selected.",
            )


# ---------------------------------------------------------------------------
# Messages → new_message
# ---------------------------------------------------------------------------

@receiver(post_save, sender='opportunities.Message')
def on_message_created(sender, instance, created, **kwargs):
    if created:
        from notifications.services import create_notification
        from django.urls import reverse

        create_notification(
            recipient=instance.receiver,
            actor=instance.sender,
            verb='new_message',
            target=instance,
            target_url=reverse('chat', kwargs={'username': instance.sender.username}),
            preview=f"{instance.sender.username} sent you a message.",
        )
