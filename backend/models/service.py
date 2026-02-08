# backend/models/service.py

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ServiceBase(BaseModel):
    """服务基础模型"""
    name: str = Field(..., description="服务名称")
    url: str = Field(..., description="OpenAPI/Swagger 文档地址")
    type: str = Field(..., description="文档类型，如 OpenAPI 3.0, Swagger 2.0, AsyncAPI")
    auth_type: Literal["none", "api_key", "basic", "oauth2"] = Field(
        default="none", 
        description="认证类型"
    )
    auth_config: dict = Field(
        default_factory=dict, 
        description="认证配置 JSON"
    )


class ServiceCreate(ServiceBase):
    """创建服务请求模型"""
    pass


class ServiceUpdate(BaseModel):
    """更新服务请求模型"""
    name: str | None = None
    url: str | None = None
    type: str | None = None
    auth_type: Literal["none", "api_key", "basic", "oauth2"] | None = None
    auth_config: dict | None = None


class Service(ServiceBase):
    """服务完整模型"""
    id: int
    status: Literal["healthy", "unhealthy"] = "healthy"
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, db_obj):
        """从数据库对象转换为 Pydantic 模型"""
        return cls(
            id=db_obj.id,
            name=db_obj.name,
            url=db_obj.url,
            type=db_obj.type,
            auth_type=db_obj.auth_type or "none",
            auth_config=db_obj.auth_config or {},
            status=db_obj.status,
            createdAt=db_obj.created_at,
            updatedAt=db_obj.updated_at,
        )

