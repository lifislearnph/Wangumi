from ..models import Anime, Person,Character,UserProfile
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q

def _do_search(query, model, sort, is_admin_filter=None):
    """
    通用搜索函数
    """
    search_strategies = [
        SearchQuery(query, search_type='websearch'),
        SearchQuery(query, search_type='plain'),
        SearchQuery(query, search_type='phrase'),
    ]

    all_results = []
    seen_ids = set()#  用于去重

    # 预先拿到当前 model 的字段名集合，加快判断
    model_fields = {f.name for f in model._meta.get_fields()}

    for search_query in search_strategies:
        qs = model.objects.annotate(
            rank=SearchRank(F("search_vector"), search_query)
        )

        q_filter = Q(rank__gt=0.01)
        # 根据模型字段动态添加过滤条件
        if "title" in model_fields:
            q_filter |= Q(title__icontains=query)
        if "title_cn" in model_fields:
            q_filter |= Q(title_cn__icontains=query)

        if "name" in model_fields:
            q_filter |= Q(name__icontains=query)

        if "pers_name" in model_fields:
            q_filter |= Q(pers_name__icontains=query)

        if "nickname" in model_fields:
            q_filter |= Q(nickname__icontains=query)

        qs = qs.filter(q_filter).order_by("-rank")[:50]

        for obj in qs:
            # 统一获取 ID
            if hasattr(obj, "id"):
                obj_id = obj.id
            elif hasattr(obj, "pers_id"):
                obj_id = obj.pers_id
            else:
                continue

            if obj_id not in seen_ids:
                seen_ids.add(obj_id)
                obj._current_rank = obj.rank
                all_results.append(obj)

    # is_admin 过滤
    if is_admin_filter is not None and "is_admin" in model_fields:
        all_results = [
            obj for obj in all_results
            if getattr(obj, "is_admin", None) == is_admin_filter
        ]
    #按照相关度/热度/时间三种方式排序
    if sort == "relevance":
        all_results.sort(key=lambda x: getattr(x, "_current_rank", 0), reverse=True)
    elif sort == "popularity":
        all_results.sort(key=lambda x: getattr(x, "popularity", 0), reverse=True)
    elif sort == "time":
        all_results.sort(key=lambda x: getattr(x, "created_at", ""), reverse=True)

    # 构造返回结果
    result = []
    for obj in all_results:
        if hasattr(obj, "id"):
            obj_id = obj.id
        elif hasattr(obj, "pers_id"):
            obj_id = obj.pers_id
        else:
            continue

        # 多种model不同方式取 name
        name = (
            getattr(obj, "name", None)
            or getattr(obj, "pers_name", None)
            or getattr(obj, "nickname", None)
            or (obj.user.username if hasattr(obj, "user") and hasattr(obj.user, "username") else None)
        )

        result.append({
            "id": obj.user.id if isinstance(obj, UserProfile) else obj_id,
            "title": getattr(obj, "title", None),
            "name": name,
            "cover_url": getattr(obj, "cover_url", None),
            "image_url": getattr(obj, "image", None),
            "pers_image_url": getattr(obj, "pers_img", None),
            "avatar_url": str(obj.avatar) if getattr(obj, "avatar", None) else None,
            "related_score": getattr(obj, "_current_rank", 0),
            "is_admin": getattr(obj, "is_admin", None),
        })

    return result

def search_single_type(query, type_name, sort):
    # 多模型的方式（一个 type 可以对应多个 model）
    model_map = {
        "anime": [(Anime, True)],
        "item": [(Anime, False)],
        "person": [(Person, None), (Character, None)],#person 同时对应Person 和 Character 模型
        "user":[(UserProfile,None)],
    }

    model_list = model_map[type_name]

    results = []
    for model, admin_filter in model_list:
        res = _do_search(query, model, sort, admin_filter)
        results.extend(res)

    return results


def search_all_types(query, sort):
    return {
        "anime": _do_search(query, Anime, sort, is_admin_filter=True),
        "item": _do_search(query, Anime, sort, is_admin_filter=False),
        "person": (
            _do_search(query, Person, sort, None)
            + _do_search(query, Character, sort, None)
        ),#person 类型包含 Person 和 Character 两个模型的结果
        "user":_do_search(query, UserProfile, sort, None)
    }
