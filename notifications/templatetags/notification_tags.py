from django import template

register = template.Library()

# Map verb → Bootstrap Icon class
VERB_ICONS = {
    'connection_request': 'bi-person-plus',
    'connection_accepted': 'bi-person-check',
    'new_message': 'bi-chat-dots',
    'solution_commented': 'bi-chat-left-text',
    'comment_replied': 'bi-reply',
    'solution_accepted': 'bi-patch-check',
    'solution_upvoted': 'bi-arrow-up-circle',
    'application_received': 'bi-inbox',
    'application_accepted': 'bi-briefcase-check',
    'application_rejected': 'bi-x-circle',
    'mention': 'bi-at',
    'system': 'bi-info-circle',
}


@register.filter
def notif_icon(verb: str) -> str:
    """Return a Bootstrap Icons class for a notification verb."""
    return VERB_ICONS.get(verb, 'bi-bell')
