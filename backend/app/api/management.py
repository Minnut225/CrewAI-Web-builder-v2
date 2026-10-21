from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.schemas.management import (
    DashboardMetricsResponse,
    SalesReportResponse,
    AuditLogListResponse,
    AuditLogResponseItem,
    EmployeeResponse,
    InventoryItemResponse,
    AuditLogCreateRequest
)
from app.services.management_service import ManagementService

router = APIRouter(prefix="/management", tags=["Management Dashboard & Reports"])

def require_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    return current_user

@router.get("/dashboard", response_model=DashboardMetricsResponse)
@router.get("/dashboard/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Get executive summary metrics for management dashboard.
    Requires MANAGER role.
    """
    return ManagementService.get_dashboard_metrics(db)

@router.get("/reports/sales", response_model=SalesReportResponse)
def get_sales_report(
    start_date: Optional[str] = Query(None, description="ISO start date filter"),
    end_date: Optional[str] = Query(None, description="ISO end date filter"),
    group_by: str = Query("day", description="Grouping: day, week, month"),
    period: Optional[str] = Query(None, description="today | week | month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Get aggregated sales report with date range and grouping.
    Requires MANAGER role.
    """
    if period:
        today = datetime.utcnow().date()
        if period == "today":
            start_date = today.isoformat()
            end_date = today.isoformat()
            group_by = "day"
        elif period == "week":
            start_date = (today - timedelta(days=7)).isoformat()
            end_date = today.isoformat()
            group_by = "day"
        elif period == "month":
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            group_by = "day"
    return ManagementService.get_sales_report(db, start_date=start_date, end_date=end_date, group_by=group_by)

@router.get("/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by audit action"),
    target_entity: Optional[str] = Query(None, description="Filter by target entity"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    List audit logs with filtering and pagination.
    Requires MANAGER role.
    """
    total, logs = ManagementService.get_audit_logs(
        db, user_id=user_id, action=action, target_entity=target_entity, limit=limit, offset=offset
    )
    items = [
        AuditLogResponseItem(
            id=log.id,
            user_id=log.user_id,
            action=str(log.action),
            target_entity=log.target_entity,
            target_id=log.target_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]
    return AuditLogListResponse(total=total, items=items)

@router.post("/audit-logs", response_model=AuditLogResponseItem, status_code=status.HTTP_201_CREATED)
def create_audit_log(
    payload: AuditLogCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an audit log entry. Accessible by authenticated users.
    """
    ip_addr = request.client.host if request.client else None
    log = ManagementService.log_audit(
        db,
        user_id=current_user.id,
        action=payload.action,
        target_entity=payload.target_entity,
        target_id=payload.target_id,
        details=payload.details,
        ip_address=ip_addr
    )
    return AuditLogResponseItem(
        id=log.id,
        user_id=log.user_id,
        action=str(log.action),
        target_entity=log.target_entity,
        target_id=log.target_id,
        details=log.details,
        ip_address=log.ip_address,
        created_at=log.created_at
    )

@router.get("/employees", response_model=List[EmployeeResponse])
def get_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    List all employees. Requires MANAGER role.
    """
    users = ManagementService.get_employees(db)
    return [
        EmployeeResponse(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]

@router.get("/inventory-status", response_model=List[InventoryItemResponse])
def get_inventory_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Get inventory status for management dashboard. Requires MANAGER role.
    """
    items = ManagementService.get_inventory_status(db)
    return [
        InventoryItemResponse(
            id=i.id,
            name=i.name,
            unit=i.unit,
            stock_quantity=i.stock_quantity,
            min_stock_threshold=i.min_stock_threshold,
            cost_per_unit=i.cost_per_unit,
            updated_at=i.updated_at
        )
        for i in items
    ]
