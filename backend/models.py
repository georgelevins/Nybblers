"""
Pydantic models for RedditDemand API.
Single source of truth for request/response shapes.
Update these when the database schema changes.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Request models ---


class SearchRequest(BaseModel):
    query: str
    subreddit: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class AlertCreateRequest(BaseModel):
    user_email: EmailStr
    query: str


# --- Search response models ---


class SearchResultItem(BaseModel):
    id: str
    title: str
    subreddit: str
    created_utc: datetime
    num_comments: int
    activity_ratio: float
    last_comment_utc: datetime | None
    similarity_score: float
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


# --- Opportunity response models ---


class OpportunityPost(BaseModel):
    id: str
    title: str
    subreddit: str
    created_utc: datetime
    num_comments: int
    activity_ratio: float
    last_comment_utc: datetime | None
    url: str | None
    ranks_on_google: bool


class OpportunitiesResponse(BaseModel):
    results: list[OpportunityPost]


# --- Thread detail models ---


class Comment(BaseModel):
    id: str
    post_id: str
    parent_id: str | None
    parent_type: str | None
    author: str | None
    body: str
    created_utc: datetime
    score: int
    controversiality: int


class ThreadDetail(BaseModel):
    id: str
    subreddit: str
    title: str
    body: str | None
    author: str | None
    created_utc: datetime
    score: int | None
    url: str | None
    num_comments: int | None
    last_comment_utc: datetime | None
    recent_comment_count: int | None
    activity_ratio: float | None
    reconstructed_text: str | None
    comments: list[Comment]


# --- Alert response models ---


class AlertCreateResponse(BaseModel):
    id: UUID
    user_email: str
    query: str
    created_at: datetime


# --- Analytics response models ---


class TimePoint(BaseModel):
    date: str
    label: str
    value: int


class MentionsTrendResponse(BaseModel):
    points: list[TimePoint]


class SubredditUsersResponse(BaseModel):
    subreddits: dict[str, list[str]]


class GrowthMomentumResponse(BaseModel):
    weekly: list[TimePoint]
    monthly: list[TimePoint]


class TopMatch(BaseModel):
    id: str
    subreddit: str
    author: str | None
    body: str
    score: int
    url: str | None
    similarity: float
    kind: str  # "post" | "comment"


class TopMatchesResponse(BaseModel):
    matches: list[TopMatch]


# --- Active threads (engagement campaign) ---


class ActiveThread(BaseModel):
    id: str
    title: str
    subreddit: str
    url: str | None
    last_comment_utc: datetime | None
    score: int
    num_comments: int
    recent_comments: int        # comments within the activity window
    velocity: float             # recent_comments / window_hours
    estimated_impressions: int  # score*4 + num_comments*100


class ActiveThreadsResponse(BaseModel):
    active_count: int
    total_estimated_impressions: int
    window_hours: int
    threads: list[ActiveThread]


# --- Combined analytics (single-request, single-embed) ---


class AnalyticsResponse(BaseModel):
    mentions: MentionsTrendResponse
    subreddits: SubredditUsersResponse
    top_matches: TopMatchesResponse
    growth: GrowthMomentumResponse


# --- Health ---


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime


class DatabaseHealthResponse(BaseModel):
    database: str  # "ok" | "unavailable"
    detail: str | None = None
