from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Comment(BaseModel):
    date: datetime
    text: str
    post_url: str

class Response(BaseModel):
    user1_comment: str
    user2_reply: str
    date: datetime
    post_url: str

class InteractionAnalysis(BaseModel):
    user1: str
    user2: str
    follows: bool
    follow_date: Optional[datetime] = None
    user1_followers: int
    post_likes: int
    post_comments: int
    comments: List[Comment]
    story_interactions: int
    responses: List[Response]
    analysis_time: float

class AnalysisRequest(BaseModel):
    user1: str
    user2: str
    use_credentials: bool = False
    max_posts: int = 100
    max_stories: int = 50
    fetch_all_posts: bool = False