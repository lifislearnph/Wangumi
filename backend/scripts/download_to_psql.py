import os
import time
import json
import argparse
from pathlib import Path
import psycopg2 as psycopg
from psycopg2.extras import Json
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# ============ 配置部分 ============
API_URL = "https://graphql.anilist.co"
PER_PAGE = 50
SLEEP_SEC = 0.5

REPO_ROOT = Path(__file__).resolve().parents[2]
def _safe_load_env():
    env_path = find_dotenv(str(REPO_ROOT / ".env"), raise_error_if_not_found=False)
    if not env_path:
        return
    try:
        load_dotenv(env_path)
    except Exception:
        # 如果 .env 中有无法解析的行，跳过以免阻塞脚本运行
        pass

_safe_load_env()

# PostgreSQL 连接配置
def _build_pg_config():
    """
    优先使用 PG_* 环境变量，其次兼容 Django 的 DB_*，默认走本地端口转发 15432。
    如果未提供密码且使用 trust 认证，psycopg 允许缺失 password。
    """
    cfg = {
        "host": os.getenv("DB_HOST") or "127.0.0.1",
        "port": os.getenv("DB_PORT") or "15432",
        "dbname": os.getenv("DB_NAME") or "wangumi_db",
        "user": os.getenv("DB_USER") or "postgres",
        "password": os.getenv("DB_PASSWORD") or "",
        "sslmode": "disable",
    }
    if not cfg["password"]:
        cfg.pop("password")
    return cfg

PG_CONFIG = _build_pg_config()

# GraphQL 查询
QUERY = """
query (
  $page: Int,
  $perPage: Int,
  $type: MediaType,
  $beforeDate: FuzzyDateInt,
  $sort: [MediaSort]
) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage }
    media(
      type: $type,
      sort: $sort,
      startDate_lesser: $beforeDate
    ) {
      id
      idMal
      title { romaji english native }
      startDate { year month day }
      format
      episodes
      status
      season
      seasonYear
      averageScore
      popularity
      genres
      coverImage {
        extraLarge
        large
        medium
        color
      }
      studios(isMain: true) { nodes { id name } }
      siteUrl
      updatedAt
      streamingEpisodes {
        title
        url
        site
        thumbnail
      }
      characters(page: 1, perPage: 20) {
        pageInfo { hasNextPage }
        edges {
          role
          node {
            id
            name { full native }
            description
            image { large }
            gender
            dateOfBirth { year month day }
          }
          voiceActors(language: JAPANESE) {
            id
            name { full native }
            languageV2
            image { large }
          }
        }
      }
      staff(perPage: 20) {
        pageInfo { hasNextPage }
        edges {
          role
          node {
            id
            name { full native }
            languageV2
            primaryOccupations
            image { large }
          }
        }
      }
    }
  }
}
"""

def get_conn():
    return psycopg.connect(**PG_CONFIG)

def fetch_page(page, per_page, before_date, sort):
    variables = {
        "page": page,
        "perPage": per_page,
        "type": "ANIME",
        "beforeDate": before_date,
        "sort": sort,
    }
    resp = requests.post(API_URL, json={"query": QUERY, "variables": variables})
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
    data = resp.json()["data"]["Page"]
    return data["media"], data["pageInfo"]["hasNextPage"]

def _parse_date(date_dict):
    if not date_dict:
        return None
    try:
        year = date_dict.get("year")
        if not year:
            return None
        month = date_dict.get("month") or 1
        day = date_dict.get("day") or 1
        return datetime(int(year), int(month), int(day)).date()
    except Exception:
        return None

def _map_character_role(role: str) -> int:
    role = (role or "").upper()
    if role == "MAIN":
        return 1
    if role == "SUPPORTING":
        return 2
    return 3

def _map_gender(gender: str) -> int:
    mapping = {
        "MALE": 1,
        "FEMALE": 2,
        "OTHER": 3,
    }
    return mapping.get((gender or "").upper(), 0)

def upsert_staff_role(cur, name: str, is_voice_role: bool = False) -> int:
    cur.execute(
        """
        INSERT INTO staff_roles (name, description, is_voice_role)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO UPDATE
        SET description = EXCLUDED.description,
            is_voice_role = EXCLUDED.is_voice_role
        RETURNING id
        """,
        (name, "", is_voice_role),
    )
    return cur.fetchone()[0]

def upsert_person(cur, node: dict, is_voice: bool = False) -> int:
    name_info = node.get("name") or {}
    pers_id = node.get("id")
    pers_name = name_info.get("full") or name_info.get("native") or "未知制作人员"
    summary = node.get("description") or ""
    image = (node.get("image") or {}).get("large") or ""
    pers_type = 1
    lang = node.get("languageV2") or ""
    is_producer = False
    is_mangaka = False
    is_artist = False
    is_writer = False
    is_illustrator = False
    is_actor = False
    cur.execute(
        """
        INSERT INTO wangumi_app_person (
            pers_id, pers_name, pers_type, pers_info,
            is_producer, is_mangaka, is_artist, is_seiyu, is_writer, is_illustrator, is_actor,
            summary, pers_img, comment_count, lock, anidb_id, ban, redirect, nsfw,
            created_at, updated_at, lastpost
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        ON CONFLICT (pers_id) DO UPDATE
        SET pers_name = EXCLUDED.pers_name,
            pers_info = COALESCE(NULLIF(EXCLUDED.pers_info, ''), wangumi_app_person.pers_info),
            is_seiyu = wangumi_app_person.is_seiyu OR EXCLUDED.is_seiyu,
            is_producer = wangumi_app_person.is_producer OR EXCLUDED.is_producer,
            is_mangaka = wangumi_app_person.is_mangaka OR EXCLUDED.is_mangaka,
            is_artist = wangumi_app_person.is_artist OR EXCLUDED.is_artist,
            is_writer = wangumi_app_person.is_writer OR EXCLUDED.is_writer,
            is_illustrator = wangumi_app_person.is_illustrator OR EXCLUDED.is_illustrator,
            is_actor = wangumi_app_person.is_actor OR EXCLUDED.is_actor,
            summary = COALESCE(NULLIF(EXCLUDED.summary, ''), wangumi_app_person.summary),
            pers_img = COALESCE(NULLIF(EXCLUDED.pers_img, ''), wangumi_app_person.pers_img),
            updated_at = COALESCE(EXCLUDED.updated_at, wangumi_app_person.updated_at),
            lastpost = COALESCE(wangumi_app_person.lastpost, EXCLUDED.lastpost)
        RETURNING pers_id
        """,
        (
            pers_id,
            pers_name,
            pers_type,
            lang,
            is_producer,
            is_mangaka,
            is_artist,
            is_voice,
            is_writer,
            is_illustrator,
            is_actor,
            summary or "",
            image or "",
            0,
            0,
            0,
            0,
            0,
            False,
        ),
    )
    return cur.fetchone()[0]

def upsert_character(cur, node: dict) -> int:
    name = (node.get("name") or {}).get("full") or (node.get("name") or {}).get("native") or "未命名角色"
    char_id = node.get("id")
    image = (node.get("image") or {}).get("large") or ""
    gender = _map_gender(node.get("gender"))
    birth = node.get("dateOfBirth") or {}
    cur.execute(
        """
        INSERT INTO characters (
            id, name, role_type, summary, infobox, image,
            gender, blood_type, birth_year, birth_month, birth_day,
            comment_count, collect_count, lock, is_banned, is_nsfw, redirect_to,
            created_at, last_commented_at
        ) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NULL)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            summary = EXCLUDED.summary,
            image = EXCLUDED.image,
            gender = EXCLUDED.gender,
            blood_type = EXCLUDED.blood_type,
            birth_year = EXCLUDED.birth_year,
            birth_month = EXCLUDED.birth_month,
            birth_day = EXCLUDED.birth_day
        RETURNING id
        """,
        (
            char_id,
            name,
            node.get("description") or "",
            "",
            image,
            gender,
            0,
            birth.get("year"),
            birth.get("month"),
            birth.get("day"),
            0,
            0,
            False,
            False,
            False,
            0,
        ),
    )
    return cur.fetchone()[0]

def upsert_character_voice(cur, character_id: int, person_id: int, note: str):
    cur.execute(
        """
        INSERT INTO character_voice (character_id, person_id, note)
        VALUES (%s, %s, %s)
        ON CONFLICT (character_id, person_id) DO UPDATE
        SET note = EXCLUDED.note
        """,
        (character_id, person_id, note),
    )

def upsert_character_appearance(cur, character_id: int, anime_id: int, role: int, order: int):
    cur.execute(
        """
        INSERT INTO character_appearance (character_id, anime_id, role, appear_eps, "order")
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (character_id, anime_id) DO UPDATE
        SET role = EXCLUDED.role,
            "order" = EXCLUDED."order"
        """,
        (character_id, anime_id, role, "", order),
    )

def upsert_anime_staff(cur, anime_id: int, person_id: int, role_id: int, order: int, note: str = "", character_id=None):
    cur.execute(
        """
        INSERT INTO anime_staff (anime_id, person_id, role_id, character_id, "order", note)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (anime_id, person_id, role_id, character_id) DO UPDATE
        SET "order" = EXCLUDED."order",
            note = EXCLUDED.note
        """,
        (anime_id, person_id, role_id, character_id, order, note),
    )

def upsert_episodes(cur, anime_id: int, total_episodes: int, streaming_eps: list):
    if streaming_eps:
        for idx, ep in enumerate(streaming_eps, start=1):
            title = ep.get("title") or f"Episode {idx}"
            url = ep.get("url") or ""
            site = ep.get("site") or ""
            online_urls = Json([{"site": site, "url": url}]) if (site or url) else Json([])
            cur.execute(
                """
                INSERT INTO wangumi_app_episode (
                    anime_id, episode_number, title, title_cn, description,
                    release_date, duration, online_urls, episode_type, disc_number,
                    rating, comments, resources, is_locked, is_banned, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (anime_id, episode_number) DO UPDATE
                SET title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    online_urls = EXCLUDED.online_urls,
                    updated_at = NOW()
                """,
                (
                    anime_id,
                    idx,
                    title,
                    "",
                    "",
                    None,
                    "",
                    online_urls,
                    1,
                    0,
                    0,
                    0,
                    0,
                    False,
                    False,
                ),
            )
    elif total_episodes:
        for ep_num in range(1, int(total_episodes) + 1):
            cur.execute(
                """
                INSERT INTO wangumi_app_episode (
                    anime_id, episode_number, title, title_cn, description,
                    release_date, duration, online_urls, episode_type, disc_number,
                    rating, comments, resources, is_locked, is_banned, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (anime_id, episode_number) DO UPDATE
                SET title = EXCLUDED.title,
                    updated_at = NOW()
                """,
                (
                    anime_id,
                    ep_num,
                    f"Episode {ep_num}",
                    "",
                    "",
                    None,
                    "",
                    Json([]),
                    1,
                    0,
                    0,
                    0,
                    0,
                    False,
                    False,
                ),
            )

def upsert_items(conn, items):
    with conn.cursor() as cur:
        for m in items:
            nodes = m.get("studios", {}).get("nodes", [])
            if nodes:
                s_id = nodes[0].get("id")
                s_name = nodes[0].get("name")
            else:
                s_id = None
                s_name = None

# 将 Unix 时间戳转换成 datetime
            updated_at_ts = m.get("updatedAt")
            updated_at = datetime.fromtimestamp(updated_at_ts) if updated_at_ts else None


            start_date = m.get("startDate") or {}
            release_date = _parse_date(start_date)

            cur.execute(
                """
                INSERT INTO wangumi_app_anime (
                    id, title, title_cn, description, release_date, airtime,
                    cover_image, cover_url, uid, rating, popularity, wishes, collections,
                    doing, on_hold, dropped, status, total_episodes, platform, is_series, nsfw, is_banned,
                    is_admin, created_at, updated_at, genres
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    title_cn = EXCLUDED.title_cn,
                    description = EXCLUDED.description,
                    release_date = EXCLUDED.release_date,
                    airtime = EXCLUDED.airtime,
                    cover_image = EXCLUDED.cover_image,
                    cover_url = EXCLUDED.cover_url,
                    uid = EXCLUDED.uid,
                    rating = EXCLUDED.rating,
                    popularity = EXCLUDED.popularity,
                    wishes = EXCLUDED.wishes,
                    collections = EXCLUDED.collections,
                    doing = EXCLUDED.doing,
                    on_hold = EXCLUDED.on_hold,
                    dropped = EXCLUDED.dropped,
                    status = EXCLUDED.status,
                    total_episodes = EXCLUDED.total_episodes,
                    platform = EXCLUDED.platform,
                    is_series = EXCLUDED.is_series,
                    nsfw = EXCLUDED.nsfw,
                    is_banned = EXCLUDED.is_banned,
                    is_admin = EXCLUDED.is_admin,
                    updated_at = EXCLUDED.updated_at,
                    genres = EXCLUDED.genres
                    """,
                (
                    m["id"],
                    (m.get("title") or {}).get("romaji") or "未知标题",
                    (m.get("title") or {}).get("native")
                    or (m.get("title") or {}).get("english")
                    or "",
                    m.get("description") or "",
                    release_date,
                    "",   # airtime
                    "",  # cover_image stored only for local uploads
                    (m.get("coverImage") or {}).get("large")
                    or (m.get("coverImage") or {}).get("extraLarge")
                    or (m.get("coverImage") or {}).get("medium")
                    or "",
                    str(m.get("idMal", "")),  # uid
                    (m.get("averageScore") or 0) / 10.0,  # rating (转换评分)
                    m.get("popularity") or 0,
                    0,  # wishes
                    0,  # collections
                    0,  # doing
                    0,  # on_hold
                    0,  # dropped
                    m.get("status") or "",
                    m.get("episodes") or 0,
                    "",  # platform
                    True if m.get("format") == "TV" else False,  # is_series
                    False,  # nsfw
                    False,  # is_banned
                    True,  # is_admin（导入数据标记为官方）
                    updated_at,  # created_at
                    updated_at,  # updated_at
                    Json(m.get("genres") or []),
                )
            )
            anime_id = m["id"]

            # Episodes
            upsert_episodes(
                cur,
                anime_id,
                m.get("episodes") or 0,
                m.get("streamingEpisodes") or [],
            )

            # Characters & voices
            character_edges = (m.get("characters") or {}).get("edges") or []
            for order, edge in enumerate(character_edges, start=1):
                character_node = edge.get("node") or {}
                char_id = upsert_character(cur, character_node)
                role_value = _map_character_role(edge.get("role"))
                upsert_character_appearance(cur, char_id, anime_id, role_value, order)

                voice_actors = edge.get("voiceActors") or []
                for va in voice_actors:
                    person_id = upsert_person(cur, va, is_voice=True)
                    upsert_character_voice(cur, char_id, person_id, va.get("languageV2") or "")
                    # 关联声优到番剧工作人员
                    voice_role_id = upsert_staff_role(cur, "Voice Actor", is_voice_role=True)
                    upsert_anime_staff(cur, anime_id, person_id, voice_role_id, order, note="voice", character_id=char_id)

            # Staff
            staff_edges = (m.get("staff") or {}).get("edges") or []
            for order, edge in enumerate(staff_edges, start=1):
                person_node = (edge or {}).get("node") or {}
                if not person_node:
                    continue
                person_id = upsert_person(cur, person_node, is_voice=False)
                role_name = edge.get("role") or "Staff"
                role_id = upsert_staff_role(cur, role_name, is_voice_role=False)
                upsert_anime_staff(cur, anime_id, person_id, role_id, order, note=person_node.get("languageV2") or "")
    conn.commit()


def _before_date_from_year(year: int) -> int:
    return year * 10000 + 101


def main():
    parser = argparse.ArgumentParser(description="抓取指定年份之前的热门番剧并写入")
    parser.add_argument("--before-year", type=int, default=2025, help="抓取该年份之前的数据，默认 2025")
    parser.add_argument("--limit", type=int, default=1, help="抓取总条数上限，默认 30")
    parser.add_argument(
        "--sort",
        type=str,
        default="POPULARITY_DESC",
        choices=["POPULARITY_DESC", "TRENDING_DESC", "SCORE_DESC"],
        help="默认 POPULARITY_DESC"
    )
    args = parser.parse_args()

    target_total = max(0, args.limit)
    if target_total == 0:
        print("limit 为 0，无需抓取。")
        return

    before_date = _before_date_from_year(args.before_year)
    sort_arg = [args.sort]

    conn = get_conn()
    page = 1
    fetched = 0
    try:
        while True:
            remaining = target_total - fetched
            if remaining <= 0:
                break
            per_page = min(PER_PAGE, remaining)
            media, has_next = fetch_page(page, per_page, before_date, sort_arg)
            if not media:
                break
            upsert_items(conn, media)
            fetched += len(media)
            print(f"Page {page}: +{len(media)} items (total {fetched}/{target_total})")
            if not has_next:
                break
            page += 1
            time.sleep(SLEEP_SEC)
    finally:
        conn.close()

    print("Finished!")

if __name__ == "__main__":
    main()
