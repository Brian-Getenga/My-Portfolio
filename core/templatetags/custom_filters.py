from django import template
from django.utils.text import slugify
from django.utils.html import mark_safe
import re

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def split(value, arg):
    """Split a string by the given delimiter."""
    if isinstance(value, str):
        return value.split(arg)
    return value

@register.filter
def split_pairs(value, arg=","):
    """Split a string into key-value pairs.
    
    Args:
        value: String like "key1:value1,key2:value2"
        arg: Delimiters string - first char is pair delimiter, rest is key-value delimiter
    
    Returns:
        List of tuples like [('key1', 'value1'), ('key2', 'value2')]
    """
    if not isinstance(value, str):
        return []
    
    delimiters = str(arg) if arg else ","
    if len(delimiters) >= 2:
        pair_delim = delimiters[0]
        kv_delim = delimiters[1]
    else:
        pair_delim = delimiters if delimiters else ","
        kv_delim = ":"
    
    pairs = []
    for pair in value.split(pair_delim):
        if kv_delim in pair:
            key, val = pair.split(kv_delim, 1)
            pairs.append((key.strip(), val.strip()))
    return pairs

@register.filter
def truncate_words(value, count=10):
    """Truncate text to a specific number of words."""
    try:
        words = str(value).split()
        if len(words) > count:
            return ' '.join(words[:count]) + '...'
        return value
    except (AttributeError, TypeError):
        return value

@register.filter
def to_list(value):
    """Convert string to list."""
    if isinstance(value, str):
        return value.split(',')
    return value

@register.filter
def get_attr(value, arg):
    """Get attribute from object safely."""
    try:
        return getattr(value, arg, '')
    except (AttributeError, TypeError):
        return ''

@register.filter
def highlight(value, term):
    """Highlight text in value."""
    if not term:
        return value
    try:
        pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
        highlighted = pattern.sub(r'<mark>\1</mark>', str(value))
        return mark_safe(highlighted)
    except (AttributeError, TypeError):
        return value

@register.filter
def format_phone(value):
    """Format phone number."""
    if not value:
        return ''
    digits = re.sub(r'\D', '', str(value))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return value

@register.filter
def format_currency(value):
    """Format value as currency."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def not_filter(value):
    """Return the logical NOT of the value."""
    return not value

@register.filter
def equals(value, arg):
    """Check if value equals arg."""
    return value == arg

@register.filter
def trim(value):
    """Remove leading and trailing whitespace."""
    try:
        return str(value).strip()
    except (AttributeError, TypeError):
        return value
