from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    class Category(models.TextChoices):
        TOOLS = "tools", _("Developer tools")
        PRODUCTIVITY = "productivity", _("Productivity")
        WEBSITES = "websites", _("Websites")
        CREATIVE = "creative", _("Creative")
        LEARNING = "learning", _("Learning")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(_("Project name"), max_length=80)
    tagline = models.CharField(_("One-line description"), max_length=160)
    description = models.TextField(_("About your project"))
    category = models.CharField(_("Category"), max_length=20, choices=Category.choices)
    tools = models.CharField(_("AI tools used"), max_length=200, blank=True)
    demo_url = models.URLField(_("Website or demo URL"), blank=True)
    repository_url = models.URLField(_("Source code URL"), blank=True)
    votes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="upvoted_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", args=[self.pk])

    @property
    def tool_list(self):
        return [tool.strip() for tool in self.tools.split(",") if tool.strip()]


class Topic(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", _("General")
        SHOWCASE = "showcase", _("Show & tell")
        HELP = "help", _("Help")
        BUILDLOG = "buildlog", _("Build logs")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topics"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="topics",
        verbose_name=_("Related project"),
    )
    title = models.CharField(_("Title"), max_length=180)
    body = models.TextField(_("Your post"))
    category = models.CharField(
        _("Category"), max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="liked_topics"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("topic_detail", args=[self.pk])


class Reply(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField(_("Your reply"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"{self.author}: {self.body[:60]}"
