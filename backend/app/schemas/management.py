# Updated management schemas
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

class DashboardMetricsResponse(BaseModel):
    total_revenue: int = Field(..., description="Total revenue in minor units (VND)")
    total_orders: int
    total_items_sold: int
    active_tables: int
    pending_orders: int
    low_stock_count: int
    revenue_growth_percent: float = 0.0

class SalesReportFilterRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    group_by: str = Field("day", description="day | week | month")

class SalesReportItem(BaseModel):
    period: str
    order_count: int = 0
    revenue: int = 0
    items_sold: int = 0
    gross_sales: int = 0
    net_sales: int = 0
    discounts: int = 0

class SalesReportSummary(BaseModel):
    total_revenue: int = 0
    total_gross_sales: int = 0
    total_net_sales: int = 0
    total_orders: int = 0
    total_items_sold: int = 0
    average_order_value: float = 0.0

class SalesReportResponse(BaseModel):
    items: List[SalesReportItem]
    summary: SalesReportSummary
    group_by: str = "day"

class AuditLogResponseItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    target_entity: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[Union[Dict[str, Any], str]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponseItem]
    page: int = 1
    size: int = 50

    class Config:
        from_attributes = True

class AuditLogCreateRequest(BaseModel):
    action: str
    target_entity: str
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class EmployeeResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "CASHIER"

class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class InventoryItemResponse(BaseModel):
    id: int
    name: str
    unit: str
    stock_quantity: int
    min_stock_threshold: int
    cost_per_unit: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
