/**
 * 解析后端返回的时间（后端已返回北京时间）
 * 直接解析，无需 UTC 转换
 */
export function parseLocalTime(timestamp: string): Date {
  if (!timestamp) return new Date()
  
  // 直接解析，后端返回的是北京时间
  const date = new Date(timestamp)
  
  // 如果解析失败，尝试手动解析
  if (isNaN(date.getTime())) {
    const cleanTs = timestamp.split('.')[0] // 去掉微秒
    
    if (cleanTs.includes('T')) {
      const [datePart, timePart] = cleanTs.split('T')
      const [year, month, day] = datePart.split('-').map(Number)
      const [hour, minute, second = 0] = timePart.split(':').map(Number)
      return new Date(year, month - 1, day, hour, minute, second)
    }
  }
  
  return date
}

/**
 * 格式化时间为本地时间字符串
 */
export function formatLocalTime(
  timestamp: string,
  options: Intl.DateTimeFormatOptions = { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit'
  }
): string {
  const date = parseLocalTime(timestamp)
  if (isNaN(date.getTime())) return '--:--'
  return date.toLocaleString('zh-CN', options)
}

/**
 * 格式化日期（月/日）
 */
export function formatDate(
  timestamp: string,
  options: Intl.DateTimeFormatOptions = { 
    month: '2-digit', 
    day: '2-digit'
  }
): string {
  const date = parseLocalTime(timestamp)
  if (isNaN(date.getTime())) return '--/--'
  return date.toLocaleString('zh-CN', options)
}
