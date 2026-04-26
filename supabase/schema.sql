-- yt-intel Supabase Schema

create table if not exists channels (
  id uuid primary key default gen_random_uuid(),
  handle text not null unique,
  name text,
  url text not null,
  category text,
  active boolean default true,
  added_at timestamptz default now()
);

create table if not exists videos (
  id uuid primary key default gen_random_uuid(),
  channel_id uuid references channels(id),
  video_id text not null unique,
  title text,
  description text,
  upload_date timestamptz,
  duration integer,
  status text default 'new' check (status in ('new', 'tracking', 'archived')),
  first_seen_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists video_snapshots (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id),
  views bigint,
  likes bigint,
  comment_count bigint,
  recorded_at timestamptz default now()
);

create table if not exists comments (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id),
  comment_id text not null unique,
  author text,
  text text,
  likes integer default 0,
  is_reply boolean default false,
  published_at timestamptz,
  collected_at timestamptz default now()
);

-- indexes
create index if not exists idx_videos_channel_id on videos(channel_id);
create index if not exists idx_videos_status on videos(status);
create index if not exists idx_snapshots_video_id on video_snapshots(video_id);
create index if not exists idx_comments_video_id on comments(video_id);
