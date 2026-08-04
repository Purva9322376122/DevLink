from django.contrib.auth.models import User


def get_reputation_history(user: User, limit: int = 20):
    from .models import ReputationEvent
    return ReputationEvent.objects.filter(user=user)[:limit]


def get_user_badges(user: User):
    from .models import UserBadge
    return UserBadge.objects.filter(user=user).select_related('badge')


def get_leaderboard(limit: int = 10):
    from accounts.models import Profile
    return Profile.objects.select_related('user').order_by('-reputation_score')[:limit]
