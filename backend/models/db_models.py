"""
SQLAlchemy 数据库表模型
定义了 Combination、McpServer、Service 和 User 的数据库结构
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index, Boolean
from sqlalchemy.orm import declarative_base

# 创建基类
Base = declarative_base()


class CombinationDB(Base):
    """组合数据库模型"""
    __tablename__ = "combinations"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="组合名称")
    description = Column(Text, default="", comment="组合描述")
    status = Column(String(20), default="active", index=True, comment="状态：active/inactive")

    # JSON 字段：存储 endpoints 列表
    # 结构：[{"serviceName": str, "serviceUrl": str, "path": str, "method": str, "summary": str}]
    endpoints = Column(JSON, nullable=False, default=list, comment="API 端点列表")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_combination_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<CombinationDB(id={self.id}, name='{self.name}', status='{self.status}')>"


class McpServerDB(Base):
    """MCP 服务数据库模型"""
    __tablename__ = "mcp_servers"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="MCP 服务名称")
    prefix = Column(String(50), unique=True, nullable=False, index=True, comment="MCP 前缀（唯一标识）")
    description = Column(Text, default="", comment="MCP 服务描述")
    status = Column(String(20), default="active", index=True, comment="状态：active/inactive")

    # JSON 字段：存储 combination_ids
    # 结构：[1, 2, 3, ...]
    combination_ids = Column(JSON, nullable=False, default=list, comment="包含的组合 ID 列表")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_mcp_server_prefix_status', 'prefix', 'status'),
    )

    def __repr__(self):
        return f"<McpServerDB(id={self.id}, name='{self.name}', prefix='{self.prefix}', status='{self.status}')>"


class ServiceDB(Base):
    """服务数据库模型"""
    __tablename__ = "services"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="服务名称")
    url = Column(Text, nullable=False, comment="OpenAPI/Swagger 文档地址")
    type = Column(String(50), nullable=False, comment="文档类型")
    status = Column(String(20), default="healthy", index=True, comment="状态：healthy/unhealthy")

    # 认证配置
    auth_type = Column(String(20), default="none", nullable=False, comment="认证类型：none/api_key/basic/oauth2")
    auth_config = Column(JSON, default=dict, nullable=False, comment="认证配置 JSON")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_service_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<ServiceDB(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"


class UserDB(Base):
    """用户数据库模型"""
    __tablename__ = "users"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    username = Column(String(100), unique=True, nullable=False, index=True, comment="用户名（唯一）")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")

    # 用户角色
    role = Column(String(20), default="user", nullable=False, index=True, comment="角色：admin/user")

    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    # 索引
    __table_args__ = (
        Index('idx_user_role_active', 'role', 'is_active'),
    )

    def __repr__(self):
        return f"<UserDB(id={self.id}, username='{self.username}', role='{self.role}', is_active={self.is_active})>"
