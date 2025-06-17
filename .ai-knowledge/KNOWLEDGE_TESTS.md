# AI Knowledge Validation Tests

## Architecture Questions
1. What framework is TaskForge built on? (Answer: Django)
2. What database system does TaskForge use? (Answer: PostgreSQL)
3. What is the background job system? (Answer: Celery with Redis)
4. Where is TaskForge deployed? (Answer: Render.com)

## Business Logic Questions
5. What is the Fireflies ingestion frequency? (Answer: 15 minutes)
6. How long is the human review window? (Answer: 18 hours)
7. What triggers auto-push to Monday.com? (Answer: Tasks pending >18 hours)
8. Which timezone does the backend use? (Answer: UTC)

## Guardian System Questions
9. What protects against regressions? (Answer: Guardian System)
10. Where is AI knowledge stored? (Answer: .ai-knowledge/ directory)
11. What requires human approval? (Answer: All code changes)
12. How are modules isolated? (Answer: Independent Django apps with event bus)
