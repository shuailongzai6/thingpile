from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()
renderer = MarkdownIt("commonmark", {"html": False, "breaks": True}).enable("table")


@register.filter
def markdown(value):
    return mark_safe(renderer.render(str(value)))
