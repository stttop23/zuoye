# 学生工作管理系统

> 大学生小组作业 · Vue 3 + Vite + Element Plus 前端项目

## 一、项目简介

面向学生会的日常事务管理前端系统，包含工作台总览、公告通知浏览、请假申请、待办事项四大模块。
本项目为**纯前端实现**，数据当前使用本地假数据（mock），接口层预留完毕，后端就绪后可直接替换。

### 🤖 AI 助手（2026-10-12 新增）

右下角悬浮唤出聊天窗，用一句中文就能把表单填好（悬浮球可以拖着换位置，松手吸附到边缘）：

| 你说 | 它干什么 |
| --- | --- |
| `下周三到周五请病假，感冒发烧` | 自动填好请假表单（只填，不提交） |
| `今天到后天事假，回家办事` | 事假 + 日期 + 原因，一次填好 |
| `新建待办：整理周例会材料，周五截止` | 打开新建弹窗并预填 |
| `打开待办事项` | 跳转页面 |
| `我有哪些待办` | 把待办念出来（含“已遍期”提醒） |
| `我的请假批了吗` | 报请假记录的状态 |
| `最近有什么公告` | 念最新的几条公告 |

左下角还有个 **🎤 语音** 按钮——懒得打字就直接说话（仅 Chrome / Edge，需要联网）。
说完文字会落到输入框，改完自己点发送，不会自动替你发。

技术上是「工具调用」式智能体：模型只负责听懂和决策，真正动手的是后端白名单校验过的代码。
六个工具：三个动手（跳页 / 填请假 / 建待办）+ 三个查数据（待办 / 公告 / 请假），
后面的只读工具让 AI 从「会填表」变成「知道事」。
模型跑在**你自己电脑上**（Ollama + `qwen2.5:7b`），不用联网、不用 API key、不花钱。

模型或代理挂掉时会自动降级：**本机模型 → 后端正则规则 → 前端兜底**，演示现场不会哑火。

> 📘 **接入文档**：[docs/AI智能体接入指南.md](docs/AI智能体接入指南.md) —— 架构、契约、怎么加新工具、踩过的坑。
> 📘 **架构文档**：[docs/项目框架.md](docs/项目框架.md) —— 目录职责、数据流、分工边界。

**响应式**：适配到手机。屏幕窄于 768px 时侧边栏自动变成抽屉，统计卡片改为一行两张，
页头改竖排，弹窗占满宽度。只用断点变量和媒体查询做的，没引任何 UI 框架。

**交互细节**：

- **AI 助手悬浮球可以拖着挪位置** —— 松手会吸附到最近的左右边缘（停在中间会挡内容），
  垂直高度按你拖到的地方保留，刷新也记得（存 localStorage）。抽屉从哪边弹出来跟着按钮走。
- **待办事项左滑露出操作** —— 往左划一下就是「完成 / 编辑 / 删除」，
  不用再去够右边那排小按钮；同时只会打开一行，点行内容或点完操作都会自己收回去。

## 二、小组成员及分工

| 成员 | 角色 | 负责内容 | 开发分支 | 负责文件 |
| --- | --- | --- | --- | --- |
| 刘皖 | 前端核心开发 / 技术规范 / 仓库管理 | 项目初始化、路由与整体布局、全局样式规范、工作台首页、公告通知页、GitHub 仓库维护与代码合并 | `main` | `router/`、`layout/`、`views/dashboard/`、`views/notice/` |
| 罗欣雨 | 请假模块开发 / 答辩主讲 | 请假申请页面、答辩 PPT 与演示讲解 | `feature/luo-xinyu` | `views/leave/` |
| 张晶 | 待办模块开发 / 项目统筹 | 待办事项页面、进度统筹与最终整合 | `feature/zhang-jing` | `views/todo/` |

## 三、技术栈

| 技术 | 版本 | 说明 |
| --- | --- | --- |
| Vue | 3.x | 组合式 API（`<script setup>`） |
| Vite | 8.x | 构建工具，秒级热更新 |
| Vue Router | 5.x | 前端路由，history 模式 |
| Element Plus | 2.x | UI 组件库（全量引入 + 中文语言包） |
| Prettier | 3.x | 代码格式化，全组统一风格 |

## 四、页面结构

```
/
├── /dashboard   工作台首页（打卡 + 数据卡片 + 快捷入口 + 最新公告）
├── /notice      公告通知（搜索 + 筛选 + 分页 + 详情弹窗）
├── /leave       请假申请（罗欣雨）
├── /todo        待办事项（张晶）
├── /assistant   AI 助手（刘皖）
└── /:pathMatch  404 页面
```

## 五、如何运行项目

前置条件：已安装 Node.js（建议 20 及以上）。

```bash
# 1. 克隆仓库
git clone https://github.com/stttop23/zuoye.git

# 2. 进入目录
cd zuoye

# 3. 安装依赖（第一次运行必须执行，约 1-3 分钟）
npm install

# 4. 启动开发服务器
npm run dev
```

浏览器打开终端中显示的地址（默认 <http://localhost:5173>）即可看到页面。

其他命令：

```bash
npm run build     # 打包生产版本，产物在 dist/
npm run preview   # 本地预览打包结果
npm run format    # 一键格式化 src 下所有代码
```

## 六、团队开发规范

### 1. 分支规范

- `main` 分支为**稳定分支**，禁止直接提交业务代码。
- 两个队友分支 `feature/luo-xinyu`、`feature/zhang-jing` **已由仓库管理员建好并推送**，队友直接切换过去即可，不需要自己创建：

```bash
git clone https://github.com/stttop23/zuoye.git
cd zuoye
git checkout feature/luo-xinyu      # 换成你自己的分支名
npm install
npm run dev
```

- 功能完成后在 GitHub 发起 Pull Request，由仓库管理员审核合并。
- 分支名统一使用拼音而非中文，避免 Windows 中文终端下出现乱码分支。

### 2. 代码规范

- **样式颜色禁止写死**，必须使用 `src/assets/styles/variables.css` 中的 CSS 变量：

```css
/* ✅ 正确 */
color: var(--st-text-primary);

/* ❌ 错误 */
color: #303133;
```

- 组件优先使用 Element Plus 现成组件，不要手写重复的表格 / 弹窗。
- **假数据统一写在 `src/mock/index.js`，不要在自己页面里再抄一份。**
  以前首页写「公告 3 条」、公告页实际 12 条，就是因为各处各写一份。
  数字一律从 `@/mock` 算出来，不要手写。
- 页面专属样式写在对应 `.vue` 文件的 `<style scoped>` 中，不要污染全局样式。
- 提交前保存文件会自动格式化（VS Code 已配置 Prettier），也可以手动执行 `npm run format`。
  想检查有没有漏掉的，跑 `npm run format:check`（覆盖 `src/` 和三个成员目录）。
  > ⚠️ 以前的 `format` 脚本只写了 `src/**`，**队友那三个文件夹根本不会被格式化**，已修。

### 3. 动效与设计规范

界面升级过一次，动效全部走变量，**不要在自己页面里各写一个 `0.3s`**。
节奏不统一的界面，看起来比完全不动还乱。

| 想做什么 | 用什么 |
| --- | --- |
| 颜色 / 圆角 / 阴影 / 间距 | `variables.css` 里的 `--st-*` 变量（新增了渐变、光晕、四层阴影、动效时长） |
| 区块淡入上移 | 加 class `st-fade-up` |
| 一排卡片挨个出现 | 再加 `st-delay-1` ~ `st-delay-6`（错峰，别一次全冒出来） |
| 图标 / 徽标「弹」出来 | `st-pop` |
| 数字从 0 滚上来 | `<CountUp :value="6" />`（`src/components/CountUp.vue`） |
| 列表项左滑露出操作 | `<SwipeRow>`（`src/components/SwipeRow.vue`，鼠标拖也行，桌面上能演示） |
| 悬停抬升 | `transform: translateY(-4px)` + `--st-shadow-hover` |
| 缓动曲线 | `--st-ease`（标准）/ `--st-ease-back`（带一点回弹） |

> ⚠️ **别漏了 `prefers-reduced-motion`。** 全局已兜底（动画时长归零），
> 但你自己写的 `animation-delay` 也要一起清零，否则开了「减少动态效果」的人
> 反而会看到一段空白。这个坑我们踩过，见 `global.css` 里的注释。
> 自己用 JS 写动画（比如数字滚动）时，也要判断一下：
> `window.matchMedia('(prefers-reduced-motion: reduce)').matches`。

### 4. 提交信息规范

| 前缀 | 含义 |
| --- | --- |
| `feat:` | 新增功能 |
| `fix:` | 修复问题 |
| `style:` | 样式调整 |
| `docs:` | 文档修改 |
| `refactor:` | 重构 |

示例：`feat: 完成公告通知页面分页功能`

### 5. 每日工作流

```bash
git pull origin main              # ① 开工前先同步别人的代码
# ...写代码...
git add .
git commit -m "feat: 完成待办列表"
git push                          # ② 收工前推送到远程
```

### 6. 注意事项

- **不要删除也不要提交 `node_modules`**（已在 `.gitignore` 中忽略）。
- 打开项目后，VS Code 会提示安装推荐插件（Volar、Prettier），请务必安装。
- 遇到报错先复制红色报错信息搜索，90% 是拼写错误或漏装依赖。

## 七、目录结构

```
zuoye/
├── liuwan/                     ★ 刘皖负责的页面
│   └── views/
│       ├── dashboard/          工作台首页
│       │   ├── index.vue         页面主体：欢迎条 + 组装子组件
│       │   └── components/       CheckIn / StatCards / QuickActions / RecentNotices
│       ├── notice/             公告通知
│       │   ├── index.vue         页面主体：页头 + 组装子组件
│       │   └── components/       NoticeFilter / NoticeTable / NoticeDetailDialog
│       ├── assistant/          AI 助手独立页面
│       │   └── index.vue         复用 src/components/AiChatPanel.vue
│       └── NotFoundView.vue    404 页面
├── luoxinyu/                   ★ 罗欣雨负责的页面
│   └── views/leave/
│       ├── index.vue             请假申请：组装子组件 + 假数据
│       └── components/           LeaveForm（表单+校验）/ LeaveRecords（记录表）
├── zhangjing/                  ★ 张晶负责的页面
│   └── views/todo/
│       ├── index.vue             待办事项：表格 + 分页 + 组装子组件
│       └── components/           TodoStats / TodoToolbar / TodoDialog
├── src/                        应用外壳（三个页面共用，不属于某个人）
│   ├── api/
│   │   ├── ai.js               AI 助手接口层（只认前后端约定的 JSON 契约）
│   │   └── geo.js              地理位置接口层（坐标→地名）
│   ├── assets/styles/
│   │   ├── variables.css       全局颜色 / 间距变量（全组统一，禁止写死色值）
│   │   └── global.css          全局基础样式
│   ├── components/
│   │   ├── AiAssistant.vue     右下角悬浮球（可拖动 + 吸附）+ 抽屉壳
│   │   ├── AiChatPanel.vue     AI 聊天本体（抽屉和独立页面共用）
│   │   ├── CountUp.vue         数字滚动（从 0 滚到目标值）
│   │   └── SwipeRow.vue        左滑露出操作（待办列表在用，通用组件）
│   ├── composables/
│   │   ├── aiAgent.js          AI 对话状态 + 填表动作总线 + 本地兜底
│   │   ├── useSpeechInput.js   语音输入（浏览器 Web Speech API 封装）
│   │   ├── notifications.js    顶栏通知中心（未读数 + 已读状态）
│   │   ├── permissions.js      权限能力表（前端控制，真正拦人靠后端）
│   │   └── userProfile.js      当前用户显示名称 + 角色（localStorage 持久化）
│   ├── layout/
│   │   └── BasicLayout.vue     整体布局：侧边栏 + 顶栏（含通知中心）+ 面包屑 + 内容区
│   ├── mock/
│   │   └── index.js            ★ 全站唯一假数据源（公告 / 待办 / 请假 / 成员 + 算出来的统计）
│   ├── router/
│   │   └── index.js            路由表（刘皖统一维护）
│   ├── App.vue
│   └── main.js                 入口：Element Plus、路由、全局样式
├── server/                     AI 代理服务（Flask，调本机模型）
│   ├── app.py                  工具定义 + 智能体循环 + 日期校正 + 本地规则兜底
│   ├── mock_data.py            ⚠️ 临时假数据（只读工具查的就是它，接数据库后删）
│   ├── requirements.txt
│   ├── .env                    本机配置（已被 gitignore，不提交）
│   └── .env.example            配置模板
├── docs/
│   ├── screenshots/            五张页面截图（README 第八节在用）
│   ├── 项目框架.md             架构与分工说明
│   ├── AI智能体接入指南.md     AI 助手：架构、契约、扩展、踩坑
│   └── AI填表方案.md           动手前的方案稿（存档）
├── .prettierrc.json            格式化规则
├── index.html
├── vite.config.js
└── package.json
```

> **拆分约定**：每个页面都是一个文件夹，`index.vue` 只做「组装」，
> 具体的表格、表单、弹窗放到同级的 `components/` 里。
> 改一个页面不会碰到别人的代码。
>
> 文件夹名用**拼音**（`liuwan` / `luoxinyu` / `zhangjing`）而不是中文，
> 和分支命名一个道理：中文路径在 Windows 终端里会显示成乱码。

## 八、项目截图

> 图片在 `docs/screenshots/`，1440 宽，点开可看大图。

**工作台** —— 欢迎条 + 每日打卡（带定位）+ 数据卡片 + 快捷入口 + 最新公告

![工作台](docs/screenshots/01-dashboard.png)

**公告通知** —— 搜索 + 类型筛选 + 分页 + 详情弹窗

![公告通知](docs/screenshots/02-notice.png)

**请假申请** —— 表单校验 + 日期联动 + 合计天数 + 申请记录

![请假申请](docs/screenshots/03-leave.png)

**待办事项** —— 统计 + 日程日历 + 筛选 + 表格

![待办事项](docs/screenshots/04-todo.png)

**AI 助手** —— 独立页面，和右下角悬浮窗共用同一份对话

![AI 助手](docs/screenshots/05-assistant.png)

**手机端** —— 侧边栏变成从左侧滑出的抽屉（点汉堡按钮开，点遮罩 / 按 Esc / 跳页面都会自动收起）

<img src="docs/screenshots/06-mobile.png" width="360" alt="手机端" />

## 九、开发进度

- [x] 项目初始化与依赖配置
- [x] 整体布局与路由框架
- [x] 全局样式变量与代码规范
- [x] 工作台首页（刘皖）
- [x] 公告通知页面（刘皖）
- [x] 按成员划分独立模块文件夹
- [x] 队友开发分支创建（`feature/luo-xinyu`、`feature/zhang-jing`）
- [x] 请假申请页面（罗欣雨）
- [x] 待办事项页面（张晶）
- [x] 自定义用户显示名称（张晶）
- [x] 按人重组目录 + 页面拆分子组件
- [x] AI 助手：询问 / 跳转 / 自然语言填表（刘皖）
- [x] AI 助手独立页面（侧边栏入口，与悬浮抽屉共享同一份对话）
- [x] AI 助手语音输入（浏览器 Web Speech API，仅 Chrome / Edge，需联网）
- [x] 本机模型接入（Ollama + qwen2.5:7b，离线可用、不需要 key）
- [x] AI 助手降级方案（本机模型 → 本地规则 → 前端兜底）
- [x] AI 助手只读工具（查待办 / 查公告 / 查请假）
- [x] 工作台每日打卡（带地理位置）
- [x] 打卡地点显示地名（高德逆地理编码，需在 `server/.env` 填 `AMAP_KEY`）
- [x] 顶栏通知中心（未读红点 + 已读状态）
- [x] 假数据统一到 `src/mock/`（首页四个数字改为从同一份数据算出来）
- [x] 五个页面的截图（`docs/screenshots/`）
- [x] 权限能力表（`src/composables/permissions.js`，公告页的「发布公告」按角色显示）
- [x] 界面动效升级（胶囊菜单、页面过渡、数字滚动、无障碍适配）
- [x] 移动端适配（窄屏侧边栏变抽屉，断点 768px）
- [x] AI 悬浮球可拖动 + 边缘吸附（位置记在 localStorage）
- [x] 待办事项左滑操作（抽出 `src/components/SwipeRow.vue`，别人也能复用）
- [ ] AI 代理部署到线上服务器
- [ ] 后端接口对接
- [ ] 把假数据换成数据库（`src/mock/` 和 `server/mock_data.py` 一起换）
- [ ] 队友页面里内联的假数据改读 `src/mock/`（待办页 / 请假页，得她们自己改）
