from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import User
from apps.courses.models import Category, Course, Module, Lesson, Enrollment
from apps.content.models import ContentBlock

class Command(BaseCommand):
    help = "Seed demo users, categories, courses, and content blocks for testing the frontend."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # 1. Users
        admin_user, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "username": "admin",
                "first_name": "System",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "is_email_verified": True,
                "terms_accepted": True,
                "privacy_accepted": True,
                "consent_timestamp": timezone.now(),
            }
        )
        admin_user.set_password("Admin123!")
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("Admin user ready: admin@example.com / Admin123!"))

        instructor_user, created = User.objects.get_or_create(
            email="instructor@example.com",
            defaults={
                "username": "instructor",
                "first_name": "Sarah",
                "last_name": "Connor",
                "role": User.Role.INSTRUCTOR,
                "is_active": True,
                "is_email_verified": True,
                "terms_accepted": True,
                "privacy_accepted": True,
                "consent_timestamp": timezone.now(),
            }
        )
        instructor_user.set_password("Instructor123!")
        instructor_user.save()
        self.stdout.write(self.style.SUCCESS("Instructor user ready: instructor@example.com / Instructor123!"))

        learner_user, created = User.objects.get_or_create(
            email="learner@example.com",
            defaults={
                "username": "learner",
                "first_name": "Alex",
                "last_name": "Rivera",
                "role": User.Role.LEARNER,
                "is_active": True,
                "is_email_verified": True,
                "terms_accepted": True,
                "privacy_accepted": True,
                "consent_timestamp": timezone.now(),
            }
        )
        learner_user.set_password("Learner123!")
        learner_user.save()
        self.stdout.write(self.style.SUCCESS("Learner user ready: learner@example.com / Learner123!"))

        # 2. Categories
        cat_cloud, _ = Category.objects.get_or_create(
            slug="cloud-devops",
            defaults={"name": "DevOps & Cloud", "description": "Microservices, Kubernetes, CI/CD"}
        )
        cat_cs, _ = Category.objects.get_or_create(
            slug="computer-science",
            defaults={"name": "Computer Science", "description": "Software Architecture, Algorithms & Systems"}
        )
        cat_web, _ = Category.objects.get_or_create(
            slug="web-development",
            defaults={"name": "Web Development", "description": "Full-Stack Web Engineering with React & Next.js"}
        )

        # 3. Course 1: Cloud-Native Microservices Architecture
        course1, created = Course.objects.get_or_create(
            slug="cloud-native-microservices-101",
            defaults={
                "title": "Cloud-Native Microservices Architecture",
                "short_description": "Master resilient distributed systems with Docker, Kubernetes, and Event-Driven Design",
                "description": "An exhaustive hands-on deep dive into building production-grade distributed microservices systems. Covers service meshes, Kafka event streaming, distributed tracing with OpenTelemetry, and zero-downtime rolling deployments.",
                "category": cat_cloud,
                "instructor": instructor_user,
                "difficulty": Course.Difficulty.INTERMEDIATE,
                "estimated_duration_minutes": 720,
                "status": Course.Status.DRAFT,
            }
        )

        # Module 1
        mod1, _ = Module.objects.get_or_create(
            course=course1,
            position=1,
            defaults={"title": "Introduction to Distributed Microservices", "description": "Core paradigms, Conway's Law, and domain boundary isolation."}
        )

        # Lesson 1.1
        les1_1, _ = Lesson.objects.get_or_create(
            module=mod1,
            position=1,
            defaults={
                "title": "Monolith to Microservices Decomposition",
                "slug": "monolith-to-microservices-decomposition",
                "is_preview": True,
                "is_published": True,
                "estimated_duration_minutes": 15,
            }
        )

        # Content blocks for Lesson 1.1
        ContentBlock.objects.get_or_create(
            lesson=les1_1,
            position=1,
            defaults={
                "block_type": ContentBlock.BlockType.VIDEO,
                "title": "Decomposition Architectural Walkthrough",
                "content_payload": {
                    "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "audio_url": "https://actions.google.com/sounds/v1/ambiences/rain_heavy.ogg",
                    "captions_url": "https://gist.githubusercontent.com/samdutton/ca37f6adc2208f86ae40/raw/sample.vtt",
                    "transcript": [
                        {"start": 0, "end": 12, "speaker": "Instructor", "text": "Welcome to Cloud-Native Microservices Architecture. Today we begin our journey into distributed systems decomposition."},
                        {"start": 12, "end": 28, "speaker": "Instructor", "text": "When transitioning from a monolithic codebase, domain boundary modeling is critical to avoid distributed monolith anti-patterns."},
                        {"start": 28, "end": 55, "speaker": "Instructor", "text": "We will utilize bounded contexts from Domain-Driven Design (DDD) to isolate business invariants and define clean communication contracts."}
                    ]
                }
            }
        )

        ContentBlock.objects.get_or_create(
            lesson=les1_1,
            position=2,
            defaults={
                "block_type": ContentBlock.BlockType.TEXT,
                "title": "Architectural Key Takeaways",
                "content_payload": {
                    "markdown": "### Bounded Contexts & Microservice Invariants\n\n- **Loose Coupling:** Services communicate exclusively via versioned asynchronous events or REST/gRPC interfaces.\n- **High Cohesion:** Every microservice owns its private persistent datastore. Shared direct database access across service boundaries is strictly prohibited.\n- **Resilience:** Circuit breakers (e.g. Netflix Hystrix/Resilience4j pattern) prevent cascading failures across service topologies."
                }
            }
        )

        # Lesson 1.2
        les1_2, _ = Lesson.objects.get_or_create(
            module=mod1,
            position=2,
            defaults={
                "title": "Interactive Service Mesh Architecture Simulation",
                "slug": "interactive-service-mesh-simulation",
                "is_preview": False,
                "is_published": True,
                "estimated_duration_minutes": 25,
            }
        )

        ContentBlock.objects.get_or_create(
            lesson=les1_2,
            position=1,
            defaults={
                "block_type": ContentBlock.BlockType.SIMULATION,
                "title": "Service Mesh Interactive Bridge",
                "content_payload": {
                    "embed_url": "https://example.com/simulations/service-mesh-demo",
                    "allow_fullscreen": True,
                    "sim_version": "2.1.0"
                }
            }
        )

        # Publish course1 (adhering to D-015 invariants)
        if course1.status != Course.Status.PUBLISHED:
            course1.publish()
            self.stdout.write(self.style.SUCCESS("Published course: Cloud-Native Microservices Architecture"))

        # Enroll learner in course1
        Enrollment.objects.get_or_create(
            learner=learner_user,
            course=course1,
            defaults={"status": Enrollment.Status.ACTIVE}
        )
        self.stdout.write(self.style.SUCCESS("Enrolled learner@example.com in Cloud-Native Microservices Architecture"))

        # 4. Course 2: Modern Full-Stack Development with Next.js 15 & Django 5
        course2, _ = Course.objects.get_or_create(
            slug="nextjs-django-fullstack",
            defaults={
                "title": "Modern Full-Stack Development with Next.js 15 & Django 5",
                "short_description": "Build production-grade applications with React Server Components, Tailwind CSS, and RESTful APIs",
                "description": "Learn to architect scalable web apps bridging modern React 19 / Next.js 15 App Router frontends with high-performance Django REST Framework backends, SimpleJWT, and PostgreSQL.",
                "category": cat_web,
                "instructor": instructor_user,
                "difficulty": Course.Difficulty.BEGINNER,
                "estimated_duration_minutes": 480,
                "status": Course.Status.DRAFT,
            }
        )
        mod2_1, _ = Module.objects.get_or_create(
            course=course2,
            position=1,
            defaults={"title": "Foundations & Environment Scaffolding", "description": "Setting up the monorepo, Docker, and dev workflows."}
        )
        les2_1, _ = Lesson.objects.get_or_create(
            module=mod2_1,
            position=1,
            defaults={
                "title": "Monorepo Setup with Docker Compose",
                "slug": "monorepo-setup-with-docker-compose",
                "is_preview": True,
                "is_published": True,
                "estimated_duration_minutes": 20,
            }
        )
        ContentBlock.objects.get_or_create(
            lesson=les2_1,
            position=1,
            defaults={
                "block_type": ContentBlock.BlockType.TEXT,
                "title": "Monorepo Best Practices",
                "content_payload": {
                    "markdown": "## Multi-Tier Architecture Structure\n\n```text\n├── backend/       # Django 5 + DRF + Celery\n├── frontend/      # Next.js 15 (App Router) + React 19 + Tailwind CSS\n├── infra/         # Docker Compose, Nginx, Dockerfiles\n└── docs/          # Architecture Decision Records (ADRs) & Flow Documentation\n```"
                }
            }
        )
        if course2.status != Course.Status.PUBLISHED:
            course2.publish()
            self.stdout.write(self.style.SUCCESS("Published course: Modern Full-Stack Development"))

        # 5. Skills & Adaptive Graph (FR-PER-01 / FR-PER-02)
        from apps.learning.models import Skill, SkillPrerequisite, LessonSkill, StudentSkill
        from apps.learning.engine import get_adaptive_engine

        sk_containers, _ = Skill.objects.get_or_create(
            slug="docker-containers",
            defaults={"name": "Docker & Containers", "description": "Container virtualization, images, multi-stage builds"}
        )
        sk_dist_sys, _ = Skill.objects.get_or_create(
            slug="distributed-systems",
            defaults={"name": "Distributed Systems", "description": "CAP theorem, consensus, network partitions"}
        )
        sk_microservices, _ = Skill.objects.get_or_create(
            slug="microservices-architecture",
            defaults={"name": "Microservices Architecture", "description": "Service decomposition, event streaming, API gateways"}
        )

        SkillPrerequisite.objects.get_or_create(skill=sk_dist_sys, prerequisite=sk_containers)
        SkillPrerequisite.objects.get_or_create(skill=sk_microservices, prerequisite=sk_dist_sys)

        # Map skills to lessons
        LessonSkill.objects.get_or_create(lesson=les1_1, skill=sk_microservices, defaults={"contribution_weight": 1.0})
        LessonSkill.objects.get_or_create(lesson=les1_2, skill=sk_dist_sys, defaults={"contribution_weight": 0.8})
        LessonSkill.objects.get_or_create(lesson=les2_1, skill=sk_containers, defaults={"contribution_weight": 1.0})

        # Seed learner mastery
        StudentSkill.objects.get_or_create(learner=learner_user, skill=sk_containers, defaults={"mastery_score": 90})
        StudentSkill.objects.get_or_create(learner=learner_user, skill=sk_dist_sys, defaults={"mastery_score": 65})
        StudentSkill.objects.get_or_create(learner=learner_user, skill=sk_microservices, defaults={"mastery_score": 50})

        # Generate initial explainable adaptive learning path
        engine = get_adaptive_engine()
        engine.generate_path(learner_user, course1)
        self.stdout.write(self.style.SUCCESS("Generated adaptive learning path for learner in Cloud-Native Microservices"))

        # 6. Interactive Assessment & Multi-Format Questions (FR-ASM-01 to FR-ASM-06)
        from apps.assessments.models import Assessment, Question, Choice

        assessment1, _ = Assessment.objects.get_or_create(
            course=course1,
            lesson=les1_1,
            defaults={
                "title": "Checkpoint: Microservices Architecture & Protocols",
                "description": "Assess your understanding of service decomposition, synchronous vs. asynchronous RPC, and resilient messaging.",
                "passing_score_percent": 70,
                "time_limit_minutes": 10,
                "max_attempts": 3,
                "randomize_questions": False,
                "is_published": True,
            }
        )

        # Q1: Single Choice Radio
        q1, _ = Question.objects.get_or_create(
            assessment=assessment1,
            position=0,
            defaults={
                "question_type": Question.QuestionType.SINGLE_CHOICE,
                "prompt": "Which communication protocol is best suited for high-throughput, low-latency inter-service RPC in microservices architectures?",
                "points": 2,
                "explanation": "gRPC utilizes HTTP/2 binary framing and Protocol Buffers, offering significant latency and throughput advantages over text-based JSON/REST.",
                "target_skill": sk_microservices,
                "discrimination_weight": 1.2,
            }
        )
        Choice.objects.get_or_create(question=q1, position=0, defaults={"text": "REST over HTTP/1.1 with JSON", "is_correct": False})
        Choice.objects.get_or_create(question=q1, position=1, defaults={"text": "gRPC over HTTP/2 with Protocol Buffers", "is_correct": True, "feedback": "Correct! Binary serialization and multiplexed streams maximize RPC performance."})
        Choice.objects.get_or_create(question=q1, position=2, defaults={"text": "SOAP with XML payloads", "is_correct": False})
        Choice.objects.get_or_create(question=q1, position=3, defaults={"text": "FTP file exchange", "is_correct": False})

        # Q2: Multiple Choice Checkbox
        q2, _ = Question.objects.get_or_create(
            assessment=assessment1,
            position=1,
            defaults={
                "question_type": Question.QuestionType.MULTIPLE_CHOICE,
                "prompt": "According to the CAP Theorem, which two properties can a distributed data store simultaneously guarantee during a network partition (Select all valid combinations)?",
                "points": 3,
                "explanation": "Under network partition (P), a distributed system must choose between Consistency (CP) or Availability (AP). It cannot guarantee both C and A concurrently while partitioned.",
                "target_skill": sk_dist_sys,
                "discrimination_weight": 1.5,
            }
        )
        Choice.objects.get_or_create(question=q2, position=0, defaults={"text": "Consistency and Partition Tolerance (CP)", "is_correct": True})
        Choice.objects.get_or_create(question=q2, position=1, defaults={"text": "Availability and Partition Tolerance (AP)", "is_correct": True})
        Choice.objects.get_or_create(question=q2, position=2, defaults={"text": "Consistency, Availability, and Partition Tolerance simultaneously (CAP)", "is_correct": False, "feedback": "Brewer's theorem proves simultaneous consistency and availability is impossible during network partitions."})
        Choice.objects.get_or_create(question=q2, position=3, defaults={"text": "Atomicity and Persistence only", "is_correct": False})

        # Q3: True / False
        q3, _ = Question.objects.get_or_create(
            assessment=assessment1,
            position=2,
            defaults={
                "question_type": Question.QuestionType.TRUE_FALSE,
                "prompt": "In cloud-native design, service workloads should ideally remain stateless, delegating persistence to dedicated database or cache tiers.",
                "points": 1,
                "explanation": "Stateless services can scale horizontally dynamically and recover instantly from node crashes.",
                "target_skill": sk_containers,
                "discrimination_weight": 0.8,
            }
        )
        Choice.objects.get_or_create(question=q3, position=0, defaults={"text": "True", "is_correct": True})
        Choice.objects.get_or_create(question=q3, position=1, defaults={"text": "False", "is_correct": False})

        # Q4: Short Answer
        q4, _ = Question.objects.get_or_create(
            assessment=assessment1,
            position=3,
            defaults={
                "question_type": Question.QuestionType.SHORT_ANSWER,
                "prompt": "Name the understandable consensus algorithm designed by Ongaro & Ousterhout as an alternative to Paxos (e.g. used in etcd and Consul).",
                "points": 2,
                "explanation": "Raft is an understandable consensus algorithm that decomposes state-machine replication into leader election, log replication, and safety.",
                "target_skill": sk_dist_sys,
                "discrimination_weight": 1.0,
            }
        )
        Choice.objects.get_or_create(question=q4, position=0, defaults={"text": "Raft", "is_correct": True})
        Choice.objects.get_or_create(question=q4, position=1, defaults={"text": "raft consensus", "is_correct": True})

        # Q5: Code Snippet
        q5, _ = Question.objects.get_or_create(
            assessment=assessment1,
            position=4,
            defaults={
                "question_type": Question.QuestionType.CODE_SNIPPET,
                "prompt": "Complete the Dockerfile healthcheck command that queries localhost:8080/health every 30 seconds:",
                "points": 2,
                "code_language": "dockerfile",
                "initial_code": "HEALTHCHECK --interval=30s --timeout=5s \\\n  CMD curl -f http://localhost:8080/health || exit 1",
                "explanation": "The HEALTHCHECK instruction informs Docker how to test a container to check that it is still working.",
                "target_skill": sk_containers,
                "discrimination_weight": 1.0,
            }
        )
        Choice.objects.get_or_create(question=q5, position=0, defaults={"text": "curl -f http://localhost:8080/health || exit 1", "is_correct": True})

        self.stdout.write(self.style.SUCCESS("Seeded interactive multi-format assessment on Lesson 1.1"))

        # 7. Interactive Simulation Block on Lesson 1.2 (FR-SIM-01 to FR-SIM-03)
        ContentBlock.objects.get_or_create(
            lesson=les1_2,
            position=2,
            defaults={
                "block_type": ContentBlock.BlockType.SIMULATION,
                "title": "Interactive Simulation: Distributed Circuit Breaker & Load Balancer",
                "content_payload": {
                    "simulation_id": "sim-dist-circuit-breaker",
                    "embed_url": "/simulations/circuit-breaker.html",
                    "passing_score": 75,
                    "nodes": ["Node-Alpha", "Node-Beta", "Node-Gamma"],
                    "failure_threshold_percent": 50,
                    "recovery_timeout_seconds": 15,
                    "instructions": "Simulate cascading network latency. Toggle node failures, trigger the circuit breaker half-open state, and successfully rebalance traffic across surviving cluster nodes."
                }
            }
        )
        self.stdout.write(self.style.SUCCESS("Seeded interactive simulation block on Lesson 1.2"))

        # 8. Discussion Forums & Threads (FR-DIS-01 to FR-DIS-03)
        from apps.discussions.models import DiscussionThread, DiscussionPost

        thread1, _ = DiscussionThread.objects.get_or_create(
            course=course1,
            lesson=les1_1,
            title="When should we choose event-driven messaging over direct synchronous RPC?",
            defaults={
                "author": learner_user,
                "body": "In our microservices project, we are evaluating Apache Kafka vs. gRPC for inter-service communication. What are the key architectural tradeoffs when deciding between asynchronous event streams and synchronous RPC?",
                "is_pinned": True,
                "upvotes_count": 5,
                "views_count": 42,
            }
        )

        post1, _ = DiscussionPost.objects.get_or_create(
            thread=thread1,
            author=instructor_user,
            defaults={
                "body": "Excellent question Alex! The fundamental rule of thumb is temporal and spatial coupling:\n\n1. **Use Synchronous RPC (gRPC/REST)** when the calling service strictly requires an immediate, deterministic response before it can proceed (e.g., payment authorization, user credential validation).\n2. **Use Asynchronous Event Streaming (Kafka/RabbitMQ)** when decoupling producer and consumer is critical, enabling independent scaling, buffering sudden traffic spikes, and multi-consumer fanout (e.g., audit logging, email notifications, analytics ingestion).\n\nIn cloud-native production, hybrid architectures are the norm!",
                "is_endorsed": True,
                "endorsed_by": instructor_user,
                "endorsed_at": timezone.now(),
                "upvotes_count": 8,
            }
        )

        DiscussionPost.objects.get_or_create(
            thread=thread1,
            author=learner_user,
            parent=post1,
            defaults={
                "body": "Thank you Sarah! That temporal decoupling explanation makes complete sense.",
                "upvotes_count": 2,
            }
        )
        self.stdout.write(self.style.SUCCESS("Seeded discussion threads with instructor endorsed solution"))

        # 9. In-App Notifications (FR-NOT-01 / FR-NOT-02)
        from apps.notifications.models import Notification

        Notification.objects.get_or_create(
            recipient=learner_user,
            title="Instructor endorsed an answer in your discussion",
            defaults={
                "notification_type": Notification.NotificationType.ANSWER_ENDORSED,
                "message": "Sarah Connor marked an official endorsed answer in 'When should we choose event-driven messaging over direct synchronous RPC?'.",
                "action_url": f"/courses/{course1.slug}",
                "is_read": False,
            }
        )
        Notification.objects.get_or_create(
            recipient=learner_user,
            title="Interactive checkpoint unlocked",
            defaults={
                "notification_type": Notification.NotificationType.ASSESSMENT_GRADED,
                "message": "You have unlocked the Checkpoint Assessment for Lesson 1.1: Microservices Architecture.",
                "action_url": f"/learn/{course1.slug}",
                "is_read": False,
            }
        )
        self.stdout.write(self.style.SUCCESS("Seeded in-app notifications for learner"))

        self.stdout.write(self.style.SUCCESS("Demo data seeding completed successfully!"))

