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


def lazy_image(self, tokens, idx, options, env):
    tokens[idx].attrSet("loading", "lazy")
    return self.image(tokens, idx, options, env)


renderer = MarkdownIt(
    "commonmark", {"html": False, "breaks": True, "highlight": highlight_code}
).enable("table")
renderer.add_render_rule("image", lazy_image)


@register.filter
def markdown(value):
    return mark_safe(renderer.render(str(value)))


@register.filter
def excerpt(value):
    """Plain text of a post's prose, leaving out code, tables and images."""
    blocks, in_table = [], False
    for token in renderer.parse(str(value)):
        if token.type in ("table_open", "table_close"):
            in_table = token.type == "table_open"
        elif token.type == "inline" and not in_table:
            # Line breaks carry no content and become spaces.
            blocks.append(
                "".join(
                    child.content or " "
                    for child in token.children
                    if child.type in ("text", "code_inline", "softbreak", "hardbreak")
                )
            )
    return " ".join(" ".join(blocks).split())


@register.filter
def tone(obj):
    """Give each person or project the same avatar color everywhere."""
    return obj.pk % 4
