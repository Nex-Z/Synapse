# backend/api/services.py
"""
服务管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.database import get_db
from models.service import Service, ServiceCreate, ServiceUpdate
from repositories.service_repository import ServiceRepository

# 路由器级别添加 JWT 认证依赖，所有端点都需要登录
router = APIRouter(
    prefix="/api/v1/services",
    tags=["services"],
    dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[Service])
async def get_services(db: AsyncSession = Depends(get_db)):
    """
    获取所有服务列表
    """
    repo = ServiceRepository(db)
    db_services = await repo.get_all()
    return [Service.from_orm(s) for s in db_services]


@router.get("/{service_id}", response_model=Service)
async def get_service(
    service_id: int = Path(..., description="服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取单个服务
    """
    repo = ServiceRepository(db)
    db_service = await repo.get_by_id(service_id)

    if not db_service:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    return Service.from_orm(db_service)


@router.post("", response_model=Service, status_code=201)
async def create_service(
    service: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新服务
    """
    repo = ServiceRepository(db)

    # 创建服务
    db_service = await repo.create(
        name=service.name,
        url=service.url,
        type=service.type,
        auth_type=service.auth_type,
        auth_config=service.auth_config
    )

    await db.commit()
    return Service.from_orm(db_service)


@router.put("/{service_id}", response_model=Service)
async def update_service(
    service_id: int = Path(..., description="服务 ID"),
    service_update: ServiceUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新服务信息
    """
    repo = ServiceRepository(db)

    # 检查服务是否存在
    existing = await repo.get_by_id(service_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    # 更新服务
    db_service = await repo.update(
        service_id=service_id,
        name=service_update.name,
        url=service_update.url,
        type=service_update.type,
        auth_type=service_update.auth_type,
        auth_config=service_update.auth_config
    )

    await db.commit()

    if not db_service:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    return Service.from_orm(db_service)


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: int = Path(..., description="服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除服务
    """
    repo = ServiceRepository(db)

    success = await repo.delete(service_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    await db.commit()
    return None
