"""Attempt to login with configured credentials and save an instaloader session file.

Run this from the workspace root. It will print diagnostic info and either save a session file
under .insta_sessions/<username>.session or print the error encountered.
"""
import os
import sys
import logging
from app.config import Config

try:
    import instaloader
except Exception as e:
    print('instaloader not installed:', e)
    sys.exit(2)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('create_session')

if not Config.INSTAGRAM_USERNAME or not Config.INSTAGRAM_PASSWORD:
    print('No INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD set in Config/.env')
    sys.exit(1)

L = instaloader.Instaloader()
L.context._session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

safe_user = Config.INSTAGRAM_USERNAME.replace('@','').replace('/','_')
session_dir = os.path.join(os.getcwd(), '.insta_sessions')
os.makedirs(session_dir, exist_ok=True)
session_file = os.path.join(session_dir, f"{safe_user}.session")

print('Attempting login for', Config.INSTAGRAM_USERNAME)
try:
    L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
    print('Login OK')
    try:
        L.save_session_to_file(session_file)
        print('Saved session to', session_file)
    except Exception as e:
        print('Failed saving session file:', e)
except Exception as e:
    print('Login failed:', type(e).__name__, str(e))
    # attempt a simple profile fetch to show detailed error
    try:
        print('Attempting profile fetch for diagnostic...')
        p = instaloader.Profile.from_username(L.context, Config.INSTAGRAM_USERNAME)
        print('Profile fetch OK (unexpected)')
    except Exception as e2:
        print('Profile fetch error:', type(e2).__name__, str(e2))

print('Done')
