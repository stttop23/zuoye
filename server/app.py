"""
AI 智能体代理服务（Flask）
==========================

它干的活只有一件：浏览器 → 本服务 → 本机大模型，再把模型的「要做的动作」翻译成前端能执行的 JSON。

    浏览器                    本服务                       本机 Ollama
  AiAssistant  →   POST /api/ai/chat  →  http://127.0.0.1:11434/v1/chat/completions
       ↑                                                  │
       └─────── { reply, actions:[...] } ←───────────────┘

模型就在本机，为什么还留这一层？
    1) 契约收口：前端只认 { reply, actions }，以后换模型只改这一层，前端一行不动
    2) 白名单校验：模型给什么不算数，这里逐字段检查过才允许落到表单上
    3) 降级：本机模型没启动 / 报错时，这里还能退回本地正则规则

启动方式：
    先确认本机 Ollama 在跑（`ollama list` 能看到 qwen2.5:7b），然后：
        python server/app.py

模型可以在 server/.env 里换（OLLAMA_MODEL）；设 OLLAMA_ENABLED=0 就把模型整个关掉，
那就只能走本地正则规则了。
"""

import json
import os
import re
from datetime import date, timedelta

import requests
from flask import Flask, jsonify, request

try:  # 有 python-dotenv 就自动读 server/.env，没有也不影响
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

app = Flask(__name__)

# 本机模型（Ollama）：不用网、不用 key、不花钱
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/v1/chat/completions")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "1") != "0"
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 冷启动要加载 4.4GB 模型，给足时间


def build_providers():
    """
    列出可用的模型通道。现在只有本机一条。

    之所以还包成一个列表：以后想接回云端模型（或换成别的本机模型）时，
    只要往这里加一项，下面的调用方一行都不用改。
    """
    providers = []
    if OLLAMA_ENABLED:
        providers.append(
            {
                "name": "ollama",
                "label": f"本机 {OLLAMA_MODEL}",
                "url": OLLAMA_URL,
                "key": "",
                "model": OLLAMA_MODEL,
                "timeout": OLLAMA_TIMEOUT,
            }
        )
    return providers

# ------------------------------------------------------------------
# 闭集选项：模型只能在下面这些值里挑，避免它自由发挥编出不存在的分类
# ------------------------------------------------------------------
LEAVE_TYPES = ("事假", "病假", "年假")
TODO_CATEGORIES = ("工作", "活动", "学习", "文档", "其他")
TODO_PRIORITIES = ("高", "中", "低")
TODO_STATUSES = ("待办", "进行中", "已完成")

PAGES = {
    "/dashboard": "工作台",
    "/notice": "公告通知",
    "/leave": "请假申请",
    "/todo": "待办事项",
}

WEEKDAY_NAMES = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
CN_NUMBERS = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# ------------------------------------------------------------------
# 工具（tools）：这就是「智能体」跟「聊天机器人」的分界线。
# 聊天机器人只会说；智能体能动手。我们把「动手能力」写成一张清单交给模型，
# 模型自己决定要不要调用，我们负责执行。
# ------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "go_to_page",
            "description": "帮用户跳转到系统里的某个页面",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "enum": list(PAGES.keys()),
                        "description": "目标页面的路由",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_leave_form",
            "description": "把请假信息填进「请假申请」页的表单。只填表，不提交，用户自己确认后再点提交。",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": list(LEAVE_TYPES), "description": "请假类型"},
                    "startTime": {"type": "string", "description": "开始日期，格式 YYYY-MM-DD"},
                    "endTime": {"type": "string", "description": "结束日期，格式 YYYY-MM-DD，不能早于开始日期"},
                    "reason": {"type": "string", "description": "请假原因，5-200 字"},
                },
                "required": ["type", "startTime", "endTime"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_todo",
            "description": "打开「待办事项」页的新建弹窗并预填内容。只预填，不保存。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "任务名称，2-40 字"},
                    "description": {"type": "string", "description": "任务描述，可空"},
                    "category": {"type": "string", "enum": list(TODO_CATEGORIES)},
                    "priority": {"type": "string", "enum": list(TODO_PRIORITIES)},
                    "assignee": {"type": "string", "description": "负责人姓名"},
                    "dueDate": {"type": "string", "description": "截止日期，格式 YYYY-MM-DD"},
                    "status": {"type": "string", "enum": list(TODO_STATUSES)},
                },
                "required": ["title", "dueDate"],
            },
        },
    },
]

SYSTEM_PROMPT = """你是「学生工作管理系统」里的 AI 助手，帮用户查东西和填表单。

当前用户叫「{user}」，正停在「{page}」页面。

{calendar}

你可以调用工具帮用户做事：
- go_to_page：切换页面
- fill_leave_form：把请假信息填进请假表单（只填、不提交）
- create_todo：打开新建待办弹窗并预填

用户只是说「打开 / 去 / 看看 某个页面」时，用 go_to_page，不要顺便建任何东西。

硬性规则：
1. 上面那张日期对照表是【算好的】，直接查表。绝对不要自己推算星期几，
   也不要写中文日期，调用工具时一律用 YYYY-MM-DD 格式。
2. 没说清楚的字段就别传，绝对不要自己编一个理由或日期塞进去。
3. reason 只能用用户原话里的信息，不要替他把话说漂亮，也不要补充用户没说的内容。
4. 用户已经把话说清楚了（类型和日期都有了）就必须调用工具，不要反问、不要只口头答应。
   只有真的缺关键信息时才反问一句。
5. 填完表一定要提醒用户「自己看一眼再提交」。
6. 调用工具前【不要】先写一段解释（小模型啰嗦一句就可能把输出额度吐光，
   导致工具参数被截断成残缺 JSON，服务端直接报错）。要调就安静地调。
7. 回答用中文，40 字以内，不要用 markdown 标题和代码块，不要复述 JSON。"""


# ==================================================================
# 一、调用大模型
# ==================================================================
def date_hints(today):
    """
    给模型一张「日期速查表」。

    为什么要给表：小模型算「下周三」经常算错——实测 qwen2.5:7b 把
    2026-10-21 算成了 10-18，给了表之后又错成 10-19。
    后来发现坑在【格式】：表里写「10月21日」，模型还得做一次转换，就又会错。
    改成直接给它 YYYY-MM-DD，它只需要【照抄】，正确率立刻上来。

    这张表对大模型也有好处：少一次推理，快一点、稳一点。
    """
    weekdays = "一二三四五六日"
    monday = today - timedelta(days=today.weekday())

    def iso(day):
        return day.isoformat()

    this_week = "  ".join(f"本周{weekdays[i]}={iso(monday + timedelta(days=i))}" for i in range(7))
    next_week = "  ".join(
        f"下周{weekdays[i]}={iso(monday + timedelta(days=7 + i))}" for i in range(7)
    )

    return "\n".join(
        [
            f"今天是 {iso(today)}（周{weekdays[today.weekday()]}）。",
            "日期速查表（【直接照抄】右边的日期，不要自己换算星期几，一律用 YYYY-MM-DD）：",
            f"  {this_week}",
            f"  {next_week}",
            f"  今天={iso(today)}  明天={iso(today + timedelta(days=1))}"
            f"  后天={iso(today + timedelta(days=2))}",
            "注意：「下周三到周五」这种写法，后面的「周五」也指【下周】五，不是本周五。",
        ]
    )


def call_model(messages, provider):
    """把对话发给指定通道（现在就是本机 Ollama），返回模型这一轮的回复对象。"""
    headers = {"Content-Type": "application/json"}
    if provider["key"]:
        headers["Authorization"] = f"Bearer {provider['key']}"

    response = requests.post(
        provider["url"],
        headers=headers,
        json={
            "model": provider["model"],
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0.2,  # 填表要稳，不要把温度调高
            # ⚠️ 必须设上限：小模型偶尔会陷入复读，没有上限就会一直吐到超时。
            #    但也不能设太小：设 400 时，模型吐工具参数吐到一半就被截断，
            #    变成一个残缺 JSON，Ollama 直接回 500
            #    （invalid tool call arguments: unexpected end of JSON input）。
            #    1024 是实测出来的甜点：够它啰嗦几句再调工具，又不会失控。
            "max_tokens": 1536,
            "stream": False,
        },
        timeout=provider["timeout"],
    )
    # 不要用 raise_for_status()：那样只能看到一个干巴巴的 "500 Server Error"，
    # 服务端到底为什么拒绝完全看不到，极难排查。
    if not response.ok:
        raise RuntimeError(f"{provider['label']} 返回 {response.status_code}：{response.text[:300]}")
    return response.json()["choices"][0]["message"]


def run_agent(history, page, user, provider):
    """
    智能体主循环：最多来回 3 轮。
    模型要么调用工具（我们执行 + 把结果喂回去），要么开口说话（结束）。
    """
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                user=user or "同学",
                page=PAGES.get(page, "工作台"),
                calendar=date_hints(date.today()),
            ),
        }
    ]
    messages += history[-8:]  # 只带最近 8 条，省 token

    actions = []
    reply = ""

    for _ in range(3):
        message = call_model(messages, provider)
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            reply = (message.get("content") or "").strip()
            break

        for call in tool_calls:
            name = call["function"]["name"]
            raw_args = call["function"].get("arguments")
            if isinstance(raw_args, dict):
                args = raw_args  # 有些实现直接给对象，不包字符串
            else:
                try:
                    args = json.loads(raw_args or "{}")
                except json.JSONDecodeError:
                    args = {}

            action = action_from_tool(name, args)
            if action and action not in actions:
                actions.append(action)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(
                        {"ok": action is not None, "action": action}, ensure_ascii=False
                    ),
                }
            )

    if not reply:
        reply = default_reply(actions)
    return reply, actions


def default_reply(actions):
    """模型光调工具不说话时的兜底文案。"""
    for action in actions:
        if action["type"] == "fill" and action["target"] == "leave":
            return "已经帮你填好了，检查一下再提交。"
        if action["type"] == "fill" and action["target"] == "todo":
            return "待办弹窗已经打开并预填，确认后保存。"
        if action["type"] == "navigate":
            return f"带你到「{PAGES.get(action['path'], '目标页')}」。"
    return "我在，有什么要办的？"


# ==================================================================
# 二、把模型给的工具参数，洗成前端能直接用的动作
#    白名单过滤：契约里没写的字段一律丢掉
# ==================================================================
def normalize_date(value):
    """只接受 2026-10-14 / 2026/10/14 / 2026.10.14，其它一律当没填。"""
    if not isinstance(value, str):
        return None
    text = value.strip().replace("/", "-").replace(".", "-")
    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def clean_leave(args):
    fields = {}
    if args.get("type") in LEAVE_TYPES:
        fields["type"] = args["type"]

    start = normalize_date(args.get("startTime"))
    end = normalize_date(args.get("endTime"))
    if start:
        fields["startTime"] = start
    if end and (not start or end >= start):
        fields["endTime"] = end
    elif end and start and end < start:
        # 结束早于开始：直接丢掉，交给表单校验去提示，别默默改数据
        pass

    reason = (args.get("reason") or "").strip()
    if reason:
        fields["reason"] = reason[:200]
    return fields


def clean_todo(args):
    fields = {}
    title = (args.get("title") or "").strip()
    if title:
        fields["title"] = title[:40]
    description = (args.get("description") or "").strip()
    if description:
        fields["description"] = description[:200]
    if args.get("category") in TODO_CATEGORIES:
        fields["category"] = args["category"]
    if args.get("priority") in TODO_PRIORITIES:
        fields["priority"] = args["priority"]
    if args.get("status") in TODO_STATUSES:
        fields["status"] = args["status"]
    assignee = (args.get("assignee") or "").strip()
    if assignee:
        fields["assignee"] = assignee
    due = normalize_date(args.get("dueDate"))
    if due:
        fields["dueDate"] = due
    return fields


def action_from_tool(name, args):
    if name == "go_to_page":
        path = args.get("path")
        return {"type": "navigate", "path": path} if path in PAGES else None
    if name == "fill_leave_form":
        fields = clean_leave(args)
        return {"type": "fill", "target": "leave", "fields": fields} if fields else None
    if name == "create_todo":
        fields = clean_todo(args)
        return {"type": "fill", "target": "todo", "fields": fields} if fields else None
    return None


def reconcile_dates(action, user_text):
    """
    用我们自己的日期解析，把模型填的日期「掰正」。

    为什么要这一步：小模型算相对日期极不可靠。实测 qwen2.5:7b 把「下周三」
    算成 10-18，给它一张日期对照表后又会算成 10-19（正确是 10-21）。
    而 resolve_dates() 是确定性的、有测试覆盖的。

    所以分工改成：
      【该模型管的】听懂人话、判断类型、提炼原因
      【不该模型管的】算日期 —— 这种确定性的活交给代码

    它算得出来就以它为准；算不出来（返回空）才用模型的值，
    这样不会把「模型故意不填」的情况覆盖掉。
    """
    if not isinstance(action, dict) or action.get("type") != "fill":
        return action

    dates = resolve_dates(user_text, date.today())
    if not dates:
        return action

    fields = action.get("fields") or {}
    target = action.get("target")

    if target == "leave":
        if "startTime" in fields:
            fields["startTime"] = dates[0].isoformat()
        if "endTime" in fields:
            fields["endTime"] = (dates[1] if len(dates) >= 2 else dates[0]).isoformat()
        start, end = fields.get("startTime"), fields.get("endTime")
        if start and end and end < start:
            fields["endTime"] = start
    elif target == "todo" and "dueDate" in fields:
        fields["dueDate"] = dates[0].isoformat()

    action["fields"] = fields
    return action


# ==================================================================
# 三、本地规则兜底（没配 key / 超时 / 断网 / 502 全走这里）
# ==================================================================
DATE_RE = re.compile(
    r"(?P<ymd>\d{4}[-/.]\d{1,2}[-/.]\d{1,2})"
    r"|(?P<md>\d{1,2}\s*月\s*\d{1,2}\s*[日号]?)"
    r"|(?P<rel>大后天|后天|明天|今天)"
    r"|(?P<dw>下下周[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|周[一二三四五六日天])"
    r"|(?P<nd>\d+\s*天后)"
)
DURATION_RE = re.compile(r"(\d+|[一二两三四五六七八九十]+)\s*天")


def monday_of(day):
    return day - timedelta(days=day.weekday())


def to_date(match, today):
    kind = match.lastgroup
    token = match.group()

    if kind == "ymd":
        return normalize_date(token) and date.fromisoformat(normalize_date(token))
    if kind == "md":
        numbers = re.findall(r"\d+", token)
        if len(numbers) != 2:
            return None
        try:
            return date(today.year, int(numbers[0]), int(numbers[1]))
        except ValueError:
            return None
    if kind == "rel":
        offsets = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3}
        return today + timedelta(days=offsets[token])
    if kind == "nd":
        return today + timedelta(days=int(re.search(r"\d+", token).group()))
    if kind == "dw":
        target = WEEKDAY_NAMES[token[-1]]
        if token.startswith("下下周"):
            return monday_of(today) + timedelta(days=14 + target)
        if token.startswith("下周"):
            return monday_of(today) + timedelta(days=7 + target)
        if token.startswith(("本周", "这周")):
            return monday_of(today) + timedelta(days=target)
        return today + timedelta(days=(target - today.weekday()) % 7)
    return None


def guess_leave_type(text):
    if re.search(r"病|发烧|感冒|头疼|头痛|不舒服|医院|输液|看病", text):
        return "病假"
    if re.search(r"年假|调休|休假", text):
        return "年假"
    return "事假"


def resolve_dates(text, today):
    """
    按出现顺序把文本里的日期片段解析成真正的日期。

    关键点：裸「周X」要跟在它前面的「下周X / 本周X」算同一周。
    否则「下周三到周五」会被算成 10-21 ~ 10-16（本周五在前面），区间直接反了。
    """
    resolved = []
    week_monday = None  # 最近一次「下周X / 本周X / 下下周X」所在的周一

    for match in DATE_RE.finditer(text):
        token = match.group()

        if match.lastgroup == "dw":
            if token.startswith("下下周"):
                week_monday = monday_of(today) + timedelta(days=14)
            elif token.startswith("下周"):
                week_monday = monday_of(today) + timedelta(days=7)
            elif token.startswith(("本周", "这周")):
                week_monday = monday_of(today)
            elif week_monday is not None:
                # 裸「周X」，前面已经有周的范围了 → 算同一周
                resolved.append(week_monday + timedelta(days=WEEKDAY_NAMES[token[-1]]))
                continue

        value = to_date(match, today)
        if value:
            resolved.append(value)

    return resolved


def guess_leave_type(text):
    if re.search(r"病|发烧|感冒|头疼|头痛|不舒服|医院|输液|看病", text):
        return "病假"
    if re.search(r"年假|调休|休假", text):
        return "年假"
    return "事假"


def clean_reason(text, leave_type):
    """把日期、「一天」这种时长、以及「请假」这类废话抠掉，剩下的才算原因。"""
    reason = DATE_RE.sub(" ", text)
    reason = DURATION_RE.sub(" ", reason)
    for word in (
        "请个假",
        "请假",
        "我想",
        "我要",
        "帮我",
        "麻烦",
        "申请",
        "请",
        leave_type,
        "到",
        "至",
        "的",
        "了",
        "，",
        "。",
        "、",
        "：",
        ":",
        "~",
        "～",
    ):
        reason = reason.replace(word, " ")
    return " ".join(reason.split())[:200]


def local_leave(text, today):
    dates = resolve_dates(text, today)
    if not dates:
        return None, "我没听出是哪几天，换个说法试试？（比如：下周三到周五）"

    start = dates[0]
    if len(dates) >= 2:
        end = dates[1]
    else:
        found = DURATION_RE.search(text)
        count = CN_NUMBERS.get(found.group(1)) if found else None
        end = start + timedelta(days=count - 1) if count else start
    if end < start:
        end = start

    leave_type = guess_leave_type(text)
    reason = clean_reason(text, leave_type)

    fields = {"type": leave_type, "startTime": start.isoformat(), "endTime": end.isoformat()}
    # 表单要求 5-200 字，短了就宁可不填，让用户自己补，别塞个半截话进去
    if len(reason) >= 5:
        fields["reason"] = reason

    reply = f"本地规则识别：{leave_type} {start.isoformat()} ~ {end.isoformat()}，已填进表单"
    reply += "，确认后再提交。" if "reason" in fields else "，原因自己补一下。"
    return {"type": "fill", "target": "leave", "fields": fields}, reply


def local_todo(text, today):
    title = re.sub(r"^(帮我|我要|我想|麻烦|新建|添加|加个|建个|一个|一条)+\s*", "", text)
    title = re.sub(r"^(待办|任务|事项)[:：]?\s*", "", title)
    title = DATE_RE.sub(" ", title)
    for word in ("截止", "之前", "以前", "前", "，", "。", "、", ",", ".", "：", ":"):
        title = title.replace(word, " ")
    title = " ".join(title.split())

    if not title:
        return None, "要建什么待办？说个标题就行。"

    fields = {"title": title[:40]}
    dates = resolve_dates(text, today)
    if dates:
        fields["dueDate"] = dates[0].isoformat()
    return {"type": "fill", "target": "todo", "fields": fields}, "本地规则解析了待办标题，打开弹窗确认一下。"


def local_parse(text, page):
    """本地兜底解析，覆盖文档里写的那些说法，解析不了就让用户自己填。"""
    today = date.today()

    # 想跳页面
    for path, name in PAGES.items():
        if name in text and re.search(r"打开|去|跳|换|看", text):
            return [{"type": "navigate", "path": path}], f"带你到「{name}」。"

    if re.search(r"请假|病假|事假|年假|休假|休息", text):
        action, reply = local_leave(text, today)
        return ([action] if action else []), reply

    if re.search(r"待办|任务", text):
        action, reply = local_todo(text, today)
        return ([action] if action else []), reply

    return [], f"我现在只连了本地规则，认不出这句。当前在「{PAGES.get(page, '工作台')}」页。"


# ==================================================================
# 四、HTTP 接口
# ==================================================================
@app.post("/api/ai/chat")
def chat():
    body = request.get_json(silent=True) or {}
    history = body.get("messages") or []
    page = body.get("page") or "/dashboard"
    user = (body.get("user") or "").strip()

    last_user_text = ""
    for message in reversed(history):
        if message.get("role") == "user":
            last_user_text = message.get("content") or ""
            break

    # 通道是一个个试的：本机模型 → 本地死规则
    failures = []
    for provider in build_providers():
        try:
            reply, actions = run_agent(history, page, user, provider)
            # 日期一律用我们自己的解析结果校对一遍，见 reconcile_dates 的说明
            actions = [reconcile_dates(action, last_user_text) for action in actions]
            return jsonify(
                {"ok": True, "source": provider["name"], "reply": reply, "actions": actions}
            )
        except Exception as error:  # 超时、断网、502、key 失效、本机没开……统统往下走
            failures.append(f"{provider['label']}：{error}")
            print(f"[降级] {provider['label']} 用不了 → {error}")

    actions, reply = local_parse(last_user_text, page)
    return jsonify(
        {
            "ok": True,
            "source": "local",
            "reply": reply,
            "actions": actions,
            "error": " ; ".join(failures)[:300],
        }
    )


@app.get("/api/ai/health")
def health():
    return jsonify(
        {
            "ok": True,
            "providers": [provider["label"] for provider in build_providers()],
        }
    )


if __name__ == "__main__":
    labels = [provider["label"] for provider in build_providers()]
    print("AI 代理已启动： http://127.0.0.1:5000")
    print("模型通道（按优先级）：", " → ".join(labels) if labels else "无（只能走本地规则）")
    app.run(host="127.0.0.1", port=5000, debug=True)
