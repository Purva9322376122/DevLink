"""
Notification system tests — model, service, selectors, views.
"""
import pytest
from django.urls import reverse


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationModel:

    def test_create_notification(self, user_factory):
        from notifications.models import Notification
        actor = user_factory(username='actor')
        recipient = user_factory(username='recipient', email='r@x.com')
        n = Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb='solution_upvoted',
            preview='actor upvoted your solution.',
            target_url='/solutions/1/',
        )
        assert n.id is not None
        assert not n.is_read
        assert str(n) == '[solution_upvoted] → recipient'

    def test_mark_read_method(self, user_factory):
        from notifications.models import Notification
        user = user_factory(username='u1')
        n = Notification.objects.create(recipient=user, verb='new_message', preview='hi')
        assert not n.is_read
        n.mark_read()
        n.refresh_from_db()
        assert n.is_read

    def test_ordering_newest_first(self, user_factory):
        from notifications.models import Notification
        user = user_factory(username='u2')
        n1 = Notification.objects.create(recipient=user, verb='new_message', preview='first')
        n2 = Notification.objects.create(recipient=user, verb='new_message', preview='second')
        qs = list(Notification.objects.filter(recipient=user))
        assert qs[0].id == n2.id


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationService:

    def test_create_notification_service(self, user_factory):
        from notifications.services import create_notification
        from notifications.models import Notification
        actor = user_factory(username='svc_actor')
        recipient = user_factory(username='svc_recipient', email='svc@x.com')
        create_notification(recipient=recipient, actor=actor, verb='connection_request',
                            preview='svc_actor sent a request.')
        assert Notification.objects.filter(recipient=recipient, verb='connection_request').count() == 1

    def test_no_self_notification(self, user_factory):
        from notifications.services import create_notification
        from notifications.models import Notification
        user = user_factory(username='selfuser', email='self@x.com')
        create_notification(recipient=user, actor=user, verb='solution_upvoted', preview='x')
        assert Notification.objects.filter(recipient=user).count() == 0

    def test_mark_notification_read(self, user_factory):
        from notifications.models import Notification
        from notifications.services import mark_notification_read
        user = user_factory(username='mru', email='mru@x.com')
        n = Notification.objects.create(recipient=user, verb='new_message', preview='msg')
        result = mark_notification_read(n.id, user)
        assert result is True
        n.refresh_from_db()
        assert n.is_read

    def test_mark_all_read(self, user_factory):
        from notifications.models import Notification
        from notifications.services import mark_all_read
        user = user_factory(username='mar', email='mar@x.com')
        Notification.objects.create(recipient=user, verb='new_message', preview='a')
        Notification.objects.create(recipient=user, verb='new_message', preview='b')
        count = mark_all_read(user)
        assert count == 2
        assert Notification.objects.filter(recipient=user, is_read=False).count() == 0

    def test_get_unread_count(self, user_factory):
        from notifications.models import Notification
        from notifications.services import get_unread_count
        user = user_factory(username='guc', email='guc@x.com')
        Notification.objects.create(recipient=user, verb='new_message', preview='a')
        Notification.objects.create(recipient=user, verb='new_message', preview='b', is_read=True)
        assert get_unread_count(user) == 1


# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationSelectors:

    def test_get_notifications_returns_all(self, user_factory):
        from notifications.models import Notification
        from notifications.selectors import get_notifications
        user = user_factory(username='sel1', email='sel1@x.com')
        Notification.objects.create(recipient=user, verb='new_message', preview='x')
        Notification.objects.create(recipient=user, verb='new_message', preview='y')
        assert get_notifications(user).count() == 2

    def test_get_notifications_unread_only(self, user_factory):
        from notifications.models import Notification
        from notifications.selectors import get_notifications
        user = user_factory(username='sel2', email='sel2@x.com')
        Notification.objects.create(recipient=user, verb='new_message', preview='x')
        Notification.objects.create(recipient=user, verb='new_message', preview='y', is_read=True)
        assert get_notifications(user, unread_only=True).count() == 1

    def test_get_recent_notifications_limit(self, user_factory):
        from notifications.models import Notification
        from notifications.selectors import get_recent_notifications
        user = user_factory(username='sel3', email='sel3@x.com')
        for i in range(15):
            Notification.objects.create(recipient=user, verb='new_message', preview=f'msg{i}')
        assert len(list(get_recent_notifications(user, limit=5))) == 5


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotificationViews:

    def test_notification_list_requires_login(self, client):
        url = reverse('notifications:list')
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_notification_list_returns_200(self, auth_client):
        url = reverse('notifications:list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_mark_all_read_view(self, auth_client, user):
        from notifications.models import Notification
        Notification.objects.create(recipient=user, verb='new_message', preview='x')
        url = reverse('notifications:mark_all_read')
        response = auth_client.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data['unread_count'] == 0

    def test_mark_single_read_view(self, auth_client, user):
        from notifications.models import Notification
        n = Notification.objects.create(recipient=user, verb='new_message', preview='x')
        url = reverse('notifications:mark_read', kwargs={'pk': n.pk})
        response = auth_client.post(url)
        assert response.status_code == 200
        n.refresh_from_db()
        assert n.is_read
