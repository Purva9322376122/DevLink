import os
from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Use a custom label to avoid colliding with django.contrib.messages
    label = 'devlink_messages'
    name = 'messages'
    verbose_name = 'Messages'
    path = os.path.dirname(os.path.abspath(__file__))