/**
 * 地理位置接口层
 * ==============
 * 只认这一份契约：
 *
 *   请求  GET /api/geo/reverse?lat=30.2741&lng=120.1551
 *
 *   响应  { ok: true, source: 'amap',
 *           region: '浙江省杭州市西湖区',  // 省+市+区/县 —— 打卡显示的就是它
 *           poi: '浙江大学玉泉校区',   // 附近最近的兴趣点，比路名好认
 *           poiDistance: '35',
 *           short: '杭州市西湖区玉古路', // 拼好的短地址（含街道门号，不含省）
 *           address: '浙江省杭州市西湖区玉古路866号' }
 *
 *        或 { ok: false, reason: '未配置 AMAP_KEY' }
 *
 * ⚠️ 拿不到地名【不是错误】，是最正常不过的情况：
 *    没配 key、没网、地图服务抽风……所以这里拿不到就返回 null，
 *    让页面退回去显示坐标。千万别 throw，否则打卡会被这件事拖死。
 *
 * 为什么不让浏览器直接调高德：
 *    浏览器里放 key，谁打开 F12 都能抄走。所以 key 放在服务端，
 *    前端只跟我们自己的 Flask 说话。
 */
const BASE_URL = import.meta.env.VITE_AI_BASE_URL || '/api'

export async function reverseGeocode({ lat, lng }) {
  if (lat == null || lng == null) return null

  try {
    const response = await fetch(`${BASE_URL}/geo/reverse?lat=${lat}&lng=${lng}`)
    if (!response.ok) return null
    const data = await response.json()
    return data.ok ? data : null
  } catch {
    return null
  }
}
