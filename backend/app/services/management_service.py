from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.menu_order import Order, OrderItem, Payment, StockMovement, AuditLog, OrderStatus, PaymentStatus, Ingredient, AuditAction
from app.models.user import User, UserRole
from app.schemas.management import (
    DashboardMetricsResponse,
    SalesReportResponse,
    SalesReportItem,
    SalesReportSummary,
    AuditLogListResponse,
    AuditLogResponseItem,
    EmployeeResponse
)

class ManagementService:
    @staticmethod
    def get_dashboard_metrics(db: Session) -> DashboardMetricsResponse:
        completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).all()
        total_revenue = sum(o.total_amount for o in completed_orders)
        total_orders = len(completed_orders)
        total_items_sold = 0
        for o in completed_orders:
            for item in o.items:
                total_items_sold += item.quantity
                
        active_tables_count = db.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.PAID]),
            Order.table_number.isnot(None)
        ).distinct(Order.table_number).count()
        
        pending_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.PAID])
        ).count()
        
        low_stock_count = db.query(Ingredient).filter(Ingredient.stock_quantity <= Ingredient.min_stock_level).count()
        
        return DashboardMetricsResponse(
            total_revenue=int(total_revenue),
            total_orders=total_orders,
            total_items_sold=total_items_sold,
            active_tables=active_tables_count,
            pending_orders=pending_orders,
            low_stock_count=low_stock_count,
            revenue_growth_percent=5.4
        )

    @staticmethod
    def get_sales_report(
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "day"
    ) -> SalesReportResponse:
        query = db.query(Order).filter(Order.status == OrderStatus.COMPLETED)
        
        if start_date:
            try:
                dt_start = datetime.fromisoformat(start_date)
                query = query.filter(Order.created_at >= dt_start)
            except ValueError:
                pass
                
        if end_date:
            try:
                dt_end = datetime.fromisoformat(end_date)
                query = query.filter(Order.created_at <= dt_end)
            except ValueError:
                pass
                
        orders = query.all()
        
        grouped_data: Dict[str, Dict[str, Any]] = {}
        total_revenue = Decimal(0)
        total_orders = len(orders)
        total_items_sold = 0
        
        for o in orders:
            if o.created_at:
                if group_by == "month":
                    key = o.created_at.strftime("%Y-%m")
                elif group_by == "week":
                    year, week, _ = o.created_at.isocalendar()
                    key = f"{year}-W{week:02d}"
                else: # day
                    key = o.created_at.strftime("%Y-%m-%d")
            else:
                key = "unknown"
                
            if key not in grouped_data:
                grouped_data[key] = {
                    "period": key,
                    "order_count": 0,
                    "revenue": Decimal(0),
                    "items_sold": 0
                }
                
            grouped_data[key]["order_count"] += 1
            grouped_data[key]["revenue"] += Decimal(o.total_amount)
            
            items_count = sum(item.quantity for item in o.items)
            grouped_data[key]["items_sold"] += items_count
            
            total_revenue += Decimal(o.total_amount)
            total_items_sold += items_count
            
        items = [
            SalesReportItem(
                period=data["period"],
                order_count=data["order_count"],
                revenue=int(data["revenue"]),
                items_sold=data["items_sold"],
                gross_sales=int(data["revenue"]),
                net_sales=int(data["revenue"]),
                discounts=0
            )
            for data in sorted(grouped_data.values(), key=lambda x: x["period"])
        ]
        
        avg_order_val = float(total_revenue / total_orders) if total_orders > 0 else 0.0
        summary = SalesReportSummary(
            total_revenue=int(total_revenue),
            total_gross_sales=int(total_revenue),
            total_net_sales=int(total_revenue),
            total_orders=total_orders,
            total_items_sold=total_items_sold,
            average_order_value=avg_order_val
        )
        
        return SalesReportResponse(
            items=items,
            summary=summary,
            group_by=group_by
        )

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        target_entity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[int, List[AuditLog]]:
        query = db.query(AuditLog)
        
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if target_entity:
            query = query.filter(AuditLog.target_entity == target_entity)
            
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        return total, logs

    @staticmethod
    def log_audit(
        db: Session,
        user_id: Optional[int],
        action: str,
        target_entity: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            target_entity=target_entity,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_employees(db: Session) -> List[User]:
        return db.query(User).all()

    @staticmethod
    def get_inventory_status(db: Session) -> List[Ingredient]:
        return db.query(Ingredient).all()
