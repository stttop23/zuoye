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
import sqlite3
import threading
from datetime import date, datetime, timedelta

import requests
from flask import Flask, jsonify, request

try:  # 有 python-dotenv 就自动读 server/.env，没有也不影响
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

app = Flask(__name__)
DATABASE_PATH = os.getenv(
    "STUDENT_WORK_DB", os.path.join(os.path.dirname(__file__), "student_work.db")
)

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

# ⚠️⚠️ 这张表是【跳转白名单】，它同时是 go_to_page 工具 path 参数的 enum。
#    漏一个页面 = 模型【根本没法选它】——不报错，但 AI 就是“跳不过去”。
#    而且前端 src/composables/aiAgent.js 里还有一张「本地兜底」的同名表，
#    两张表必须一起改！之前加通讯录时只改了前端那张，
#    结果后端跳不了 /contacts（问「打开通讯录」会得到「已带你到…」但没跳）。
PAGES = {
    "/dashboard": "工作台",
    "/notice": "公告通知",
    "/leave": "请假申请",
    "/todo": "待办事项",
    "/contacts": "通讯录",
    "/chat": "群聊",
    "/assistant": "AI 助手",
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
            "name": "chat_action",
            "description": (
                "操作群聊界面。必须根据用户的措辞选 action：\n"
                "- 用户说「帮我写一句 / 起草 / 拟一句」→ action=draft（只把草稿填进输入框，不发送）\n"
                "- 用户说「发 / 发送 / 发出去 / 发给」→ action=send（真的发出去）\n"
                "- 只是想看某个群 → action=open\n"
                "分不清就用 draft（宁可只填不发，消息发出去撤不回来）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["open", "draft", "send"],
                        "description": "open=只切到那个群；draft=只填草稿；send=真发出去",
                    },
                    "text": {
                        "type": "string",
                        "description": "要写/要发的内容。用用户的原话，不要替他润色。draft / send 必填",
                    },
                    "group": {
                        "type": "string",
                        "description": "群名称，可省略；省略则用当前打开的群",
                    },
                },
                "required": ["action"],
            },
        },
    },
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
    {
        "type": "function",
        "function": {
            "name": "manage_todo",
            "description": "对待办做事：标为完成、重新打开、删除、或打开编辑弹窗。用户说「把XX标成完成」「XX做完了」「删掉XX」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["complete", "reopen", "delete", "edit"],
                        "description": "complete=完成、reopen=重新打开、delete=删除、edit=打开编辑弹窗",
                    },
                    "title": {"type": "string", "description": "待办的标题，照拄用户说的那几个字"},
                },
                "required": ["action", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "undo_check_in",
            "description": "撤销今天的打卡。用户说「撤销打卡」「我打错了」时调用。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_leave",
            "description": "撤销用户自己的【还没审批的】请假申请。用户说「撤销我的请假」「那条请假不请了」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": list(LEAVE_TYPES),
                        "description": "请假类型，只在用户提到了具体哪种假时才填",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "review_leave",
            "description": "审批请假申请：通过或驳回。只有管理员能调。用户说「通过张晶的请假」「把李四那条驳回」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "申请人的姓名"},
                    "status": {"type": "string", "enum": ["已通过", "已驳回"]},
                },
                "required": ["name", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_notice",
            "description": "在公告页搜一条公告并打开它的详情弹窗。用户说「看看奖学金那条公告」「搜一下活动通知」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "要搜的词，照拄用户说的"},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "switch_role",
            "description": "切换当前用户的身份（学生 ↔ 管理员）。用户说「切到管理员」「换回学生」时调用。",
            "parameters": {
                "type": "object",
                "properties": {"role": {"type": "string", "enum": ["student", "admin"]}},
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_user",
            "description": "改当前用户的显示名称。用户说「以后叫我小王」「把我名字改成…」时调用。",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "新的显示名称，1-20 字"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_setting",
            "description": "开关界面设置：界面动效、未读红点。用户说「把动效关掉」「别显示红点了」时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": ["界面动效", "未读红点"]},
                    "value": {"type": "boolean", "description": "true = 打开，false = 关掉"},
                },
                "required": ["name", "value"],
            },
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
    {
        "type": "function",
        "function": {
            "name": "checkin_status",
            "description": "查今天的打卡情况（打没打、几点打的、在哪儿）。用户问「我今天打卡了吗」「我打卡了吗」时调用。",
            "parameters": {"type": "object", "properties": {}},
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
- undo_check_in：撤销今天的打卡
- manage_todo：对待办做事（完成 / 重新打开 / 删除 / 打开编辑弹窗）
- cancel_leave：撤销自己还没审批的请假
- review_leave：审批请假（通过 / 驳回，只有管理员能调）
- open_notice：在公告页搜一条公告并打开详情
- switch_role：切换身份（学生 / 管理员）
- rename_user：改用户的显示名称
- toggle_setting：开关界面动效、未读红点
- list_todos / list_notices / list_leave_records / checkin_status：查数据（只读，不会改任何东西）

用户只是说「打开 / 去 / 进入 某个页面」时，只用 go_to_page，
不要调只读工具、也不要建任何东西。注意这几句差别很大：
  「打开公告」＝切到公告页，不是念一遍公告列表。
  「有什么公告 / 公告都写了啥」才是查数据。
  「看看奖学金那条公告」＝搜出来并打开详情（open_notice）。
  「我今天打卡了吗 / 打卡了没」＝问情况，调 checkin_status；「帮我打卡」才是 check_in。

工具返回的数据就是用户此刻页面上真实的那一份（前端每次发消息都会把数据推上来），
所以你读到什么就说什么，不用怀疑它会过期。

「打卡」要用 check_in，不能用 go_to_page 代替：他要的是把卡打上，不是看一眼打卡页面。
调完 check_in 只回一句「正在帮你打卡」就行，【不要】写成「已完成 / 打卡成功」——
真正打没打成由浏览器说了算（可能今天已经打过，也可能定位被拒）。
但「我今天打卡了吗」是【问情况】，要调 checkin_status（只读），不要调 check_in。

几个带「撤销 / 删」的说法，别选错工具：
  「撤销打卡」→ undo_check_in；「撤销我的请假」→ cancel_leave；
  「删掉那条待办」→ manage_todo（action=delete）。
审批类（review_leave）只有管理员能调：当前身份是学生时，
用户让你审批就照直说「切到管理员才能审批」，不要硬调。
审批只能动【还没审批的】记录；已经批过的不重复审。

硬性规则：
0. 【最重要】用户说「打开 / 去 / 进入 / 切到 某个页面」时，只调 go_to_page，
   绝对不要调只读工具、也不要念列表。他要去那个页面，不是让你把里面的内容念一遍。
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
    r"请假|病假|事假|年假|休假|待办|任务|事项|公告|通知|新建|添加|建个|加个|打卡|签到|"
    r"打开|进入|跳|帮我|查一|看一下|有哪些|多少|几条|批了吗|通过了吗|逾期|"
    r"撤销|审批|驳回|完成|做完了|删掉|删除|改成|搜一下|看看|切到|换回|叫我|关掉|"
    r"群聊|群里|群发|发言|发一句|发条|写一句|起草"
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

# 只说「稍候一下就动手」但一个动作都没产出 —— 也是空口承诺。
# ⚠️ 不要把光秃的「正在」放进来：查数据时模型也会说「正在查」，那不是撚谎。
PROMISE_RE = re.compile(r"稍候|马上|这就|立刻|处理中|切换中|正在帮你|正在为")

# 工具名清单：模型把工具名当话说了出来（实测「undo_check_in」、
# 「cancel_leave {"kind": "事假"}」）—— 看着像做到了，其实一个工具都没调。
# 工具一多（现在 15 个）小模型特别容易这样。
TOOL_NAMES = tuple(tool["function"]["name"] for tool in TOOLS)


def sanitize(reply, actions, user_text, page, read_result, snapshot=None):
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
    # 后来补的两种（都是工具变多之后实测出来的毛病）：
    tool_named = any(f" {name}" in f" {reply}" for name in TOOL_NAMES)
    promised = bool(PROMISE_RE.search(reply))
    # 第三种：直接把用户的话复读回去（实测「切到管理员」→回一句「切到管理员」）。
    # 正常回答不会比用户的话还短还一模一样。
    echoed = bool(reply.strip()) and reply.strip() in user_text
    if not (leaked or claimed or tool_named or promised or echoed):
        return reply, actions

    local_actions, local_reply = local_parse(user_text, page, snapshot)
    if local_actions:
        return local_reply, local_actions

    if leaked or tool_named or promised or echoed:
        # 这几类话都不能给用户看：
        #   泄漏的催办词 / 光报工具名（manage_todo({...})）/ 空口承诺 / 复读。
        # 优先拿只读结果当回话，没有就说一句老实的话。
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


def user_context(user, snapshot=None):
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

    ⚠️ 这里也必须用前端上报的快照，不能读 mock_data 的种子：
        这是「AI 说的和页面上显示的对不上」的【第二个来源】——
        档案袋里塞的是旧数据，模型照着抄得越认真，错得越离谱。
        快照拿不到才退回种子（见 snapshot_list）。

    接了数据库之后，这里就是一次按当前用户查表的 SQL，其他地方不用改。
    """
    who = (user or "").strip()
    if not who:
        return "用户数据：未登录，没有可查的个人数据。"

    lines = ["下面是当前用户的【真实数据】。用户问到时直接照这里说，不要编："]

    todos = filter_todos(snapshot_list(snapshot, "todos") or mock_data.TODOS, assignee=who)
    if todos:
        brief = "；".join(
            f"{item['title']}（{item['dueDate']}，{item['status']}"
            f"{'，已逾期' if item['overdue'] else ''}）"
            for item in todos
        )
        lines.append(f"- 他的待办共 {len(todos)} 条：{brief}")
    else:
        lines.append("- 他的待办：0 条")

    leaves = filter_leave_records(
        snapshot_list(snapshot, "leaveRecords") or mock_data.LEAVE_RECORDS, name=who
    )
    if leaves:
        brief = "；".join(
            f"{item['type']} {item['startDate']} 到 {item['endDate']}，状态 {item['status']}"
            for item in leaves
        )
        lines.append(f"- 他的请假共 {len(leaves)} 条：{brief}")
    else:
        lines.append("- 他的请假：0 条")

    all_notices = snapshot_list(snapshot, "notices") or mock_data.NOTICES
    notices = filter_notices(all_notices, limit=3)
    lines.append(
        f"- 公告一共 {len(all_notices)} 条，最新的三条："
        + "；".join(f"{item['title']}（{item['publishTime'][:10]}）" for item in notices)
    )

    state = read_checkin(snapshot)
    if state.get("known"):
        if state.get("checked_in"):
            lines.append(f"- 他今天已打卡（{state.get('time') or ''}）")
        else:
            lines.append("- 他今天还没打卡")

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


def run_agent(history, page, user, provider, snapshot=None):
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
                data=user_context(user, snapshot),
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

            result, action = run_tool(name, args, user, snapshot)
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
    reply, actions = sanitize(reply, actions, last_user_text, page, last_read, snapshot)
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
    # 打卡不是列表，单独说一句
    if "checked_in" in result:
        if result.get("checked_in"):
            where = f"，{result['place']}" if result.get("place") else ""
            return f"今天 {result.get('time') or ''} 打过卡了{where}。"
        return "今天还没打卡。"
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


# 群聊动作（三个），体检时要一起管
CHAT_ACTIONS = ("chat_open", "chat_draft", "chat_send")

# 「发」类的措辞：出现这些词，就是用户要求真发出去
CHAT_SEND_RE = re.compile(r"发出去|发送|发给|发到|发一句|发一条|发个|发句")
# 「写」类的措辞：只要求写草稿
CHAT_DRAFT_RE = re.compile(r"帮我写|起草|拟一?句|写一?句|写条|填一?句")


def _normalize_for_compare(text):
    """去掉空白和标点，只留下“字”。比对“这句话是不是用户说的”时用。"""
    return re.sub(r"[\s。！!？?，,、：:；;\"'「」『』]+", "", text or "")


def enforce_chat(actions, user_text):
    """
    群聊动作的事后体检。返回 (新 actions, 需要覆盖的回复或 None)。

    ⚠️⚠️ 两道都是实测出来的，不是防患于未然：

    1. 【正文必须是用户的原话】
       小模型会凭空编。实测「在群里发消息」，它编出了
       正文「大家好，今天天气不错哦！」和一个【不存在的】群名「班级群」。
       消息发出去撤不回来，而且是拿用户的名义发的 —— 对不上就整条丢掉，宁可什么都不做。
       （比对前两边都去标点空白，「明天开会」和「明天开会。」要算一样。）

    2. 【draft / send 由用户的措辞决定，不由模型决定】
       实测 5 句里 5 句都被判成 draft，连「在开发1群发一句…」也是 ——
       小模型分不清「写一句」和「发一句」。
       所以：说了发就是 send，说了写就是 draft，两个都出现按【发】算。

    3. 【「打开 XX 群」要真的切过去】
       模型往往只给一个 navigate(/chat)，不会去调 chat_action(open)，
       于是回复说着「已经帮你切到项目讨论组了」，其实只打开了群聊页。
       这里用 local_chat 把它补上。

    返回 (新 actions, 要覆盖的回复或 None)。
    """
    user_norm = _normalize_for_compare(user_text)
    wants_send = bool(CHAT_SEND_RE.search(user_text or ""))
    wants_draft = bool(CHAT_DRAFT_RE.search(user_text or ""))

    out = []
    flipped_to_send = False
    dropped = 0
    for action in actions or []:
        kind = action.get("type")
        if kind not in CHAT_ACTIONS:
            out.append(action)
            continue
        if kind == "chat_open":
            out.append(action)
            continue

        text = (action.get("text") or "").strip()
        if not text or _normalize_for_compare(text) not in user_norm:
            # 模型自己编的正文 → 丢掉
            dropped += 1
            continue

        # ⚠️ 群名也要验来源：实测用户只说「帮我写一句明天下午三点开会」，
        #    根本没提群，模型却自己编了个「学生工作群」塞进 group。
        #    编出来的群名会被前端挡掉（那个守卫是对的），但回复却会说
        #    「已经拟好了」—— 用户看到的是“说了做了、其实什么都没做”。
        #    所以只要群名不是用户原话里的，就丢掉群名（动作保留，发到当前群去）。
        group = (action.get("groupName") or "").strip()
        if group and _normalize_for_compare(group) not in user_norm:
            action = {**action, "groupName": ""}

        if wants_send:
            if kind != "chat_send":
                flipped_to_send = True
            action = {**action, "type": "chat_send"}
        elif wants_draft:
            action = {**action, "type": "chat_draft"}
        out.append(action)

    # 「打开 XX 群」：补上切群那一步（见 docstring 第 3 条）
    if not any(item.get("type") == "chat_open" for item in out):
        local = local_chat(user_text)
        if local and local["type"] == "chat_open":
            out.append(local)

    if dropped:
        # 动作丢了，回复也得换掉 —— 不然它会念着编的内容问「发出去吗」
        return out, "这句我没听清要发什么内容，再说具体一点？"
    if flipped_to_send:
        # 模型那句「你可以点发送按钮」和刚改的动作矛盾，一并覆盖
        return out, "正在帮你发出去。"
    return out, None


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
    if name == "undo_check_in":
        return {"type": "checkin_undo"}
    if name == "manage_todo":
        # 只认可枚举里的四个动作，其余一律丢掉（跟字段白名单一个思路）
        todo_action = args.get("action")
        title = (args.get("title") or "").strip()
        if todo_action in ("complete", "reopen", "delete", "edit") and title:
            return {"type": "todo_action", "action": todo_action, "title": title[:40]}
        return None
    if name == "cancel_leave":
        kind = args.get("kind")
        return {"type": "leave_cancel", "kind": kind if kind in LEAVE_TYPES else ""}
    if name == "review_leave":
        applicant = (args.get("name") or "").strip()
        status = args.get("status")
        if applicant and status in ("已通过", "已驳回"):
            return {"type": "leave_review", "name": applicant[:20], "status": status}
        return None
    if name == "open_notice":
        keyword = (args.get("keyword") or "").strip()
        return {"type": "notice_open", "keyword": keyword[:40]} if keyword else None
    if name == "switch_role":
        role = args.get("role")
        return {"type": "switch_role", "role": role} if role in ("student", "admin") else None
    if name == "rename_user":
        new_name = (args.get("name") or "").strip()
        return {"type": "rename_user", "name": new_name[:20]} if new_name else None
    if name == "toggle_setting":
        setting = args.get("name")
        if setting in ("界面动效", "未读红点") and isinstance(args.get("value"), bool):
            return {"type": "toggle_setting", "name": setting, "value": args["value"]}
        return None
    if name == "chat_action":
        # 群聊：一个工具 + 一个 action 枚举。
        # ⚠️ 为什么不做成三个独立工具（open_chat / draft_chat / send_chat）：
        #    小模型在「三个长得很像的工具」之间选错的概率很高（本项目踩过：
        #    工具从 7 个加到 15 个之后，选择准确率明显下降）。
        #    同一件事的几个模式压成一个 enum 参数，表征上更稳。
        action = args.get("action")
        text = (args.get("text") or "").strip()
        group = (args.get("group") or "").strip()
        if action == "open":
            return {"type": "chat_open", "groupName": group[:20]}
        # draft / send 必须有内容 —— 没有内容就不是一个动作，直接丢掉
        if action in ("draft", "send") and text:
            return {
                "type": "chat_draft" if action == "draft" else "chat_send",
                "text": text[:200],
                "groupName": group[:20],
            }
        return None
    return None


READ_TOOL_NAMES = ("list_todos", "list_notices", "list_leave_records", "checkin_status")

# 模型说「全部 / 所有人」时不按人筛选
ALL_WORDS = ("全部", "所有", "所有人", "*", "大家")


def wants_all(value):
    return str(value or "").strip() in ALL_WORDS


def pick(item, keys):
    """只把模型需要知道的字段挑出来，别把整个对象塞过去浪费 token。"""
    return {key: item.get(key) for key in keys if item.get(key) is not None}


def snapshot_list(snapshot, key):
    """
    从「现场快照」里取一份列表。

    为什么要有这个东西：只读工具以前读的是 mock_data.py 里【手抄】的一份，
    而用户在页面上的增删改那边根本不知道 —— 于是 AI 会一本正经地告诉你
    一条你已经做完的待办「还是待办」。这比单纯答错更伤，因为听着有据可查。

    现在前端每次发消息都把当前数据一起带上来（src/composables/appStore.js
    的 agentSnapshot），这里优先用它 —— 相当于把「看录像回放」改成「看监控现场」。
    快照里没这个 key（比如页面还没打开过）才退回 mock_data 里的种子。
    """
    if not isinstance(snapshot, dict) or key not in snapshot:
        return None
    value = snapshot.get(key)
    return value if isinstance(value, list) else None


def filter_todos(items, assignee=None, status=None, overdue_only=False):
    """查待办。逾期与否由这里的代码判断 —— 这种日期比较不能交给模型算。"""
    today = date.today().isoformat()
    result = []

    for item in items:
        if not wants_all(assignee) and assignee and item.get("assignee") != assignee:
            continue
        if status and item.get("status") != status:
            continue
        due = item.get("dueDate") or ""
        overdue = bool(due) and due < today and item.get("status") != "已完成"
        if overdue_only and not overdue:
            continue
        row = pick(item, ("id", "title", "category", "priority", "assignee", "dueDate", "status"))
        row["overdue"] = overdue
        result.append(row)

    result.sort(key=lambda row: row.get("dueDate") or "")
    result.sort(key=lambda row: row.get("status") == "已完成")
    return result


def filter_notices(items, type_=None, keyword=None, limit=3):
    """查公告。排序和前端一致：置顶的在前，然后按 id 从大到小。"""
    kw = (keyword or "").strip()
    result = []

    for item in items:
        if type_ and item.get("type") != type_:
            continue
        if kw and kw not in (item.get("title") or ""):
            continue
        result.append(pick(item, ("id", "title", "type", "author", "publishTime", "top")))

    result.sort(key=lambda row: row.get("id") or 0, reverse=True)
    result.sort(key=lambda row: not row.get("top"))
    try:
        count = int(limit)
    except (TypeError, ValueError):
        count = 5
    return result[: max(1, min(count, 12))]


def filter_leave_records(items, name=None, status=None):
    """查请假记录。name 传「全部」查所有人。"""
    result = []
    for item in items:
        if not wants_all(name) and name and item.get("name") != name:
            continue
        if status and item.get("status") != status:
            continue
        result.append(
            pick(
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
    result.sort(key=lambda row: row.get("id") or 0, reverse=True)
    return result


def read_checkin(snapshot):
    """
    查今天的打卡。打卡记录存在浏览器里（坐标、地名只有浏览器拿得到），
    所以这份数据【只可能】从快照来，没有快照就老实说不知道。
    """
    today = date.today().isoformat()
    state = (snapshot or {}).get("checkin") if isinstance(snapshot, dict) else None
    if not isinstance(state, dict):
        return {"ok": True, "known": False, "today": today, "note": "打卡记录在用户浏览器里，这次没拿到"}

    place = state.get("place") or {}
    # 和页面上显示的口径保持一致：省市县（+ 附近 POI）。
    # ⚠️ 顺序必须和 CheckIn.vue 的 placeText 一样，否则会出现
    #    「页面写浙江省杭州市拱墅区、AI 答鸡爪山」的同源不同答。
    region = place.get("region") or ""
    poi = place.get("poi") or ""
    place_text = " · ".join([x for x in (region, poi) if x]) or place.get("short") or place.get("address") or ""
    return {
        "ok": True,
        "known": True,
        "today": today,
        "checked_in": state.get("lastDate") == today,
        "time": state.get("lastTime") or "",
        "streak": state.get("streak") or 0,
        "place": place_text,
        "items": [],
    }


def run_tool(name, args, user, snapshot=None):
    """
    执行模型点名的工具，返回 (喂回给模型的结果, 给前端执行的动作)。

    为什么要把这两件事分开：
        老写法默认「调工具 = 前端得做点什么」，所以结果里只回一个 action。
        但「查我的待办」这种只读工具是【取数据给模型看】，前端什么都不用做 ——
        硬塞一个 action 回去，前端会收到它不认识的动作类型。

    所以：只读工具 → 有结果、没动作；写工具 → 有动作。

    user 是当前登录用户名，只读工具在不填人名时用它当默认值，
    这样「我有哪些待办」查的就是他自己，而不是所有人。

    snapshot 是前端上报的现场数据，只读工具优先用它（见 snapshot_list）。
    """
    if name in READ_TOOL_NAMES:
        return read_tool(name, args, user, snapshot), None

    action = action_from_tool(name, args)
    return {"ok": action is not None, "action": action}, action


def read_tool(name, args, user, snapshot=None):
    """只读工具的实现：把结果整理成 JSON 交回给模型。"""
    try:
        if name == "checkin_status":
            return read_checkin(snapshot)

        if name == "list_todos":
            items = filter_todos(
                snapshot_list(snapshot, "todos") or mock_data.TODOS,
                assignee=(args.get("assignee") or user or "").strip(),
                status=args.get("status"),
                overdue_only=bool(args.get("overdue_only")),
            )
        elif name == "list_notices":
            items = filter_notices(
                snapshot_list(snapshot, "notices") or mock_data.NOTICES,
                type_=args.get("type"),
                keyword=args.get("keyword"),
                limit=args.get("limit"),
            )
        elif name == "list_leave_records":
            items = filter_leave_records(
                snapshot_list(snapshot, "leaveRecords") or mock_data.LEAVE_RECORDS,
                name=(args.get("name") or user or "").strip(),
                status=args.get("status"),
            )
        else:
            return {"ok": False, "error": f"没有这个工具：{name}"}
    except Exception as error:  # 数据格式不对也别把整个请求带崩
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


def local_chat(text):
    """
    群聊：从一句话里拆出「干什么 / 发去哪 / 说什么」。

    ⚠️ 措辞决定动作，必须严格区分：
        「帮我写一句…」→ chat_draft（只填草稿，用户自己按发送）
        「发一句…」「发出去」→ chat_send（真发）
      两个词都出现（「写一句…然后发出去」）→ 按发算，因为用户明确说了发。

    ⚠️ 抽不出正文就返回 None，交给上层说「认不出」。
      绝不能把整句话当消息发出去 —— 群消息发出去撤不回来，宁可不做。
      正因如此，「发消息」这种没带正文的说法也要落到 None 上。

    返回 None 或 {type, text, groupName}
    """
    if not text:
        return None

    send_words = re.search(r"发出去|发送|发给|发到|发一句|发一条|发个|发句", text)
    draft_words = re.search(r"帮我写|起草|拟一?句|写一?句|写条|填一?句", text)
    open_words = re.search(r"打开|进入|切到|换到", text)
    # 【不能】用「text 里有『群』字」当门槛：「项目讨论组」里面没有「群」字，
    # 那样会直接错过「打开项目讨论组」。真正的门槛在下面的群名提取。
    if not (send_words or draft_words or open_words):
        return None

    # 群名：形如「XX群 / XX讨论组 / XX小组」。
    # ⚠️ 前面的 {2,12} 是贪心的：「帮我在开发1群发一句」会被整个吃成「帮我在开发1群」；
    #    「打开群聊」则会吃成「打开群」（把动词当成了群名）。
    #    所以匹配完要把常见的动词/代词前缀削掉；削完不足两个字就当「没说群名」。
    group = ""
    group_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,12}(?:群|讨论组|小组))", text)
    if group_match:
        raw = re.sub(
            r"^(帮我|给我|帮忙|麻烦|请|打开|进入|切到|换到|看看|看|在|到|去|一下|这个|那个)+",
            "",
            group_match.group(1),
        )
        if len(raw) >= 2:
            group = raw

    # 正文按这个顺序找，越靠前越可靠：
    #   1. 「发/写 + 量词 + 正文」—— 必须带量词（一句/一条/个）。
    #      这样「在群里发消息」抽不出正文，会老实落到 None，
    #      而不是把「消息」两个字发出去。
    #   2. 引号里的
    #   3. 冒号/逗号后面的
    content = ""
    tail = re.search(r"(?:发|写|填)(?:一?[句条个])[:：,，]?\s*([^。！!？?]{1,120})", text)
    if tail:
        content = tail.group(1)
    else:
        quoted = re.search(r"[「『\"'\u201c]([^」』\"'\u201d]{1,120})[」』\"'\u201d]", text)
        if quoted:
            content = quoted.group(1)
        else:
            after = re.search(r"[：:，,]\s*([^。！!？?]{1,120})", text)
            if after:
                content = after.group(1)
    content = content.strip()

    if not content:
        # 没有正文 → 只可能是「打开某个群」
        if open_words and group:
            return {"type": "chat_open", "groupName": group}
        return None

    action = "chat_draft" if (draft_words and not send_words) else "chat_send"
    return {"type": action, "text": content, "groupName": group}


def local_parse(text, page, snapshot=None):
    """本地兜底解析，覆盖文档里写的那些说法，解析不了就让用户自己填。"""
    today = date.today()

    # 「我今天打卡了吗」是问情况，不是命令。
    # 本来下面那个问句守卫会把它挡掉，但打卡状态就在快照里，能如实回答 ——
    # 该知道的就说知道，别装作不知道。
    if re.search(r"打卡|签到", text) and re.search(r"吗|了没|有没有|记录|情况|几次", text):
        state = read_checkin(snapshot)
        if not state.get("known"):
            return [], "打卡记录存在这台浏览器里，我这次没拿到。"
        if state.get("checked_in"):
            where = f"，{state['place']}" if state.get("place") else ""
            return [], f"今天 {state.get('time')} 打过了{where}，连续 {state.get('streak')} 天。"
        return [], "今天还没打卡。"

    # ⚠️ 问句不是命令，直接不接。
    # 踩过：「我有哪些待办」被 local_todo 当成「新建待办」，弹出一个空弹窗 ——
    # 查数据的句子绝不能走本地命令兜底（那是只读工具的活）。
    if re.search(r"有哪些|有多少|几条|哪些|什么|怎么样|了吗|吗？|吗\?|吗$", text):
        return [], f"这个得查数据，我现在连不上后端。当前在「{PAGES.get(page, '工作台')}」页。"

    # 打卡（含撤销）。注意先判撤销，不然「撤销打卡」会先被下面的打卡分支吃掉
    if re.search(r"打卡|签到", text):
        if re.search(r"撤销|取消|打错|不算|反悔", text):
            return [{"type": "checkin_undo"}], "正在帮你撤销打卡。"
        return [{"type": "checkin"}], "正在帮你打卡。"

    # 身份切换（演示用）：要求同时出现「身份词」和「切换词」，免得乱切
    if re.search(r"切换|切到|切成|换成|变成|切回", text):
        if re.search(r"管理员|老师", text):
            return [{"type": "switch_role", "role": "admin"}], "已切到管理员。"
        if re.search(r"学生", text):
            return [{"type": "switch_role", "role": "student"}], "已切回学生。"

    # 改显示名称
    named = re.search(r"(?:叫我|喊我|名字改成|改名为|改成)\s*([一-龥A-Za-z0-9]{1,12})", text)
    if named and not re.search(r"待办|任务|公告|请假", text):
        new_name = named.group(1).strip()
        return [{"type": "rename_user", "name": new_name}], f"以后就叫你「{new_name}」。"

    # 界面设置开关（开/关靠否定词判断）
    if re.search(r"动效|动画", text):
        on = not re.search(r"关|取消|不要|别|停止", text)
        return (
            [{"type": "toggle_setting", "name": "界面动效", "value": on}],
            f"界面动效已{'打开' if on else '关闭'}。",
        )
    if re.search(r"红点|未读", text):
        on = not re.search(r"关|取消|不要|别|隐藏", text)
        return (
            [{"type": "toggle_setting", "name": "未读红点", "value": on}],
            f"未读红点已{'打开' if on else '关闭'}。",
        )

    # 想跳页面
    for path, name in PAGES.items():
        if name in text and re.search(r"打开|去|跳|换|看", text):
            return [{"type": "navigate", "path": path}], f"带你到「{name}」。"

    chat = local_chat(text)
    if chat:
        # 回复口径：send 只说「正在帮你发」—— 真正发没发出去由浏览器说了算
        # （群可能已经被切走、正文可能被清空），不能替它宣布成功。
        target = f"「{chat['groupName']}」" if chat.get("groupName") else "当前群"
        if chat["type"] == "chat_open":
            return [chat], f"带你到{target}。"
        if chat["type"] == "chat_draft":
            return [chat], f"草稿已写进{target}的输入框，看一眼再按发送。"
        return [chat], f"正在帮你发到{target}。"

    if re.search(r"请假|病假|事假|年假|休假|休息", text):
        # 撤销自己的申请：要在「填表」之前判
        if re.search(r"撤销|取消|不请了|反悔", text):
            kind = next((t for t in LEAVE_TYPES if t in text), "")
            return [{"type": "leave_cancel", "kind": kind}], "正在帮你撤销那条请假。"
        # 审批：要有「人」和「通过/驳回」
        if re.search(r"通过|批准|同意|驳回|不批|拒绝", text):
            status = "已通过" if re.search(r"通过|批准|同意", text) else "已驳回"
            person = re.search(r"([一-龥]{2,3})的(?:请假|申请)", text)
            if person:
                return (
                    [{"type": "leave_review", "name": person.group(1), "status": status}],
                    f"准备{'通过' if status == '已通过' else '驳回'}「{person.group(1)}」的申请。",
                )
        action, reply = local_leave(text, today)
        return ([action] if action else []), reply

    if re.search(r"公告|通知", text):
        # 「看看 XX 那条公告」→ 搜出来并打开详情
        kw = re.search(r"[「『\"']([^」』\"']{2,20})[」』\"']", text)
        if kw:
            return [{"type": "notice_open", "keyword": kw.group(1)}], f"搜一下「{kw.group(1)}」。"

    # 待办：注意不能只认「待办/任务」这两个词 —— 用户经常说
    # 「把整理期末学生工作总结标成完成」，整句里根本没出现「待办」。
    if re.search(
        r"待办|任务|标成完成|标记为?完成|设为完成|做完|搞定了|重新打开|删掉|删除", text
    ):
        if re.search(r"完成|做完|搞定|打勾|标成", text):
            title = extract_title(text)
            return ([{"type": "todo_action", "action": "complete", "title": title}] if title else []), "把它标成完成。"
        if re.search(r"删掉|删除|不要了|去掉", text):
            title = extract_title(text)
            return ([{"type": "todo_action", "action": "delete", "title": title}] if title else []), "准备删掉它。"
        action, reply = local_todo(text, today)
        return ([action] if action else []), reply

    return [], f"我现在只连了本地规则，认不出这句。当前在「{PAGES.get(page, '工作台')}」页。"


# 从一句话里抽待办标题：优先带引号的，否则把命令词剔掉剩下的就是标题
TITLE_NOISE = re.compile(
    r"帮我把|帮我|把|请|麻烦|一下|这条|那条|这个|那个|待办的|待办事项|待办|任务|"
    r"标成完成|标记为?完成|设为?完成|标成已完成|已完成|完成|做完了|做完|搞定|打勾|"
    r"删掉|删除|不要了|去掉|重新打开|恢复|改一下|修改|"
    r"的|了|吧|噘|。|，|！|？|、"
)


def extract_title(text):
    quoted = re.search(r"[「『\"']([^」』\"']{2,40})[」』\"']", text)
    if quoted:
        return quoted.group(1).strip()[:40]
    return TITLE_NOISE.sub("", text).strip()[:40]


# 用户在说「打开/进入/切到 某个页面」。
# ⚠️ 必须把「看看某条公告」这类挑开：它也含页面名（公告）+ 一个动词，
#    但那是要搜具体一条，不是要跳页。所以带「的 / 那条 / 这个 / 搜 / 找」的不算。
PAGE_REQUEST_RE = re.compile(r"打开|进入|切到|跳转到")
PAGE_DETAIL_RE = re.compile(r"的|那条|这条|那个|这个|搜|找")


def page_request(text):
    if not PAGE_REQUEST_RE.search(text) or PAGE_DETAIL_RE.search(text):
        return None, None
    for path, name in PAGES.items():
        if name in text:
            return path, name
    return None, None


def enforce_navigation(reply, actions, user_text):
    """
    确定性兜底：用户在说「打开 X 页面」时，只允许跳转。

    为什么需要它：工具变到 15 个之后，小模型反复把「打开待办事项」理解成「念一遍待办列表」
    （它调了 list_todos，还会给你讲得头头是道）。提示词里写了规则也没用。
    → 这种完全能写死的意图就直接写死，跟 local_parse 一个思路。
    """
    if actions:
        return reply, actions
    path, name = page_request(user_text)
    if not path:
        return reply, actions
    return f"带你到「{name}」。", [{"type": "navigate", "path": path}]


# 只收「一看就是在下命令」的说法。
# ⚠️ 口径宁窄勿宽：像「我有哪些待办」这种查数据的句子绝不能进来，
#    否则会把模型查到的真答案换成本地兜底的呛人话。
#    下面的词都是「动词 + 明确对象」，查数据的问句里不会出现。
COMMAND_ONLY_RE = re.compile(
    r"切换|切到|切成|换成|变成|切回|动效|动画|红点|叫我|喊我|名字改成|改名为|"
    r"撤销|删掉|删除|标成完成|标记为?完成|重新打开|通过|驳回|不批|拒绝"
)


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    with connect_database() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                author TEXT NOT NULL,
                publish_time TEXT NOT NULL,
                top INTEGER NOT NULL DEFAULT 0,
                content TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS leaves (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                rejection_reason TEXT NOT NULL DEFAULT '',
                apply_time TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                assignee TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workspace_meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                initialized INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        db.execute("INSERT OR IGNORE INTO workspace_meta (id, initialized) VALUES (1, 0)")
        if db.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0:
            db.executemany(
                """INSERT INTO notices
                   (id, title, type, author, publish_time, top, content)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        item["id"],
                        item["title"],
                        item["type"],
                        item["author"],
                        item["publishTime"],
                        int(item.get("top", False)),
                        item.get("content", ""),
                    )
                    for item in mock_data.NOTICES
                ],
            )
        if db.execute("SELECT COUNT(*) FROM leaves").fetchone()[0] == 0:
            db.executemany(
                """INSERT INTO leaves
                   (id, name, type, start_date, end_date, days, reason, status,
                    rejection_reason, apply_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        item["id"],
                        item["name"],
                        item["type"],
                        item["startDate"],
                        item["endDate"],
                        item["days"],
                        item["reason"],
                        item["status"],
                        item.get("rejectionReason", ""),
                        item["applyTime"],
                    )
                    for item in mock_data.LEAVE_RECORDS
                ],
            )
        if db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0:
            db.executemany(
                """INSERT INTO todos
                   (id, title, description, category, priority, assignee, due_date, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        item["id"],
                        item["title"],
                        item.get("description", ""),
                        item["category"],
                        item["priority"],
                        item["assignee"],
                        item["dueDate"],
                        item["status"],
                    )
                    for item in mock_data.TODOS
                ],
            )


def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_workspace(data):
    if not isinstance(data, dict) or any(
        not isinstance(data.get(key), list) for key in ("todos", "notices", "leaveRecords")
    ):
        return False
    if any(len(data[key]) > 10000 for key in ("todos", "notices", "leaveRecords")):
        return False

    def valid_id(item):
        return isinstance(item.get("id"), int) and not isinstance(item.get("id"), bool) and item["id"] > 0

    notices = data["notices"]
    if any(
        not isinstance(item, dict)
        or not valid_id(item)
        or not isinstance(item.get("title"), str)
        or not 1 <= len(item["title"].strip()) <= 100
        or item.get("type") not in ("通知", "活动", "制度")
        or not isinstance(item.get("author"), str)
        or not item["author"].strip()
        or not isinstance(item.get("publishTime"), str)
        or not isinstance(item.get("top", False), bool)
        or not isinstance(item.get("content", ""), str)
        or len(item.get("content", "")) > 10000
        for item in notices
    ):
        return False

    leaves = data["leaveRecords"]
    if any(
        not isinstance(item, dict)
        or not valid_id(item)
        or not isinstance(item.get("name"), str)
        or not item["name"].strip()
        or item.get("type") not in LEAVE_TYPES
        or not valid_date(item.get("startDate"))
        or not valid_date(item.get("endDate"))
        or item["endDate"] < item["startDate"]
        or not isinstance(item.get("days"), int)
        or isinstance(item.get("days"), bool)
        or item["days"] < 1
        or not isinstance(item.get("reason"), str)
        or not 5 <= len(item["reason"]) <= 200
        or item.get("status") not in ("待审批", "已通过", "已驳回")
        or not isinstance(item.get("rejectionReason", ""), str)
        or not isinstance(item.get("applyTime"), str)
        for item in leaves
    ):
        return False

    todos = data["todos"]
    if any(
        not isinstance(item, dict)
        or not valid_id(item)
        or not isinstance(item.get("title"), str)
        or not 2 <= len(item["title"].strip()) <= 40
        or not isinstance(item.get("description", ""), str)
        or len(item.get("description", "")) > 200
        or item.get("category") not in TODO_CATEGORIES
        or item.get("priority") not in TODO_PRIORITIES
        or not isinstance(item.get("assignee"), str)
        or not item["assignee"].strip()
        or not valid_date(item.get("dueDate"))
        or item.get("status") not in TODO_STATUSES
        for item in todos
    ):
        return False

    return all(
        len({item["id"] for item in items}) == len(items)
        for items in (notices, leaves, todos)
    )


def serialize_notice(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "type": row["type"],
        "author": row["author"],
        "publishTime": row["publish_time"],
        "top": bool(row["top"]),
        "content": row["content"],
    }


def serialize_leave(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "startDate": row["start_date"],
        "endDate": row["end_date"],
        "days": row["days"],
        "reason": row["reason"],
        "status": row["status"],
        "rejectionReason": row["rejection_reason"],
        "applyTime": row["apply_time"],
    }


def serialize_todo(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "category": row["category"],
        "priority": row["priority"],
        "assignee": row["assignee"],
        "dueDate": row["due_date"],
        "status": row["status"],
    }


@app.get("/api/workspace")
def get_workspace():
    with connect_database() as db:
        initialized = db.execute(
            "SELECT initialized FROM workspace_meta WHERE id = 1"
        ).fetchone()["initialized"]
        data = {
            "notices": [
                serialize_notice(row)
                for row in db.execute("SELECT * FROM notices ORDER BY top DESC, id DESC")
            ],
            "leaveRecords": [
                serialize_leave(row)
                for row in db.execute("SELECT * FROM leaves ORDER BY id DESC")
            ],
            "todos": [
                serialize_todo(row)
                for row in db.execute("SELECT * FROM todos ORDER BY id DESC")
            ],
        }
    return jsonify({"ok": True, "data": data, "initialized": bool(initialized)})


@app.put("/api/workspace")
def save_workspace():
    body = request.get_json(silent=True)
    data = body.get("data") if isinstance(body, dict) else None
    if not valid_workspace(data):
        return jsonify({"ok": False, "error": "工作区数据无效"}), 400

    with connect_database() as db:
        db.execute("DELETE FROM notices")
        db.execute("DELETE FROM leaves")
        db.execute("DELETE FROM todos")
        db.executemany(
            """INSERT INTO notices
               (id, title, type, author, publish_time, top, content)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    item["id"], item["title"], item["type"], item["author"],
                    item["publishTime"], int(item.get("top", False)), item.get("content", ""),
                )
                for item in data["notices"]
            ],
        )
        db.executemany(
            """INSERT INTO leaves
               (id, name, type, start_date, end_date, days, reason, status,
                rejection_reason, apply_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    item["id"], item["name"], item["type"], item["startDate"],
                    item["endDate"], item["days"], item["reason"], item["status"],
                    item.get("rejectionReason", ""), item["applyTime"],
                )
                for item in data["leaveRecords"]
            ],
        )
        db.executemany(
            """INSERT INTO todos
               (id, title, description, category, priority, assignee, due_date, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    item["id"], item["title"], item.get("description", ""), item["category"],
                    item["priority"], item["assignee"], item["dueDate"], item["status"],
                )
                for item in data["todos"]
            ],
        )
        db.execute("UPDATE workspace_meta SET initialized = 1 WHERE id = 1")
    return jsonify({"ok": True})


def enforce_commands(reply, actions, user_text, page, snapshot=None):
    """
    模型什么动作都没产出、但用户这句是【明确命令】时，用本地规则把动作补上。

    实测：同一句「切到管理员」，新开对话 3 次全对；
    一旦前面聊过几句（带历史），就变成只回一句「切到管理员身份。」不动手 ——
    小模型的老毛病。提示词救不了，所以这里用确定性的规则接着。
    """
    if actions or not COMMAND_ONLY_RE.search(user_text):
        return reply, actions
    local_actions, local_reply = local_parse(user_text, page, snapshot)
    if not local_actions:
        return reply, actions
    return local_reply, local_actions


# ==================================================================
# 四、HTTP 接口
# ==================================================================
@app.post("/api/ai/chat")
def chat():
    body = request.get_json(silent=True) or {}
    history = body.get("messages") or []
    page = body.get("page") or "/dashboard"
    user = (body.get("user") or "").strip()
    # 前端每次请求都会带上页面上真实的业务数据（见 src/composables/appStore.js）。
    # 只读工具优先用它，这样 AI 读到的和用户眼前看到的永远是同一份。
    snapshot = body.get("data") if isinstance(body.get("data"), dict) else {}

    last_user_text = ""
    for message in reversed(history):
        if message.get("role") == "user":
            last_user_text = message.get("content") or ""
            break

    # 通道是一个个试的：本机模型 → 本地死规则
    failures = []
    for provider in build_providers():
        try:
            reply, actions = run_agent(history, page, user, provider, snapshot)
            # 日期一律用我们自己的解析结果校对一遍，见 reconcile_dates 的说明
            actions = [reconcile_dates(action, last_user_text) for action in actions]
            # 群聊动作体检：正文必须是用户原话（防编造）+ 措辞决定写还是发
            actions, chat_reply = enforce_chat(actions, last_user_text)
            if chat_reply:
                reply = chat_reply
            # 「打开某页面」这类能写死的意图，别让小模型去猜
            reply, actions = enforce_navigation(reply, actions, last_user_text)
            # 模型没动手但用户确实在下命令 —— 本地规则补上（见函数注释里的实测）
            reply, actions = enforce_commands(reply, actions, last_user_text, page, snapshot)
            return jsonify(
                {"ok": True, "source": provider["name"], "reply": reply, "actions": actions}
            )
        except Exception as error:  # 超时、断网、502、key 失效、本机没开……统统往下走
            failures.append(f"{provider['label']}：{error}")
            print(f"[降级] {provider['label']} 用不了 → {error}")

    actions, reply = local_parse(last_user_text, page, snapshot)
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

    province = text_field(parts.get("province"))
    city = text_field(parts.get("city"))
    district = text_field(parts.get("district"))

    # 省 + 市 + 区/县 = 「省市县」（页面要显示的就是这三级）
    # ⚠️ 两个坑，都不能写死三段拼接：
    #   1. 【直辖市】高德会把 province 和 city 都填成同一个值（北京市/北京市）
    #      → 直接相加拼出「北京市北京市朝阳区」。必须去重。
    #   2. 【省直辖县级行政区】（如海南省五指山市）city 会是空；
    #      个别情况下 province 也是空 —— 所以按顺序判空追加。
    region_parts = [province]
    if city and city != province:
        region_parts.append(city)
    if district:
        region_parts.append(district)
    region = "".join(region_parts)

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
            city or province,
            district,
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
        "region": region,
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


# ==================================================================
# 六、语音转文字（本机 Whisper）
#
# 和上面那个「AI 代理」是两件事，别混：
#   /api/ai/chat  → 文字进去、文字出来（听懂人话 = 本机 qwen2.5）
#   /api/asr      → 音频进去、文字出来（听清人话 = 本机 Whisper）
#
# 为什么不用浏览器自带的语音识别：
#   浏览器那个要把音频发到 Google / 微软的服务器 ——
#   「数据不出这台机器」这句话在语音这一环就破了。
#   搬到这里之后，整条链路（录音→识别→理解）全在本机。
#
# 实现细节和取舍说明见 asr.py 的文件头。
# ==================================================================
try:  # 没装 faster-whisper 也要能启动服务，只是 /api/asr 会报错
    import asr as asr_service
except ImportError:  # 万一用 `python -m server.app` 启动
    try:
        from server import asr as asr_service
    except ImportError:
        asr_service = None

# 一次上传的音频大小上限。浏览器录几十秒也就几百 KB，给到 25MB 很宽松了。
# ⚠️ 加这个是防止有人往这里灌大文件，把内存吃满。
ASR_MAX_BYTES = 25 * 1024 * 1024


@app.post("/api/asr")
def speech_to_text():
    if asr_service is None:
        return jsonify({"ok": False, "error": "服务端没装 faster-whisper"}), 503

    upload = request.files.get("audio")
    if upload is None:
        return jsonify({"ok": False, "error": "没有收到音频（字段名要叫 audio）"}), 400

    data = upload.read()
    if len(data) > ASR_MAX_BYTES:
        return jsonify({"ok": False, "error": "音频太大了"}), 413

    try:
        result = asr_service.transcribe(data)
    except Exception as error:  # 解码失败、模型文件缺失……都别把服务打崩
        print(f"[ASR] 转写失败：{error}")
        return jsonify({"ok": False, "error": str(error)[:300]}), 500

    print(f"[ASR] 音频 {result.get('audio_seconds')}s → 用了 {result.get('seconds')}s：{result.get('text')}")
    return jsonify(result)


@app.get("/api/asr/status")
def asr_status():
    """前端进来先问一句：用的哪个模型、跑在哪、加载了没。"""
    if asr_service is None:
        return jsonify({"ok": False, "error": "服务端没装 faster-whisper"})
    return jsonify({"ok": True, **asr_service.model_info()})


def start_asr_warmup():
    """
    后台把 Whisper 预热好（加载模型 + 空跑一次）。

    为什么不直接在主线程里调：加载模型要好几秒，会拖慢服务启动。
    为什么又要预热：实测「进程里的第一次推理」比后面每一次都慢好几倍，
    而这个代价会正好落在答辩时说的第一句话上。
    """
    if asr_service is None:
        return
    threading.Thread(target=asr_service.warm_up, name="asr-warmup", daemon=True).start()


# 初始化 SQLite 数据库，并为全新数据库写入演示种子。
initialize_database()


# 调试模式开关。
# 抽成常量是因为下面要用它判断「该不该预热」——
# 直接读 app.debug 会踩坑：在 app.run(debug=True) 之前那一刻它还是 False。
DEBUG = True

if __name__ == "__main__":
    labels = [provider["label"] for provider in build_providers()]
    print("AI 代理已启动： http://127.0.0.1:5000")
    print("模型通道（按优先级）：", " → ".join(labels) if labels else "无（只能走本地规则）")
    print("逆地理编码（坐标→地名）：", "已配 AMAP_KEY" if AMAP_KEY else "未配 AMAP_KEY（打卡只显示坐标）")
    print(
        "语音转文字（音频→文字）：",
        f"本机 Whisper {asr_service.ASR_MODEL}（{asr_service.ASR_DEVICE}/{asr_service.ASR_COMPUTE_TYPE}，首次调用时加载）"
        if asr_service
        else "未装 faster-whisper",
    )
    # 预热只在「真正处理请求」的那个进程里做。
    # debug=True 时 Werkzeug 会再起一个子进程来干活（子进程里 WERKZEUG_RUN_MAIN=true），
    # 父进程只是看着文件变化。两个都预热 = 白占一份内存（模型 1.5GB）也白烧一遍 CPU。
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not DEBUG:
        start_asr_warmup()
    app.run(host="127.0.0.1", port=5000, debug=DEBUG)
