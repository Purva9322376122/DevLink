"""
Tests for the reputation app.
"""
import pytest
from django.contrib.auth.models import User

from accounts.models import Profile
from reputation.models import (
    Badge,
    ReputationEvent,
    UserBadge,
    get_level_for_score,
    LEVEL_THRESHOLDS,
)
from reputation.services import award_reputation, get_user_level
from reputation.selectors import (
    get_reputation_history,
    get_user_badges,
    get_leaderboard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    u = User.objects.create_user(username='reputester', password='pass123', email='rep@test.com')
    Profile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def badge(db):
    return Badge.objects.create(
        name='Test Badge',
        slug='test-badge',
        description='A test badge',
        icon='bi-award',
        trigger='rep_100',
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReputationEventModel:
    def test_str_representation(self, user):
        event = ReputationEvent.objects.create(
            user=user,
            event_type='problem_posted',
            delta=5,
            description='Posted a problem',
        )
        assert 'reputester' in str(event)
        assert 'problem_posted' in str(event)
        assert '+5' in str(event)

    def test_negative_delta_str(self, user):
        event = ReputationEvent.objects.create(
            user=user,
            event_type='spam_reported',
            delta=-15,
            description='Spam',
        )
        assert '-15' in str(event)

    def test_delta_map_has_all_event_types(self):
        for event_type, _ in ReputationEvent.EVENT_TYPES:
            assert event_type in ReputationEvent.DELTA_MAP


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAwardReputation:
    def test_creates_event(self, user):
        event = award_reputation(user, 'problem_posted', 'Test problem')
        assert event is not None
        assert event.event_type == 'problem_posted'
        assert event.delta == 5
        assert event.user == user

    def test_positive_delta_increases_score(self, user):
        award_reputation(user, 'solution_accepted', 'Accepted')
        profile = Profile.objects.get(user=user)
        assert profile.reputation_score == 25

    def test_negative_delta_decreases_score(self, user):
        award_reputation(user, 'spam_reported', 'Spam')
        profile = Profile.objects.get(user=user)
        assert profile.reputation_score == -15

    def test_multiple_events_accumulate(self, user):
        award_reputation(user, 'problem_posted', 'P1')
        award_reputation(user, 'solution_upvoted', 'V1')
        profile = Profile.objects.get(user=user)
        assert profile.reputation_score == 5 + 10  # 15

    def test_unknown_event_type_returns_none(self, user):
        result = award_reputation(user, 'nonexistent_event')
        assert result is None

    def test_profile_score_atomic_update(self, user):
        """Profile score must reflect the sum of all events."""
        for _ in range(3):
            award_reputation(user, 'comment_helpful', 'helpful')
        profile = Profile.objects.get(user=user)
        assert profile.reputation_score == 6  # 3 * 2

    def test_event_stored_in_db(self, user):
        award_reputation(user, 'connection_accepted', 'Connected')
        assert ReputationEvent.objects.filter(user=user, event_type='connection_accepted').exists()


# ---------------------------------------------------------------------------
# Level tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetUserLevel:
    def test_beginner_at_zero(self, user):
        assert get_user_level(user) == 'Beginner'

    def test_contributor_at_100(self, user):
        Profile.objects.filter(user=user).update(reputation_score=100)
        assert get_user_level(user) == 'Contributor'

    def test_expert_at_1500(self, user):
        Profile.objects.filter(user=user).update(reputation_score=1500)
        assert get_user_level(user) == 'Expert'

    def test_legend_at_6000(self, user):
        Profile.objects.filter(user=user).update(reputation_score=6000)
        assert get_user_level(user) == 'Legend'

    def test_level_thresholds_are_ordered(self):
        thresholds = [t for t, _ in LEVEL_THRESHOLDS]
        assert thresholds == sorted(thresholds)


class TestGetLevelForScore:
    def test_below_first_threshold(self):
        assert get_level_for_score(0) == 'Beginner'

    def test_exactly_at_threshold(self):
        assert get_level_for_score(100) == 'Contributor'

    def test_between_thresholds(self):
        assert get_level_for_score(200) == 'Contributor'

    def test_negative_score(self):
        assert get_level_for_score(-50) == 'Beginner'

    def test_very_high_score(self):
        assert get_level_for_score(99999) == 'Legend'


# ---------------------------------------------------------------------------
# Badge tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBadgeAwarding:
    def test_rep_100_badge_awarded(self, user, badge):
        # Set score to 100 and trigger via award
        Profile.objects.filter(user=user).update(reputation_score=95)
        award_reputation(user, 'solution_upvoted', 'upvote')  # +10 => 105
        assert UserBadge.objects.filter(user=user, badge=badge).exists()

    def test_badge_not_duplicated(self, user, badge):
        Profile.objects.filter(user=user).update(reputation_score=100)
        award_reputation(user, 'problem_posted')
        award_reputation(user, 'problem_posted')
        count = UserBadge.objects.filter(user=user, badge=badge).count()
        assert count == 1


# ---------------------------------------------------------------------------
# Selector tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSelectors:
    def test_get_reputation_history_empty(self, user):
        result = get_reputation_history(user)
        assert list(result) == []

    def test_get_reputation_history_returns_events(self, user):
        award_reputation(user, 'problem_posted', 'p1')
        award_reputation(user, 'problem_posted', 'p2')
        result = get_reputation_history(user)
        assert len(list(result)) == 2

    def test_get_reputation_history_limit(self, user):
        for _ in range(5):
            award_reputation(user, 'comment_helpful')
        result = get_reputation_history(user, limit=3)
        assert len(list(result)) == 3

    def test_get_user_badges_empty(self, user):
        result = get_user_badges(user)
        assert list(result) == []

    def test_get_user_badges_returns_badge(self, user, badge):
        UserBadge.objects.create(user=user, badge=badge)
        result = get_user_badges(user)
        assert len(list(result)) == 1

    def test_get_leaderboard_ordered_by_score(self, db):
        u1 = User.objects.create_user(username='u1', password='x')
        u2 = User.objects.create_user(username='u2', password='x')
        Profile.objects.get_or_create(user=u1, defaults={'reputation_score': 50})
        Profile.objects.get_or_create(user=u2, defaults={'reputation_score': 200})
        # Update scores directly
        Profile.objects.filter(user=u1).update(reputation_score=50)
        Profile.objects.filter(user=u2).update(reputation_score=200)

        leaderboard = get_leaderboard(limit=10)
        scores = [p.reputation_score for p in leaderboard]
        assert scores == sorted(scores, reverse=True)

    def test_get_leaderboard_respects_limit(self, db):
        for i in range(5):
            u = User.objects.create_user(username=f'lb_user_{i}', password='x')
            Profile.objects.get_or_create(user=u)

        result = get_leaderboard(limit=3)
        assert len(list(result)) == 3
