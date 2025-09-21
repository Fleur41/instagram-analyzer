import instaloader
from datetime import datetime
from typing import Dict, List, Optional
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
        
        # Configure instaloader for better performance
        self.L.context._session.timeout = 30
        self.L.context._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if use_credentials and Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
            try:
                self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                logger.info("Logged in successfully")
            except Exception as e:
                logger.warning(f"Login failed: {e}")

    def get_profile(self, username: str):
        """Get Instagram profile with better error handling"""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            logger.info(f"Successfully fetched profile for {username}")
            return profile
        except instaloader.exceptions.ProfileNotExistsException:
            raise Exception(f"Profile '{username}' does not exist or is private")
        except Exception as e:
            raise Exception(f"Could not fetch profile for {username}: {e}")

    def analyze_interactions(self, user1: str, user2: str, max_posts: int = 15, max_stories: int = 5) -> Dict:
        """Enhanced analysis function with detailed data"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting detailed analysis: {user1} -> {user2}")
            
            # Get profiles
            user1_profile = self.get_profile(user1)
            user2_profile = self.get_profile(user2)
            
            # Get detailed profile info
            profile_info = self._get_profile_info(user1_profile, user2_profile)
            
            # Analyze posts in detail
            post_analysis = self._analyze_posts_detailed(user1, user2_profile, max_posts)
            
            # Get recent posts info
            recent_posts = self._get_recent_posts_info(user2_profile, min(5, max_posts))
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "user1": user1,
                "user2": user2,
                **profile_info,
                **post_analysis,
                "recent_posts": recent_posts,
                "analysis_time": analysis_time,
                "status": "success",
                "message": "Detailed analysis completed successfully"
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

    def _get_profile_info(self, user1_profile, user2_profile) -> Dict:
        """Get detailed profile information"""
        return {
            "user1_followers": getattr(user1_profile, 'followers', 0),
            "user1_following": getattr(user1_profile, 'followees', 0),
            "user1_posts": getattr(user1_profile, 'mediacount', 0),
            "user2_followers": getattr(user2_profile, 'followers', 0),
            "user2_following": getattr(user2_profile, 'followees', 0),
            "user2_posts": getattr(user2_profile, 'mediacount', 0),
            "user2_is_private": getattr(user2_profile, 'is_private', False),
            "user2_is_verified": getattr(user2_profile, 'is_verified', False),
        }

    def _analyze_posts_detailed(self, user1: str, user2_profile, max_posts: int) -> Dict:
        """Detailed analysis of posts with comprehensive data"""
        like_count = 0
        comments = []
        posts_analyzed = 0
        total_likes_on_posts = 0
        total_comments_on_posts = 0
        
        try:
            logger.info(f"Analyzing up to {max_posts} posts from {user2_profile.username}")
            
            for i, post in enumerate(user2_profile.get_posts()):
                if i >= max_posts:
                    break
                
                posts_analyzed += 1
                total_likes_on_posts += getattr(post, 'likes', 0)
                total_comments_on_posts += getattr(post, 'comments', 0)
                
                # Small delay to avoid rate limiting
                time.sleep(random.uniform(0.2, 0.5))
                
                # Analyze this post for user1 interactions
                post_interactions = self._analyze_single_post(user1, post)
                like_count += post_interactions["likes"]
                comments.extend(post_interactions["comments"])
                
                logger.debug(f"Analyzed post {i+1}: {post_interactions}")
                    
        except Exception as e:
            logger.warning(f"Post analysis had issues: {e}")
        
        return {
            "posts_analyzed": posts_analyzed,
            "user1_likes_count": like_count,
            "user1_comments_count": len(comments),
            "user1_comments": comments,
            "total_likes_on_analyzed_posts": total_likes_on_posts,
            "total_comments_on_analyzed_posts": total_comments_on_posts,
            "analysis_notes": f"Analyzed {posts_analyzed} most recent posts"
        }

    def _analyze_single_post(self, user1: str, post) -> Dict:
        """Analyze a single post for user interactions"""
        likes = 0
        comments = []
        
        try:
            # Check if user1 liked this post
            if hasattr(post, 'get_likes') and getattr(post, 'likes', 0) > 0:
                try:
                    # Check first 50 likes for performance
                    like_samples = 0
                    for like in post.get_likes():
                        if hasattr(like, 'username') and like.username == user1:
                            likes = 1
                            break
                        like_samples += 1
                        if like_samples >= 50:
                            break
                except Exception as e:
                    logger.debug(f"Like check failed: {e}")
            
            # Check if user1 commented on this post
            if hasattr(post, 'get_comments') and getattr(post, 'comments', 0) > 0:
                try:
                    # Check all comments (within reason)
                    comment_samples = 0
                    for comment in post.get_comments():
                        if (hasattr(comment, 'owner') and 
                            hasattr(comment.owner, 'username') and 
                            comment.owner.username == user1):
                            comments.append({
                                "date": getattr(comment, 'created_at_utc', datetime.now()).isoformat(),
                                "text": getattr(comment, 'text', ''),
                                "post_url": getattr(post, 'url', ''),
                                "post_date": getattr(post, 'date', datetime.now()).isoformat(),
                                "likes_on_post": getattr(post, 'likes', 0),
                                "comments_on_post": getattr(post, 'comments', 0)
                            })
                        comment_samples += 1
                        if comment_samples >= 100:  # Limit to 100 comments per post
                            break
                except Exception as e:
                    logger.debug(f"Comment check failed: {e}")
                    
        except Exception as e:
            logger.debug(f"Post analysis failed: {e}")
        
        return {
            "likes": likes,
            "comments": comments
        }

    def _get_recent_posts_info(self, profile, count: int) -> List[Dict]:
        """Get information about recent posts"""
        recent_posts = []
        
        try:
            for i, post in enumerate(profile.get_posts()):
                if i >= count:
                    break
                
                recent_posts.append({
                    "post_date": getattr(post, 'date', datetime.now()).isoformat(),
                    "likes": getattr(post, 'likes', 0),
                    "comments": getattr(post, 'comments', 0),
                    "caption": getattr(post, 'caption', '')[:100] + "..." if getattr(post, 'caption', '') else "",
                    "url": getattr(post, 'url', ''),
                    "is_video": getattr(post, 'is_video', False)
                })
                
        except Exception as e:
            logger.warning(f"Could not get recent posts info: {e}")
        
        return recent_posts












# import instaloader
# from datetime import datetime
# from typing import Dict, List, Optional
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
        
#         if use_credentials and Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
#             try:
#                 self.L.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
#                 logger.info("Logged in successfully")
#             except Exception as e:
#                 logger.warning(f"Login failed: {e}")

#     def get_profile(self, username: str):
#         """Get Instagram profile"""
#         try:
#             # Set timeout for the session
#             self.L.context._session.timeout = 20
#             return instaloader.Profile.from_username(self.L.context, username)
#         except Exception as e:
#             logger.error(f"Failed to fetch profile for {username}: {e}")
#             raise Exception(f"Could not fetch profile for {username}: {e}")

#     def analyze_interactions(self, user1: str, user2: str, max_posts: int = 10, max_stories: int = 5) -> Dict:
#         """Main analysis function"""
#         start_time = datetime.now()
        
#         try:
#             logger.info(f"Starting analysis: {user1} -> {user2}")
            
#             # Get profiles
#             user1_profile = self.get_profile(user1)
#             user2_profile = self.get_profile(user2)
            
#             # Basic info
#             user1_followers = getattr(user1_profile, 'followers', 'Unknown')
#             user2_followers = getattr(user2_profile, 'followers', 'Unknown')
            
#             # Analyze posts
#             post_stats = self._analyze_posts(user1, user2_profile, max_posts)
            
#             analysis_time = (datetime.now() - start_time).total_seconds()
            
#             result = {
#                 "user1": user1,
#                 "user2": user2,
#                 "user1_followers": user1_followers,
#                 "user2_followers": user2_followers,
#                 "post_likes": post_stats["likes"],
#                 "post_comments": post_stats["comments_count"],
#                 "comments": post_stats["comments"],
#                 "analysis_time": analysis_time,
#                 "status": "success",
#                 "message": "Analysis completed successfully"
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

#     def _analyze_posts(self, user1: str, user2_profile, max_posts: int) -> Dict:
#         """Analyze posts for interactions"""
#         like_count = 0
#         comments = []
        
#         try:
#             posts = user2_profile.get_posts()
#             for i, post in enumerate(posts):
#                 if i >= max_posts:
#                     break
                
#                 # Small delay to avoid rate limiting
#                 time.sleep(random.uniform(0.1, 0.3))
                
#                 # Check likes
#                 try:
#                     if hasattr(post, 'get_likes'):
#                         like_samples = 0
#                         for like in post.get_likes():
#                             if hasattr(like, 'username') and like.username == user1:
#                                 like_count += 1
#                                 break
#                             like_samples += 1
#                             if like_samples >= 10:  # Only check first 10 likers
#                                 break
#                 except Exception as e:
#                     logger.debug(f"Like check failed for post {i}: {e}")
                
#                 # Check comments
#                 try:
#                     if hasattr(post, 'get_comments'):
#                         comment_samples = 0
#                         for comment in post.get_comments():
#                             if (hasattr(comment, 'owner') and 
#                                 hasattr(comment.owner, 'username') and 
#                                 comment.owner.username == user1):
#                                 comments.append({
#                                     "date": getattr(comment, 'created_at_utc', datetime.now()),
#                                     "text": getattr(comment, 'text', '')[:150],
#                                     "post_url": getattr(post, 'url', '')
#                                 })
#                                 break  # Only one comment per post
#                             comment_samples += 1
#                             if comment_samples >= 5:  # Only check first 5 comments
#                                 break
#                 except Exception as e:
#                     logger.debug(f"Comment check failed for post {i}: {e}")
                    
#         except Exception as e:
#             logger.warning(f"Post analysis had issues: {e}")
        
#         return {
#             "likes": like_count,
#             "comments_count": len(comments),
#             "comments": comments
#         }

