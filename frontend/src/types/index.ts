export type UserRole = 'CASHIER' | 'MANAGER';

export type OrderType = 'DINE_IN' | 'TAKEAWAY';

export type OrderStatus = 'PENDING' | 'PAID' | 'COMPLETED' | 'CANCELLED';

export type PaymentMethod = 'CASH' | 'QR_PAY' | 'CARD';

export type PaymentStatus = 'SUCCESS' | 'FAILED' | 'PENDING';

export type MovementType = 'IMPORT' | 'EXPORT' | 'ADJUSTMENT';

export interface User {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  username: string;
}

export interface Category {
  id: number;
  name: string;
  slug?: string;
  display_order?: number;
}

export interface ProductRecipeItem {
  id: number;
  ingredient_id: number;
  quantity_required: number;
  ingredient_name?: string;
  unit?: string;
}

export interface Product {
  id: number;
  category_id: number;
  name: string;
  slug?: string;
  price: number;
  cost_price?: number;
  image_url?: string;
  is_available?: boolean;
  is_active?: boolean;
  description?: string;
  recipes?: ProductRecipeItem[];
}

export interface Ingredient {
  id: number;
  name: string;
  unit: string;
  stock_quantity: number;
  min_threshold: number;
  cost_per_unit: number;
  updated_at: string;
  current_stock?: number;
  min_stock_level?: number;
  cost_price?: number;
}

export interface StockImportRequest {
  ingredient_id: number;
  quantity: number;
  unit_price: number;
  supplier_name?: string;
  note?: string;
}

export interface OrderItemCreate {
  product_id: number;
  quantity: number;
  note?: string;
}

export interface OrderCreate {
  table_number?: string | number;
  order_type: OrderType;
  customer_name?: string;
  note?: string;
  items: OrderItemCreate[];
}

export interface OrderItemResponse {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  note?: string;
}

export interface OrderPaymentResponse {
  id: number;
  amount: number;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_code?: string;
  created_at: string;
}

export interface OrderResponse {
  id: number;
  order_number: string;
  user_id: number;
  customer_name?: string;
  table_number?: string | number;
  order_type: OrderType;
  status: OrderStatus;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  note?: string;
  created_at: string;
  updated_at: string;
  items: OrderItemResponse[];
  payments: OrderPaymentResponse[];
}

export interface CheckoutRequest {
  payment_method: PaymentMethod;
  amount_paid?: number;
  transaction_code?: string;
  amount_tendered?: number;
  idempotency_key?: string;
}

export interface CheckoutResponse {
  order_id: number;
  order_number: string;
  status: OrderStatus;
  total_amount: number;
  amount_paid: number;
  change_due: number;
  payment: OrderPaymentResponse;
  message: string;
}

export interface InventoryMovement {
  id: number;
  ingredient_id: number;
  movement_type: MovementType;
  quantity: number;
  unit_price: number;
  reference_id?: string;
  note?: string;
  created_at: string;
  ingredient_name?: string;
}

/* -------------------------------------------------------------------------- */
/* Phase 5 Management Dashboard, Sales Reports & Audit Logs TypeScript Types   */
/* -------------------------------------------------------------------------- */

export interface DashboardMetricsResponse {
  total_revenue: number; // in VND (minor units / integers)
  total_orders: number;
  total_items_sold: number;
  active_tables: number;
  pending_orders: number;
  low_stock_count: number;
  revenue_growth_percent: number;
}

export interface SalesReportFilterRequest {
  start_date?: string; // YYYY-MM-DD
  end_date?: string;   // YYYY-MM-DD
  group_by?: string;   // 'day' | 'week' | 'month'
}

export interface SalesReportItem {
  period: string;      // e.g. "2025-05-10"
  revenue: number;     // total revenue in period
  order_count: number; // total orders in period
}

export interface SalesReportResponse {
  start_date?: string;
  end_date?: string;
  group_by: string;
  total_revenue: number;
  total_orders: number;
  items: SalesReportItem[];
}

export interface AuditLogResponseItem {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  target_entity?: string;
  target_id?: string | number;
  details?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

export interface AuditLogListResponse {
  total: number;
  items: AuditLogResponseItem[];
}
