import re
from datetime import datetime, timezone
import yt_dlp


def _parse_date(date_str: str | None) -> str | None:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def _parse_ts(ts: int | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def get_channel_recent_videos(channel_url: str, max_videos: int = 15) -> list[dict]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlist_items": f"1-{max_videos}",
    }
    url = channel_url.rstrip("/") + "/videos"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        entries = result.get("entries") or []
        videos = []
        for e in entries:
            if not e or not e.get("id"):
                continue
            videos.append({
                "id": e["id"],
                "title": e.get("title"),
                "upload_date": e.get("upload_date"),
                "upload_date_iso": _parse_date(e.get("upload_date")),
                "duration": e.get("duration"),
                "url": f"https://www.youtube.com/watch?v={e['id']}",
            })
        return videos


def get_video_detail(video_id: str, max_comments: int = 200) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                "comment_sort": ["top"],
                "max_comments": [str(max_comments)],
            }
        },
        "skip_download": True,
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    comments_raw = info.get("comments") or []
    comments = []
    for c in comments_raw:
        comments.append({
            "id": c.get("id", ""),
            "author": c.get("author", ""),
            "text": c.get("text", ""),
            "like_count": c.get("like_count", 0),
            "parent": c.get("parent", "root"),
            "timestamp_iso": _parse_ts(c.get("timestamp")),
        })

    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "description": info.get("description", ""),
        "upload_date": info.get("upload_date"),
        "upload_date_iso": _parse_date(info.get("upload_date")),
        "duration": info.get("duration"),
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "comment_count": info.get("comment_count", 0),
        "comments": comments,
    }
