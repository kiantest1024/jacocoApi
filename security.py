"""
安全相关功能模块。
"""

import os
import time
import hmac
import hashlib
import secrets
import ipaddress
from typing import List, Optional, Dict, Any, Set, Callable

from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader

from config import settings


# API 密钥认证
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME)

# 从环境变量获取 API 密钥
API_KEY = os.getenv("API_KEY", "")
if not API_KEY:
    # 如果未设置，生成一个随机密钥并警告用户
    API_KEY = secrets.token_urlsafe(32)
    print(f"警告: 未设置 API_KEY 环境变量。已生成随机密钥: {API_KEY}")
    print("请在生产环境中设置 API_KEY 环境变量。")


# IP 白名单
IP_WHITELIST_STR = os.getenv("IP_WHITELIST", "")
IP_WHITELIST: Set[str] = set()
IP_NETWORKS: List[ipaddress.IPv4Network] = []

if IP_WHITELIST_STR:
    for ip in IP_WHITELIST_STR.split(","):
        ip = ip.strip()
        if "/" in ip:
            # 这是一个 CIDR 网络
            try:
                IP_NETWORKS.append(ipaddress.IPv4Network(ip))
            except ValueError:
                print(f"警告: 无效的 CIDR 网络: {ip}")
        else:
            # 这是一个单独的 IP
            IP_WHITELIST.add(ip)


# Webhook 签名密钥轮换
WEBHOOK_SECRETS: Dict[str, str] = {
    "current": settings.GIT_WEBHOOK_SECRET
}

# 如果设置了旧密钥，添加到字典中
OLD_WEBHOOK_SECRET = os.getenv("OLD_GIT_WEBHOOK_SECRET", "")
if OLD_WEBHOOK_SECRET:
    WEBHOOK_SECRETS["old"] = OLD_WEBHOOK_SECRET


def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    验证 API 密钥。
    
    参数:
        api_key: API 密钥
        
    返回:
        如果验证成功，则返回 API 密钥
        
    异常:
        如果验证失败，则引发 HTTPException
    """
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API 密钥"
        )
    return api_key


def verify_ip_whitelist(request: Request) -> bool:
    """
    验证 IP 白名单。
    
    参数:
        request: FastAPI 请求对象
        
    返回:
        如果验证成功，则返回 True
        
    异常:
        如果验证失败，则引发 HTTPException
    """
    # 如果未设置白名单，则允许所有 IP
    if not IP_WHITELIST and not IP_NETWORKS:
        return True
    
    # 获取客户端 IP
    client_ip = request.client.host
    
    # 检查是否在白名单中
    if client_ip in IP_WHITELIST:
        return True
    
    # 检查是否在网络范围内
    try:
        ip_obj = ipaddress.IPv4Address(client_ip)
        for network in IP_NETWORKS:
            if ip_obj in network:
                return True
    except ValueError:
        # 无效的 IP 地址
        pass
    
    # IP 不在白名单中
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="IP 地址不在白名单中"
    )


def verify_webhook_signature(body: bytes, signature: str, signature_type: str = "sha256") -> bool:
    """
    验证 webhook 签名。
    
    参数:
        body: 请求体
        signature: 签名
        signature_type: 签名类型（sha1 或 sha256）
        
    返回:
        如果验证成功，则返回 True，否则返回 False
    """
    # 移除签名类型前缀
    if "=" in signature:
        sig_parts = signature.split("=", 1)
        if len(sig_parts) == 2:
            signature_type = sig_parts[0]
            signature = sig_parts[1]
    
    # 选择哈希算法
    hash_func = hashlib.sha256 if signature_type == "sha256" else hashlib.sha1
    
    # 尝试使用所有密钥验证签名
    for secret_key in WEBHOOK_SECRETS.values():
        expected_signature = hmac.new(
            secret_key.encode(),
            body,
            hash_func
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            return True
    
    return False


# 速率限制器
class RateLimiter:
    """
    速率限制器类。
    """
    
    def __init__(self, requests_limit: int, window_seconds: int):
        """
        初始化速率限制器。
        
        参数:
            requests_limit: 时间窗口内的请求限制
            window_seconds: 时间窗口（秒）
        """
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    async def __call__(self, request: Request):
        """
        检查请求是否超过速率限制。
        
        参数:
            request: FastAPI 请求对象
            
        返回:
            如果未超过限制，则返回 True
            
        异常:
            如果超过限制，则引发 HTTPException
        """
        client_ip = request.client.host
        now = time.time()
        
        # 初始化或清理旧请求
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        else:
            # 移除比窗口时间更旧的请求
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] 
                if now - ts < self.window_seconds
            ]
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.requests_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"超过速率限制。最大 {self.requests_limit} 请求每 {self.window_seconds} 秒。"
            )
        
        # 添加当前请求时间戳
        self.requests[client_ip].append(now)
        
        # 继续处理请求
        return True


# 创建速率限制器实例
rate_limiter = RateLimiter(
    requests_limit=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
)


# 安全中间件
def create_security_middleware() -> Callable:
    """
    创建安全中间件。
    
    返回:
        安全中间件函数
    """
    async def security_middleware(request: Request, call_next):
        """
        安全中间件函数。
        
        参数:
            request: FastAPI 请求对象
            call_next: 下一个中间件函数
            
        返回:
            响应对象
        """
        # 添加安全头
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    return security_middleware
