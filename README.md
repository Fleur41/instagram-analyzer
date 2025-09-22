Instagram Analyzer
==================

Quick start — run locally

1) Create a Python virtual environment (macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Create a `.env` file in the project root containing at least:

```properties
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
API_HOST=0.0.0.0
API_PORT=8000
```

Note: storing credentials in `.env` is convenient for local testing but not recommended for production. Consider using a secrets manager for production use.

4) (Recommended) Create an Instaloader session file interactively. This avoids 401 errors when fetching profile data and is the most reliable way to authenticate.

- Activate the virtualenv (if not active):

```bash
source .venv/bin/activate
```

- Run Instaloader interactive login (it will prompt for password and any 2FA/challenge):

```bash
instaloader -l <your_username>
```

- Move the generated session into the app session folder so the API can reuse it:

```bash
mkdir -p .insta_sessions
mv <your_username>.session .insta_sessions/<your_username>.session
```

Alternatively you can use the provided script to attempt programmatic login (may still fail on 2FA/challenge):

```bash
PYTHONPATH=. python3 scripts/create_session.py
```

5) Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6) Open the frontend in a browser:

```
http://127.0.0.1:8000/frontend
```

Useful endpoints

- GET /auth/test — check whether configured credentials/session file were loaded
- POST /analyze — start a background analysis (returns a task id)
- GET /status/{task_id} — check analysis status and retrieve results
- GET /profile/{username} — quick fetch of profile metadata (public or via saved session)

Troubleshooting

- If you see repeated `HTTP error code 401` from Instaloader, create a session file via the interactive `instaloader -l` flow and place it into `.insta_sessions/` as described above.
- The app looks for `.insta_sessions/<INSTAGRAM_USERNAME>.session` by default when `use_credentials` is enabled.

Security

This project is intended for local testing and research. Do NOT commit your `.env` or session files to a public repository.
