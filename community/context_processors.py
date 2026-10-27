from django.contrib.auth.models import User

from .models import Project, Topic


def community_context(request):
    return {
        "current_nav": "projects" if request.path.startswith("/projects") else "forum",
        "community_stats": {
            "projects": Project.objects.count(),
            "topics": Topic.objects.count(),
            "members": User.objects.filter(is_active=True).count(),
        },
        "recent_projects": Project.objects.select_related("owner")[:3],
    }
