Create a complete FastAPI backend project with Docker and Codex agent workflow.

Requirements:

1. Create project structure:

* app/

  * main.py
  * routes/tasks.py
  * services/task_service.py
* tests/test_tasks.py
* docker/Dockerfile
* docker/docker-compose.yml
* .agents/

  * planner.md
  * coder.md
  * tester.md
  * reviewer.md
  * skills/docker-safe-feature/SKILL.md
* .codex/

  * config.toml
  * hooks.json
* AGENTS.md
* requirements.txt
* README.md

2. Backend:

* FastAPI app
* endpoints:

  * GET /health
  * POST /tasks
  * GET /tasks
  * POST /tasks/{id}/complete
* use in-memory storage
* keep routes thin, logic in services

3. Tests:

* use pytest
* cover:

  * create task
  * list tasks
  * complete task
  * not found

4. Docker:

* python:3.11-slim
* expose port 8000
* simple docker-compose

5. Codex:

* AGENTS.md with rules:

  * minimal changes
  * service layer logic
  * testing required
* subagents:

  * planner: plan only
  * coder: implement
  * tester: tests
  * reviewer: review
* skill docker-safe-feature:

  * plan → code → test → review

6. Hooks:

* block dangerous bash commands
* stop hook reminder for tests

Constraints:

* keep everything simple
* no unnecessary dependencies
* no TODOs

Output:

* show file tree
* then full content of all files
