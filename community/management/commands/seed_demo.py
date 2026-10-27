from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from community.models import Project, Reply, Topic

AUTHORS = (
    ("maya", "Maya", "Chen"),
    ("theo", "Theo", "Brooks"),
    ("nora", "Nora", "Park"),
    ("eli", "Eli", "Rivera"),
    ("jules", "Jules", "Morgan"),
    ("sam", "Sam", "Okafor"),
)

PROJECTS = (
    {
        "name": "Paper Lantern",
        "owner": "maya",
        "tagline": "A quieter reading list for ideas you want to come back to.",
        "category": "productivity",
        "tools": "Claude Code, Django, SQLite",
        "description": (
            "Save an article, write one sentence about why it matters, and find it again "
            "when you need it. **Paper Lantern** keeps the note beside the source.\n\n"
            "The first version has topic shelves, a reading queue, and plain-text export. "
            "I used AI to explore the data model, then cut everything that made saving "
            "a link feel like filing paperwork.\n\n"
            "**Next experiment:** a weekly digest of things I saved but never opened."
        ),
        "votes": ("theo", "nora", "eli", "sam"),
    },
    {
        "name": "Pocket Garden",
        "owner": "nora",
        "tagline": "Plant a tiny browser garden, one unhurried moment at a time.",
        "category": "creative",
        "tools": "Cursor, JavaScript, Canvas",
        "description": (
            "A small canvas toy about arranging plants, stones, and empty space. "
            "There are no streaks, scores, or crops to rescue.\n\n"
            "AI helped with the drawing primitives and pointer interactions. "
            "The interesting work was tuning the colors and slowing the animation down. "
            "Your garden stays in your browser, with an image export for sharing.\n\n"
            "**Looking for feedback:** does the touch interaction feel deliberate or fiddly?"
        ),
        "votes": ("maya", "theo", "jules", "sam", "eli"),
    },
    {
        "name": "Tab Tidy",
        "owner": "theo",
        "tagline": "Turn a pile of bookmarks into a few useful collections.",
        "category": "tools",
        "tools": "Claude Code, Python, HTMX",
        "description": (
            "Import a bookmarks file, group links by topic, and keep the handful you "
            "actually use. Suggestions stay editable; nothing gets deleted automatically.\n\n"
            "The prototype started with a very ambitious clustering feature. "
            "A simple review queue turned out to be more useful. "
            "It now includes duplicate suggestions and a portable HTML export.\n\n"
            "**Current question:** should folders and tags coexist, or is that one system too many?"
        ),
        "votes": ("maya", "eli", "jules"),
    },
    {
        "name": "Quiet Hours",
        "owner": "eli",
        "tagline": "A daily plan that leaves a little room for being human.",
        "category": "productivity",
        "tools": "Cursor, Django, HTMX",
        "description": (
            "Choose three things for today, give them generous time blocks, and move "
            "unfinished work without a guilt-inducing overdue counter.\n\n"
            "I built the first flow with AI, then rewrote the copy and removed the "
            "dashboard. The useful part is a single page that still makes sense on "
            "a busy afternoon.\n\n"
            "**In progress:** keyboard shortcuts and a better empty state."
        ),
        "votes": ("maya", "nora", "sam"),
    },
    {
        "name": "Trailmark",
        "owner": "sam",
        "tagline": "A little home on the web for walks worth remembering.",
        "category": "websites",
        "tools": "Claude Code, Django, CSS",
        "description": (
            "A personal walking journal with photos, short notes, and broad location "
            "labels. It is about noticing a street, not racing a route.\n\n"
            "AI helped scaffold the journal and image layouts. I kept the location "
            "field intentionally approximate and made every entry private until shared.\n\n"
            "**Next:** a printable seasonal collection for the walks that deserve paper."
        ),
        "votes": ("nora", "jules"),
    },
    {
        "name": "Tiny Atlas",
        "owner": "jules",
        "tagline": "Explore geography through small questions and friendly maps.",
        "category": "learning",
        "tools": "Cursor, Python, JavaScript",
        "description": (
            "A collection of short geography activities: compare distances, trace a river, "
            "or guess which places share a latitude. Each answer includes an explanation.\n\n"
            "I use AI for interaction prototypes and manually check the learning material. "
            "The goal is curiosity rather than a leaderboard.\n\n"
            "**Looking for collaborators:** people who enjoy turning a surprising fact "
            "into a good five-minute exercise."
        ),
        "votes": ("maya", "nora", "theo", "sam"),
    },
    {
        "name": "Color Field",
        "owner": "nora",
        "tagline": "Try a palette on an interface before you fall in love with it.",
        "category": "creative",
        "tools": "Claude Code, JavaScript, CSS",
        "description": (
            "A palette playground with real interface samples: a form, a card, "
            "a chart, and a long paragraph. Colors have jobs instead of just swatches.\n\n"
            "The prototype supports light and dark previews, contrast readouts, "
            "and CSS custom-property export. AI handled the repetitive UI while "
            "I experimented with how a palette should be edited.\n\n"
            "**Design note:** changing a background should make its text color easy to review."
        ),
        "votes": ("theo", "eli", "jules"),
    },
    {
        "name": "Release Room",
        "owner": "theo",
        "tagline": "Keep a readable story of what changed in your side project.",
        "category": "tools",
        "tools": "Cursor, Django, SQLite",
        "description": (
            "A lightweight release journal for small projects. Collect a few notes "
            "during the week, then publish a clear update with screenshots and links.\n\n"
            "It keeps drafts separate from published updates and exports Markdown. "
            "There is no repository hosting or automatic claim that every commit "
            "is newsworthy.\n\n"
            "**Next decision:** whether feedback belongs under each release or in "
            "one ongoing project discussion."
        ),
        "votes": ("maya", "sam"),
    },
)

TOPICS = (
    {
        "title": "What are you making this week? Small things welcome.",
        "author": "maya",
        "category": "general",
        "body": (
            "A place for the project that is too small for a big launch post.\n\n"
            "Share **what it does**, **what you learned**, and **one thing you are stuck on**. "
            "A sketch or an unfinished experiment counts.\n\n"
            "Mine: making my reading list useful before adding another feature to it."
        ),
        "likes": ("theo", "nora", "eli", "jules", "sam"),
        "replies": (
            (
                "eli",
                "A daily planner with only three slots. The hard part is resisting a fourth.",
            ),
            (
                "sam",
                "A walking journal. I spent more time choosing the photo layout than writing the views.",
            ),
            (
                "jules",
                "A map exercise about latitude. My first version accidentally taught people how to guess the UI.",
            ),
            (
                "nora",
                "A tiny garden you can rearrange. No login, no streak, just a nice place to put a rock.",
            ),
        ),
    },
    {
        "title": "Paper Lantern: I removed the summary button and kept the notes",
        "author": "maya",
        "category": "showcase",
        "project": "Paper Lantern",
        "body": (
            "The original prototype summarized every saved article. I could collect "
            "summaries forever without remembering why I saved anything.\n\n"
            "The new flow asks for one optional sentence: **What made you save this?** "
            "That tiny bit of friction feels useful.\n\n"
            "Would you write a note while saving, or only when you return to read?"
        ),
        "likes": ("nora", "eli", "sam"),
        "replies": (
            (
                "theo",
                "While saving, but only if it is optional. Sometimes the whole note is just 'for the settings screen'.",
            ),
            (
                "sam",
                "A prompt like 'What will this help with?' would give me a better starting point than an empty box.",
            ),
            (
                "maya",
                "That is a good distinction. I will try the more specific prompt and keep the field optional.",
            ),
        ),
    },
    {
        "title": "Pocket Garden, a browser toy with absolutely no daily streak",
        "author": "nora",
        "category": "showcase",
        "project": "Pocket Garden",
        "body": (
            "I wanted to make something pleasant that did not ask me to optimize anything. "
            "So: plants, stones, a little wind.\n\n"
            "The first AI-generated version had currency and unlockable items. "
            "Removing those made the idea much clearer.\n\n"
            "Next up is touch input. Dragging a small plant with a finger needs "
            "more space than dragging it with a mouse."
        ),
        "likes": ("maya", "eli", "jules", "sam"),
        "replies": (
            (
                "eli",
                "Please keep the empty space. Every garden app I have tried seems determined to fill it.",
            ),
            (
                "jules",
                "Could the plant lift slightly above your finger while dragging? It might make placement easier.",
            ),
        ),
    },
    {
        "title": "Tab Tidy: folders, tags, or just a really good search box?",
        "author": "theo",
        "category": "help",
        "project": "Tab Tidy",
        "body": (
            "The bookmark importer works, but I am stuck on organization. "
            "Folders are familiar; tags handle links that belong in two places.\n\n"
            "Supporting both would be easy to generate and harder to explain. "
            "For a first version, which would you actually use?\n\n"
            "My current leaning: collections with a quick search, and no nested folders."
        ),
        "likes": ("maya", "jules"),
        "replies": (
            (
                "maya",
                "Collections. I usually remember the project I needed a link for, not the category of the article.",
            ),
            (
                "nora",
                "Let a link live in two collections and I would not need tags yet.",
            ),
            (
                "theo",
                "That is a smaller model than the one I was sketching. Going to try it with my own bookmarks first.",
            ),
        ),
    },
    {
        "title": "Quiet Hours build log: the empty state became the main screen",
        "author": "eli",
        "category": "buildlog",
        "project": "Quiet Hours",
        "body": (
            "This week's change was mostly subtraction.\n\n"
            "- Removed the completion chart.\n"
            "- Put today's three tasks above the fold.\n"
            "- Replaced 'overdue' with a choice to move or drop a task.\n\n"
            "AI made it very easy to build a dashboard. Watching myself avoid that "
            "dashboard was the useful part."
        ),
        "likes": ("maya", "nora", "sam"),
        "replies": (
            (
                "sam",
                "The option to drop something sounds useful. Moving the same task every day is a decision too.",
            ),
        ),
    },
    {
        "title": "Trailmark: deciding what a walking journal should leave out",
        "author": "sam",
        "category": "buildlog",
        "project": "Trailmark",
        "body": (
            "I removed exact route tracking from the first version. A neighborhood "
            "name and a photo say enough about most of my walks.\n\n"
            "The project now starts with a private entry and an explicit sharing step. "
            "It feels closer to a notebook than a fitness app.\n\n"
            "I am trying a layout with one large photo and a short note underneath."
        ),
        "likes": ("nora", "eli"),
        "replies": (
            (
                "nora",
                "A seasonal view could be lovely: the same tree in four entries, instead of four routes on a map.",
            ),
            (
                "sam",
                "That is exactly the kind of pattern I want to notice. Adding it to the sketchbook.",
            ),
        ),
    },
    {
        "title": "Tiny Atlas: how do you check learning content generated with AI?",
        "author": "jules",
        "category": "help",
        "project": "Tiny Atlas",
        "body": (
            "The interactive map was the easy part. Writing a good explanation "
            "for a wrong answer takes longer.\n\n"
            "I currently keep a source link next to each fact and review the "
            "question separately from the code. The AI helps rephrase, but I do "
            "not treat its answer as a source.\n\n"
            "Has anyone found a lightweight review workflow for a small educational project?"
        ),
        "likes": ("maya", "sam", "theo"),
        "replies": (
            (
                "maya",
                "I would also record when you checked the source. Some 'facts' are really measurements with a date.",
            ),
            (
                "theo",
                "Try answering your own question without the map. It catches cases where the wording gives the answer away.",
            ),
        ),
    },
    {
        "title": "Color Field: exporting a palette as something you can actually use",
        "author": "nora",
        "category": "showcase",
        "project": "Color Field",
        "body": (
            "The export now uses roles instead of numbered colors:\n\n"
            "```css\n:root {\n  --surface: #f8f6f0;\n  --text: #25352b;\n"
            "  --accent: #426b50;\n}\n```\n\n"
            "It is a small change, but it makes the preview and the exported CSS "
            "speak the same language. Next I want to make contrast checks easier "
            "to understand without turning the page into a warning panel."
        ),
        "likes": ("theo", "eli", "jules"),
        "replies": (
            (
                "eli",
                "Show the exact text-and-background pair being checked. A score beside an isolated swatch is hard to act on.",
            ),
        ),
    },
    {
        "title": "Release Room: a changelog is a story, not a commit dump",
        "author": "theo",
        "category": "showcase",
        "project": "Release Room",
        "body": (
            "My first draft imported every commit and asked AI to summarize it. "
            "The result was accurate enough and not very helpful to a reader.\n\n"
            "Now each update starts with **What can someone do differently?** "
            "Technical notes have their own optional section.\n\n"
            "I am keeping the first version manual while I figure out which parts "
            "of the writing process actually need help."
        ),
        "likes": ("maya", "sam"),
        "replies": (),
    },
    {
        "title": "The most useful prompt I added was 'ask me before adding a dependency'",
        "author": "theo",
        "category": "general",
        "body": (
            "Not a magic prompt, just a useful boundary for my small projects.\n\n"
            "> Before adding a package, explain what it replaces and whether the "
            "existing stack already covers the job.\n\n"
            "It has made me think about the shape of the app instead of approving "
            "whatever scaffolding appears. What short instruction has made "
            "your collaboration with a coding assistant better?"
        ),
        "likes": ("maya", "nora", "eli", "sam"),
        "replies": (
            (
                "jules",
                "'Explain the user-visible change before the implementation.' It catches a surprising amount of work I never asked for.",
            ),
            (
                "maya",
                "I ask for one small working path first. It is easier to discuss a form I can use than a list of future modules.",
            ),
            (
                "eli",
                "'If two approaches are reasonable, show me the tradeoff.' Especially useful when I do not know what I am missing.",
            ),
        ),
    },
    {
        "title": "What makes you leave useful feedback on someone else's project?",
        "author": "sam",
        "category": "general",
        "body": (
            "I find it easier to respond to 'Does this screen make sense on a phone?' "
            "than 'Any feedback?'\n\n"
            "Maybe project posts should end with one specific question and a small "
            "thing to try. What would make you spend five minutes testing a stranger's build?"
        ),
        "likes": ("maya", "nora"),
        "replies": (
            (
                "nora",
                "A clear task and no signup just to see the idea. A short recording helps if I am on my phone.",
            ),
            (
                "jules",
                "Knowing what is intentionally unfinished. Otherwise I worry I am pointing out something obvious.",
            ),
        ),
    },
)


class Command(BaseCommand):
    help = "Add optional fictional demo projects and conversations; existing content is kept."

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        counts = {"authors": 0, "projects": 0, "topics": 0, "replies": 0}
        user_model = get_user_model()

        for key, first_name, last_name in AUTHORS:
            user, created = user_model.objects.get_or_create(
                username=f"demo_{key}",
                defaults={"first_name": first_name, "last_name": last_name},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
                counts["authors"] += 1
            users[key] = user

        projects = {}
        for data in PROJECTS:
            project, created = Project.objects.get_or_create(
                name=data["name"],
                owner=users[data["owner"]],
                defaults={
                    field: data[field]
                    for field in ("tagline", "description", "category", "tools")
                },
            )
            if created:
                project.votes.add(*(users[key] for key in data["votes"]))
                counts["projects"] += 1
            projects[data["name"]] = project

        for data in TOPICS:
            topic, created = Topic.objects.get_or_create(
                title=data["title"],
                author=users[data["author"]],
                defaults={
                    "body": data["body"],
                    "category": data["category"],
                    "project": projects.get(data.get("project")),
                },
            )
            if not created:
                continue
            topic.likes.add(*(users[key] for key in data["likes"]))
            counts["topics"] += 1
            for author, body in data["replies"]:
                Reply.objects.create(topic=topic, author=users[author], body=body)
                counts["replies"] += 1

        summary = ", ".join(f"{count} {name}" for name, count in counts.items())
        self.stdout.write(
            self.style.SUCCESS(f"Fictional demo content added: {summary}.")
        )
