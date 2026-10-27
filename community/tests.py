import re

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Project, Reply, Topic
from .queries import project_list, topic_list
from .templatetags.community_tags import excerpt, markdown


class CommunityWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            "maker", password="a-real-test-password-47"
        )
        cls.reader = User.objects.create_user(
            "reader", password="a-real-test-password-48"
        )
        cls.project = Project.objects.create(
            owner=cls.owner,
            name="Garden notes",
            tagline="A small writing space",
            description="Built for a slower internet.",
            category="productivity",
        )
        cls.topic = Topic.objects.create(
            author=cls.owner,
            project=cls.project,
            title="How should offline sync work?",
            body="Looking for real-world experience.",
            category="help",
        )

    def test_signup_publish_project_discuss_and_reply(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmaker",
                "email": "maker@example.com",
                "password1": "a-new-account-password-49",
                "password2": "a-new-account-password-49",
            },
        )
        self.assertRedirects(response, reverse("forum"))
        response = self.client.post(
            reverse("project_create"),
            {
                "name": "Pocket garden",
                "tagline": "A garden in your pocket",
                "description": "## The idea\nA place for small notes.",
                "category": "creative",
                "tools": "Cursor, Claude Code",
                "repository_url": "https://github.com/example/garden",
            },
        )
        project = Project.objects.get(name="Pocket garden")
        self.assertRedirects(response, project.get_absolute_url())
        self.assertEqual(project.owner.username, "newmaker")
        response = self.client.post(
            reverse("topic_create"),
            {
                "title": "What should we build next?",
                "body": "Would offline mode be helpful?",
                "category": "help",
                "project": project.pk,
            },
        )
        topic = Topic.objects.get(title="What should we build next?")
        self.assertRedirects(response, topic.get_absolute_url())
        self.assertContains(self.client.get(reverse("forum")), topic.title)
        self.assertContains(self.client.get(project.get_absolute_url()), topic.title)
        self.assertContains(self.client.get(topic.get_absolute_url()), project.name)
        response = self.client.post(
            reverse("reply_create", args=[topic.pk]),
            {"body": "Yes, especially on trains."},
        )
        reply = topic.replies.get()
        self.assertRedirects(response, f"{topic.get_absolute_url()}#reply-{reply.pk}")
        self.assertEqual(reply.author, project.owner)

    def test_invalid_reply_keeps_language_and_like_returns_on_topic_page(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse("reply_create", args=[self.topic.pk]), {"body": "   "}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.topic.replies.exists())
        return_urls = re.findall(
            r'name="next"[^>]*value="([^"]+)"', response.content.decode()
        )
        topic_url = self.topic.get_absolute_url()
        self.assertTrue(return_urls)
        self.assertEqual(set(return_urls), {topic_url})
        response = self.client.post(
            reverse("set_language"),
            {"language": "zh-hans", "next": return_urls[0]},
        )
        self.assertRedirects(response, topic_url)
        response = self.client.post(
            reverse("topic_like", args=[self.topic.pk]), {"next": return_urls[1]}
        )
        self.assertRedirects(response, topic_url)
        response = self.client.post(
            reverse("topic_like", args=[self.topic.pk]),
            {"next": return_urls[1]},
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(response, f'name="next" value="{topic_url}"')

    def test_only_authors_can_edit(self):
        self.client.force_login(self.reader)
        self.assertEqual(
            self.client.post(
                reverse("project_edit", args=[self.project.pk]), {"name": "Changed"}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("topic_edit", args=[self.topic.pk]), {"title": "Changed"}
            ).status_code,
            404,
        )
        self.project.refresh_from_db()
        self.topic.refresh_from_db()
        self.assertEqual(self.project.name, "Garden notes")
        self.assertEqual(self.topic.title, "How should offline sync work?")

    def test_votes_toggle_and_counts_do_not_multiply_with_discussions(self):
        Topic.objects.create(
            author=self.owner,
            project=self.project,
            title="Another thread",
            body="A second discussion",
        )
        Reply.objects.create(author=self.owner, topic=self.topic, body="First reply")
        Reply.objects.create(author=self.reader, topic=self.topic, body="Second reply")
        self.client.force_login(self.reader)
        for url, relation in [
            (reverse("project_vote", args=[self.project.pk]), self.project.votes),
            (reverse("topic_like", args=[self.topic.pk]), self.topic.likes),
        ]:
            response = self.client.post(url, HTTP_HX_REQUEST="true")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(relation.count(), 1)
            response = self.client.post(url, HTTP_HX_REQUEST="true")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(relation.count(), 0)
        self.project.votes.add(self.owner, self.reader)
        self.topic.likes.add(self.reader)
        self.assertEqual(
            project_list(self.reader).get(pk=self.project.pk).vote_count, 2
        )
        self.assertEqual(topic_list(self.reader).get(pk=self.topic.pk).like_count, 1)
        self.assertEqual(topic_list(self.reader).get(pk=self.topic.pk).reply_count, 2)

    def test_filtering_and_search_keep_project_discussions_connected(self):
        unrelated = Topic.objects.create(
            author=self.owner,
            title="Weekend plans",
            body="What are you reading?",
            category="general",
        )
        response = self.client.get(reverse("forum"), {"project": self.project.pk})
        self.assertContains(response, self.topic.title)
        self.assertNotContains(response, unrelated.title)
        self.assertContains(
            self.client.get(reverse("projects"), {"q": "Garden"}), self.project.tagline
        )
        filtered = self.client.get(reverse("projects"), {"category": "tools"})
        self.assertEqual(filtered.context["page_obj"].paginator.count, 0)

    def test_anonymous_mutations_and_expired_htmx_session(self):
        response = self.client.post(
            reverse("reply_create", args=[self.topic.pk]),
            {"body": "Anonymous reply", "next": self.topic.get_absolute_url()},
        )
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.topic.get_absolute_url()}"
        )
        self.assertEqual(self.topic.replies.count(), 0)
        response = self.client.post(
            reverse("project_vote", args=[self.project.pk]),
            {"next": self.project.get_absolute_url()},
            HTTP_HX_REQUEST="true",
        )
        self.assertIn(reverse("login"), response.headers["HX-Redirect"])
        self.assertEqual(self.project.votes.count(), 0)
        self.assertEqual(
            self.client.get(
                reverse("project_vote", args=[self.project.pk])
            ).status_code,
            405,
        )

    def test_csrf_is_required_and_external_return_url_is_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.reader)
        self.assertEqual(
            csrf_client.post(
                reverse("project_vote", args=[self.project.pk])
            ).status_code,
            403,
        )
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse("project_vote", args=[self.project.pk]),
            {"next": "https://unrelated.example/"},
        )
        self.assertRedirects(response, self.project.get_absolute_url())

    def test_markdown_formats_code_without_executing_html_or_javascript(self):
        html = markdown(
            '**Hello**\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n\n```python\nprint("hello")\n```'
        )
        self.assertIn("<strong>Hello</strong>", html)
        self.assertIn('class="language-python"', html)
        self.assertIn('<span class="nb">print</span>', html)
        self.assertNotIn("<script>", html)
        self.assertNotIn('href="javascript:', html)
        response = self.client.post(
            reverse("markdown_preview", args=["body"]), {"body": "**Hi**"}
        )
        self.assertContains(response, "<strong>Hi</strong>")
        self.assertEqual(
            excerpt('**Hello**\n\n```python\nprint("hello")\n```'), "Hello"
        )
        self.assertIn('loading="lazy"', markdown("![shot](https://example.com/a.png)"))

    def test_language_switch_is_persistent_and_does_not_translate_user_content(self):
        response = self.client.post(
            reverse("set_language"), {"language": "zh-hans", "next": reverse("forum")}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("forum"))
        self.assertContains(response, 'lang="zh-hans"')
        self.assertContains(response, "论坛")
        self.assertContains(response, self.topic.title)
        self.client.post(
            reverse("set_language"), {"language": "en", "next": reverse("forum")}
        )
        self.assertContains(self.client.get(reverse("forum")), 'lang="en"')
