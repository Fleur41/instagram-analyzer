import instaloader
from datetime import datetime
from typing import Dict, Callable, Optional
import time
from app.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastInstagramAnalyzer:
    def __init__(self, use_credentials: bool = False):
        self.L = instaloader.Instaloader()
        self.use_credentials = use_credentials
        
        # Faster configuration
        self.L.context._session.timeout = 15
        self.L.context._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Try to reuse a saved session for the configured username to avoid repeated logins
        self._session_file = None
        try:
            if Config.INSTAGRAM_USERNAME:
                # session filename in workspace
                import os
                safe_user = Config.INSTAGRAM_USERNAME.replace('@', '').replace('/', '_')
                session_dir = os.path.join(os.getcwd(), '.insta_sessions')
                os.makedirs(session_dir, exist_ok=True)
                self._session_file = os.path.join(session_dir, f"{safe_user}.session")
                # try to load session file
                try:
                    self.L.context.log("Attempting to load saved session")
                    self.L.load_session_from_file(Config.INSTAGRAM_USERNAME, self._session_file)
                    self.L.context.log("Loaded saved session")
                except Exception:
                    # If loading session fails and credentials provided, try login and save
                    if use_credentials and Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
                        try:
                            self.L.context.log("No saved session, attempting login")
                            self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                            try:
                                self.L.save_session_to_file(self._session_file)
                                self.L.context.log(f"Saved session to {self._session_file}")
                            except Exception:
                                # Not critical if saving fails
                                pass
                        except Exception as e:
                            logger.debug(f"Login failed (continuing without credentials): {e}")
        except Exception:
            # Keep going without session if anything goes wrong here
            pass

    def get_profile_fast(self, username: str):
        """Fast profile fetching with timeout"""
        # Try a couple of times with simple backoff; if 401 occurs and we have creds, try login once
        import time as _time
        last_exc = None
        tried_credential_login = False

        for attempt in range(3):
            try:
                return instaloader.Profile.from_username(self.L.context, username)
            except Exception as e:
                last_exc = e
                msg = str(e)
                logger.debug(f"Profile fetch attempt {attempt+1} failed for {username}: {msg}")

                # If 401 and no credentials available, short-circuit with a helpful error
                if ('HTTP error code 401' in msg or '401' in msg) and not (self.use_credentials or (Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD)):
                    raise Exception(f"Could not fetch profile for {username}: 401 Unauthorized — login required or Instagram is blocking guest requests.")

                # If 401 and we have credentials, try login once then retry
                if ('HTTP error code 401' in msg or '401' in msg) and (Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD) and not tried_credential_login:
                    tried_credential_login = True
                    try:
                        logger.info("Received 401 — attempting credentialed login and retry using configured credentials")
                        self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                        if self._session_file:
                            try:
                                self.L.save_session_to_file(self._session_file)
                            except Exception:
                                pass
                        # immediately retry once after login
                        try:
                            return instaloader.Profile.from_username(self.L.context, username)
                        except Exception as retry_exc:
                            last_exc = retry_exc
                            logger.debug(f"Retry after login failed: {retry_exc}")
                            # fallthrough to outer backoff/loop which will now exit
                    except Exception as login_e:
                        logger.debug(f"Login retry failed: {login_e}")

                # backoff a bit before the next attempt
                _time.sleep(0.8 * (attempt + 1))

        raise Exception(f"Could not fetch profile for {username}: {last_exc}")

    def analyze_interactions_fast(self, user1: str, user2: str, max_posts: int = 5, fetch_all: bool = False,
                                 status_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Ultra-fast analysis function"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting FAST analysis: {user1} -> {user2}")
            
            # Get profiles quickly
            user2_profile = self.get_profile_fast(user2)
            
            # Basic profile info (richer)
            profile_info = {
                "profile": {
                    "username": getattr(user2_profile, 'username', user2),
                    "full_name": getattr(user2_profile, 'full_name', ''),
                    "biography": getattr(user2_profile, 'biography', ''),
                    "profile_pic_url": getattr(user2_profile, 'profile_pic_url', ''),
                    "is_private": getattr(user2_profile, 'is_private', False),
                    "followers": getattr(user2_profile, 'followers', 0),
                    "following": getattr(user2_profile, 'followees', 0),
                    "total_posts": getattr(user2_profile, 'mediacount', 0)
                }
            }
            
            # FAST post analysis (limited)
            # If fetch_all is requested, use internal 0 marker to fetch all but cap to SAFE_MAX
            SAFE_MAX = 500
            if fetch_all:
                effective_max = SAFE_MAX
            else:
                effective_max = min(10, max_posts)

            fast_results = self._analyze_posts_very_fast(user1, user2_profile, effective_max,
                                                         fetch_all=fetch_all,
                                                         status_callback=status_callback)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "user1": user1,
                "user2": user2,
                **profile_info,
                **fast_results,
                "analysis_time": analysis_time,
                "status": "success",
                "message": "Fast analysis completed"
            }
            
            return result
            
        except Exception as e:
            analysis_time = (datetime.now() - start_time).total_seconds()
            return {
                "user1": user1,
                "user2": user2,
                "error": str(e),
                "analysis_time": analysis_time,
                "status": "error"
            }

    def _analyze_posts_very_fast(self, user1: str, user2_profile, max_posts: int, fetch_all: bool = False,
                                 status_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Very fast post analysis with strict limits"""
        user1_likes = 0
        user1_comments = []
        posts_checked = 0
        recent_posts = []

        try:
            posts_iter = user2_profile.get_posts()
            for i, post in enumerate(posts_iter):
                # Respect the supplied cap; max_posts==0 means 'no cap' but we guard earlier
                if max_posts and i >= max_posts:
                    break

                posts_checked += 1

                # Check for user1 like (sampled)
                try:
                    if hasattr(post, 'get_likes') and getattr(post, 'likes', 0) > 0:
                        like_check_count = 0
                        max_like_check = 500 if fetch_all else 5
                        for like in post.get_likes():
                            if getattr(like, 'username', None) == user1:
                                user1_likes += 1
                                break
                            like_check_count += 1
                            if like_check_count >= max_like_check:
                                break
                except Exception as e:
                    logger.debug(f"Like-check skipped for a post due to: {e}")

                # Check for user1 comments (sampled)
                try:
                    if hasattr(post, 'get_comments') and getattr(post, 'comments', 0) > 0:
                        comment_check_count = 0
                        max_comment_check = 200 if fetch_all else 3
                        for comment in post.get_comments():
                            owner = getattr(comment, 'owner', None)
                            if owner and getattr(owner, 'username', None) == user1:
                                user1_comments.append({
                                    "text": getattr(comment, 'text', '')[:500],
                                    "post_date": getattr(post, 'date', datetime.now()).strftime('%Y-%m-%d')
                                })
                                break
                            comment_check_count += 1
                            if comment_check_count >= max_comment_check:
                                break
                except Exception as e:
                    logger.debug(f"Comment-check skipped for a post due to: {e}")

                # Collect sample or full lists for display (capped)
                try:
                    sample_likes = []
                    if hasattr(post, 'get_likes'):
                        like_collect_count = 0
                        max_like_collect = 500 if fetch_all else 5
                        for like in post.get_likes():
                            username = getattr(like, 'username', None)
                            if username:
                                sample_likes.append(username)
                            like_collect_count += 1
                            if like_collect_count >= max_like_collect:
                                break

                    sample_comments = []
                    if hasattr(post, 'get_comments'):
                        comment_collect_count = 0
                        max_comment_collect = 200 if fetch_all else 3
                        for comment in post.get_comments():
                            try:
                                owner = getattr(comment, 'owner', None)
                                username = getattr(owner, 'username', None)
                                text = getattr(comment, 'text', '')
                                sample_comments.append({"username": username, "text": text[:500]})
                            except Exception:
                                pass
                            comment_collect_count += 1
                            if comment_collect_count >= max_comment_collect:
                                break

                        # provide richer post info: full timestamp and direct post link (shortcode)
                        post_date = getattr(post, 'date', datetime.now())
                        shortcode = getattr(post, 'shortcode', None)
                        post_link = f"https://www.instagram.com/p/{shortcode}/" if shortcode else getattr(post, 'url', '')
                        # determine if user1 liked or commented on this post
                        user1_liked_flag = user1 in sample_likes
                        user1_commented_flag = any((c.get('username') == user1) for c in sample_comments)

                        recent_posts.append({
                            "post_date": post_date.strftime('%Y-%m-%d'),
                            "timestamp": post_date.isoformat(),
                            "epoch": int(post_date.timestamp()),
                            "likes": getattr(post, 'likes', 0),
                            "comments": getattr(post, 'comments', 0),
                            "sample_likes": sample_likes,
                            "sample_comments": sample_comments,
                            "caption": getattr(post, 'caption', '')[:2000],
                            "url": getattr(post, 'url', ''),
                            "post_link": post_link,
                            "user1_liked": user1_liked_flag,
                            "user1_commented": user1_commented_flag
                        })
                except Exception as e:
                    logger.debug(f"Failed to sample recent post details: {e}")

                # Gentle pause
                try:
                    time.sleep(0.02)
                except Exception:
                    pass

                # Emit partial progress if requested
                if status_callback:
                    try:
                        partial = {
                            "posts_checked": posts_checked,
                            "user1_likes_found": user1_likes,
                            "user1_comments_found": len(user1_comments),
                            "user1_comments": user1_comments,
                            "analysis_scope": f"Checked {posts_checked} most recent posts quickly",
                            "recent_posts": recent_posts
                        }
                        status_callback(partial)
                    except Exception:
                        pass

        except Exception as e:
            logger.debug(f"Fast analysis had minor issues: {e}")

        return {
            "posts_checked": posts_checked,
            "user1_likes_found": user1_likes,
            "user1_comments_found": len(user1_comments),
            "user1_comments": user1_comments,
            "analysis_scope": f"Checked {posts_checked} most recent posts quickly",
            "recent_posts": recent_posts
        }
