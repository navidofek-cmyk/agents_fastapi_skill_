Run the generated project using Docker.

Steps:

1. Verify all required files exist:

* docker/Dockerfile
* docker/docker-compose.yml
* requirements.txt

2. If anything is missing, fix it.

3. Build and run the project:

* docker compose up --build

4. Verify:

* backend is running on http://localhost:8000
* GET /health returns status ok

5. If something fails:

* debug the issue
* fix Dockerfile or compose
* rerun

6. Provide final output:

* status (running / failed)
* working URL
* commands used
* any fixes applied
