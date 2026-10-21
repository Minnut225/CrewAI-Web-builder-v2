import axios, { AxiosInstance } from 'axios';
import {
  User,
  TokenResponse,
  Category,
  Product,
  Ingredient,
  StockImportRequest,
  OrderCreate,
  OrderResponse,
  CheckoutRequest,
  CheckoutResponse,
  InventoryMovement,
  DashboardMetricsResponse,
  SalesReportResponse,
  AuditLogListResponse
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to attach bearer token
    this.client.interceptors.request.use(
      (config) => {
        let token = localStorage.getItem('access_token') || localStorage.getItem('coffeeflow_token');
        if (token && token.startsWith('mock-')) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('coffeeflow_token');
          token = null;
        }
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle 401 unauthorized
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('coffeeflow_token');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(usernameOrPayload: string | { username: string; password?: string } | URLSearchParams, password?: string): Promise<TokenResponse> {
    let payload: any;
    if (typeof usernameOrPayload === 'string') {
      payload = { username: usernameOrPayload, password: password || '' };
    } else if (usernameOrPayload instanceof URLSearchParams) {
      payload = {
        username: usernameOrPayload.get('username') || '',
        password: usernameOrPayload.get('password') || ''
      };
    } else {
      payload = usernameOrPayload;
    }

    const response = await this.client.post<TokenResponse>('/auth/login', payload);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('coffeeflow_token', response.data.access_token);
      if (response.data.role) {
        localStorage.setItem('user_role', response.data.role);
        localStorage.setItem('coffeeflow_role', response.data.role);
      }
    }
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Categories & Products
  async getCategories(): Promise<Category[]> {
    const response = await this.client.get<Category[]>('/categories');
    return response.data;
  }

  async getProducts(categoryId?: number): Promise<Product[]> {
    const url = categoryId ? `/products?category_id=${categoryId}` : '/products';
    const response = await this.client.get<Product[]>(url);
    return response.data;
  }

  // Inventory
  async getIngredients(): Promise<Ingredient[]> {
    const response = await this.client.get<Ingredient[]>('/inventory/ingredients');
    return response.data;
  }

  async importStock(data: StockImportRequest): Promise<any> {
    const response = await this.client.post('/inventory/import', data);
    return response.data;
  }

  async getMovements(): Promise<InventoryMovement[]> {
    const response = await this.client.get<InventoryMovement[]>('/inventory/movements');
    return response.data;
  }

  async getInventoryMovements(): Promise<InventoryMovement[]> {
    return this.getMovements();
  }

  // Orders & Checkout
  async getOrders(status?: string): Promise<OrderResponse[]> {
    const url = status ? `/orders?status=${status}` : '/orders';
    const response = await this.client.get<OrderResponse[]>(url);
    return response.data;
  }

  async getOrderById(orderId: number): Promise<OrderResponse> {
    const response = await this.client.get<OrderResponse>(`/orders/${orderId}`);
    return response.data;
  }

  async createOrder(data: OrderCreate, idempotencyKey?: string): Promise<OrderResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['X-Idempotency-Key'] = idempotencyKey;
    }
    const response = await this.client.post<OrderResponse>('/orders', data, {
      headers,
    });
    return response.data;
  }

  async checkoutOrder(orderId: number, data: CheckoutRequest, idempotencyKey?: string): Promise<CheckoutResponse> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['X-Idempotency-Key'] = idempotencyKey;
    }
    const response = await this.client.post<CheckoutResponse>(`/orders/${orderId}/checkout`, data, {
      headers,
    });
    return response.data;
  }

  async updateOrderStatus(orderId: number, status: string): Promise<OrderResponse> {
    const response = await this.client.patch<OrderResponse>(`/orders/${orderId}/status`, { status });
    return response.data;
  }

  async confirmOrder(orderId: number): Promise<OrderResponse> {
    const response = await this.client.post<OrderResponse>(`/orders/${orderId}/confirm`);
    return response.data;
  }

  async updateProduct(productId: number, data: any): Promise<Product> {
    const response = await this.client.put<Product>(`/products/${productId}`, data);
    return response.data;
  }

  async createProduct(data: any): Promise<Product> {
    const response = await this.client.post<Product>('/products', data);
    return response.data;
  }

  async getReportsSummary(): Promise<any> {
    const response = await this.client.get<any>('/reports/summary');
    return response.data;
  }

  // Management Dashboard, Reports & Audit Logs (Phase 5)
  async getDashboardMetrics(): Promise<DashboardMetricsResponse> {
    const response = await this.client.get<DashboardMetricsResponse>('/management/dashboard/metrics');
    return response.data;
  }

  async getSalesReports(params?: { start_date?: string; end_date?: string; group_by?: string; period?: string }): Promise<SalesReportResponse> {
      const response = await this.client.get<SalesReportResponse>('/management/reports/sales', { params });
      return response.data;
    }

  async getAuditLogs(params?: { user_id?: number; action?: string; target_entity?: string; limit?: number; offset?: number }): Promise<AuditLogListResponse> {
    const query = new URLSearchParams();
    if (params?.user_id) query.append('user_id', String(params.user_id));
    if (params?.action) query.append('action', params.action);
    if (params?.target_entity) query.append('target_entity', params.target_entity);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.offset) query.append('offset', String(params.offset));
    const suffix = query.toString() ? `?${query.toString()}` : '';
    const response = await this.client.get<AuditLogListResponse>(`/management/audit-logs${suffix}`);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
