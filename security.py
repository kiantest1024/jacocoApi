import os
import secrets
import hashlib
import hmac
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    API_KEY = secrets.token_urlsafe(32)
    print(f"警告: 未设置 API_KEY 环境变量。已生成随机密钥: {API_KEY}")
    print("请在生产环境中设置 API_KEY 环境变量。")

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = security) -> str:
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API 密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    try:
        algorithm, signature = signature_header.split('=', 1)
        if algorithm != 'sha256':
            return False
        
        expected_signature = hmac.new(
            settings.GIT_WEBHOOK_SECRET.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    except (ValueError, AttributeError):
        return False

def verify_gitlab_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    
    try:
        return hmac.compare_digest(signature_header, settings.GIT_WEBHOOK_SECRET)
    except (ValueError, AttributeError):
        return False
