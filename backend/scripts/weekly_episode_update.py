"""
该脚本用于每周更新已有番剧的新集数数据，
不添加新番剧，只更新已存在番剧的剧集信息。适用于华为云函数流环境。
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import pg8000.native


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置常量
API_URL = "https://graphql.anilist.co"
PER_PAGE = 50
SLEEP_SEC = 0.5
WEEKS_BACK = 1  # 查询过去1周内更新的番剧
MAX_ANIME_PER_UPDATE = 200  # 每次最多处理200部番剧

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

def get_existing_anime_ids(conn) -> List[int]:
    """
    从数据库获取所有已存在的番剧ID列表
    """
    try:
        result = conn.run("SELECT id FROM wangumi_app_anime ORDER BY id")
        anime_ids = [row[0] for row in result]
        logger.info(f"数据库中现有 {len(anime_ids)} 部番剧")
        return anime_ids
    except Exception as e:
        logger.error(f"获取已有番剧ID失败: {e}")
        return []

def build_weekly_query() -> str:
    """
    构建获取近期更新番剧的GraphQL查询
    重点关注正在连载且有新剧集的番剧
    """
    return """
    query ($page: Int, $perPage: Int, $sort: [MediaSort]) {
        Page(page: $page, perPage: $perPage) {
            pageInfo { currentPage hasNextPage }
            media(
                type: ANIME,
                status_in: [RELEASING, FINISHED],
                sort: $sort
            ) {
                id
                idMal
                title { romaji english native }
                startDate { year month day }
                endDate { year month day }
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
            }
        }
    }
    """

def fetch_recently_updated_anime(start_date: int, page: int = 1, per_page: int = PER_PAGE) -> Tuple[List[Dict], bool]:
    """
    获取近期更新的番剧数据
    返回: (番剧列表, 是否有下一页)
    """
    query = build_weekly_query()

    variables = {
        "page": page,
        "perPage": per_page,
        "sort": ["UPDATED_AT_DESC", "POPULARITY_DESC"]
    }

    try:
        response = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            timeout=30
        )
        response.raise_for_status()

        result = response.json()

        # 检查GraphQL错误
        if "errors" in result:
            error_details = result["errors"]
            error_msg = f"GraphQL错误: {error_details}"
            logger.error(error_msg)
            raise Exception(error_msg)

        data = result.get("data", {}).get("Page", {})
        media = data.get("media", [])
        has_next_page = data.get("pageInfo", {}).get("hasNextPage", False)

        logger.info(f"获取到 {len(media)} 部近期更新番剧数据 (页面 {page})")
        return media, has_next_page

    except Exception as e:
        logger.error(f"获取番剧数据失败: {e}")
        # 打印响应内容用于调试
        if 'response' in locals() and hasattr(response, 'text'):
            logger.error(f"响应内容: {response.text}")
        raise

def get_date_weeks_ago(weeks: int) -> int:
    """
    获取N周前的日期，转换为AniList格式 (YYYYMMDD)
    """
    target_date = datetime.now() - timedelta(weeks=weeks)
    return int(target_date.strftime("%Y%m%d"))

def get_timestamp_weeks_ago(weeks: int) -> int:
    """
    获取N周前的时间戳
    """
    target_time = datetime.now() - timedelta(weeks=weeks)
    return int(target_time.timestamp())

def is_recently_updated(anime: Dict, cutoff_timestamp: int) -> bool:
    """
    检查番剧是否在指定时间后更新过
    """
    updated_at = anime.get("updatedAt", 0)
    return updated_at >= cutoff_timestamp

def update_existing_anime_data(conn, anime_list: List[Dict]) -> int:
    """
    更新已存在番剧的基本信息（不插入新番剧）
    """
    processed = 0
    for anime in anime_list:
        try:
            anime_id = anime.get("id")
            if not anime_id:
                continue

            title_info = anime.get("title", {})
            updated_at_ts = anime.get("updatedAt")
            updated_at = datetime.fromtimestamp(updated_at_ts).isoformat() if updated_at_ts else None

            # 只更新已存在的番剧，使用ON CONFLICT DO NOTHING避免插入新数据
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
                    cover_url = EXCLUDED.cover_url,
                    rating = EXCLUDED.rating,
                    popularity = EXCLUDED.popularity,
                    status = EXCLUDED.status,
                    total_episodes = EXCLUDED.total_episodes,
                    updated_at = EXCLUDED.updated_at,
                    genres = EXCLUDED.genres
            """

            params = {
                'id': anime_id,
                "title": title_info.get("romaji") or "未知标题",
                "title_cn": title_info.get("native") or title_info.get("english") or "",
                "description": anime.get("description", ""),
                "release_date": None,  # 周更新不修改发布日期
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
            logger.debug(f"更新番剧 {anime_id} ({title_info.get('romaji', '未知标题')}) 信息")
        except Exception as e:
            logger.error(f"更新番剧 {anime.get('id')} 时出错: {e}")
            continue
    return processed

def update_anime_episodes(conn, anime_list: List[Dict]) -> int:
    """
    更新番剧剧集信息
    重点关注新的剧集数据
    """
    updated = 0
    total_new_episodes = 0

    for anime in anime_list:
        try:
            anime_id = anime["id"]
            streaming_eps = anime.get("streamingEpisodes", [])

            if streaming_eps:
                new_episodes_count = 0
                for idx, ep in enumerate(streaming_eps, start=1):
                    # 使用索引作为集数
                    episode_number = idx

                    title = ep.get("title") or f"Episode {episode_number}"
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
                        "episode_number": episode_number,
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

                    try:
                        conn.run(sql, **params)
                        new_episodes_count += 1
                    except Exception as ep_error:
                        # 如果是重复数据，继续处理其他剧集
                        if "duplicate" in str(ep_error).lower():
                            continue
                        else:
                            raise ep_error

                if new_episodes_count > 0:
                    updated += 1
                    total_new_episodes += new_episodes_count
                    logger.info(f"番剧 {anime_id} 新增了 {new_episodes_count} 集内容")
            else:
                logger.debug(f"番剧 {anime_id} 无新剧集信息")

        except Exception as e:
            logger.error(f"更新番剧 {anime.get('id')} 剧集时出错: {e}")
            continue

    logger.info(f"总共新增了 {total_new_episodes} 集内容")
    return updated

def execute_weekly_update(event=None, context=None):
    """
    华为云函数流执行入口 - 周更新

    参数:
        event: 华为云函数事件数据
        context: 华为云函数上下文

    返回:
        dict: 执行结果
    """
    logger.info("周度番剧更新任务开始")

    try:
        # 连接数据库
        conn = get_db_connection()

        # 获取已存在的番剧ID列表
        existing_anime_ids = get_existing_anime_ids(conn)
        if not existing_anime_ids:
            logger.warning("数据库中没有找到任何番剧，无法进行周更新")
            conn.close()
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "数据库中没有找到任何番剧，无法进行周更新"
                }, ensure_ascii=False)
            }

        # 计算时间过滤条件
        cutoff_timestamp = get_timestamp_weeks_ago(WEEKS_BACK)
        cutoff_date = datetime.fromtimestamp(cutoff_timestamp)
        logger.info(f"只处理过去 {WEEKS_BACK} 周内更新的番剧 (截止时间: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")

        # 分页获取和处理番剧数据
        total_anime_updated = 0
        total_episodes_updated = 0
        page = 1
        processed_anime_ids = []

        try:
            consecutive_empty_pages = 0
            max_empty_pages = 3  # 连续3页没有符合条件的番剧就停止

            while True:
                # 检查是否已达到最大处理数量
                if total_anime_updated >= MAX_ANIME_PER_UPDATE:
                    logger.info(f"已达到最大处理数量 {MAX_ANIME_PER_UPDATE} 部番剧，停止处理")
                    break

                logger.info(f"正在获取第 {page} 页近期更新数据...")
                anime_list, has_next = fetch_recently_updated_anime(0, page)  # start_date不再使用

                if not anime_list:
                    logger.info("没有更多番剧数据")
                    break

                # 基于时间过滤番剧
                recent_anime_list = []
                for anime in anime_list:
                    if is_recently_updated(anime, cutoff_timestamp):
                        recent_anime_list.append(anime)
                        processed_anime_ids.append(anime.get("id"))

                if not recent_anime_list:
                    consecutive_empty_pages += 1
                    logger.info(f"第 {page} 页没有过去 {WEEKS_BACK} 周内更新的番剧 (连续空页: {consecutive_empty_pages})")

                    # 如果连续几页都没有符合条件的番剧，可能已经处理完近期更新的数据
                    if consecutive_empty_pages >= max_empty_pages:
                        logger.info(f"连续 {max_empty_pages} 页没有符合条件的番剧，停止获取")
                        break

                    if not has_next:
                        break

                    page += 1
                    time.sleep(SLEEP_SEC)
                    continue
                else:
                    consecutive_empty_pages = 0  # 重置连续空页计数

                # 如果当前页的数据会超过最大限制，则截取
                remaining = MAX_ANIME_PER_UPDATE - total_anime_updated
                if len(recent_anime_list) > remaining:
                    recent_anime_list = recent_anime_list[:remaining]
                    logger.info(f"截取本页数据为 {len(recent_anime_list)} 部，以达到最大处理限制")

                logger.info(f"第 {page} 页找到 {len(recent_anime_list)} 部过去 {WEEKS_BACK} 周内更新的番剧")

                # 更新番剧基本信息
                anime_updated = update_existing_anime_data(conn, recent_anime_list)
                total_anime_updated += anime_updated

                # 更新剧集信息
                episodes_updated = update_anime_episodes(conn, recent_anime_list)
                total_episodes_updated += episodes_updated

                logger.info(f"第 {page} 页处理完成: 番剧 {anime_updated} 部, 剧集 {episodes_updated} 部 (总计: {total_anime_updated}/{MAX_ANIME_PER_UPDATE})")

                if not has_next:
                    logger.info("所有数据获取完成")
                    break

                page += 1
                time.sleep(SLEEP_SEC)

        finally:
            conn.close()

        result = {
            "cutoff_timestamp": cutoff_timestamp,
            "cutoff_date": cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
            "weeks_back": WEEKS_BACK,
            "total_existing_anime": len(existing_anime_ids),
            "total_anime_updated": total_anime_updated,
            "total_episodes_updated": total_episodes_updated,
            "pages_processed": page - 1,
            "processed_anime_ids": processed_anime_ids[:10]  # 只返回前10个ID作为示例
        }

        logger.info(f"周度番剧更新完成: {result}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "周度番剧更新完成",
                "result": result
            }, ensure_ascii=False)
        }

    except Exception as e:
        logger.error(f"周度番剧更新失败: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "周度番剧更新失败",
                "error": str(e)
            }, ensure_ascii=False)
        }

# 本地测试函数
def test_weekly_update_simulation():
    """
    本地测试周度番剧更新流程
    """
    logger.info("=== 周度番剧更新本地测试开始 ===")

    try:
        result = execute_weekly_update()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"测试失败: {e}")

    logger.info("=== 周度番剧更新本地测试结束 ===")

if __name__ == "__main__":
    test_weekly_update_simulation()