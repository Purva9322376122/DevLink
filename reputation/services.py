from django.db import transaction
from django.contrib.auth.models import User
from .models import ReputationEvent, Badge, UserBadge, get_level_for_score, LEVEL_THRESHOLDS


def award_reputation(user: User, event_type: str, description: str = '') -> ReputationEvent:
    """Award or deduct reputation atomically. Returns the created event."""
    delta = ReputationEvent.DELTA_MAP.get(event_type, 0)
    if delta == 0:
        return None

    with transaction.atomic():
        event = ReputationEvent.objects.create(
            user=user,
            event_type=event_type,
            delta=delta,
            description=description,
        )
        # Update profile score atomically
        from django.db.models import F
        from accounts.models import Profile
        Profile.objects.filter(user=user).update(
            reputation_score=F('reputation_score') + delta
        )

    # Check badge eligibility after commit
    _check_badges(user)
    return event


def _check_badges(user: User) -> None:
    """Award any newly-earned badges to the user."""
    from accounts.models import Profile
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return

    score = profile.reputation_score
    problems = user.problems.count() if hasattr(user, 'problems') else 0
    accepted = user.solutions.filter(is_accepted=True).count() if hasattr(user, 'solutions') else 0

    try:
        from django.db.models import Q
        from opportunities.models import Connection
        connections = Connection.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).count()
    except Exception:
        connections = 0

    _try_award(user, 'first_problem', problems >= 1)
    _try_award(user, 'first_accepted', accepted >= 1)
    _try_award(user, 'rep_100', score >= 100)
    _try_award(user, 'rep_1000', score >= 1000)
    _try_award(user, 'connector', connections >= 10)


def _try_award(user: User, trigger: str, condition: bool) -> None:
    if not condition:
        return
    try:
        badge = Badge.objects.get(trigger=trigger)
        UserBadge.objects.get_or_create(user=user, badge=badge)
    except Badge.DoesNotExist:
        pass


def get_user_level(user: User) -> str:
    from accounts.models import Profile
    try:
        score = Profile.objects.get(user=user).reputation_score
    except Profile.DoesNotExist:
        score = 0
    return get_level_for_score(score)
