from django.contrib import admin

from .models import Project, Reply, Topic


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "category", "created_at"]
    list_filter = ["category"]
    search_fields = ["name", "tagline"]
    autocomplete_fields = ["owner"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "project", "created_at"]
    list_filter = ["category"]
    search_fields = ["title", "body"]
    autocomplete_fields = ["author", "project"]


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ["topic", "author", "created_at"]
    search_fields = ["body"]
    autocomplete_fields = ["author", "topic"]
