import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:8010"
  },
  webServer: {
    command:
      "bash -lc 'cd .. && rm -f e2e-tasks.db && if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi; TASKS_DB_PATH=$(pwd)/e2e-tasks.db \"$PY\" -m uvicorn app.main:app --host 127.0.0.1 --port 8010'",
    url: "http://127.0.0.1:8010/health",
    reuseExistingServer: true
  }
});
