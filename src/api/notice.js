/**
 * 公告附件：上传 / 地址 / 大小格式化
 * ================================
 *
 * 文件本身不经过前端存储：上传后后端落在 server/uploads/，接口只返回
 * { name, size, url }，公告里存的就是这三个字段。刷新、换设备都还能下载。
 *
 * ⚠️ 大小格式化放在这里，是因为发布弹窗和详情弹窗都要用 —— 写两份早晚会漂。
 */

const BASE_URL = '/api'

/** 上传一个文件，返回 { name, size, url }。失败时抛 Error（message 可以直接给用户看） */
export async function uploadAttachment(file) {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch(`${BASE_URL}/upload`, { method: 'POST', body })

  // 413（文件过大）时 Flask 返回的是 HTML，不是 JSON —— 不能直接 await response.json()
  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok || !payload?.ok) {
    throw new Error(payload?.error || `上传失败（${response.status}）`)
  }
  return payload.file
}

/** 1024 → 1 KB；1.2MB → 1.2 MB */
export function formatFileSize(bytes) {
  const size = Number(bytes)
  if (!Number.isFinite(size) || size <= 0) return '0 KB'
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
