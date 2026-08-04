from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def content_type_id(obj):
    """Return the ContentType ID for the given model instance."""
    return ContentType.objects.get_for_model(obj).pk
