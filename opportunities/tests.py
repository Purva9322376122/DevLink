"""
Opportunities smoke tests.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestOpportunityListView:

    def test_opportunity_list_returns_200(self, client):
        url = reverse('opportunity_list')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestOpportunityDetailView:

    def test_opportunity_detail_404_for_nonexistent(self, client, db):
        url = reverse('opportunity_detail', kwargs={'id': 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_opportunity_detail_200_for_existing(self, client, user):
        from opportunities.models import Opportunity
        opp = Opportunity.objects.create(
            user=user,
            title='Backend Developer',
            description='Looking for a Django developer.',
            required_skills='Python, Django',
        )
        url = reverse('opportunity_detail', kwargs={'id': opp.id})
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCreateOpportunityView:

    def test_create_opportunity_requires_login(self, client, db):
        url = reverse('create_opportunity')
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_create_opportunity_returns_200_authenticated(self, auth_client):
        url = reverse('create_opportunity')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_create_opportunity_post(self, auth_client, user):
        from opportunities.models import Opportunity
        url = reverse('create_opportunity')
        response = auth_client.post(url, {
            'title': 'Test Opportunity',
            'description': 'We are looking for developers.',
            'required_skills': 'Python, REST API',
        })
        assert response.status_code in (200, 302)
        assert Opportunity.objects.filter(title='Test Opportunity', user=user).exists()


@pytest.mark.django_db
class TestSelectors:

    def test_get_conversations_returns_empty_for_new_user(self, user):
        from opportunities.selectors import get_conversations
        result = get_conversations(user)
        assert result == []


@pytest.mark.django_db
class TestChatMessageModel:
    """Test Message model enhancements for real-time chat."""

    def test_message_has_delivery_fields(self, user, user_two):
        """Test Message model has delivery and read receipt fields."""
        from opportunities.models import Message
        msg = Message.objects.create(
            sender=user,
            receiver=user_two,
            content="Hello",
        )
        assert hasattr(msg, 'is_delivered')
        assert hasattr(msg, 'is_read')
        assert hasattr(msg, 'file_url')
        assert hasattr(msg, 'file_type')
        assert hasattr(msg, 'is_pinned')
        assert hasattr(msg, 'is_edited')
        assert msg.is_delivered is False
        assert msg.is_read is False

    def test_message_with_file_attachment(self, user, user_two):
        """Test Message can store file metadata."""
        from opportunities.models import Message
        msg = Message.objects.create(
            sender=user,
            receiver=user_two,
            content="Check this file",
            file_url="https://example.com/file.pdf",
            file_type="file",
        )
        assert msg.file_url == "https://example.com/file.pdf"
        assert msg.file_type == "file"

    def test_message_mark_delivered(self, user, user_two):
        """Test marking message as delivered."""
        from opportunities.models import Message
        msg = Message.objects.create(
            sender=user,
            receiver=user_two,
            content="Test",
        )
        assert msg.is_delivered is False
        msg.mark_delivered()
        assert msg.is_delivered is True

    def test_message_mark_read(self, user, user_two):
        """Test marking message as read."""
        from opportunities.models import Message
        msg = Message.objects.create(
            sender=user,
            receiver=user_two,
            content="Test",
        )
        assert msg.is_read is False
        msg.mark_read()
        assert msg.is_read is True


@pytest.mark.django_db
class TestChatServices:
    """Test chat service functions."""

    def test_create_message_service(self, user, user_two):
        """Test creating a message via service."""
        from opportunities.chat_services import create_message
        msg = create_message(user, user_two, "Hello from service")
        assert msg.sender == user
        assert msg.receiver == user_two
        assert msg.content == "Hello from service"
        assert msg.is_delivered is False

    def test_mark_message_delivered_service(self, user, user_two):
        """Test marking message as delivered via service."""
        from opportunities.chat_services import create_message, mark_message_delivered
        msg = create_message(user, user_two, "Test")
        delivered_msg = mark_message_delivered(msg.id)
        assert delivered_msg.is_delivered is True

    def test_mark_conversation_read_service(self, user, user_two):
        """Test marking all messages in conversation as read."""
        from opportunities.chat_services import create_message, mark_conversation_read
        create_message(user_two, user, "Message 1")
        create_message(user_two, user, "Message 2")
        
        count = mark_conversation_read(user, user_two)
        assert count == 2
        
        # Verify messages are marked as read
        from opportunities.models import Message
        unread = Message.objects.filter(
            receiver=user,
            sender=user_two,
            is_read=False
        ).count()
        assert unread == 0

    def test_get_connection_check(self, user, user_two):
        """Test checking if two users are connected."""
        from opportunities.models import Connection
        from opportunities.chat_services import get_connection_check
        
        # No connection yet
        assert not get_connection_check(user, user_two)
        
        # Create connection
        Connection.objects.create(user1=user, user2=user_two)
        
        # Should now be connected (bidirectional)
        assert get_connection_check(user, user_two)
        assert get_connection_check(user_two, user)


@pytest.mark.django_db
class TestChatSelectors:
    """Test chat data selector functions."""

    def test_get_messages_between(self, user, user_two):
        """Test getting messages between two users."""
        from opportunities.chat_selectors import get_messages_between
        from opportunities.chat_services import create_message
        
        msg1 = create_message(user, user_two, "First")
        msg2 = create_message(user_two, user, "Second")
        
        messages = get_messages_between(user, user_two)
        assert len(messages) == 2
        assert messages[0].content == "First"
        assert messages[1].content == "Second"

    def test_get_unread_count(self, user, user_two):
        """Test getting unread message count."""
        from opportunities.chat_selectors import get_unread_count
        from opportunities.chat_services import create_message
        
        create_message(user_two, user, "Unread 1")
        create_message(user_two, user, "Unread 2")
        create_message(user, user_two, "Sent")  # Not counted in user's unread
        
        count = get_unread_count(user, user_two)
        assert count == 2

    def test_get_conversations(self, user, user_two, user_three):
        """Test getting conversation list for a user."""
        from opportunities.chat_selectors import get_conversations
        from opportunities.chat_services import create_message
        
        create_message(user, user_two, "Hello")
        create_message(user_three, user, "Hi there")
        
        conversations = get_conversations(user)
        assert len(conversations) == 2
        # Most recent should be first
        assert conversations[0]['other_user'].id in [user_two.id, user_three.id]

