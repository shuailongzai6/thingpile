from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

register = template.Library()
formatter = HtmlFormatter(nowrap=True)


def highlight_code(code, language, attrs):
    try:
        return highlight(code, get_lexer_by_name(language), formatter)
    except ClassNotFound:
        return ""


renderer = MarkdownIt(
    "commonmark", {"html": False, "breaks": True, "highlight": highlight_code}
).enable("table")


@register.filter
def markdown(value):
    return mark_safe(renderer.render(str(value)))


@register.filter
def tone(obj):
    """Give each person or project the same avatar color everywhere."""
    return obj.pk % 4
