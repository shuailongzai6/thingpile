from django.db.models import BooleanField, Count, Exists, Max, OuterRef, Value
from django.db.models.functions import Coalesce

from .models import Project, Topic


def project_list(user):
    voted = (
        Exists(
            Project.votes.through.objects.filter(
                project_id=OuterRef("pk"), user_id=user.pk
            )
        )
        if user.is_authenticated
        else Value(False, output_field=BooleanField())
    )
    return Project.objects.select_related("owner").annotate(
        vote_count=Count("votes", distinct=True),
        discussion_count=Count("topics", distinct=True),
        has_voted=voted,
    )


def topic_list(user):
    liked = (
        Exists(
            Topic.likes.through.objects.filter(topic_id=OuterRef("pk"), user_id=user.pk)
        )
        if user.is_authenticated
        else Value(False, output_field=BooleanField())
    )
    return Topic.objects.select_related("author", "project").annotate(
        reply_count=Count("replies", distinct=True),
        like_count=Count("likes", distinct=True),
        has_liked=liked,
        last_activity=Coalesce(Max("replies__created_at"), "created_at"),
    )


def category_counts(model):
    counts = dict(
        model.objects.order_by().values_list("category").annotate(total=Count("pk"))
    )
    return [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in model.Category.choices
    ]
