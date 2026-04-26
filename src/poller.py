"""
Main polling script - runs every 2h via GitHub Actions.
Logic:
  1. Fetch active channels from Supabase
  2. For each channel, get recent videos via yt-dlp
  3. New video → collect detail + comments → insert → notify Telegram
  4. Tracking video (< 72h) → update snapshot
  5. Tracking video (>= 72h) → set archived
"""
import os
import sys
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
load_dotenv()

import db
import collector
import notifier

TRACKING_HOURS = 72


def hours_since(iso_str: str | None) -> float:
    if not iso_str:
        return 0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(tz=timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 0


def process_channel(channel: dict):
    handle = channel.get("handle") or channel.get("name")
    url = channel["url"]
    print(f"\n[poller] Checking channel: {handle}")

    videos = collector.get_channel_recent_videos(url, max_videos=15)
    print(f"[poller] Found {len(videos)} recent videos")

    for v in videos:
        vid = v["id"]
        existing = db.video_exists(vid)

        if not existing:
            print(f"[poller] NEW video: {v['title'][:60]}")
            detail = collector.get_video_detail(vid, max_comments=200)
            row = db.insert_video(channel["id"], detail)
            db.insert_snapshot(row["id"], detail)
            db.insert_comments(row["id"], detail.get("comments", []))
            db.update_video_status(vid, "tracking")

            notifier.send_telegram(
                f"🎬 <b>새 영상 감지</b>\n"
                f"채널: {handle}\n"
                f"제목: {detail['title']}\n"
                f"조회수: {detail['view_count']:,} | 댓글: {len(detail['comments'])}개\n"
                f"https://www.youtube.com/watch?v={vid}"
            )
        else:
            age_h = hours_since(existing.get("first_seen_at"))
            if existing["status"] == "tracking":
                if age_h >= TRACKING_HOURS:
                    print(f"[poller] ARCHIVING: {vid} (age {age_h:.1f}h)")
                    db.update_video_status(vid, "archived")
                else:
                    print(f"[poller] SNAPSHOT: {vid} (age {age_h:.1f}h)")
                    detail = collector.get_video_detail(vid, max_comments=0)
                    db.insert_snapshot(existing["id"], detail)


def main():
    channels = db.get_active_channels()
    if not channels:
        print("[poller] No active channels found")
        sys.exit(0)

    print(f"[poller] Processing {len(channels)} channels")
    for ch in channels:
        try:
            process_channel(ch)
        except Exception as e:
            print(f"[poller] ERROR on channel {ch.get('handle')}: {e}")

    print("\n[poller] Done.")


if __name__ == "__main__":
    main()
