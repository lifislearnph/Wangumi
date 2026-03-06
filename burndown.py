import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import os

# ==================== 配置区 ====================
project_id = "75462783"
gitlab_private_token = "glpat-88bmnNgGbXlofmBhUasubm86MQp1OmkyOXlpCw.01.1202z6b4w"

# 🔧 自定义开发起止时间（这才是燃尽图的时间轴起点）
DEVELOPMENT_START_DATE = '2025-11-11'  # ✅ 改成你们真正开始开发的那天
DEVELOPMENT_END_DATE = '2025-11-20'    # ✅ Sprint 结束时间

# 获取所有 issues 的命令
get_issue_cmd = 'curl --header "PRIVATE-TOKEN: ' + gitlab_private_token + '" "https://gitlab.com/api/v4/projects/' \
                + project_id + '/issues?per_page=100" > all_issues.json'

os.system(get_issue_cmd)

# 加载数据
with open("all_issues.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

# 生成开发周期内的所有日期（作为 X 轴）
dt = datetime.strptime(DEVELOPMENT_START_DATE, "%Y-%m-%d")
dates = []
current_date_str = DEVELOPMENT_START_DATE
while current_date_str <= DEVELOPMENT_END_DATE:
    dates.append(current_date_str)
    dt += timedelta(days=1)
    current_date_str = dt.strftime("%Y-%m-%d")

# -----------------------------------------------------
# 核心逻辑变更：计算“开发开始时”的总工作量（即当时未关闭的 issue 数）
# -----------------------------------------------------

def count_open_as_of(target_date):
    """统计截至 target_date 当天仍 open 的 issue 数量"""
    count = 0
    for issue in data:
        created_at = issue['created_at'][:10]
        closed_at = issue['closed_at']

        # 必须在 target_date 或之前创建
        if created_at > target_date:
            continue
        if closed_at is not None:
            closed_date = closed_at[:10]
        else:
            closed_date = None
        # 如果未关闭，或关闭时间晚于 target_date，则视为 still open
        if closed_date is None or closed_date > target_date:
            count += 1
    return count

# 初始任务数 = 开发第一天开始前的未关闭 issue 数
initial_count = count_open_as_of(DEVELOPMENT_START_DATE)

# 构建每日剩余任务数（从开发第0天到最后一天）
issues_cnt = []
for date in dates:
    remaining = count_open_as_of(date)
    issues_cnt.append(remaining)

# -----------------------------------------------------
# ✅ 关键：以下绘图代码与你原来的完全一致！
# -----------------------------------------------------

# expected line: from initial_count to 0
expected_x = [0, len(dates) - 1]
expected_y = [initial_count, 0]

actual_x = range(0, len(issues_cnt))
actual_y = issues_cnt

fig, ax = plt.subplots(figsize=(15, 10))
expected = plt.plot(expected_x, expected_y, color='green', label='expected')
actual = plt.plot(actual_x, actual_y, color='blue', label='actual')
plt.xticks(range(0, len(dates)), dates, rotation=45)
plt.legend()
plt.xlabel('Date')
plt.ylabel('Issues Count')
plt.savefig('burndown_chart.png')

print(f"✅ Burndown chart generated with development period: {DEVELOPMENT_START_DATE} → {DEVELOPMENT_END_DATE}")
print(f"   Initial workload: {initial_count} issues")
