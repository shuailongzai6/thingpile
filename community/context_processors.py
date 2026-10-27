from django.contrib.auth.models import User
from django.utils.functional import SimpleLazyObject

from .models import Project, Topic


def community_context(request):
    return {
        "current_nav": "projects" if request.path.startswith("/projects") else "forum",
        "community_stats": SimpleLazyObject(
            lambda: {
                "projects": Project.objects.count(),
                "topics": Topic.objects.count(),
                "members": User.objects.filter(is_active=True).count(),
            }
        ),
        "recent_projects": Project.objects.all()[:3],
    }
