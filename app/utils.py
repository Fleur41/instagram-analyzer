import instaloader
import requests
from datetime import datetime
from typing import Dict,  Optional
from bs4 import BeautifulSoup
import time
import random
from app.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAnalyzer:
    def __init__(self, use_credentials: bool = False):
        self.L = instaloader.Instaloader()
        self.use_credentials = use_credentials
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session.timeout = 30  # 30 second timeout
        
        if use_credentials and Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
            try:
                self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                logger.info("Logged in successfully using instaloader")
            except Exception as e:
                logger.warning(f"Instaloader login failed: {e}")

    def get_profile(self, username: str):
        """Get Instagram profile with timeout"""
        try:
            # Set timeout for profile fetching
            import signal
            from contextlib import contextmanager

            class TimeoutException(Exception):
                pass

            @contextmanager
            def time_limit(seconds):
                def signal_handler(signum, frame):
                    raise TimeoutException("Timed out!")
                signal.signal(signal.SIGALRM, signal_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)

            try:
                with time_limit(30):  # 30 second timeout
                    return instaloader.Profile.from_username(self.L.context, username)
            except TimeoutException:
                raise Exception("Profile fetch timed out")
                
        except Exception as e:
            logger.warning(f"Instaloader failed for {username}: {e}")
            raise Exception(f"Could not fetch profile for {username}: {e}")

    def analyze_interactions(self, user1: str, user2: str, max_posts: int = 30, max_stories: int = 10) -> Dict:
        """Main analysis function with timeout protection"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting analysis: {user1} -> {user2}")
            
            # Get profiles with timeout
            user1_profile = self.get_profile(user1)
            user2_profile = self.get_profile(user2)
            
            # Basic info
            follows = self._check_follows(user1_profile, user2_profile)
            follow_date = self._get_follow_date(user1, user2_profile)
            
            # Post interactions (with individual timeouts)
            post_stats = self._analyze_post_interactions(user1, user2_profile, max_posts)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "user1": user1,
                "user2": user2,
                "follows": follows,
                "follow_date": follow_date,
                "user1_followers": getattr(user1_profile, 'followers', 'Unknown'),
                "post_likes": post_stats["likes"],
                "post_comments": post_stats["comments_count"],
                "comments": post_stats["comments"],
                "story_interactions": 0,  # Disabled due to API restrictions
                "responses": [],  # Disabled for speed
                "analysis_time": analysis_time,
                "status": "success",
                "message": "Story analysis and response tracking disabled for performance"
            }
            
            logger.info(f"Analysis completed in {analysis_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "user1": user1,
                "user2": user2,
                "error": str(e),
                "analysis_time": analysis_time,
                "status": "error"
            }

    def _check_follows(self, follower, target) -> bool:
        """Check if user1 follows user2 - simplified for speed"""
        try:
            # This is a simplified check to avoid timeouts
            return False  # Disabled for performance
        except:
            return False

    def _get_follow_date(self, user1: str, target_user) -> Optional[datetime]:
        """Approximate follow date - simplified for speed"""
        return None  # Disabled for performance

    def _analyze_post_interactions(self, user1: str, user2_profile, max_posts: int) -> Dict:
        """Analyze post interactions with timeout protection"""
        like_count = 0
        comments = []
        
        try:
            posts = user2_profile.get_posts()
            for i, post in enumerate(posts):
                if i >= max_posts:
                    break
                
                # Add small delay
                time.sleep(random.uniform(0.1, 0.5))
                
                # Check likes (simplified)
                try:
                    if hasattr(post, 'likes') and post.likes > 0:
                        # Just check the count, don't iterate through all likes
                        if post.likes < 1000:  # Only check small posts for performance
                            liker_usernames = [like.username for like in post.get_likes() if hasattr(like, 'username')]
                            if user1 in liker_usernames:
                                like_count += 1
                except:
                    pass
                
                # Check comments
                try:
                    if hasattr(post, 'get_comments'):
                        for comment in post.get_comments():
                            if hasattr(comment, 'owner') and hasattr(comment.owner, 'username'):
                                if comment.owner.username == user1:
                                    comments.append({
                                        "date": getattr(comment, 'created_at_utc', datetime.now()),
                                        "text": getattr(comment, 'text', '')[:100],  # Limit text length
                                        "post_url": getattr(post, 'url', '')
                                    })
                                    break  # Only count one comment per post for performance
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Post analysis partially failed: {e}")
        
        return {
            "likes": like_count,
            "comments_count": len(comments),
            "comments": comments[:10]  # Limit to 10 comments for response size
        }

# import instaloader
# import requests
# from datetime import datetime
# from typing import Dict, List, Optional, Tuple
# from bs4 import BeautifulSoup
# import time
# import random
# from app.config import Config
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class InstagramAnalyzer:
#     def __init__(self, use_credentials: bool = False):
#         self.L = instaloader.Instaloader()
#         self.use_credentials = use_credentials
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         })
        
#         if use_credentials and Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
#             try:
#                 self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
#                 logger.info("Logged in successfully using instaloader")
#             except Exception as e:
#                 logger.warning(f"Instaloader login failed: {e}")
#                 self._web_login()

#     def _web_login(self):
#         """Alternative web login method"""
#         try:
#             login_url = "https://www.instagram.com/accounts/login/"
#             session_url = "https://www.instagram.com/accounts/login/ajax/"
            
#             # Get CSRF token
#             response = self.session.get(login_url)
#             soup = BeautifulSoup(response.text, 'html.parser')
#             csrf = soup.find('meta', attrs={'name': 'csrf-token'})
#             csrf_token = csrf['content'] if csrf else ''
            
#             # Login payload
#             payload = {
#                 'username': Config.INSTAGRAM_USERNAME,
#                 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{Config.INSTAGRAM_PASSWORD}',
#                 'queryParams': '{}',
#                 'optIntoOneTap': 'false'
#             }
            
#             headers = {
#                 'X-CSRFToken': csrf_token,
#                 'X-Instagram-AJAX': '1',
#                 'X-Requested-With': 'XMLHttpRequest',
#                 'Referer': login_url
#             }
            
#             login_response = self.session.post(session_url, data=payload, headers=headers)
#             if login_response.json().get('authenticated'):
#                 logger.info("Web login successful")
#             else:
#                 logger.warning("Web login failed")
                
#         except Exception as e:
#             logger.error(f"Web login error: {e}")

#     def get_profile(self, username: str):
#         """Get Instagram profile with fallback methods"""
#         try:
#             # Try instaloader first
#             return instaloader.Profile.from_username(self.L.context, username)
#         except Exception as e:
#             logger.warning(f"Instaloader failed for {username}: {e}")
#             return self._get_profile_web(username)

#     def _get_profile_web(self, username: str):
#         """Fallback web scraping method for profile"""
#         try:
#             url = f"https://www.instagram.com/{username}/?__a=1&__d=1"
#             response = self.session.get(url, timeout=10)
            
#             if response.status_code == 200:
#                 data = response.json()
#                 user_info = data.get('graphql', {}).get('user', {})
                
#                 # Create a mock profile-like object
#                 class MockProfile:
#                     def __init__(self, user_data):
#                         self.username = user_data.get('username')
#                         self.followers = user_data.get('edge_followed_by', {}).get('count', 0)
#                         self.following = user_data.get('edge_follow', {}).get('count', 0)
#                         self.userid = user_data.get('id')
#                         self.is_private = user_data.get('is_private', False)
                
#                 return MockProfile(user_info)
#             else:
#                 raise Exception(f"HTTP {response.status_code}")
                
#         except Exception as e:
#             logger.error(f"Web profile fetch failed for {username}: {e}")
#             raise Exception(f"Could not fetch profile for {username}")

#     def analyze_interactions(self, user1: str, user2: str, max_posts: int = 50, max_stories: int = 25) -> Dict:
#         """Main analysis function with robust error handling"""
#         start_time = datetime.now()
        
#         try:
#             logger.info(f"Starting analysis: {user1} -> {user2}")
            
#             user1_profile = self.get_profile(user1)
#             user2_profile = self.get_profile(user2)
            
#             # Basic info
#             follows = self._check_follows(user1_profile, user2_profile)
#             follow_date = self._get_follow_date(user1, user2_profile)
            
#             # Post interactions
#             post_stats = self._analyze_post_interactions(user1, user2_profile, max_posts)
            
#             # Story interactions (limited due to API restrictions)
#             story_stats = self._analyze_story_interactions(user1, user2_profile, min(10, max_stories))
            
#             # Responses
#             responses = self._analyze_responses(user1, user2, user2_profile, min(25, max_posts))
            
#             analysis_time = (datetime.now() - start_time).total_seconds()
            
#             result = {
#                 "user1": user1,
#                 "user2": user2,
#                 "follows": follows,
#                 "follow_date": follow_date,
#                 "user1_followers": getattr(user1_profile, 'followers', 'Unknown'),
#                 "post_likes": post_stats["likes"],
#                 "post_comments": post_stats["comments_count"],
#                 "comments": post_stats["comments"],
#                 "story_interactions": story_stats,
#                 "responses": responses,
#                 "analysis_time": analysis_time,
#                 "status": "success"
#             }
            
#             logger.info(f"Analysis completed in {analysis_time:.2f} seconds")
#             return result
            
#         except Exception as e:
#             logger.error(f"Analysis failed: {e}")
#             analysis_time = (datetime.now() - start_time).total_seconds()
            
#             return {
#                 "user1": user1,
#                 "user2": user2,
#                 "error": str(e),
#                 "analysis_time": analysis_time,
#                 "status": "error"
#             }

#     def _check_follows(self, follower, target) -> bool:
#         """Check if user1 follows user2 with fallback"""
#         try:
#             if hasattr(target, 'get_followers'):
#                 return follower in target.get_followers()
#             return False
#         except Exception:
#             return False

#     def _get_follow_date(self, user1: str, target_user) -> Optional[datetime]:
#         """Approximate follow date with fallback"""
#         try:
#             # Try to get from recent posts
#             for post in target_user.get_posts():
#                 try:
#                     if hasattr(post, 'get_likes'):
#                         for like in post.get_likes():
#                             if like.username == user1:
#                                 return post.date
#                     break  # Only check first post
#                 except Exception:
#                     continue
#         except Exception:
#             pass
#         return None

#     def _analyze_post_interactions(self, user1: str, user2_profile, max_posts: int) -> Dict:
#         """Analyze post interactions with error handling"""
#         like_count = 0
#         comments = []
        
#         try:
#             posts = user2_profile.get_posts()
#             for i, post in enumerate(posts):
#                 if i >= max_posts:
#                     break
                
#                 # Add delay to avoid rate limiting
#                 time.sleep(random.uniform(0.5, 1.5))
                
#                 # Check likes
#                 try:
#                     if hasattr(post, 'get_likes') and post.likes > 0:
#                         for like in post.get_likes():
#                             if like.username == user1:
#                                 like_count += 1
#                                 break
#                 except Exception:
#                     pass
                
#                 # Check comments
#                 try:
#                     if hasattr(post, 'get_comments'):
#                         for comment in post.get_comments():
#                             if comment.owner.username == user1:
#                                 comments.append({
#                                     "date": getattr(comment, 'created_at_utc', datetime.now()),
#                                     "text": getattr(comment, 'text', ''),
#                                     "post_url": getattr(post, 'url', '')
#                                 })
#                 except:
#                     pass
                    
#         except Exception as e:
#             logger.warning(f"Post analysis partially failed: {e}")
        
#         return {
#             "likes": like_count,
#             "comments_count": len(comments),
#             "comments": comments
#         }

#     def _analyze_story_interactions(self, user1: str, user2_profile, max_stories: int) -> int:
#         """Analyze story interactions - simplified due to API restrictions"""
#         return 0  # Stories are heavily restricted in current API

#     def _analyze_responses(self, user1: str, user2: str, user2_profile, max_posts: int) -> List[Dict]:
#         """Analyze responses to user1 with error handling"""
#         responses = []
        
#         try:
#             posts = user2_profile.get_posts()
#             for i, post in enumerate(posts):
#                 if i >= max_posts:
#                     break
                
#                 time.sleep(random.uniform(0.5, 1.0))
                
#                 try:
#                     if hasattr(post, 'get_comments'):
#                         user1_comments = []
#                         user2_replies = []
                        
#                         for comment in post.get_comments():
#                             comment_owner = getattr(comment, 'owner', None)
#                             if comment_owner and comment_owner.username == user1:
#                                 user1_comments.append(comment)
#                             elif comment_owner and comment_owner.username == user2:
#                                 user2_replies.append(comment)
                        
#                         # Check for responses
#                         for user1_comment in user1_comments:
#                             for user2_reply in user2_replies:
#                                 if (hasattr(user2_reply, 'created_at_utc') and 
#                                     hasattr(user1_comment, 'created_at_utc') and
#                                     user2_reply.created_at_utc > user1_comment.created_at_utc):
#                                     responses.append({
#                                         "user1_comment": getattr(user1_comment, 'text', ''),
#                                         "user2_reply": getattr(user2_reply, 'text', ''),
#                                         "date": user2_reply.created_at_utc,
#                                         "post_url": getattr(post, 'url', '')
#                                     })
#                 except Exception:
#                     continue
                    
#         except Exception as e:
#             logger.warning(f"Response analysis partially failed: {e}")
        
#         return responses