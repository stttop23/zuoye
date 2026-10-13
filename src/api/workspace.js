const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  let data
  try {
    data = await response.json()
  } catch {
    throw new Error(`服务器返回了无法识别的数据（${response.status}）`)
  }

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `请求失败（${response.status}）`)
  }
  return data
}

export async function getWorkspaceSnapshot() {
  const result = await request('/workspace')
  return { data: result.data, initialized: result.initialized }
}

export function saveWorkspaceSnapshot(data) {
  return request('/workspace', {
    method: 'PUT',
    body: JSON.stringify({ data }),
  })
}
