# backend/core/auth_handler.py
"""
认证处理器模块

支持多种认证方式：
- none: 无认证
- api_key: API Key 认证（支持 header 或 query 参数）
- basic: HTTP Basic 认证
- oauth2: OAuth2 Client Credentials 认证
"""

import base64
from typing import Dict, Any, Optional
import httpx
from datetime import datetime, timedelta


class OAuth2TokenCache:
    """OAuth2 Token 缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get_token(self, cache_key: str) -> Optional[str]:
        """获取缓存的 token，如果已过期则返回 None"""
        if cache_key not in self._cache:
            return None
        
        cached = self._cache[cache_key]
        if datetime.now() >= cached["expires_at"]:
            del self._cache[cache_key]
            return None
        
        return cached["access_token"]
    
    def set_token(self, cache_key: str, access_token: str, expires_in: int):
        """缓存 token，提前 60 秒过期以避免边界问题"""
        self._cache[cache_key] = {
            "access_token": access_token,
            "expires_at": datetime.now() + timedelta(seconds=max(0, expires_in - 60))
        }


# 全局 token 缓存实例
_token_cache = OAuth2TokenCache()


class AuthHandler:
    """认证处理器"""
    
    @staticmethod
    async def apply_auth(
        auth_type: str,
        auth_config: Dict[str, Any],
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> None:
        """
        根据认证类型应用认证信息
        
        Args:
            auth_type: 认证类型 (none, api_key, basic, oauth2)
            auth_config: 认证配置
            headers: HTTP 请求头（会被修改）
            params: HTTP 请求参数（会被修改）
        """
        if auth_type == "none" or not auth_config:
            return
        
        if auth_type == "api_key":
            await AuthHandler._apply_api_key_auth(auth_config, headers, params)
        elif auth_type == "basic":
            await AuthHandler._apply_basic_auth(auth_config, headers)
        elif auth_type == "oauth2":
            await AuthHandler._apply_oauth2_auth(auth_config, headers)
    
    @staticmethod
    async def _apply_api_key_auth(
        config: Dict[str, Any],
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> None:
        """应用 API Key 认证"""
        key_name = config.get("key_name", "X-API-Key")
        key_value = config.get("key_value", "")
        key_location = config.get("key_location", "header")
        
        if not key_value:
            return
        
        if key_location == "header":
            headers[key_name] = key_value
        elif key_location == "query":
            params[key_name] = key_value
    
    @staticmethod
    async def _apply_basic_auth(
        config: Dict[str, Any],
        headers: Dict[str, str]
    ) -> None:
        """应用 HTTP Basic 认证"""
        username = config.get("username", "")
        password = config.get("password", "")
        
        if not username:
            return
        
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
    
    @staticmethod
    async def _apply_oauth2_auth(
        config: Dict[str, Any],
        headers: Dict[str, str]
    ) -> None:
        """应用 OAuth2 Client Credentials 认证"""
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")
        token_url = config.get("token_url", "")
        
        if not all([client_id, client_secret, token_url]):
            return
        
        # 尝试从缓存获取 token
        cache_key = f"{token_url}:{client_id}"
        access_token = _token_cache.get_token(cache_key)
        
        if not access_token:
            # 获取新 token
            access_token = await AuthHandler._fetch_oauth2_token(
                token_url, client_id, client_secret
            )
            if access_token:
                # 默认缓存 1 小时
                _token_cache.set_token(cache_key, access_token, 3600)
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    
    @staticmethod
    async def _fetch_oauth2_token(
        token_url: str,
        client_id: str,
        client_secret: str
    ) -> Optional[str]:
        """
        获取 OAuth2 access token
        
        使用 Client Credentials Grant 流程
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    
                    if access_token:
                        # 更新缓存过期时间
                        cache_key = f"{token_url}:{client_id}"
                        _token_cache.set_token(cache_key, access_token, expires_in)
                        return access_token
                
                print(f"OAuth2 token fetch failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"OAuth2 token fetch error: {e}")
            return None
