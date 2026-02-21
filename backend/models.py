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


class DemandCountRequest(BaseModel):
    query: str
    subreddit: str | None = None
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)


class SearchLeadsRequest(BaseModel):
    query: str
    subreddit: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)


class AlertCreateRequest(BaseModel):
    user_email: EmailStr
    query: str


# --- Search response models ---


class SearchResultItem(BaseModel):
    id: str
    title: str
    subreddit: str
    author: str | None  # so you can surface "people who want the solution"
    created_utc: datetime
    num_comments: int
    recent_comment_count: int  # comments in last 90 days — "still active?"
    activity_ratio: float
    last_comment_utc: datetime | None
    similarity_score: float
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]


class DemandCountResponse(BaseModel):
    matching_posts: int
    distinct_authors: int
    total_comments_on_matching: int


class LeadResultItem(BaseModel):
    comment_id: str
    post_id: str
    author: str | None
    snippet: str
    similarity_score: float
    post_url: str


class SearchLeadsResponse(BaseModel):
    results: list[LeadResultItem]


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


# --- Health ---


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime
