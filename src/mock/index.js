/**
 * 全站唯一的假数据源
 * ==================
 *
 * 为什么要有这个文件：
 *   之前假数据散在 6 个地方（首页、公告页、请假页、待办页、通知、后端 mock_data.py），
 *   各写各的。结果首页写着「公告数量 3」，点进公告页一看有 12 条 ——
 *   老师第一眼就会发现。数字对不上，比缺功能更丢人。
 *
 * 所以：**假数据只在这里写一份**，谁要谁 import。
 *   数字想写错都不可能了，因为它就是从同一份数据数出来的。
 *
 * ⚠️ 接后端时怎么处理：
 *   这些文件全都不需要了，改成从接口拉。页面里 import 的地方换成请求即可。
 *   后端那个 `server/mock_data.py` 也一起删掉（它现在是手抄这里的一份，
 *   留着就是等着两边不一致）。
 *
 * ⚠️ 现在它只是「**初始种子**」：真正跑起来的数据在 `src/composables/appStore.js`，
 *    那里把这份种子装进 ref、加上 localStorage 持久化，页面统一从那边拿。
 *    所以在页面上新建/删除的东西刷新也不会丢，而直接改本文件只影响「第一次打开」。
 *
 *    以前还有两处「漏网」：`zhangjing/views/todo/index.vue` 和
 *    `luoxinyu/views/leave/index.vue` 里各自内联了一份，现已一并收归 appStore。
 */

/** 小组成员（写死，因为它不是业务数据） */
export const MEMBERS = ['刘皖', '罗欣雨', '张晶']

/** 通讯录演示数据；联系方式为虚构示例，不对应真实号码或邮箱 */
export const DIRECTORY_CONTACTS = [
  {
    id: 1,
    name: '刘皖',
    department: '技术组',
    role: '前端核心开发',
    phone: '138****1024',
    email: 'liu.wan@example.com',
  },
  {
    id: 2,
    name: '罗欣雨',
    department: '事务组',
    role: '请假模块负责人',
    phone: '139****2058',
    email: 'luo.xinyu@example.com',
  },
  {
    id: 3,
    name: '张晶',
    department: '项目组',
    role: '项目统筹',
    phone: '137****3167',
    email: 'zhang.jing@example.com',
  },
]

/** ---------- 公告通知 ---------- */
export const NOTICES = [
  {
    id: 12,
    title: '关于期末学生工作总结的通知',
    type: '通知',
    author: '张晶',
    publishTime: '2026-10-02 09:15',
    top: true,
    content:
      '请各部门于 10 月 15 日前提交本学期工作总结，内容包括工作成果、存在问题及下学期计划。总结需以 Word 文档形式发送至学生会邮箱。',
  },
  {
    id: 11,
    title: '校园文化活动报名开始啦',
    type: '活动',
    author: '罗欣雨',
    publishTime: '2026-10-01 14:30',
    top: true,
    content:
      '本届校园文化活动共设 8 个项目，报名截止时间为 10 月 10 日 18:00，欢迎各班级积极组织参与。',
  },
  {
    id: 10,
    title: '学生会例会时间调整说明',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-28 16:40',
    top: false,
    content: '因课程安排冲突，本周例会调整至周三 19:00，地点仍为综合楼 302 教室。',
  },
  {
    id: 9,
    title: '学生考勤管理制度（修订版）',
    type: '制度',
    author: '张晶',
    publishTime: '2026-09-25 11:20',
    top: false,
    content: '本次修订主要明确请假审批流程与销假要求，自发布之日起执行。',
  },
  {
    id: 8,
    title: '国庆假期值班安排',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-23 08:50',
    top: false,
    content: '假期期间每日安排 2 名同学值班，具体名单见附件。',
  },
  {
    id: 7,
    title: '宿舍卫生检查结果公示',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-20 10:00',
    top: false,
    content: '本次检查共评出优秀宿舍 12 间，具体名单已张贴于宿舍楼下公告栏。',
  },
  {
    id: 6,
    title: '志愿服务招募通知',
    type: '活动',
    author: '张晶',
    publishTime: '2026-09-18 15:10',
    top: false,
    content: '社区支教志愿服务招募 20 人，服务时间为每周六上午。',
  },
  {
    id: 5,
    title: '关于使用统一开发规范的说明',
    type: '制度',
    author: '刘皖',
    publishTime: '2026-09-15 09:00',
    top: false,
    content: '为保证代码风格一致，全组统一使用 Prettier 格式化，颜色统一走 CSS 变量。',
  },
  {
    id: 4,
    title: '新生入学教育安排',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-12 13:45',
    top: false,
    content: '新生入学教育分三批进行，具体时间见各班级群通知。',
  },
  {
    id: 3,
    title: '班级篮球赛报名通知',
    type: '活动',
    author: '张晶',
    publishTime: '2026-09-10 17:30',
    top: false,
    content: '篮球赛即日起接受报名，每队 5 至 8 人，报名请联系体育委员。',
  },
  {
    id: 2,
    title: '关于奖学金评定工作的通知',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-08 10:20',
    top: false,
    content: '奖学金评定材料提交截止时间为 9 月 20 日，请务必按时提交。',
  },
  {
    id: 1,
    title: '新学期学生干部名单公布',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-01 09:00',
    top: false,
    content: '经个人申报与面试考评，新学期学生干部名单现予公布。',
  },
]

/** ---------- 待办事项（与 zhangjing/views/todo/index.vue 对齐） ---------- */
export const TODOS = [
  {
    id: 1,
    title: '整理期末学生工作总结',
    category: '文档',
    priority: '高',
    assignee: '刘皖',
    dueDate: '2026-10-15',
    status: '待办',
  },
  {
    id: 2,
    title: '核对校园文化活动报名名单',
    category: '活动',
    priority: '高',
    assignee: '张晶',
    dueDate: '2026-10-10',
    status: '进行中',
  },
  {
    id: 3,
    title: '更新国庆假期值班安排',
    category: '工作',
    priority: '中',
    assignee: '罗欣雨',
    dueDate: '2026-10-08',
    status: '待办',
  },
  {
    id: 4,
    title: '汇总志愿服务时长',
    category: '文档',
    priority: '低',
    assignee: '张晶',
    dueDate: '2026-10-05',
    status: '已完成',
  },
  {
    id: 5,
    title: '准备学生会周例会材料',
    category: '工作',
    priority: '中',
    assignee: '刘皖',
    dueDate: '2026-10-09',
    status: '进行中',
  },
  {
    id: 6,
    title: '完成新学期活动复盘',
    category: '活动',
    priority: '低',
    assignee: '罗欣雨',
    dueDate: '2026-10-20',
    status: '待办',
  },
]

/** ---------- 请假记录（与 luoxinyu/views/leave/index.vue 对齐） ---------- */
export const LEAVE_RECORDS = [
  /*
   * 这条是【别人】的待审批申请，故意的：
   * 审批有个「不能批自己的申请」的校验，而当前登录用户就是刘皖 ——
   * 如果待审批的全是刘皖自己的，管理员在演示时就没东西可批了。
   */
  {
    id: 4,
    name: '罗欣雨',
    type: '事假',
    startDate: '2026-10-16',
    endDate: '2026-10-16',
    days: 1,
    reason: '参加校外竞赛需要提前到场准备',
    status: '待审批',
    applyTime: '2026-10-12 09:20',
  },
  {
    id: 3,
    name: '刘皖',
    type: '事假',
    startDate: '2026-09-28',
    endDate: '2026-09-28',
    days: 1,
    reason: '家中有事，需要回家处理',
    status: '待审批',
    applyTime: '2026-09-26 20:12',
  },
  {
    id: 2,
    name: '张晶',
    type: '病假',
    startDate: '2026-09-15',
    endDate: '2026-09-16',
    days: 2,
    reason: '感冒发烧，校医院建议休息两天',
    status: '已通过',
    applyTime: '2026-09-14 08:30',
  },
  {
    id: 1,
    name: '罗欣雨',
    type: '年假',
    startDate: '2026-09-05',
    endDate: '2026-09-05',
    days: 1,
    reason: '参加校外竞赛，需要请假一天',
    status: '已驳回',
    rejectionReason: '请补充指导老师同意证明后重新提交。',
    applyTime: '2026-09-03 19:05',
  },
]

/**
 * 首页那四个数字、最新公告都不在这里了 —— 它们得从**运行时的**同一份数据里数出来，
 * 见 `src/composables/appStore.js` 的 dashboardSummary() / latestNotices()。
 * 本文件只负责当「初始种子」，页面不再直接 import 这里的数组。
 */
