"""
临时假数据（给 AI 只读工具用）
==============================

为什么会有这个文件：
    现在待办 / 公告 / 请假记录是【写死在各个 .vue 页面里的假数据】，
    后端根本看不到它们。AI 要回答「我还有哪些待办」，得先有数据可查。

    ⚠️ 前端的唯一数据源现在是 `src/mock/index.js`（首页数字、公告页都读它）。
    后端是 Python，没法 import 一个 .js，所以这里只能【手抄一份】。
    改数据请先改 `src/mock/index.js`，再同步到这里 —— 以后端为准是反的，
    因为用户看到的是前端。

⚠️ 这是临时方案，别当真数据用：
    后端一接上数据库，就应该删掉这个文件，改成查库，比如
        SELECT * FROM todos WHERE assignee = ?
    那时候前端页面里的假数据也要一起删掉。
    理由很实在：数据只能有一个源头。两边各存一份，改了一边忘了另一边，
    AI 说的和页面上显示的就是两回事，这种 bug 最难查。

    所以：前端假数据改了，记得来这里同步改。

对应的前端文件（数据源头在那边，以那边为准）：
    src/mock/index.js                  ← 唯一数据源，改这里
    zhangjing/views/todo/index.vue     ← ⚠️ 张晶的页面里还内联着一份 TODOS
    luoxinyu/views/leave/index.vue     ← ⚠️ 罗欣雨的页面里还内联着一份记录
"""

from datetime import date

# ------------------------------------------------------------------
# 待办事项（抄自 zhangjing/views/todo/index.vue）
# ⚠️ assignee 里的「刘皖」在前端是 userName.value，等于当前登录用户
# ------------------------------------------------------------------
TODOS = [
    {
        "id": 1,
        "title": "整理期末学生工作总结",
        "description": "汇总各部门工作成果、存在问题和下学期计划。",
        "category": "文档",
        "priority": "高",
        "assignee": "刘皖",
        "dueDate": "2026-10-15",
        "status": "待办",
    },
    {
        "id": 2,
        "title": "核对校园文化活动报名名单",
        "description": "确认各班级报名信息并反馈缺漏。",
        "category": "活动",
        "priority": "高",
        "assignee": "张晶",
        "dueDate": "2026-10-10",
        "status": "进行中",
    },
    {
        "id": 3,
        "title": "更新国庆假期值班安排",
        "description": "核对值班人员和联系方式。",
        "category": "工作",
        "priority": "中",
        "assignee": "罗欣雨",
        "dueDate": "2026-10-08",
        "status": "待办",
    },
    {
        "id": 4,
        "title": "汇总志愿服务时长",
        "description": "整理本月志愿服务签到记录。",
        "category": "文档",
        "priority": "低",
        "assignee": "张晶",
        "dueDate": "2026-10-05",
        "status": "已完成",
    },
    {
        "id": 5,
        "title": "准备学生会周例会材料",
        "description": "收集本周各部门进展，整理议题。",
        "category": "工作",
        "priority": "中",
        "assignee": "刘皖",
        "dueDate": "2026-10-09",
        "status": "进行中",
    },
    {
        "id": 6,
        "title": "完成新学期活动复盘",
        "description": "归档活动照片、预算和反馈问卷。",
        "category": "活动",
        "priority": "低",
        "assignee": "罗欣雨",
        "dueDate": "2026-10-20",
        "status": "待办",
    },
]

# ------------------------------------------------------------------
# 公告通知（抄自 liuwan/views/notice/index.vue）
# ------------------------------------------------------------------
NOTICES = [
    {
        "id": 12,
        "title": "关于期末学生工作总结的通知",
        "type": "通知",
        "author": "张晶",
        "publishTime": "2026-10-02 09:15",
        "top": True,
    },
    {
        "id": 11,
        "title": "校园文化活动报名开始啦",
        "type": "活动",
        "author": "罗欣雨",
        "publishTime": "2026-10-01 14:30",
        "top": True,
    },
    {
        "id": 10,
        "title": "学生会例会时间调整说明",
        "type": "通知",
        "author": "刘皖",
        "publishTime": "2026-09-28 16:40",
        "top": False,
    },
    {
        "id": 9,
        "title": "学生考勤管理制度（修订版）",
        "type": "制度",
        "author": "张晶",
        "publishTime": "2026-09-25 11:20",
        "top": False,
    },
    {
        "id": 8,
        "title": "国庆假期值班安排",
        "type": "通知",
        "author": "刘皖",
        "publishTime": "2026-09-23 08:50",
        "top": False,
    },
    {
        "id": 7,
        "title": "宿舍卫生检查结果公示",
        "type": "通知",
        "author": "罗欣雨",
        "publishTime": "2026-09-20 10:00",
        "top": False,
    },
    {
        "id": 6,
        "title": "志愿服务招募通知",
        "type": "活动",
        "author": "张晶",
        "publishTime": "2026-09-18 15:10",
        "top": False,
    },
    {
        "id": 5,
        "title": "关于使用统一开发规范的说明",
        "type": "制度",
        "author": "刘皖",
        "publishTime": "2026-09-15 09:00",
        "top": False,
    },
    {
        "id": 4,
        "title": "新生入学教育安排",
        "type": "通知",
        "author": "罗欣雨",
        "publishTime": "2026-09-12 13:45",
        "top": False,
    },
    {
        "id": 3,
        "title": "班级篮球赛报名通知",
        "type": "活动",
        "author": "张晶",
        "publishTime": "2026-09-10 17:30",
        "top": False,
    },
    {
        "id": 2,
        "title": "关于奖学金评定工作的通知",
        "type": "通知",
        "author": "刘皖",
        "publishTime": "2026-09-08 10:20",
        "top": False,
    },
    {
        "id": 1,
        "title": "新学期学生干部名单公布",
        "type": "通知",
        "author": "罗欣雨",
        "publishTime": "2026-09-01 09:00",
        "top": False,
    },
]

# ------------------------------------------------------------------
# 请假记录（抄自 luoxinyu/views/leave/index.vue）
# ------------------------------------------------------------------
LEAVE_RECORDS = [
    {
        "id": 3,
        "name": "刘皖",
        "type": "事假",
        "startDate": "2026-09-28",
        "endDate": "2026-09-28",
        "days": 1,
        "reason": "家中有事，需要回家处理",
        "status": "待审批",
        "applyTime": "2026-09-26 20:12",
    },
    {
        "id": 2,
        "name": "张晶",
        "type": "病假",
        "startDate": "2026-09-15",
        "endDate": "2026-09-16",
        "days": 2,
        "reason": "感冒发烧，校医院建议休息两天",
        "status": "已通过",
        "applyTime": "2026-09-14 08:30",
    },
    {
        "id": 1,
        "name": "罗欣雨",
        "type": "年假",
        "startDate": "2026-09-05",
        "endDate": "2026-09-05",
        "days": 1,
        "reason": "参加校外竞赛，需要请假一天",
        "status": "已驳回",
        "rejectionReason": "请补充指导老师同意证明后重新提交。",
        "applyTime": "2026-09-03 19:05",
    },
]

# 模型说「全部 / 所有人」时不按人筛选
ALL_WORDS = ("全部", "所有", "所有人", "*", "大家")


def _wants_all(value):
    return str(value or "").strip() in ALL_WORDS


def _pick(item, keys):
    """只把模型需要知道的字段挑出来，别把整个对象塞过去浪费 token。"""
    return {key: item.get(key) for key in keys if item.get(key) is not None}


def list_todos(assignee=None, status=None, overdue_only=False):
    """
    查待办。assignee 传「全部」查所有人，传具体名字查那个人，不传/传空则不过滤。
    overdue_only 由这里的代码判断是否逾期 —— 这种日期比较不能交给模型算。
    """
    today = date.today().isoformat()
    result = []

    for item in TODOS:
        if not _wants_all(assignee) and assignee and item["assignee"] != assignee:
            continue
        if status and item["status"] != status:
            continue
        # 逾期 = 过了截止日期、又还没做完
        if overdue_only and not (item["dueDate"] < today and item["status"] != "已完成"):
            continue
        row = _pick(item, ("id", "title", "category", "priority", "assignee", "dueDate", "status"))
        row["overdue"] = item["dueDate"] < today and item["status"] != "已完成"
        result.append(row)

    result.sort(key=lambda row: (row["status"] == "已完成", row["dueDate"]))
    return result


def list_notices(type_=None, keyword=None, limit=3):
    """查公告。排序和前端一致：置顶的在前，然后按 id 从大到小。"""
    kw = (keyword or "").strip()
    result = []

    for item in NOTICES:
        if type_ and item["type"] != type_:
            continue
        if kw and kw not in item["title"]:
            continue
        result.append(_pick(item, ("id", "title", "type", "author", "publishTime", "top")))

    result.sort(key=lambda row: (not row["top"], -row["id"]))
    try:
        count = int(limit)
    except (TypeError, ValueError):
        count = 5
    return result[: max(1, min(count, 12))]


def list_leave_records(name=None, status=None):
    """查请假记录。name 传「全部」查所有人。"""
    result = []
    for item in LEAVE_RECORDS:
        if not _wants_all(name) and name and item["name"] != name:
            continue
        if status and item["status"] != status:
            continue
        result.append(
            _pick(
                item,
                (
                    "id",
                    "name",
                    "type",
                    "startDate",
                    "endDate",
                    "days",
                    "reason",
                    "status",
                    "rejectionReason",
                    "applyTime",
                ),
            )
        )
    result.sort(key=lambda row: -row["id"])
    return result
