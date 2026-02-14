/**
 * 解析无时区时间戳（后端已返回北京时间）
 * 避免使用 new Date() 导致的 UTC 转换问题
 */
export function parseLocalTime(timestamp: string): Date {
  if (!timestamp) return new Date()
  
  // 如果带时区，直接解析
  if (timestamp.includes('Z') || 
      (timestamp.includes('+') && timestamp.indexOf('+') > 10) ||
      (timestamp.includes('-') && timestamp.lastIndexOf('-') > 10)) {
    return new Date(timestamp)
  }
  
  // 无时区（后端已返回北京时间），手动解析并直接创建 UTC 时间避免浏览器时区转换
  const cleanTs = timestamp.split('.')[0] // 去掉微秒
  
  if (cleanTs.includes('T')) {
    const [datePart, timePart] = cleanTs.split('T')
    const [year, month, day] = datePart.split('-').map(Number)
    const [hour, minute, second = 0] = timePart.split(':').map(Number)
    // 使用 Date.UTC 创建 UTC 时间，避免浏览器本地时区影响
    return new Date(Date.UTC(year, month - 1, day, hour, minute, second))
  } else if (cleanTs.includes(' ')) {
    const [datePart, timePart] = cleanTs.split(' ')
    const [year, month, day] = datePart.split('-').map(Number)
    const [hour, minute, second = 0] = timePart.split(':').map(Number)
    return new Date(Date.UTC(year, month - 1, day, hour, minute, second))
  }
  
  return new Date(timestamp)
}

/**
 * 格式化时间为本地时间字符串
 */
export function formatLocalTime(
  timestamp: string,
  options: Intl.DateTimeFormatOptions = { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit',
    timeZone: 'UTC'  // 使用 UTC 时区，因为 parseLocalTime 返回的是 UTC 时间
  }
): string {
  const date = parseLocalTime(timestamp)
  if (isNaN(date.getTime())) return '--:--'
  return date.toLocaleString('zh-CN', options)
}
