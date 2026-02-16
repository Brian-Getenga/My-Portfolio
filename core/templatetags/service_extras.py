# Create this file at: core/templatetags/service_extras.py

from django import template

register = template.Library()

@register.filter
def split(value, arg=','):
    """
    Split a string by a delimiter
    Usage: {{ service.technologies|split:',' }}
    """
    if value:
        return [item.strip() for item in str(value).split(arg) if item.strip()]
    return []

@register.filter
def multiply(value, arg):
    """
    Multiply value by arg
    Usage: {{ forloop.counter0|multiply:100 }}
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0