import os
from supabase import create_client, Client

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


def get_active_channels():
    return get_client().table("channels").select("*").eq("active", True).execute().data


def video_exists(video_id: str) -> dict | None:
    rows = get_client().table("videos").select("*").eq("video_id", video_id).execute().data
    return rows[0] if rows else None


def insert_video(channel_id: str, info: dict) -> dict:
    row = {
        "channel_id": channel_id,
        "video_id": info["id"],
        "title": info.get("title"),
        "description": info.get("description", "")[:2000],
        "upload_date": info.get("upload_date_iso"),
        "duration": int(info["duration"]) if info.get("duration") is not None else None,
        "status": "new",
    }
    return get_client().table("videos").insert(row).execute().data[0]


def update_video_status(video_id: str, status: str):
    get_client().table("videos").update({"status": status, "updated_at": "now()"}).eq("video_id", video_id).execute()


def insert_snapshot(video_db_id: str, info: dict):
    row = {
        "video_id": video_db_id,
        "views": info.get("view_count", 0),
        "likes": info.get("like_count", 0),
        "comment_count": info.get("comment_count", 0),
    }
    get_client().table("video_snapshots").insert(row).execute()


def insert_comments(video_db_id: str, comments: list):
    if not comments:
        return
    rows = []
    for c in comments:
        rows.append({
            "video_id": video_db_id,
            "comment_id": c.get("id", ""),
            "author": c.get("author", ""),
            "text": (c.get("text") or "")[:2000],
            "likes": c.get("like_count", 0),
            "is_reply": c.get("parent") != "root",
            "published_at": c.get("timestamp_iso"),
        })
    # upsert to avoid duplicates
    get_client().table("comments").upsert(rows, on_conflict="comment_id").execute()


def get_tracking_videos():
    return get_client().table("videos").select("*").eq("status", "tracking").execute().data
