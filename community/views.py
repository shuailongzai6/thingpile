from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import ProjectForm, ReplyForm, SignUpForm, TopicForm
from .models import Project, Topic
from .queries import category_counts, project_list, topic_list


def return_to(request, fallback):
    target = request.POST.get("next", request.GET.get("next", ""))
    if target and url_has_allowed_host_and_scheme(
        target, {request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return fallback


def member_action(view):
    """Keep a login redirect out of the small HTMX vote target."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            response = redirect_to_login(return_to(request, reverse("forum")))
            if request.headers.get("HX-Request"):
                return HttpResponse(headers={"HX-Redirect": response.url})
            return response
        return view(request, *args, **kwargs)

    return wrapped


def forum(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "active")
    topics = topic_list(request.user)
    selected_project = None
    if q:
        topics = topics.filter(
            Q(title__icontains=q) | Q(body__icontains=q) | Q(project__name__icontains=q)
        )
    if category:
        topics = topics.filter(category=category)
    if project_id := request.GET.get("project"):
        selected_project = (
            get_object_or_404(Project, pk=project_id)
            if project_id.isdecimal()
            else None
        )
        topics = (
            topics.filter(project=selected_project)
            if selected_project
            else topics.none()
        )
    ordering = {
        "active": "-last_activity",
        "latest": "-created_at",
        "top": "-like_count",
    }
    topics = topics.order_by(ordering.get(sort, "-last_activity"), "-pk")
    return render(
        request,
        "community/forum.html",
        {
            "page_obj": Paginator(topics, 12).get_page(request.GET.get("page")),
            "q": q,
            "category": category,
            "sort": sort,
            "categories": category_counts(Topic),
            "selected_project": selected_project,
            "project_options": Project.objects.order_by("name"),
        },
    )


def projects(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "latest")
    items = project_list(request.user)
    if q:
        items = items.filter(
            Q(name__icontains=q)
            | Q(tagline__icontains=q)
            | Q(description__icontains=q)
            | Q(tools__icontains=q)
        )
    if category:
        items = items.filter(category=category)
    ordering = "-vote_count" if sort == "top" else "-created_at"
    return render(
        request,
        "community/projects.html",
        {
            "page_obj": Paginator(items.order_by(ordering, "-pk"), 12).get_page(
                request.GET.get("page")
            ),
            "q": q,
            "category": category,
            "sort": sort,
            "categories": category_counts(Project),
        },
    )


def project_detail(request, pk):
    project = get_object_or_404(project_list(request.user), pk=pk)
    topics = (
        topic_list(request.user)
        .filter(project=project)
        .order_by("-last_activity", "-pk")
    )
    page = Paginator(topics, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "community/project_detail.html",
        {
            "project": project,
            "topics": page,
            "page_obj": page,
            "topic_count": page.paginator.count,
        },
    )


def topic_detail(request, pk):
    topic = get_object_or_404(topic_list(request.user), pk=pk)
    return render_topic(request, topic, ReplyForm())


def render_topic(request, topic, reply_form):
    replies = topic.replies.select_related("author")
    return render(
        request,
        "community/topic_detail.html",
        {
            "topic": topic,
            "replies": replies,
            "reply_form": reply_form,
            "page_url": topic.get_absolute_url(),
            "categories": category_counts(Topic),
        },
    )


@login_required
def project_create(request):
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(
            request, _("Your project is live. Start a discussion to tell its story.")
        )
        return redirect(project)
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "title": _("Share your project"),
            "subtitle": _("Give your work a home in the community."),
            "submit_label": _("Publish project"),
            "back_url": reverse("projects"),
        },
    )


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    form = ProjectForm(
        request.POST if request.method == "POST" else None, instance=project
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Project updated."))
        return redirect(project)
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "title": _("Edit project"),
            "subtitle": project.name,
            "submit_label": _("Save changes"),
            "back_url": project.get_absolute_url(),
        },
    )


@login_required
def topic_create(request):
    initial = {}
    if (project_id := request.GET.get("project")) and project_id.isdecimal():
        initial["project"] = get_object_or_404(Project, pk=project_id)
    form = TopicForm(
        request.POST if request.method == "POST" else None, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        topic = form.save(commit=False)
        topic.author = request.user
        topic.save()
        messages.success(request, _("Your discussion is live."))
        return redirect(topic)
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "title": _("Start a discussion"),
            "subtitle": _("A question, a small win, or something worth talking about."),
            "submit_label": _("Publish discussion"),
            "back_url": initial["project"].get_absolute_url()
            if initial
            else reverse("forum"),
        },
    )


@login_required
def topic_edit(request, pk):
    topic = get_object_or_404(Topic, pk=pk, author=request.user)
    form = TopicForm(request.POST if request.method == "POST" else None, instance=topic)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Discussion updated."))
        return redirect(topic)
    return render(
        request,
        "community/form.html",
        {
            "form": form,
            "title": _("Edit discussion"),
            "subtitle": topic.title,
            "submit_label": _("Save changes"),
            "back_url": topic.get_absolute_url(),
        },
    )


@require_POST
@member_action
def reply_create(request, pk):
    topic = get_object_or_404(topic_list(request.user), pk=pk)
    form = ReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.topic = topic
        reply.author = request.user
        reply.save()
        return redirect(f"{topic.get_absolute_url()}#reply-{reply.pk}")
    return render_topic(request, topic, form)


@require_POST
@member_action
def project_vote(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.votes.filter(pk=request.user.pk).exists():
        project.votes.remove(request.user)
    else:
        project.votes.add(request.user)
    if request.headers.get("HX-Request"):
        return render(
            request,
            "partials/vote.html",
            {"project": project_list(request.user).get(pk=pk)},
        )
    return redirect(return_to(request, project.get_absolute_url()))


@require_POST
@member_action
def topic_like(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if topic.likes.filter(pk=request.user.pk).exists():
        topic.likes.remove(request.user)
    else:
        topic.likes.add(request.user)
    if request.headers.get("HX-Request"):
        return render(
            request,
            "partials/like.html",
            {"topic": topic_list(request.user).get(pk=pk)},
        )
    return redirect(return_to(request, topic.get_absolute_url()))


def signup(request):
    if request.user.is_authenticated:
        return redirect("forum")
    form = SignUpForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, _("Welcome to Buildroom. Make yourself at home."))
        return redirect(return_to(request, reverse("forum")))
    return render(
        request,
        "registration/signup.html",
        {"form": form, "next": return_to(request, "")},
    )
