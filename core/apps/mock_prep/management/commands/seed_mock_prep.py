from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.mock_prep.models import InterviewTrack, Question, QuestionCategory, Technology
from apps.profiles.models import EngineerLevel


TRACKS = [
    ("Backend Engineer", "backend"),
    ("Frontend Engineer", "frontend"),
    ("Full Stack Engineer", "fullstack"),
]

TECHNOLOGIES = [
    ("JavaScript", "javascript"),
    ("React", "react"),
    ("Python", "python"),
    ("Django", "django"),
    ("Node.js", "nodejs"),
    ("PostgreSQL", "postgresql"),
    ("System Design", "system-design"),
]

QUESTIONS = [
    {
        "prompt": "Tell me about a time you had a disagreement with a teammate about a technical decision. How did you resolve it?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["javascript", "python"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Describe a project where you had to learn a new technology quickly. What was your approach?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["javascript", "react", "python"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Tell me about a time you missed a deadline. What happened and what did you learn?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["python", "django"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "How do you handle receiving critical feedback on your code during a review?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["javascript", "react"],
        "estimated_minutes": 2,
    },
    {
        "prompt": "Describe a situation where you had to mentor a junior developer. What strategies did you use?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Explain the difference between REST and GraphQL. When would you choose one over the other?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django", "nodejs"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "What is the event loop in JavaScript and how does it handle asynchronous operations?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.MID,
        "tracks": ["frontend", "fullstack"],
        "technologies": ["javascript", "nodejs", "react"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Explain how React's virtual DOM works and why it improves performance.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["frontend", "fullstack"],
        "technologies": ["javascript", "react"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "What are Django middleware classes and describe a use case where you would write custom middleware.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Explain database indexing. What types of indexes exist in PostgreSQL and when should you use each?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django", "postgresql"],
        "estimated_minutes": 4,
    },
    {
        "prompt": "What is the difference between authentication and authorization? How would you implement both in a web API?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django", "nodejs"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Explain closures in JavaScript with a practical example.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["frontend", "fullstack"],
        "technologies": ["javascript", "react"],
        "estimated_minutes": 2,
    },
    {
        "prompt": "How does Python's GIL affect multi-threaded applications? What alternatives exist?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend"],
        "technologies": ["python", "django"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "What are React hooks? Explain useState and useEffect and when you would use each.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["frontend", "fullstack"],
        "technologies": ["javascript", "react"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Describe how you would debug a slow API endpoint in production.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django", "postgresql"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Design a URL shortening service like bit.ly. Walk me through the high-level architecture.",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "postgresql"],
        "estimated_minutes": 5,
    },
    {
        "prompt": "How would you design a real-time notification system for a social media app?",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "nodejs"],
        "estimated_minutes": 5,
    },
    {
        "prompt": "Design a rate limiter for a public API. What algorithms would you consider?",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.MID,
        "tracks": ["backend"],
        "technologies": ["system-design", "python"],
        "estimated_minutes": 4,
    },
    {
        "prompt": "How would you design the feed for a Twitter-like application at scale?",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "postgresql"],
        "estimated_minutes": 5,
    },
    {
        "prompt": "Design a file upload and storage system that supports large files and resumable uploads.",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "nodejs"],
        "estimated_minutes": 5,
    },
    {
        "prompt": "How would you architect a multi-tenant SaaS application with data isolation requirements?",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "django", "postgresql"],
        "estimated_minutes": 5,
    },
    {
        "prompt": "Explain the CAP theorem and how it applies to choosing a database for an e-commerce checkout system.",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend"],
        "technologies": ["system-design", "postgresql"],
        "estimated_minutes": 4,
    },
    {
        "prompt": "What is the difference between SQL and NoSQL databases? Give examples of when you would use each.",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.JUNIOR,
        "tracks": ["backend", "fullstack"],
        "technologies": ["postgresql", "python"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "How do you ensure code quality in a team? Talk about testing, CI/CD, and code review practices.",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["javascript", "python"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Describe how you would implement caching in a Django application. What caching strategies exist?",
        "category": QuestionCategory.TECHNICAL,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["python", "django"],
        "estimated_minutes": 3,
    },
    {
        "prompt": "Design a search autocomplete feature for an e-commerce site with millions of products.",
        "category": QuestionCategory.SYSTEM_DESIGN,
        "level": EngineerLevel.MID,
        "tracks": ["backend", "fullstack"],
        "technologies": ["system-design", "postgresql"],
        "estimated_minutes": 4,
    },
    {
        "prompt": "Tell me about a time you improved application performance significantly. What was your process?",
        "category": QuestionCategory.BEHAVIORAL,
        "level": EngineerLevel.SENIOR,
        "tracks": ["backend", "frontend", "fullstack"],
        "technologies": ["python", "react"],
        "estimated_minutes": 3,
    },
]


class Command(BaseCommand):
    help = "Seed mock prep tracks, technologies, and sample questions"

    def handle(self, *args, **options):
        track_map: dict[str, InterviewTrack] = {}
        for name, slug in TRACKS:
            track, _ = InterviewTrack.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "is_active": True},
            )
            track_map[slug] = track

        tech_map: dict[str, Technology] = {}
        for name, slug in TECHNOLOGIES:
            tech, _ = Technology.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "is_active": True},
            )
            tech_map[slug] = tech

        for tech in tech_map.values():
            if tech.slug in {"javascript", "react", "nodejs"}:
                tech.tracks.set([track_map["frontend"], track_map["fullstack"]])
            elif tech.slug in {"python", "django", "postgresql"}:
                tech.tracks.set([track_map["backend"], track_map["fullstack"]])
            elif tech.slug == "system-design":
                tech.tracks.set(list(track_map.values()))

        created_count = 0
        for item in QUESTIONS:
            prompt = item["prompt"]
            existing = Question.objects.filter(prompt=prompt).first()
            if existing:
                question = existing
            else:
                question = Question.objects.create(
                    prompt=prompt,
                    category=item["category"],
                    level=item["level"],
                    estimated_minutes=item["estimated_minutes"],
                    is_active=True,
                )
                created_count += 1

            question.tracks.set([track_map[slug] for slug in item["tracks"]])
            question.technologies.set(
                [tech_map[slug] for slug in item["technologies"]]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(track_map)} tracks, {len(tech_map)} technologies, "
                f"and {len(QUESTIONS)} questions ({created_count} newly created)."
            )
        )
