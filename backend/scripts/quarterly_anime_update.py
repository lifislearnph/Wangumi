"""
该脚本用于在每年1月、4月、7月、10月从外部API拉取当季更新的番剧数据，
并更新到PostgreSQL数据库中。适用于华为云函数流环境。
"""

import os
import time
import json 
import logging
import requests
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import pg8000.native


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置常量
API_URL = "https://graphql.anilist.co"
PER_PAGE = 50
SLEEP_SEC = 0.5

# 华为云函数流环境变量配置
def get_pg_config():
    """
    获取数据库连接配置
    优先使用华为云函数环境变量，其次使用本地 Django 风格配置环境变量
    """
    # 华为云函数环境变量
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    dbname = os.getenv("PG_DATABASE")
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")
    sslmode = os.getenv("PG_SSLMODE") or "prefer"

    # 如果华为云变量未设置，尝试本地 Django 环境变量
    if not host:
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = os.getenv("DB_PORT", "15432")
        dbname = os.getenv("POSTGRES_DB", "wangumi_db")
        user = os.getenv("DB_USER", "gumi")
        password = os.getenv("DB_PASSWORD", "1234")
        # sslmode 在本地一般不启用
        sslmode = "disable"

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
    }

def get_db_connection():
    config = get_pg_config()
    try:
        conn = pg8000.native.Connection(
            host=config['host'],
            port=int(config['port']),
            database=config['dbname'],
            user=config['user'],
            password=config['password']
        )
        logger.info(f"数据库连接成功: {config['host']}:{config['port']}/{config['dbname']}")
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


def is_quarter_month() -> bool:
    """
    检查当前月份是否为季度月份（1、4、7、10）
    华为云函数流会定期调用此函数，但只在季度月份执行实际更新
    """
    current_month = datetime.now().month
    return current_month in [1, 4, 7, 10]

def get_current_season() -> Tuple[int, str]:
    """
    获取当前季度信息
    返回: (年份, 季节名称)
    """
    now = datetime.now()
    year = now.year
    month = now.month

    if month in [1, 2, 3]:
        season = "WINTER"  # 冬季（冬季番剧在1月更新）
    elif month in [4, 5, 6]:
        season = "SPRING"  # 春季
    elif month in [7, 8, 9]:
        season = "SUMMER"  # 夏季
    else:
        season = "FALL"    # 秋季

    return year, season

def build_season_query(year: int, season: str) -> str:
    """
    构建获取当季番剧的GraphQL查询
    """
    return f"""
    query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int, $sort: [MediaSort]) {{
        Page(page: $page, perPage: $perPage) {{
            pageInfo {{ currentPage hasNextPage }}
            media(
                type: ANIME,
                season: $season,
                seasonYear: $seasonYear,
                sort: $sort,
                status: RELEASING
            ) {{
                id
                idMal
                title {{ romaji english native }}
                startDate {{ year month day }}
                format
                episodes
                status
                season
                seasonYear
                averageScore
                popularity
                genres
                coverImage {{
                    extraLarge
                    large
                    medium
                    color
                }}
                studios(isMain: true) {{ nodes {{ id name }} }}
                siteUrl
                updatedAt
                streamingEpisodes {{
                    title
                    url
                    site
                    thumbnail
                }}
                characters(page: 1, perPage: 20) {{
                    pageInfo {{ hasNextPage }}
                    edges {{
                        role
                        node {{
                            id
                            name {{ full native }}
                            description
                            image {{ large }}
                            gender
                            dateOfBirth {{ year month day }}
                        }}
                        voiceActors(language: JAPANESE) {{
                            id
                            name {{ full native }}
                            languageV2
                            image {{ large }}
                        }}
                    }}
                }}
                staff(perPage: 20) {{
                    pageInfo {{ hasNextPage }}
                    edges {{
                        role
                        node {{
                            id
                            name {{ full native }}
                            languageV2
                            primaryOccupations
                            image {{ large }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    """

def fetch_seasonal_anime(year: int, season: str, page: int = 1, per_page: int = PER_PAGE) -> Tuple[List[Dict], bool]:
    """
    获取当季番剧数据
    返回: (番剧列表, 是否有下一页)
    """
    query = build_season_query(year, season)
    variables = {
        "page": page,
        "perPage": per_page,
        "season": season,
        "seasonYear": year,
        "sort": ["POPULARITY_DESC", "START_DATE_DESC"]
    }

    try:
        response = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            timeout=30
        )
        response.raise_for_status()

        data = response.json().get("data", {}).get("Page", {})
        media = data.get("media", [])
        has_next_page = data.get("pageInfo", {}).get("hasNextPage", False)

        logger.info(f"获取到 {len(media)} 部番剧数据 (页面 {page})")
        return media, has_next_page

    except Exception as e:
        logger.error(f"获取番剧数据失败: {e}")
        raise

def parse_date(date_dict: Optional[Dict]) -> Optional[date]:
    """解析API返回的日期字典"""
    if not date_dict:
        return None
    try:
        year = date_dict.get("year")
        if not year:
            return None
        month = date_dict.get("month") or 1
        day = date_dict.get("day") or 1
        return date(int(year), int(month), int(day))
    except Exception:
        return None

def map_character_role(role: str) -> int:
    """映射角色类型"""
    role = (role or "").upper()
    if role == "MAIN":
        return 1
    if role == "SUPPORTING":
        return 2
    return 3  # OTHER

def map_gender(gender: str) -> int:
    """映射性别"""
    mapping = {
        "MALE": 1,
        "FEMALE": 2,
        "OTHER": 3,
    }
    return mapping.get((gender or "").upper(), 0)


def upsert_anime_data(conn, anime_list: List[Dict]) -> int:
    processed = 0
    for anime in anime_list:
        try:
            # 先打印调试信息，查看数据结构
            anime_id = anime.get("id")
            if not anime_id:
                logger.warning(f"跳过番剧，缺少 id 字段: {anime.get('title', {}).get('romaji', '未知标题')}")
                continue
        
            title_info = anime.get("title", {})
            start_date = parse_date(anime.get("startDate"))
            updated_at_ts = anime.get("updatedAt")
            updated_at = datetime.fromtimestamp(updated_at_ts).isoformat() if updated_at_ts else None
            studio_nodes = anime.get("studios", {}).get("nodes", [])
            studio_name = studio_nodes[0].get("name") if studio_nodes else ""

            sql = """
                INSERT INTO wangumi_app_anime (
                    id, title, title_cn, description, release_date, airtime,
                    cover_image, cover_url, uid, rating, popularity, wishes, collections,
                    doing, on_hold, dropped, status, total_episodes, platform, is_series,
                    nsfw, is_banned, is_admin, created_at, updated_at, genres
                ) VALUES (:id,:title,:title_cn,:description,:release_date,:airtime,
                            :cover_image,:cover_url,:uid,:rating,:popularity,:wishes,:collections,
                            :doing,:on_hold,:dropped,:status,:total_episodes,:platform,:is_series,
                            :nsfw,:is_banned,:is_admin,:created_at,:updated_at,:genres)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    title_cn = EXCLUDED.title_cn,
                    description = EXCLUDED.description,
                    release_date = EXCLUDED.release_date,
                    cover_url = EXCLUDED.cover_url,
                    rating = EXCLUDED.rating,
                    popularity = EXCLUDED.popularity,
                    status = EXCLUDED.status,
                    total_episodes = EXCLUDED.total_episodes,
                    updated_at = EXCLUDED.updated_at,
                    genres = EXCLUDED.genres
            """

            params = {
                'id': anime.get('id') or "",  # 注意这里应该是 "id" 不是 "anime_id"
                "title": title_info.get("romaji") or "未知标题",
                "title_cn": title_info.get("native") or title_info.get("english") or "",
                "description": anime.get("description", ""),
                "release_date": start_date.isoformat() if start_date else None,
                "airtime": "",
                "cover_image": "",
                "cover_url": (anime.get("coverImage") or {}).get("large") or "",
                "uid": str(anime.get("idMal", "")),
                "rating": (anime.get("averageScore") or 0) / 10.0,
                "popularity": anime.get("popularity", 0),
                "wishes": 0,
                "collections": 0,
                "doing": 0,
                "on_hold": 0,
                "dropped": 0,
                "status": anime.get("status", ""),
                "total_episodes": anime.get("episodes") or 0,
                "platform": "",
                "is_series": anime.get("format") == "TV",
                "nsfw": False,
                "is_banned": False,
                "is_admin": True,
                "created_at": updated_at,
                "updated_at": updated_at,
                "genres": json.dumps(anime.get("genres", []))
            }
    
            conn.run(sql, **params)
            processed += 1
        except Exception as e:
            logger.error(f"处理番剧 {anime.get('id')} 时出错: {e}")
            continue
    return processed


def update_anime_episodes(conn, anime_list: List[Dict]) -> int:
    """
    更新番剧剧集信息
    只有当有具体的流媒体剧集信息时才插入剧集，有总集数但没有具体内容时不插入
    """
    updated = 0
    for anime in anime_list:
        try:
            anime_id = anime["id"]
            streaming_eps = anime.get("streamingEpisodes", [])

            # 只有当有流媒体剧集信息时才插入剧集数据
            if streaming_eps:
                for idx, ep in enumerate(streaming_eps, start=1):
                    title = ep.get("title") or f"Episode {idx}"
                    url = ep.get("url") or ""
                    site = ep.get("site") or ""
                    online_urls = json.dumps([{"site": site, "url": url}]) if (site or url) else json.dumps([])

                    sql = """
                        INSERT INTO wangumi_app_episode (
                            anime_id, episode_number, title, title_cn, description,
                            release_date, duration, online_urls, episode_type, disc_number,
                            rating, comments, resources, is_locked, is_banned, created_at, updated_at
                        ) VALUES (:anime_id, :episode_number, :title, :title_cn, :description,
                            :release_date, :duration, :online_urls, :episode_type, :disc_number,
                            :rating, :comments, :resources, :is_locked, :is_banned, NOW(), NOW())
                        ON CONFLICT (anime_id, episode_number) DO UPDATE
                        SET title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            online_urls = EXCLUDED.online_urls,
                            updated_at = NOW()
                    """

                    params = {
                        "anime_id": anime_id,
                        "episode_number": idx,
                        "title": title,
                        "title_cn": "",
                        "description": "",
                        "release_date": None,
                        "duration": "",
                        "online_urls": online_urls,
                        "episode_type": 1,
                        "disc_number": 0,
                        "rating": 0,
                        "comments": 0,
                        "resources": 0,
                        "is_locked": False,
                        "is_banned": False
                    }

                    conn.run(sql, **params)

                updated += 1
                logger.info(f"番剧 {anime_id} 插入了 {len(streaming_eps)} 个具体剧集")
            else:
                # 没有流媒体剧集信息时，即使有总集数也不插入剧集
                logger.debug(f"番剧 {anime_id} 无具体剧集信息，跳过剧集插入")

        except Exception as e:
            logger.error(f"更新番剧 {anime.get('id')} 剧集时出错: {e}")
            continue

    return updated

def execute_quarterly_update(event=None, context=None):
    """
    华为云函数流执行入口

    参数:
        event: 华为云函数事件数据
        context: 华为云函数上下文

    返回:
        dict: 执行结果
    """
    logger.info("季度番剧更新任务开始")

    try:
        # 检查是否为季度月份
        if not is_quarter_month():
            logger.info("当前不是季度月份，跳过更新")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "当前不是季度月份，跳过更新",
                    "current_month": datetime.now().month
                }, ensure_ascii=False)
            }

        # 获取当前季度信息
        year, season = get_current_season()
        logger.info(f"开始更新 {year} 年 {season} 季度番剧")

        # 连接数据库
        conn = get_db_connection()

        # 分页获取和处理番剧数据
        total_processed = 0
        total_episodes_updated = 0
        page = 1

        try:
            while True:
                logger.info(f"正在获取第 {page} 页数据...")
                anime_list, has_next = fetch_seasonal_anime(year, season, page)

                if not anime_list:
                    logger.info("没有更多番剧数据")
                    break

                # 插入或更新番剧基本信息
                processed_count = upsert_anime_data(conn, anime_list)
                total_processed += processed_count

                # 更新集数信息
                episodes_updated = update_anime_episodes(conn, anime_list)
                total_episodes_updated += episodes_updated

                logger.info(f"第 {page} 页处理完成: 番剧 {processed_count} 部, 集数 {episodes_updated} 集")

                if not has_next:
                    logger.info("所有数据获取完成")
                    break

                page += 1
                time.sleep(SLEEP_SEC)  # 避免API限流

        finally:
            conn.close()

        result = {
            "year": year,
            "season": season,
            "total_anime_processed": total_processed,
            "total_episodes_updated": total_episodes_updated,
            "pages_processed": page - 1
        }

        logger.info(f"季度番剧更新完成: {result}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "季度番剧更新完成",
                "result": result
            }, ensure_ascii=False)
        }

    except Exception as e:
        logger.error(f"季度番剧更新失败: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "季度番剧更新失败",
                "error": str(e)
            }, ensure_ascii=False)
        }

# 本地测试函数
def test_quarterly_update_simulation():
    """
    快速本地测试季度番剧更新流程
    - 模拟当前月份为季度月份
    - 执行完整拉取和写入流程
    """
    logger.info("=== 模拟季度月份本地测试开始 ===")

    # 暂时覆盖 is_quarter_month 函数，使其总返回 True
    global is_quarter_month
    original_is_quarter_month = is_quarter_month
    is_quarter_month = lambda: True

    try:
        result = execute_quarterly_update()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        # 恢复原函数
        is_quarter_month = original_is_quarter_month

    logger.info("=== 模拟季度月份本地测试结束 ===")


if __name__ == "__main__":
    test_quarterly_update_simulation()
