from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Project, Reply, Topic


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email"]


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "tagline",
            "category",
            "description",
            "tools",
            "demo_url",
            "repository_url",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": _("What is your project called?")}
            ),
            "tagline": forms.TextInput(
                attrs={"placeholder": _("What does it help people do?")}
            ),
            "description": forms.Textarea(attrs={"rows": 9}),
            "tools": forms.TextInput(
                attrs={"placeholder": "Claude Code, Cursor, Lovable"}
            ),
        }
        help_texts = {
            "description": _(
                "Describe the idea, how you built it, and what you learned. Markdown supported."
            ),
            "tools": _("Separate tools with commas."),
            "repository_url": _(
                "Optional. Link to your repository on GitHub, GitLab, or another host."
            ),
            "demo_url": _("Optional. Add a live website or demo people can try."),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["title", "category", "project", "body"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": _("What would you like to talk about?")}
            ),
            "body": forms.Textarea(attrs={"rows": 10}),
        }
        help_texts = {
            "project": _(
                "Optional. This post will also appear in the project's discussion area."
            ),
            "body": _(
                "Markdown supported. Share context, ask a question, or tell your story."
            ),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 4, "placeholder": _("Add to the conversation…")}
            )
        }
