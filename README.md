# 学生工作管理系统

> 大学生小组作业 · Vue 3 + Vite + Element Plus 前端项目

## 一、项目简介

面向学生会的日常事务管理前端系统，包含工作台总览、公告通知浏览、请假申请、待办事项四大模块。
本项目为**纯前端实现**，数据当前使用本地假数据（mock），接口层预留完毕，后端就绪后可直接替换。

### 🤖 AI 助手（2026-10-12 新增）

右下角悬浮唤出聊天窗，用一句中文就能把表单填好：

| 你说 | 它干什么 |
| --- | --- |
| `下周三到周五请病假，感冒发烧` | 自动填好请假表单（只填，不提交） |
| `今天到后天事假，回家办事` | 事假 + 日期 + 原因，一次填好 |
| `新建待办：整理周例会材料，周五截止` | 打开新建弹窗并预填 |
| `打开待办事项` | 跳转页面 |

左下角还有个 **🎤 语音** 按钮——懒得打字就直接说话（仅 Chrome / Edge，需要联网）。
说完文字会落到输入框，改完自己点发送，不会自动替你发。

技术上是「工具调用」式智能体：模型只负责听懂和决策，真正动手的是后端白名单校验过的代码。
模型跑在**你自己电脑上**（Ollama + `qwen2.5:7b`），不用联网、不用 API key、不花钱。

模型或代理挂掉时会自动降级：**本机模型 → 后端正则规则 → 前端兜底**，演示现场不会哑火。

> 📘 **接入文档**：[docs/AI智能体接入指南.md](docs/AI智能体接入指南.md) —— 架构、契约、怎么加新工具、踩过的坑。
> 📘 **架构文档**：[docs/项目框架.md](docs/项目框架.md) —— 目录职责、数据流、分工边界。

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
├── /dashboard   工作台首页（数据卡片 + 快捷入口 + 最新公告）
├── /notice      公告通知（搜索 + 筛选 + 分页 + 详情弹窗）
├── /leave       请假申请（罗欣雨）
├── /todo        待办事项（张晶）
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
- 页面专属样式写在对应 `.vue` 文件的 `<style scoped>` 中，不要污染全局样式。
- 提交前保存文件会自动格式化（VS Code 已配置 Prettier），也可以手动执行 `npm run format`。

### 3. 提交信息规范

| 前缀 | 含义 |
| --- | --- |
| `feat:` | 新增功能 |
| `fix:` | 修复问题 |
| `style:` | 样式调整 |
| `docs:` | 文档修改 |
| `refactor:` | 重构 |

示例：`feat: 完成公告通知页面分页功能`

### 4. 每日工作流

```bash
git pull origin main              # ① 开工前先同步别人的代码
# ...写代码...
git add .
git commit -m "feat: 完成待办列表"
git push                          # ② 收工前推送到远程
```

### 5. 注意事项

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
│       │   └── components/       StatCards / QuickActions / RecentNotices
│       ├── notice/             公告通知
│       │   ├── index.vue         页面主体：页头 + 组装子组件
│       │   └── components/       NoticeFilter / NoticeTable / NoticeDetailDialog
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
│   │   └── ai.js               AI 助手接口层（只认前后端约定的 JSON 契约）
│   ├── assets/styles/
│   │   ├── variables.css       全局颜色 / 间距变量（全组统一，禁止写死色值）
│   │   └── global.css          全局基础样式
│   ├── components/
│   │   └── AiAssistant.vue     右下角悬浮 AI 助手（全站常驻）
│   ├── composables/
│   │   ├── aiAgent.js          AI 对话状态 + 填表动作总线 + 本地兜底
│   │   ├── useSpeechInput.js   语音输入（浏览器 Web Speech API 封装）
│   │   └── userProfile.js      当前用户显示名称（localStorage 持久化）
│   ├── layout/
│   │   └── BasicLayout.vue     整体布局：侧边栏 + 顶栏 + 面包屑 + 内容区
│   ├── router/
│   │   └── index.js            路由表（刘皖统一维护）
│   ├── App.vue
│   └── main.js                 入口：Element Plus、路由、全局样式
├── server/                     AI 代理服务（Flask，调本机模型）
│   ├── app.py                  工具定义 + 智能体循环 + 日期校正 + 本地规则兜底
│   ├── requirements.txt
│   ├── .env                    本机配置（已被 gitignore，不提交）
│   └── .env.example            配置模板
├── docs/
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

> 答辩前补充。

| 页面 | 截图 |
| --- | --- |
| 工作台首页 | 待补充 |
| 公告通知 | 待补充 |
| 请假申请 | 待补充 |
| 待办事项 | 待补充 |

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
- [x] AI 助手语音输入（浏览器 Web Speech API，仅 Chrome / Edge，需联网）
- [x] 本机模型接入（Ollama + qwen2.5:7b，离线可用、不需要 key）
- [x] AI 助手降级方案（本机模型 → 本地规则 → 前端兜底）
- [ ] AI 代理部署到线上服务器
- [ ] 后端接口对接
