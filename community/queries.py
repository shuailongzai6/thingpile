from django.db.models import (
    BooleanField,
    Count,
    Exists,
    Func,
    IntegerField,
    OuterRef,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce

from .models import Project, Reply, Topic


def count(rows):
    """Count related rows in a subquery, so several counts never multiply joins."""
    return Subquery(
        rows.order_by().values(
            n=Func("pk", function="COUNT", output_field=IntegerField())
        )
    )


def project_list(user):
    votes = Project.votes.through.objects.filter(project=OuterRef("pk"))
    voted = (
        Exists(votes.filter(user_id=user.pk))
        if user.is_authenticated
        else Value(False, output_field=BooleanField())
    )
    return Project.objects.select_related("owner").annotate(
        vote_count=count(votes),
        discussion_count=count(Topic.objects.filter(project=OuterRef("pk"))),
        has_voted=voted,
    )


def topic_list(user):
    likes = Topic.likes.through.objects.filter(topic=OuterRef("pk"))
    replies = Reply.objects.filter(topic=OuterRef("pk"))
    liked = (
        Exists(likes.filter(user_id=user.pk))
        if user.is_authenticated
        else Value(False, output_field=BooleanField())
    )
    return Topic.objects.select_related("author", "project").annotate(
        reply_count=count(replies),
        like_count=count(likes),
        has_liked=liked,
        last_activity=Coalesce(
            Subquery(replies.order_by("-created_at").values("created_at")[:1]),
            "created_at",
        ),
    )


def category_counts(model):
    counts = dict(
        model.objects.order_by().values_list("category").annotate(total=Count("pk"))
    )
    return [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in model.Category.choices
    ]
