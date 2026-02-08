# backend/repositories/service_repository.py

from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.db_models import ServiceDB


class ServiceRepository:
    """服务数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[ServiceDB]:
        """获取所有服务"""
        result = await self.session.execute(select(ServiceDB))
        return list(result.scalars().all())

    async def get_by_id(self, service_id: int) -> Optional[ServiceDB]:
        """根据 ID 获取服务"""
        result = await self.session.execute(
            select(ServiceDB).where(ServiceDB.id == service_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        url: str,
        type: str,
        auth_type: str = "none",
        auth_config: dict = None
    ) -> ServiceDB:
        """创建新服务"""
        service = ServiceDB(
            name=name,
            url=url,
            type=type,
            auth_type=auth_type,
            auth_config=auth_config or {},
            status="healthy",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(service)
        await self.session.flush()
        await self.session.refresh(service)
        return service

    async def update(
        self,
        service_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        type: Optional[str] = None,
        auth_type: Optional[str] = None,
        auth_config: Optional[dict] = None
    ) -> Optional[ServiceDB]:
        """更新服务"""
        service = await self.get_by_id(service_id)
        if not service:
            return None

        if name is not None:
            service.name = name
        if url is not None:
            service.url = url
        if type is not None:
            service.type = type
        if auth_type is not None:
            service.auth_type = auth_type
        if auth_config is not None:
            service.auth_config = auth_config

        service.updated_at = datetime.now()
        await self.session.flush()
        await self.session.refresh(service)
        return service

    async def delete(self, service_id: int) -> bool:
        """删除服务"""
        service = await self.get_by_id(service_id)
        if not service:
            return False

        await self.session.delete(service)
        await self.session.flush()
        return True

    async def toggle_status(self, service_id: int) -> Optional[ServiceDB]:
        """切换服务状态"""
        service = await self.get_by_id(service_id)
        if not service:
            return None

        # 切换状态
        service.status = "unhealthy" if service.status == "healthy" else "healthy"
        service.updated_at = datetime.now()
        await self.session.flush()
        await self.session.refresh(service)
        return service
