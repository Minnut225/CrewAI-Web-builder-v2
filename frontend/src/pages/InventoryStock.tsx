import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Ingredient, InventoryMovement } from '../types';

export default function InventoryStockPage() {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [loading, setLoading] = useState(true);

  // Import Modal State
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [selectedIngredientId, setSelectedIngredientId] = useState<number>(0);
  const [importQty, setImportQty] = useState<number>(1000);
  const [importPrice, setImportPrice] = useState<number>(250);
  const [importNote, setImportNote] = useState<string>('');
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    loadInventoryData();
  }, []);

  const loadInventoryData = async () => {
    setLoading(true);
    try {
      const ings = await api.getIngredients();
      setIngredients(ings || []);
      const movs = await api.getInventoryMovements();
      setMovements(movs || []);
    } catch (err) {
      console.warn('API offline or error loading inventory, using fallback mock data', err);
      const mockIngs: Ingredient[] = [
        { id: 1, name: 'Hạt Cà Phê Arabica', unit: 'g', stock_quantity: 4500, min_threshold: 1000, cost_per_unit: 250, updated_at: new Date().toISOString() },
        { id: 2, name: 'Sữa Đặc Ngọt (Lon 1kg)', unit: 'lon', stock_quantity: 12, min_threshold: 5, cost_per_unit: 28000, updated_at: new Date().toISOString() },
        { id: 3, name: 'Sữa Tươi Tiệt Trùng (1L)', unit: 'lít', stock_quantity: 24, min_threshold: 10, cost_per_unit: 32000, updated_at: new Date().toISOString() },
        { id: 4, name: 'Đường Phèn / Đường Trắng', unit: 'g', stock_quantity: 8500, min_threshold: 2000, cost_per_unit: 25, updated_at: new Date().toISOString() },
        { id: 5, name: 'Bột Cacao Nguyên Chất', unit: 'g', stock_quantity: 650, min_threshold: 800, cost_per_unit: 180, updated_at: new Date().toISOString() },
      ];
      setIngredients(mockIngs);
      setMovements([
        { id: 101, ingredient_id: 1, movement_type: 'IMPORT', quantity: 5000, unit_price: 250, note: 'Nhập lô mới Arabica', created_at: new Date().toISOString(), ingredient_name: 'Hạt Cà Phê Arabica' },
        { id: 102, ingredient_id: 2, movement_type: 'IMPORT', quantity: 15, unit_price: 28000, note: 'Nhập sữa đặc', created_at: new Date().toISOString(), ingredient_name: 'Sữa Đặc Ngọt (Lon 1kg)' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIngredientId) return;
    setImporting(true);
    try {
      await api.importStock({
        ingredient_id: Number(selectedIngredientId),
        quantity: Number(importQty),
        unit_price: Number(importPrice),
        supplier_name: importNote || 'Nhà cung cấp chính',
        note: importNote
      });
      setIsImportModalOpen(false);
      setImportNote('');
      loadInventoryData();
      alert('Nhập kho thành công!');
    } catch (err: any) {
      console.error('Failed to import stock', err);
      alert('Lỗi nhập kho: ' + (err.response?.data?.detail || err.message));
    } finally {
      setImporting(false);
    }
  };

  const lowStockCount = ingredients.filter(i => (i.stock_quantity ?? 0) <= (i.min_threshold ?? 0)).length;

  return (
    <div className="space-y-6">
      {/* Header & Quick stats */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-surface p-6 rounded-2xl border border-[#88512A]/15 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2">
            <span className="material-symbols-outlined text-3xl text-caramel">inventory_2</span>
            Quản Lý Kho Nguyên Liệu
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Theo dõi tồn kho theo thời gian thực, cảnh báo nguyên liệu sắp hết và lịch sử xuất/nhập kho.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadInventoryData}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-caramel/30 bg-surface text-caramel hover:bg-caramel/10 font-semibold text-sm transition-all"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
            <span>Làm mới</span>
          </button>
          <button
            onClick={() => {
              if (ingredients.length > 0) setSelectedIngredientId(ingredients[0].id);
              setIsImportModalOpen(true);
            }}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-caramel hover:bg-caramel-hover text-on-primary font-bold text-sm shadow-md transition-all"
          >
            <span className="material-symbols-outlined text-lg">add_box</span>
            <span>Nhập Kho Mới</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-surface p-6 rounded-2xl border border-[#88512A]/15 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-on-surface-variant">Tổng Nguyên Liệu</span>
            <span className="material-symbols-outlined text-caramel bg-caramel/10 p-2 rounded-xl">category</span>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-primary">{ingredients.length}</span>
            <span className="text-xs font-medium text-success">Đang theo dõi</span>
          </div>
        </div>

        <div className="bg-surface p-6 rounded-2xl border border-[#88512A]/15 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-on-surface-variant">Cần Nhập Hàng Gấp</span>
            <span className="material-symbols-outlined text-error bg-error/10 p-2 rounded-xl">warning</span>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-error">{lowStockCount}</span>
            <span className="text-xs font-medium text-error">Dưới định mức tối thiểu</span>
          </div>
        </div>

        <div className="bg-surface p-6 rounded-2xl border border-[#88512A]/15 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-on-surface-variant">Lịch Sử Biến Động</span>
            <span className="material-symbols-outlined text-info bg-info/10 p-2 rounded-xl">history</span>
          </div>
          <div className="mt-4 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-primary">{movements.length}</span>
            <span className="text-xs font-medium text-on-surface-variant">Giao dịch gần đây</span>
          </div>
        </div>
      </div>

      {/* Main Table: Ingredients Inventory */}
      <div className="bg-surface rounded-2xl border border-[#88512A]/15 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-[#88512A]/10 flex items-center justify-between">
          <h2 className="font-bold text-primary text-lg flex items-center gap-2">
            <span className="material-symbols-outlined text-caramel">list_alt</span>
            Danh Sách Tồn Kho Nguyên Liệu
          </h2>
          <span className="text-xs text-on-surface-variant font-medium">Cập nhật tự động theo công thức bán hàng</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-on-surface-variant">Đang tải dữ liệu kho...</div>
        ) : ingredients.length === 0 ? (
          <div className="p-12 text-center text-on-surface-variant">Không tìm thấy nguyên liệu nào trong kho.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container border-b border-[#88512A]/10 text-xs font-bold text-primary uppercase tracking-wider">
                  <th className="px-6 py-3.5">Nguyên Liệu</th>
                  <th className="px-6 py-3.5">Tồn Hiện Tại</th>
                  <th className="px-6 py-3.5">Định Mức Tối Thiểu</th>
                  <th className="px-6 py-3.5">Đơn Giá Trung Bình</th>
                  <th className="px-6 py-3.5">Trạng Thái</th>
                  <th className="px-6 py-3.5 text-right">Thao Tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#88512A]/10">
                {ingredients.map((ing) => {
                  const cur = ing.stock_quantity ?? 0;
                  const min = ing.min_threshold ?? 0;
                  const isLow = cur <= min;
                  return (
                    <tr key={ing.id} className="hover:bg-surface-container-low transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-primary">
                        #{ing.id} {ing.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-on-surface-variant font-semibold">
                        {cur.toLocaleString()} {ing.unit}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-on-surface-variant">
                        {min.toLocaleString()} {ing.unit}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-on-surface-variant">
                        {(ing.cost_per_unit ?? 0).toLocaleString('vi-VN')} ₫
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {isLow ? (
                          <span className="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-error/15 text-error">
                            Cần nhập hàng
                          </span>
                        ) : (
                          <span className="px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-success/15 text-success">
                            Ổn định
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => {
                            setSelectedIngredientId(ing.id);
                            setImportPrice(ing.cost_per_unit || 1000);
                            setIsImportModalOpen(true);
                          }}
                          className="text-caramel hover:text-primary transition-colors bg-caramel/10 px-3 py-1.5 rounded-lg text-xs font-semibold"
                        >
                          Nhập thêm
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Movements Section */}
      <div className="bg-surface rounded-2xl border border-[#88512A]/15 shadow-sm overflow-hidden mt-6">
        <div className="px-6 py-4 border-b border-[#88512A]/10 flex items-center justify-between">
          <h2 className="font-bold text-primary text-lg flex items-center gap-2">
            <span className="material-symbols-outlined text-caramel">receipt_long</span>
            Lịch Sử Nhập / Xuất Kho Gần Đây
          </h2>
          <span className="text-xs text-on-surface-variant font-medium">Ghi nhận log kiểm toán kho</span>
        </div>
        {movements.length === 0 ? (
          <div className="p-8 text-center text-on-surface-variant text-sm">Chưa có lịch sử biến động kho.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container border-b border-[#88512A]/10 text-xs font-bold text-primary uppercase tracking-wider">
                  <th className="px-6 py-3">Mã GD</th>
                  <th className="px-6 py-3">Nguyên Liệu</th>
                  <th className="px-6 py-3">Loại Biến Động</th>
                  <th className="px-6 py-3">Số Lượng</th>
                  <th className="px-6 py-3">Đơn Giá</th>
                  <th className="px-6 py-3">Ghi Chú</th>
                  <th className="px-6 py-3">Thời Gian</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#88512A]/10 text-sm">
                {movements.map((m) => (
                  <tr key={m.id} className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-3 font-semibold text-primary">#{m.id}</td>
                    <td className="px-6 py-3 text-on-surface-variant font-medium">{m.ingredient_name || `ID #${m.ingredient_id}`}</td>
                    <td className="px-6 py-3">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        m.movement_type === 'IMPORT' ? 'bg-success/15 text-success' : 'bg-warning/15 text-warning'
                      }`}>
                        {m.movement_type === 'IMPORT' ? 'NHẬP KHO' : m.movement_type === 'EXPORT' ? 'XUẤT KHO' : 'ĐIỀU CHỈNH'}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-bold text-primary">
                      {m.movement_type === 'IMPORT' ? '+' : '-'}{m.quantity.toLocaleString()}
                    </td>
                    <td className="px-6 py-3 text-on-surface-variant">{(m.unit_price || 0).toLocaleString('vi-VN')} ₫</td>
                    <td className="px-6 py-3 text-on-surface-variant">{m.note || '---'}</td>
                    <td className="px-6 py-3 text-on-surface-variant text-xs">{new Date(m.created_at).toLocaleString('vi-VN')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Import Modal */}
      {isImportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-surface rounded-2xl max-w-md w-full p-6 border border-[#88512A]/20 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-[#88512A]/20 mb-4">
              <h3 className="text-lg font-bold text-primary flex items-center gap-2">
                <span className="material-symbols-outlined text-caramel">add_shopping_cart</span>
                Nhập Thêm Nguyên Liệu Vào Kho
              </h3>
              <button
                onClick={() => setIsImportModalOpen(false)}
                className="text-on-surface-variant hover:text-primary transition-colors"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Chọn Nguyên Liệu</label>
                <select
                  value={selectedIngredientId}
                  onChange={(e) => setSelectedIngredientId(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-semibold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                >
                  {ingredients.map((ing) => (
                    <option key={ing.id} value={ing.id}>
                      {ing.name} (Tồn: {ing.stock_quantity} {ing.unit})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Số Lượng Nhập</label>
                  <input
                    type="number"
                    value={importQty}
                    onChange={(e) => setImportQty(Number(e.target.value))}
                    className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-bold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                    required
                    min={1}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Đơn Giá Nhập (VNĐ)</label>
                  <input
                    type="number"
                    value={importPrice}
                    onChange={(e) => setImportPrice(Number(e.target.value))}
                    className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-bold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                    required
                    min={0}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Ghi Chú / Nhà Cung Cấp</label>
                <input
                  type="text"
                  value={importNote}
                  onChange={(e) => setImportNote(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-medium focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                  placeholder="Ví dụ: Nhập từ công ty Vinamilk"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#88512A]/20">
                <button
                  type="button"
                  onClick={() => setIsImportModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl border border-[#88512A]/30 text-[#88512A] hover:bg-[#88512A]/10 font-semibold text-sm transition-all"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  disabled={importing}
                  className="px-6 py-2.5 rounded-xl bg-[#88512A] hover:bg-[#6e4121] text-white font-bold text-sm shadow-md transition-all flex items-center space-x-2"
                >
                  {importing ? (
                    <span>Đang lưu...</span>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-base">check</span>
                      <span>Xác Nhận Nhập Kho</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
