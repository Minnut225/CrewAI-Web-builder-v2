import { useState, useEffect } from 'react';
import api from '../services/api';

export default function CashierPOS() {
  const [categories, setCategories] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Cart state
  const [cartItems, setCartItems] = useState<Array<{ product: any; quantity: number; notes: string; unitPrice: number }>>([]);
  const [orderType, setOrderType] = useState<"DINE_IN" | "TAKEAWAY">('DINE_IN');
  const [tableNumber, setTableNumber] = useState('04');
  const [customerName, setCustomerName] = useState('');

  // Checkout modal state
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'CASH' | 'QR_PAY' | 'CARD'>('CASH');
  const [amountTendered, setAmountTendered] = useState('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [successOrder, setSuccessOrder] = useState<any | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [catRes, prodRes] = await Promise.all([
        api.getCategories(),
        api.getProducts()
      ]);
      setCategories(catRes);
      setProducts(prodRes);
      if (catRes.length > 0) {
        setSelectedCategory(catRes[0].id);
      }
    } catch (err) {
      console.error('Failed to load POS data from API, using fallback defaults', err);
      const fallbackCats = [
        { id: 1, name: 'Cà phê truyền thống', display_order: 1 },
        { id: 2, name: 'Cà phê máy & Espresso', display_order: 2 },
        { id: 3, name: 'Trà trái cây & Cold Brew', display_order: 3 },
        { id: 4, name: 'Bánh ngọt & Snack', display_order: 4 }
      ];
      const fallbackProds = [
        { id: 1, category_id: 1, name: 'Cà phê sữa đá Sài Gòn', price: 35000, is_available: true, image_url: '' },
        { id: 2, category_id: 1, name: 'Cà phê đen đá nguyên chất', price: 30000, is_available: true, image_url: '' },
        { id: 3, category_id: 2, name: 'Espresso Double Shot', price: 45000, is_available: true, image_url: '' },
        { id: 4, category_id: 2, name: 'Cappuccino Ý', price: 55000, is_available: true, image_url: '' },
        { id: 5, category_id: 3, name: 'Trà đào cam sả', price: 50000, is_available: true, image_url: '' },
        { id: 6, category_id: 3, name: 'Cold Brew hoa quả', price: 60000, is_available: true, image_url: '' },
        { id: 7, category_id: 4, name: 'Bánh sừng bò bơ Pháp (Croissant)', price: 38000, is_available: true, image_url: '' },
        { id: 8, category_id: 4, name: 'Bánh tiramisu cacao', price: 48000, is_available: true, image_url: '' }
      ];
      setCategories(fallbackCats);
      setProducts(fallbackProds);
      setSelectedCategory(1);
    }
  };

  const handleAddToCart = (product: any) => {
    setCartItems(prev => {
      const existing = prev.find(item => item.product.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prev, { product, quantity: 1, notes: '', unitPrice: product.price }];
    });
  };

  const updateQuantity = (productId: number, delta: number) => {
    setCartItems(prev =>
      prev
        .map(item => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as any[]
    );
  };

  const removeItem = (productId: number) => {
    setCartItems(prev => prev.filter(item => item.product.id !== productId));
  };

  const subtotal = cartItems.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);
  const vat = Math.round(subtotal * 0.1);
  const totalAmount = subtotal + vat;

  const numericTendered = parseFloat(amountTendered.replace(/\D/g, '')) || 0;
  const changeDue = numericTendered >= totalAmount ? numericTendered - totalAmount : 0;

  const handleOpenCheckout = () => {
    if (cartItems.length === 0) return;
    setAmountTendered(totalAmount.toString());
    setCheckoutError(null);
    setIsCheckoutOpen(true);
  };

  const handleConfirmCheckout = async () => {
    if (numericTendered < totalAmount) {
      setCheckoutError('INSUFFICIENT_PAYMENT: Số tiền khách đưa chưa đủ thanh toán tổng đơn hàng.');
      return;
    }
    setCheckoutLoading(true);
    setCheckoutError(null);
    try {
      const orderPayload = {
        order_type: orderType,
        table_number: orderType === 'DINE_IN' ? tableNumber : undefined,
        customer_name: customerName || 'Khách lẻ',
        items: cartItems.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          notes: item.notes || undefined
        }))
      };

      const createdOrder = await api.createOrder(orderPayload);

      const idempKey = `pos-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const checkoutPayload = {
        payment_method: paymentMethod,
        amount_paid: numericTendered,
        amount_tendered: numericTendered,
        idempotency_key: idempKey
      };

      const checkoutRes = await api.updateOrderStatus(createdOrder.id, 'PAID');
      setSuccessOrder({ ...createdOrder, checkout: checkoutRes });
      setIsCheckoutOpen(false);
      setCartItems([]);
    } catch (err: any) {
      console.error('Checkout error:', err);
      setCheckoutError(err.response?.data?.detail || 'Thanh toán thất bại. Vui lòng thử lại.');
    } finally {
      setCheckoutLoading(false);
    }
  };

  const filteredProducts = products.filter(p => {
    const matchesCat = selectedCategory ? p.category_id === selectedCategory : true;
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const formatVND = (amount: number) => {
    return amount.toLocaleString('vi-VN') + ' ₫';
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-on-background font-sans">
      <aside className="w-20 bg-surface-container flex flex-col items-center justify-between py-6 border-r border-outline-variant/30 z-10">
        <div className="flex flex-col items-center gap-8">
          <div className="w-12 h-12 rounded-2xl bg-primary text-on-primary flex items-center justify-center shadow-md">
            <span className="material-symbols-outlined text-[28px]">local_cafe</span>
          </div>
          <nav className="flex flex-col gap-4">
            <a href="/pos" className="w-12 h-12 rounded-xl bg-primary-container text-on-primary-container flex items-center justify-center shadow-sm" title="Bán hàng POS">
              <span className="material-symbols-outlined">point_of_sale</span>
            </a>
            <a href="/dashboard" className="w-12 h-12 rounded-xl text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center transition" title="Tổng quan">
              <span className="material-symbols-outlined">dashboard</span>
            </a>
            <a href="/orders" className="w-12 h-12 rounded-xl text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center transition" title="Đơn hàng">
              <span className="material-symbols-outlined">receipt_long</span>
            </a>
            <a href="/products" className="w-12 h-12 rounded-xl text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center transition" title="Thực đơn">
              <span className="material-symbols-outlined">restaurant_menu</span>
            </a>
            <a href="/inventory" className="w-12 h-12 rounded-xl text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center transition" title="Kho hàng">
              <span className="material-symbols-outlined">inventory_2</span>
            </a>
            <a href="/reports" className="w-12 h-12 rounded-xl text-on-surface-variant hover:bg-surface-container-high flex items-center justify-center transition" title="Báo cáo doanh thu">
              <span className="material-symbols-outlined">bar_chart</span>
            </a>
          </nav>
        </div>
        <div className="flex flex-col items-center gap-4">
          <button onClick={() => { localStorage.clear(); window.location.href = '/login'; }} className="w-12 h-12 rounded-xl text-error hover:bg-error-container/20 flex items-center justify-center transition" title="Đăng xuất">
            <span className="material-symbols-outlined">logout</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col h-full overflow-hidden bg-background">
        <header className="h-20 bg-surface-container-lowest border-b border-outline-variant/20 px-8 flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1 max-w-lg">
            <div className="relative w-full">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
              <input
                type="text"
                placeholder="Tìm kiếm đồ uống, món ăn..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-surface-container-low border border-outline-variant/40 rounded-xl text-on-surface focus:outline-none focus:border-primary transition text-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 bg-surface-container-low px-4 py-2 rounded-xl border border-outline-variant/30">
              <div className="w-9 h-9 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                NV
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-semibold text-on-surface">Thu ngân 01</span>
                <span className="text-[10px] text-on-surface-variant">Ca sáng (06:00 - 14:00)</span>
              </div>
            </div>
          </div>
        </header>

        <div className="px-8 py-4 bg-surface-container-low border-b border-outline-variant/20 flex items-center gap-3 overflow-x-auto">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-5 py-2.5 rounded-xl font-medium text-sm transition whitespace-nowrap shadow-sm flex items-center gap-2 ${
                selectedCategory === cat.id
                  ? 'bg-primary text-on-primary shadow-md'
                  : 'bg-surface-container-lowest text-on-surface hover:bg-surface-container'
              }`}
            >
              <span>{cat.name}</span>
            </button>
          ))}
        </div>

        <div className="flex-1 p-8 overflow-y-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filteredProducts.map(product => (
              <div
                key={product.id}
                onClick={() => handleAddToCart(product)}
                className="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl p-4 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-primary/50 transition group"
              >
                <div className="w-full h-36 bg-surface-container rounded-xl mb-4 flex items-center justify-center text-primary group-hover:scale-105 transition duration-300 overflow-hidden relative">
                  <span className="material-symbols-outlined text-[48px]">local_cafe</span>
                  <div className="absolute top-2 right-2 bg-surface-container-lowest/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-bold text-primary shadow-sm">
                    {formatVND(product.price)}
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <h3 className="font-semibold text-on-surface text-base line-clamp-1">{product.name}</h3>
                  <p className="text-xs text-on-surface-variant">Sẵn sàng phục vụ</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <aside className="w-[420px] bg-surface-container-lowest border-l border-outline-variant/30 flex flex-col h-full shadow-2xl z-10">
        <div className="p-6 border-b border-outline-variant/20 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">receipt</span>
              <span>Đơn hàng hiện tại</span>
            </h2>
            <button
              onClick={() => setCartItems([])}
              className="text-xs text-error hover:underline font-medium"
            >
              Xóa tất cả
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 bg-surface-container p-1 rounded-xl">
            <button
              onClick={() => setOrderType('DINE_IN')}
              className={`py-2 rounded-lg text-xs font-semibold transition ${
                orderType === 'DINE_IN'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Tại bàn (Dine-in)
            </button>
            <button
              onClick={() => setOrderType('TAKEAWAY')}
              className={`py-2 rounded-lg text-xs font-semibold transition ${
                orderType === 'TAKEAWAY'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Mang đi (Takeaway)
            </button>
          </div>

          {orderType === 'DINE_IN' && (
            <div className="flex items-center gap-3">
              <label className="text-xs font-medium text-on-surface-variant whitespace-nowrap">Số bàn:</label>
              <input
                type="text"
                value={tableNumber}
                onChange={e => setTableNumber(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/30 rounded-xl px-3 py-1.5 text-sm font-semibold text-on-surface text-center"
              />
            </div>
          )}

          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-on-surface-variant whitespace-nowrap">Khách hàng:</label>
            <input
              type="text"
              placeholder="Tên khách hàng (mặc định Khách lẻ)"
              value={customerName}
              onChange={e => setCustomerName(e.target.value)}
              className="w-full bg-surface-container border border-outline-variant/30 rounded-xl px-3 py-1.5 text-sm text-on-surface"
            />
          </div>
        </div>

        <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-4">
          {cartItems.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-on-surface-variant gap-2 py-12">
              <span className="material-symbols-outlined text-[48px] text-outline">shopping_cart</span>
              <p className="text-sm font-medium">Chưa có món trong đơn hàng</p>
              <p className="text-xs text-outline">Chọn món từ thực đơn bên trái để thêm vào đơn</p>
            </div>
          ) : (
            cartItems.map(item => (
              <div key={item.product.id} className="bg-surface-container/50 border border-outline-variant/20 rounded-xl p-3 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-on-surface">{item.product.name}</span>
                  <button
                    onClick={() => removeItem(item.product.id)}
                    className="text-outline hover:text-error transition"
                  >
                    <span className="material-symbols-outlined text-[18px]">close</span>
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-primary">{formatVND(item.unitPrice * item.quantity)}</span>
                  <div className="flex items-center gap-2 bg-surface-container-lowest border border-outline-variant/30 rounded-lg px-2 py-1">
                    <button
                      onClick={() => updateQuantity(item.product.id, -1)}
                      className="w-5 h-5 flex items-center justify-center text-on-surface hover:bg-surface-container rounded"
                    >
                      -
                    </button>
                    <span className="text-xs font-bold px-1">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.product.id, 1)}
                      className="w-5 h-5 flex items-center justify-center text-on-surface hover:bg-surface-container rounded"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-6 border-t border-outline-variant/20 bg-surface-container-low flex flex-col gap-3">
          <div className="flex justify-between text-xs text-on-surface-variant">
            <span>Tạm tính</span>
            <span>{formatVND(subtotal)}</span>
          </div>
          <div className="flex justify-between text-xs text-on-surface-variant">
            <span>Thuế VAT (10%)</span>
            <span>{formatVND(vat)}</span>
          </div>
          <div className="flex justify-between text-base font-bold text-on-surface pt-2 border-t border-outline-variant/20">
            <span>Tổng cộng</span>
            <span className="text-primary">{formatVND(totalAmount)}</span>
          </div>
          <button
            onClick={handleOpenCheckout}
            disabled={cartItems.length === 0}
            className={`w-full py-3.5 rounded-xl font-bold text-sm shadow-lg flex items-center justify-center gap-2 transition ${
              cartItems.length === 0
                ? 'bg-outline/20 text-outline cursor-not-allowed'
                : 'bg-primary text-on-primary hover:opacity-90'
            }`}
          >
            <span className="material-symbols-outlined">payments</span>
            <span>Thanh toán đơn hàng</span>
          </button>
        </div>
      </aside>

      {isCheckoutOpen && (
        <div className="fixed inset-0 bg-surface/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest max-w-md w-full rounded-2xl shadow-2xl border border-outline-variant/30 p-6 flex flex-col gap-6 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-4">
              <h3 className="text-lg font-bold text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">point_of_sale</span>
                <span>Thanh toán & Idempotency</span>
              </h3>
              <button
                onClick={() => setIsCheckoutOpen(false)}
                className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="flex flex-col gap-4">
              <div className="bg-primary-container/20 p-4 rounded-xl border border-primary/20 flex flex-col gap-1">
                <span className="text-xs text-on-surface-variant">Tổng tiền cần thanh toán</span>
                <span className="text-2xl font-bold text-primary">{formatVND(totalAmount)}</span>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-on-surface-variant">Phương thức thanh toán</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => setPaymentMethod('CASH')}
                    className={`py-3 rounded-xl font-semibold text-xs border transition flex flex-col items-center gap-1 ${
                      paymentMethod === 'CASH'
                        ? 'bg-primary text-on-primary border-primary shadow-sm'
                        : 'bg-surface-container-low text-on-surface border-outline-variant/30'
                    }`}
                  >
                    <span className="material-symbols-outlined">payments</span>
                    <span>Tiền mặt (Cash)</span>
                  </button>
                  <button
                    onClick={() => setPaymentMethod('QR_PAY')}
                    className={`py-3 rounded-xl font-semibold text-xs border transition flex flex-col items-center gap-1 ${
                      paymentMethod === 'QR_PAY'
                        ? 'bg-primary text-on-primary border-primary shadow-sm'
                        : 'bg-surface-container-low text-on-surface border-outline-variant/30'
                    }`}
                  >
                    <span className="material-symbols-outlined">qr_code_2</span>
                    <span>Mã QR</span>
                  </button>
                  <button
                    onClick={() => setPaymentMethod('CARD')}
                    className={`py-3 rounded-xl font-semibold text-xs border transition flex flex-col items-center gap-1 ${
                      paymentMethod === 'CARD'
                        ? 'bg-primary text-on-primary border-primary shadow-sm'
                        : 'bg-surface-container-low text-on-surface border-outline-variant/30'
                    }`}
                  >
                    <span className="material-symbols-outlined">credit_card</span>
                    <span>Thẻ / Card</span>
                  </button>
                </div>
              </div>

              {paymentMethod === 'CASH' && (
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold text-on-surface-variant">Số tiền khách đưa (VND)</label>
                  <input
                    type="text"
                    value={amountTendered}
                    onChange={e => setAmountTendered(e.target.value)}
                    className="bg-surface-container border border-outline-variant/30 rounded-xl px-4 py-3 text-lg font-bold text-on-surface focus:outline-none focus:border-primary"
                    placeholder="Nhập số tiền..."
                  />
                  <div className="flex items-center justify-between text-xs font-medium text-on-surface-variant mt-1">
                    <span>Tiền thối lại (Change):</span>
                    <span className="font-bold text-primary text-base">{formatVND(changeDue)}</span>
                  </div>
                </div>
              )}

              {checkoutError && (
                <div className="bg-error-container/20 border border-error/30 text-error p-3 rounded-xl text-xs font-medium">
                  {checkoutError}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-outline-variant/20">
              <button
                onClick={() => setIsCheckoutOpen(false)}
                className="px-5 py-2.5 rounded-xl font-semibold text-xs text-on-surface-variant hover:bg-surface-container"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleConfirmCheckout}
                disabled={checkoutLoading}
                className="px-6 py-2.5 rounded-xl font-bold text-xs bg-primary text-on-primary hover:opacity-90 shadow-md flex items-center gap-2"
              >
                {checkoutLoading && <span className="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>}
                <span>Xác nhận thanh toán</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {successOrder && (
        <div className="fixed inset-0 bg-surface/85 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container-lowest max-w-sm w-full rounded-2xl shadow-2xl border border-outline-variant/30 p-6 flex flex-col items-center text-center gap-4 animate-in fade-in zoom-in duration-200">
            <div className="w-16 h-16 rounded-full bg-primary/20 text-primary flex items-center justify-center shadow-inner">
              <span className="material-symbols-outlined text-[36px]">check_circle</span>
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-lg font-bold text-on-surface">Thanh toán thành công!</h3>
              <p className="text-xs text-on-surface-variant">Đơn hàng #{successOrder.id} đã được ghi nhận và in hóa đơn.</p>
            </div>
            <div className="bg-surface-container w-full p-4 rounded-xl flex flex-col gap-2 text-left">
              <div className="flex justify-between text-xs">
                <span className="text-on-surface-variant">Hình thức:</span>
                <span className="font-semibold text-on-surface">{successOrder.checkout?.payment_method}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-on-surface-variant">Tổng thanh toán:</span>
                <span className="font-bold text-primary">{formatVND(successOrder.total_amount)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-on-surface-variant">Tiền thối lại:</span>
                <span className="font-bold text-on-surface">{formatVND(successOrder.checkout?.change_due || 0)}</span>
              </div>
            </div>
            <button
              onClick={() => setSuccessOrder(null)}
              className="w-full py-3 rounded-xl font-bold text-sm bg-primary text-on-primary shadow-md hover:opacity-90 transition mt-2"
            >
              Tiếp tục bán hàng
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
