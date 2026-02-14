"""
系统日志 API
从数据库和 Docker 容器获取日志
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Query
from sqlalchemy import select, desc, func
from app.schemas import ApiResponse
from app.core.database import async_session_maker
from app.models.v4_models import WorkflowLog
import requests_unixsocket
import requests
import re
import json

router = APIRouter(prefix="/logs", tags=["logs"])

# 配置 requests 使用 unix socket
session = requests.Session()
session.mount('http+unix://', requests_unixsocket.UnixAdapter())


def get_docker_logs(service: str, lines: int = 100) -> List[dict]:
    """从 Docker 容器获取日志（直接调用 Docker HTTP API）"""
    container_map = {
        'api': 'xhs_api',
        'worker': 'xhs_worker',
        'scheduler': 'xhs_scheduler',
        'nginx': 'xhs_nginx'
    }
    
    if service not in container_map:
        return []
    
    container_name = container_map[service]
    logs = []
    
    try:
        # 直接调用 Docker HTTP API
        url = f'http+unix://%2Fvar%2Frun%2Fdocker.sock/v1.44/containers/{container_name}/logs'
        params = {
            'stdout': 'true',
            'stderr': 'true',
            'timestamps': 'true',
            'tail': str(min(lines * 3, 500))  # 获取更多用于过滤
        }
        
        response = session.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Docker 日志有 8 字节的头部（stream 类型 + 大小），需要处理
            raw_logs = response.content
            
            # 解析日志（跳过头部）
            offset = 0
            log_lines = []
            
            while offset < len(raw_logs):
                if offset + 8 > len(raw_logs):
                    break
                
                # 读取头部
                header = raw_logs[offset:offset+8]
                stream_type = header[0]
                size = int.from_bytes(header[4:8], 'big')
                
                if offset + 8 + size > len(raw_logs):
                    break
                
                # 读取日志内容
                log_content = raw_logs[offset+8:offset+8+size].decode('utf-8', errors='ignore')
                log_lines.append(log_content)
                
                offset += 8 + size
            
            # 如果没有头部格式，直接按行解析
            if not log_lines:
                log_lines = raw_logs.decode('utf-8', errors='ignore').strip().split('\n')
            
            for line in log_lines:
                if line.strip():
                    parsed = parse_docker_log_line(line.strip(), service)
                    if parsed:
                        logs.append(parsed)
            
            # 只返回最新的 N 条
            logs = logs[-lines:] if len(logs) > lines else logs
        else:
            print(f"[Log API] Docker API 返回错误: {response.status_code}")
            
    except Exception as e:
        print(f"[Log API] 获取 {service} 日志失败: {e}")
    
    return logs


def parse_docker_log_line(line: str, service: str) -> Optional[dict]:
    """解析 Docker 日志行"""
    # Docker 日志格式: 2026-02-12T18:12:01.072Z [2026-02-13 02:12:01,072: INFO/MainProcess] ...
    # 第一个时间戳是 UTC（Docker 引擎添加），第二个是北京时间（应用程序打印）
    # 我们需要提取第二个时间戳
    
    timestamp = None
    message = line
    
    # 首先尝试从 message 中提取应用程序打印的时间 [YYYY-MM-DD HH:MM:SS,mmm
    app_time_pattern = r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),(\d{3})\s*:\s*(\w+)\]'
    app_match = re.search(app_time_pattern, line)
    if app_match:
        # 提取应用程序时间（已经是北京时间）
        time_str = app_match.group(1)
        try:
            timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            # message 从应用程序日志开始
            message = line[app_match.end():].strip()
            if message.startswith(':'):
                message = message[1:].strip()
        except Exception as e:
            print(f"[Log API] 应用程序时间解析失败: {time_str}, 错误: {e}")
            timestamp = None
    
    # 如果没找到应用程序时间，尝试提取 Docker 时间戳
    if not timestamp:
        patterns = [
            # ISO 格式带 T（Docker 添加的 UTC 时间）
            (r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(.*)$', '%Y-%m-%dT%H:%M:%S'),
            # 普通格式
            (r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+(.*)$', '%Y-%m-%d %H:%M:%S'),
        ]
        
        for pattern, fmt in patterns:
            match = re.match(pattern, line)
            if match:
                timestamp_str = match.group(1)
                message = match.group(2).strip()
                try:
                    # 解析时间
                    if 'Z' in timestamp_str:
                        # UTC 时间，转换为北京时间
                        timestamp_utc = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamp = timestamp_utc + timedelta(hours=8)
                    else:
                        # 已经是本地时间
                        timestamp = datetime.fromisoformat(timestamp_str) if 'T' in timestamp_str else datetime.strptime(timestamp_str.split('.')[0], fmt)
                except Exception as e:
                    print(f"[Log API] 时间解析失败: {timestamp_str}, 错误: {e}")
                    timestamp = None
                break
    
    # 如果没有解析到时间戳，使用当前容器时间（北京时间）
    if not timestamp:
        timestamp = datetime.now()
    
    # 确定日志级别
    # 优先从日志行开头提取级别（如 "ERROR: ..."、"INFO: ..."）
    level = 'INFO'
    
    # 检查日志行前缀
    if message.startswith('ERROR:'):
        level = 'ERROR'
    elif message.startswith('WARNING:') or message.startswith('WARN:'):
        level = 'WARNING'
    elif message.startswith('DEBUG:'):
        level = 'DEBUG'
    elif message.startswith('CRITICAL:'):
        level = 'ERROR'
    else:
        # 如果没有前缀，检查是否包含错误关键词（但排除URL参数中的）
        upper_msg = message.upper()
        # 排除 "level=ERROR" 这种URL参数的情况
        if 'EXCEPTION' in upper_msg or 'TRACEBACK' in upper_msg:
            level = 'ERROR'
        elif 'FAILED' in upper_msg and 'HTTP' not in upper_msg:
            level = 'ERROR'
    
    return {
        'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else datetime.now().isoformat(),
        'service': service,
        'level': level,
        'message': message[:500]  # 限制长度
    }


@router.get("", response_model=ApiResponse)
async def get_logs(
    service: Optional[str] = Query(None, description="服务名称: api/worker/scheduler/nginx"),
    level: Optional[str] = Query(None, description="日志级别: INFO/WARNING/ERROR/DEBUG"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    获取系统日志
    
    从数据库(WorkflowLog)和 Docker 容器实时日志获取
    """
    try:
        all_logs = []
        
        # 1. 从 Docker 获取实时容器日志
        if service:
            docker_logs = get_docker_logs(service, lines=limit)
            all_logs.extend(docker_logs)
        else:
            # 获取所有服务的日志
            for svc in ['api', 'worker', 'scheduler']:
                docker_logs = get_docker_logs(svc, lines=50)
                all_logs.extend(docker_logs)
        
        # 2. 从数据库获取工作流日志
        async with async_session_maker() as session:
            query = select(WorkflowLog)
            
            # 按服务过滤
            if service:
                service_agent_map = {
                    'api': ['Research Agent', 'Creator Agent', 'Compliance Agent', 'Publisher Agent', 'Human Review'],
                    'worker': ['Celery Worker'],
                    'scheduler': ['Celery Beat']
                }
                if service in service_agent_map:
                    agents = service_agent_map[service]
                    query = query.where(WorkflowLog.agent_name.in_(agents))
            
            # 只获取最近24小时的日志
            since = datetime.now() - timedelta(hours=24)
            query = query.where(WorkflowLog.created_at >= since)
            
            query = query.order_by(desc(WorkflowLog.created_at)).limit(limit)
            
            result = await session.execute(query)
            db_logs = result.scalars().all()
            
            for log in db_logs:
                service_name = 'api'
                if 'Worker' in log.agent_name:
                    service_name = 'worker'
                elif 'Scheduler' in log.agent_name or 'Beat' in log.agent_name:
                    service_name = 'scheduler'
                
                level_map = {
                    'SUCCESS': 'INFO',
                    'COMPLETED': 'INFO',
                    'FAILED': 'ERROR',
                    'BLOCKED': 'ERROR',
                    'RUNNING': 'DEBUG',
                    'PENDING': 'INFO'
                }
                log_level = level_map.get(log.status, 'INFO')
                
                if level and log_level != level:
                    continue
                
                message = f"[{log.agent_name}] {log.action}"
                if log.output_data:
                    try:
                        output_str = json.dumps(log.output_data, ensure_ascii=False)[:200]
                        message += f" - {output_str}"
                    except:
                        pass
                
                all_logs.append({
                    'timestamp': log.created_at.isoformat() if log.created_at else datetime.now().isoformat(),
                    'service': service_name,
                    'level': log_level,
                    'message': message
                })
        
        # 3. 合并并排序（按时间倒序）
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 按级别过滤
        if level:
            all_logs = [log for log in all_logs if log['level'] == level]
        
        # 分页
        total = len(all_logs)
        paginated_logs = all_logs[offset:offset + limit]
        
        return ApiResponse(
            data={
                "logs": paginated_logs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        import traceback
        print(f"[Log API] 错误: {e}\n{traceback.format_exc()}")
        return ApiResponse(
            code=500,
            message=f"获取日志失败: {str(e)}"
        )
