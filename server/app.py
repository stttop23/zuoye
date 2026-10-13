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

try:  # 同目录下的临时假数据，为什么有这个东西见它自己的文件头
    import mock_data
except ImportError:  # 万一用 `python -m server.app` 启动
    from server import mock_data

# 本机模型（Ollama）：不用网、不用 key、不花钱
OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/v1/chat/completions")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "1") != "0"
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 冷启动要加载 4.4GB 模型，给足时间

# 高德地图的 Key，用来把经纬度换成地名（逆地理编码）。不填也能跑，只是显示坐标
AMAP_KEY = os.getenv("AMAP_KEY", "").strip()


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
    {
        "type": "function",
        "function": {
            "name": "check_in",
            "description": "帮用户完成今天的打卡。用户说「帮我打卡」「打个卡」「今天还没打卡」时调用。",
            # 打卡不需要参数：时间用当天，位置用浏览器定位。
            # 服务端【做不了】这件事 —— 定位是浏览器的能力，所以这里只递一个信号给前端。
            "parameters": {"type": "object", "properties": {}},
        },
    },

    # ---------------- 下面三个是【只读】工具：只查数据，不改任何东西 ----------------
    # 它们让 AI 从「会填表」变成「知道事」。
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "查待办事项列表。用户问「我有哪些待办」「这周要做什么」「有什么逾期了」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "assignee": {
                        "type": "string",
                        "description": "只在用户明确问别人（如「张晶的待办」）时才填姓名；问「我的」时【不要填】，更不要填「全部」",
                    },
                    "status": {
                        "type": "string",
                        "enum": list(TODO_STATUSES),
                        "description": "只看某个状态，不填就不筛",
                    },
                    "overdue_only": {
                        "type": "boolean",
                        "description": "true 就只看已遍期的（过了截止日期且未完成）",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notices",
            "description": "查公告通知列表。用户问「最近有什么公告」「有没有活动通知」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["通知", "活动", "制度"]},
                    "keyword": {"type": "string", "description": "标题关键词，如「奖学金」"},
                    "limit": {"type": "integer", "description": "最多返回几条，默认 3"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_leave_records",
            "description": "查请假申请记录。用户问「我的请假批了吗」「我请过几次假」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "只在用户明确问别人（如「张晶的请假」）时才填姓名；问「我的」时【不要填】",
                    },
                    "status": {"type": "string", "enum": ["待审批", "已通过", "已驳回"]},
                },
            },
        },
    },
]

SYSTEM_PROMPT = """你是「学生工作管理系统」里的 AI 助手，帮用户查东西和填表单。

当前用户叫「{user}」，正停在「{page}」页面。

{calendar}
{data}
你可以调用工具帮用户做事：
- go_to_page：切换页面
- fill_leave_form：把请假信息填进请假表单（只填、不提交）
- create_todo：打开新建待办弹窗并预填
- check_in：帮用户完成今天的打卡（位置由浏览器定位）
- list_todos / list_notices / list_leave_records：查数据（只读，不会改任何东西）

用户只是说「打开 / 去 / 进入 某个页面」时，只用 go_to_page，
不要调只读工具、也不要建任何东西。注意这两句差别很大：
  「打开公告」＝切到公告页，不是念一遍公告列表。
  「有什么公告 / 公告都写了啥」才是查数据。

「打卡」要用 check_in，不能用 go_to_page 代替：他要的是把卡打上，不是看一眼打卡页面。
调完 check_in 只回一句「正在帮你打卡」就行，【不要】写成「已完成 / 打卡成功」——
真正打没打成由浏览器说了算（可能今天已经打过，也可能定位被拒）。

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
7. 回答要短，不要有一句废话（这是聊天小气泡，长了很难看）：
   - 只是确认 / 填表：一句话，25 字以内。
   - 查数据：最多列 3 条，用「1. 2. 3.」列，多的说「还有 N 条」，不要写额外解释和客套。
   不要用 markdown 标题和代码块，不要复述 JSON，不要重复用户已经知道的事。
8. 用户问「我有哪些待办」「最近有什么公告」「我的请假批了吗」这类问题，
   必须先调对应的只读工具把数据查出来再回答。绝对不能凭印象编一份列表。
9. 只读工具返回的 items 是空的，就直说「没有」，不要自己补。
   条数以工具返回的 count 为准，不要自己数。提到具体事项时最多提 3 条，多的就说「还有 N 条」。
10. 问「我的」东西时，只读工具里【不要填人名】，让它默认查当前用户就行。
    状态、日期、人名必须照抄工具返回的值，一个说法都不要自己改。"""

# ⚠️ 维护提示：上面这段 SYSTEM_PROMPT 里【绝对不能出现任何具体业务值】。
#    不能出现某个状态名、某个人名、某个理由，连「举例说明」都不行。
#    踩过两次坑：
#      1) 早期为了让模型理解 reason，提示词里写了「用户说『感冒发烧』」，
#         结果模型把「感冒发烧」抄进了 answer，当成用户的请假原因。
#      2) 为了说明别用别人的记录，提示词里举了一个状态名当反例，
#         结果模型直接把这个状态名当成了查询结果 —— 实测 8 次错 8 次。
#    小模型对提示词里的字面值没有「这是举例」的概念，只会照着抄。

# 用户这句话像是在【下指令或问数据】，而不是纯闲聊。
# 只有像下指令时才做「追问一次」的补救 —— 不然「你好」也会被逼着乱调工具。
ACTION_HINT_RE = re.compile(
    r"请假|病假|事假|年假|休假|待办|任务|事项|公告|通知|新建|添加|建个|加个|打卡|签到|跳|帮我|查一|看一下|有哪些|多少|几条|批了吗|通过了吗|逾期"
)

NO_TOOL_MARK = "无需工具"

# 追问用的提示词：给它一个台阶，别把「你好」也逼成乱调工具
NUDGE_PROMPT = (
    "停一下。你刚才没有调用任何工具就直接回答了 —— 如果用户是在下指令或问数据，"
    "那个答案是编的，不允许。\n"
    f"现在：需要动手或查数据，就立刻调用合适的工具；"
    f"确实只是闲聊、什么工具都用不上，就只回复「{NO_TOOL_MARK}」这四个字。"
)

# 模型偶尔会把上面那段催办话原样吐给用户（实测出现过），这些词就是泄了
LEAK_MARKS = ("停一下", "无需工具", "系统检查", "那个答案是编的")

# 模型嘴上说「已经帮你做了 / 已经建好了」但一个动作都没产出 —— 它在撒谎。
# 这种谎最坑：界面上什么都没发生，用户还以为做好了。
CLAIM_RE = re.compile(
    r"已经|已帮|已为|帮你|已填|填好|已新建|已创建|已添加|已切换|已打开|已做好|已提交"
)


def sanitize(reply, actions, user_text, page, read_result):
    """
    模型输出的最后一道体检。两种毛病都不认它那句，改走本地规则兜底：

    1) 提示词泄漏：它把我们的催办话原样吐出来了（实测出现过）。
    2) 谎报已做事：说「已经帮你建好了」，但 actions 是空的 —— 界面根本没反应。

    只有本地规则【确实能产出动作】时才替换，否则保留模型的话。
    这点很重要：问「我的请假批了吗」时模型也会说「已经查到了」，
    这不是撒谎，本地规则又接不住，误伤就把对的答案换成了错的。
    """
    if actions or not reply:
        return reply, actions

    leaked = any(mark in reply for mark in LEAK_MARKS)
    claimed = bool(CLAIM_RE.search(reply))
    if not (leaked or claimed):
        return reply, actions

    local_actions, local_reply = local_parse(user_text, page)
    if local_actions:
        return local_reply, local_actions

    if leaked:
        # 本地规则也接不住，但这句泄漏的话不能给用户看
        reply = summarize_read(read_result) if read_result else "没太听懂，换个说法试试？"
    return reply, actions


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


def user_context(user):
    """
    把当前用户的真实数据直接摆进系统提示词（像给他递一份档案袋）。

    为什么要这么干 —— 踩过的坑：
        光在提示词里写「问数据必须先调只读工具」，小模型【只有单轮对话】时听，
        一旦对话有了历史（用户问第二句），它就自作主张直接答，
        连工具都不调，凭空编一个状态出来。
        实测：没历史 3 次全对；有历史 3 次全错（把别人的状态安到了用户头上）。

        与其反复打磨提示词（试过，没用），不如把数据摆在它眼前 ——
        和日期那件事一个思路：确定性的东西不要交给模型去推，
        它只要【照抄】就不会错。

        两者不矛盾：这份档案袋先保证“不会说错”，
        只读工具再负责“档案袋里没写的”（别人的记录、按条件筛）。

    接了数据库之后，这里就是一次按当前用户查表的 SQL，其他地方不用改。
    """
    who = (user or "").strip()
    if not who:
        return "用户数据：未登录，没有可查的个人数据。"

    lines = ["下面是当前用户的【真实数据】。用户问到时直接照这里说，不要编："]

    todos = mock_data.list_todos(assignee=who)
    if todos:
        brief = "；".join(
            f"{item['title']}（{item['dueDate']}，{item['status']}"
            f"{'，已逾期' if item['overdue'] else ''}）"
            for item in todos
        )
        lines.append(f"- 他的待办共 {len(todos)} 条：{brief}")
    else:
        lines.append("- 他的待办：0 条")

    leaves = mock_data.list_leave_records(name=who)
    if leaves:
        brief = "；".join(
            f"{item['type']} {item['startDate']} 到 {item['endDate']}，状态 {item['status']}"
            for item in leaves
        )
        lines.append(f"- 他的请假共 {len(leaves)} 条：{brief}")
    else:
        lines.append("- 他的请假：0 条")

    notices = mock_data.list_notices(limit=3)
    lines.append(
        f"- 公告一共 {len(mock_data.NOTICES)} 条，最新的三条："
        + "；".join(f"{item['title']}（{item['publishTime'][:10]}）" for item in notices)
    )

    lines.append("上面没写到的东西（别人的记录、按条件筛），再用只读工具去查。")
    return "\n".join(lines)


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
                data=user_context(user),
            ),
        }
    ]
    messages += history[-8:]  # 只带最近 8 条，省 token

    last_user_text = ""
    for item in reversed(history):
        if item.get("role") == "user":
            last_user_text = item.get("content") or ""
            break

    actions = []
    reply = ""
    last_read = None  # 最近一次只读工具的结果，兜底文案要用
    nudged = False

    for _ in range(3):
        message = call_model(messages, provider)
        tool_calls = message.get("tool_calls") or []
        content = (message.get("content") or "").strip()

        # ---------- 防「光说不动手」 ----------
        # 实测最要命的一类错：模型不调工具，直接开口答，内容全是编的。
        #   「建个待办 明天截止」→ 回一句「已经为你新建」，其实什么都没建
        #   「张晶有哪些待办」  → 回一句「没有找到」，其实有两条
        # 而且【有历史对话时特别容易这样】，单轮反而正常。
        #
        # 试过 tool_choice="required"，本机这版 Ollama 直接忽略，没用。
        # 所以改成「追问一次」：告诉它刚才那样不行，需要工具就现在调、
        # 真的只是闲聊就回「无需工具」——给个台阶，免得「你好」也被逼着乱调工具。
        if not tool_calls and not nudged and not actions and ACTION_HINT_RE.search(last_user_text):
            nudged = True
            messages.append({"role": "system", "content": NUDGE_PROMPT})
            retry = call_model(messages, provider)
            retry_calls = retry.get("tool_calls") or []
            retry_text = (retry.get("content") or "").strip()

            if retry_calls:
                message, tool_calls = retry, retry_calls
            elif NO_TOOL_MARK in retry_text:
                # 它说确实不用工具 —— 那第一遍那个回答就是正经答案
                message = {"role": "assistant", "content": content}
            else:
                message = retry
                content = retry_text

        messages.append(message)

        if not tool_calls:
            reply = content
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

            result, action = run_tool(name, args, user)
            if action and action not in actions:
                actions.append(action)
            if name in READ_TOOL_NAMES:
                last_read = result

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    if not reply:
        reply = default_reply(actions, last_read)
    reply, actions = sanitize(reply, actions, last_user_text, page, last_read)
    return reply, actions


def default_reply(actions, read_result=None):
    """模型光调工具不说话时的兜底文案。"""
    for action in actions:
        if action["type"] == "fill" and action["target"] == "leave":
            return "已经帮你填好了，检查一下再提交。"
        if action["type"] == "fill" and action["target"] == "todo":
            return "待办弹窗已经打开并预填，确认后保存。"
        if action["type"] == "navigate":
            return f"带你到「{PAGES.get(action['path'], '目标页')}」。"
    # 查完数据不说话：把查到的念一遍，总比干吧吧一句「我在」强
    if read_result:
        return summarize_read(read_result) or "我在，有什么要办的？"
    return "我在，有什么要办的？"


def summarize_read(result):
    """把只读工具的结果压成一句话（模型没吭声时用）。"""
    if not result.get("ok"):
        return "查数据的时候出错了。"
    items = result.get("items") or []
    if not items:
        return "没查到符合条件的记录。"
    names = []
    for item in items[:3]:
        name = item.get("title") or item.get("name") or ""
        if name:
            names.append(name)
    tail = "……" if len(items) > 3 else ""
    return f"查到 {len(items)} 条：{'、'.join(names)}{tail}"


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
    if name == "check_in":
        # 打卡整个流程（取定位 → 查地名 → 落记录）都在浏览器里跑：
        # 定位是浏览器的能力，服务端拿不到坐标。所以这里只递一个信号。
        return {"type": "checkin"}
    return None


READ_TOOL_NAMES = ("list_todos", "list_notices", "list_leave_records")


def run_tool(name, args, user):
    """
    执行模型点名的工具，返回 (喂回给模型的结果, 给前端执行的动作)。

    为什么要把这两件事分开：
        老写法默认「调工具 = 前端得做点什么」，所以结果里只回一个 action。
        但「查我的待办」这种只读工具是【取数据给模型看】，前端什么都不用做 ——
        硬塞一个 action 回去，前端会收到它不认识的动作类型。

    所以：只读工具 → 有结果、没动作；写工具 → 有动作。

    user 是当前登录用户名，只读工具在不填人名时用它当默认值，
    这样「我有哪些待办」查的就是他自己，而不是所有人。
    """
    if name in READ_TOOL_NAMES:
        return read_tool(name, args, user), None

    action = action_from_tool(name, args)
    return {"ok": action is not None, "action": action}, action


def read_tool(name, args, user):
    """只读工具的实现：把结果整理成 JSON 交回给模型。"""
    try:
        if name == "list_todos":
            items = mock_data.list_todos(
                assignee=(args.get("assignee") or user or "").strip(),
                status=args.get("status"),
                overdue_only=bool(args.get("overdue_only")),
            )
        elif name == "list_notices":
            items = mock_data.list_notices(
                type_=args.get("type"),
                keyword=args.get("keyword"),
                limit=args.get("limit"),
            )
        elif name == "list_leave_records":
            items = mock_data.list_leave_records(
                name=(args.get("name") or user or "").strip(),
                status=args.get("status"),
            )
        else:
            return {"ok": False, "error": f"没有这个工具：{name}"}
    except Exception as error:  # 数据文件写错了也别把整个请求带崩
        return {"ok": False, "error": str(error)[:200]}

    return {"ok": True, "count": len(items), "today": date.today().isoformat(), "items": items}


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

    # 打卡：整个流程在浏览器里跑，这里只回一个动作
    if re.search(r"打卡|签到", text):
        return [{"type": "checkin"}], "正在帮你打卡。"

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


# ==================================================================
# 五、地理：把经纬度换成地名（逆地理编码）
#
# 为什么非要一个 key：
#   浏览器自带的定位只给一串坐标，里面没有地名。要「这是哪条路、哪个学校」，
#   必须再拿坐标去查地图服务。国内能用的（高德/腾讯/百度）全都要 key，
#   免费的 OpenStreetMap 在国内连不上（实测超时）。
#
# 为什么在服务端调，不在浏览器里调：
#   放浏览器里，谁打开 F12 都能把 key 抄走。放服务端，key 不出这台机器。
#   顺带好处：以后想换腾讯/百度，前端一行都不用改。
#
# key 怎么弄（约 5 分钟，个人开发者免费 5000 次/天）：
#   1. 打开 https://lbs.amap.com/ ，注册并完成个人实名认证
#   2. 控制台 → 应用管理 → 我的应用 → 创建应用
#   3. 添加 Key，服务平台【必须选「Web服务」】（选错成「Web端」会报 10009）
#   4. 把 key 填到 server/.env 的 AMAP_KEY=
# ==================================================================
AMAP_REVERSE_URL = "https://restapi.amap.com/v3/geocode/regeo"


# 高德表示「没查到」的方式不统一：有的字段给 ""，有的给 []。统一收拾成字符串。
def text_field(value):
    return value if isinstance(value, str) else ""


def amap_reverse(lat, lng):
    """坐标 → 地名。拿不到就返回 ok=False，绝不让打卡本身失败。"""
    if not AMAP_KEY:
        return {"ok": False, "reason": "未配置 AMAP_KEY", "hint": "见 server/.env.example"}

    try:
        response = requests.get(
            AMAP_REVERSE_URL,
            params={
                "key": AMAP_KEY,
                # ⚠️ 高德要的是「经度,纬度」，跟大家习惯的「纬度,经度」反着，别写错
                "location": f"{lng},{lat}",
                # ⚠️ 必须是 all：只有它才会返回附近的 pois（学校、大楼、商场）。
                #    一开始写的是 base，于是下面「POI 优先」那段代码永远拿不到数据 —— 白写。
                "extensions": "all",
                "radius": 300,
            },
            timeout=8,
        )
        payload = response.json()
    except Exception as error:  # 断网、超时、返回的不是 JSON
        return {"ok": False, "reason": f"请求高德失败：{str(error)[:120]}"}

    if payload.get("status") != "1":
        # 10001 key 无效 / 10003 额度过 / 10009 平台类型选错 / 10012 请求过快
        return {
            "ok": False,
            "reason": f"高德返回 {payload.get('infocode')}：{payload.get('info')}",
        }

    regeo = payload.get("regeocode") or {}
    parts = regeo.get("addressComponent") or {}

    # 由远到近拼一个短地址（不要省，太长了手机上换行很难看）
    # ⚠️ 高德把「路名」放在 streetNumber.street 里，没有顶层的 street 字段。
    #    一开始写成 parts["street"]，拼出来是「灵隐街道866号」—— 路名丢了。
    street_number = parts.get("streetNumber")
    if isinstance(street_number, dict):
        street = text_field(street_number.get("street"))
        number = text_field(street_number.get("number"))
    else:
        street, number = "", ""

    short = "".join(
        [
            text_field(parts.get("city")) or text_field(parts.get("province")),
            text_field(parts.get("district")),
            text_field(parts.get("township")),
            street,
            number,
        ]
    )

    # 高德还会顺带返回附近的兴趣点（学校、大楼、商场），这个比路名更好认
    pois = regeo.get("pois") or []
    first = pois[0] if pois and isinstance(pois[0], dict) else {}

    return {
        "ok": True,
        "source": "amap",
        "poi": text_field(first.get("name")),
        "poiDistance": text_field(first.get("distance")),
        "short": short,
        "address": text_field(regeo.get("formatted_address")),
    }


@app.get("/api/geo/reverse")
def geo_reverse():
    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "reason": "lat / lng 必须是数字"}), 400
    return jsonify(amap_reverse(lat, lng))


if __name__ == "__main__":
    labels = [provider["label"] for provider in build_providers()]
    print("AI 代理已启动： http://127.0.0.1:5000")
    print("模型通道（按优先级）：", " → ".join(labels) if labels else "无（只能走本地规则）")
    print("逆地理编码（坐标→地名）：", "已配 AMAP_KEY" if AMAP_KEY else "未配 AMAP_KEY（打卡只显示坐标）")
    app.run(host="127.0.0.1", port=5000, debug=True)
