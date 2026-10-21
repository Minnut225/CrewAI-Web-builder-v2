import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Product, Category } from '../types';

export default function ProductsMenu() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState<number>(1);
  const [price, setPrice] = useState<number>(35000);
  const [costPrice, setCostPrice] = useState<number>(10000);
  const [description, setDescription] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [catRes, prodRes] = await Promise.all([
        api.getCategories(),
        api.getProducts()
      ]);
      setCategories(catRes);
      setProducts(prodRes);
      if (catRes.length > 0) setCategoryId(catRes[0].id);
    } catch (err: any) {
      console.warn('Backend offline, using fallback products/categories', err);
      const mockCats: Category[] = [
        { id: 1, name: 'Cà Phê Truyền Thống', display_order: 1 },
        { id: 2, name: 'Cà Phê Máy (Espresso)', display_order: 2 },
        { id: 3, name: 'Trà Sữa & Trà Trái Cây', display_order: 3 },
      ];
      const mockProds: Product[] = [
        { id: 1, category_id: 1, name: 'Cà Phê Sữa Đá', price: 35000, cost_price: 10000, is_active: true, description: 'Cà phê rang xay đậm đà kết hợp sữa đặc ngọt' },
        { id: 2, category_id: 1, name: 'Cà Phê Đen Đá', price: 30000, cost_price: 8000, is_active: true, description: 'Cà phê đen nguyên chất đá mát lạnh' },
        { id: 3, category_id: 2, name: 'Cappuccino', price: 55000, cost_price: 18000, is_active: true, description: 'Espresso thơm béo với lớp bọt sữa mịn màng' },
      ];
      setCategories(mockCats);
      setProducts(mockProds);
      setCategoryId(mockCats[0].id);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAddModal = () => {
    setEditingProduct(null);
    setName('');
    setPrice(35000);
    setCostPrice(10000);
    setDescription('');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (prod: Product) => {
    setEditingProduct(prod);
    setName(prod.name);
    setCategoryId(prod.category_id);
    setPrice(prod.price);
    setCostPrice(prod.cost_price || 10000);
    setDescription(prod.description || '');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        await api.updateProduct(editingProduct.id, {
          name,
          category_id: Number(categoryId),
          price: Number(price),
          cost_price: Number(costPrice),
          description
        });
        alert('Cập nhật món thành công!');
      } else {
        await api.createProduct({
          name,
          category_id: Number(categoryId),
          price: Number(price),
          cost_price: Number(costPrice),
          description,
          is_active: true
        });
        alert('Thêm món mới thành công!');
      }
      setIsModalOpen(false);
      await fetchData();
    } catch (err: any) {
      alert('Lỗi lưu sản phẩm: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-container-high p-6 rounded-2xl border border-outline-variant/30 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow-md">
            <span className="material-symbols-outlined text-2xl">restaurant_menu</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-primary">Quản Lý Thực Đơn & Sản Phẩm</h1>
            <p className="text-xs text-on-surface-variant">Cấu hình danh mục, món nước và giá bán chuẩn</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchData}
            className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container text-primary hover:bg-surface-container-highest text-sm font-semibold transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
            <span>Làm mới</span>
          </button>
          <button 
            onClick={handleOpenAddModal}
            className="flex items-center space-x-2 px-5 py-2.5 bg-primary hover:bg-primary-container text-on-primary rounded-xl shadow-md transition-all font-semibold text-sm"
          >
            <span className="material-symbols-outlined text-lg">add</span>
            <span>Thêm Món Mới</span>
          </button>
        </div>
      </div>

      <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/30 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-outline-variant/20 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-lg text-primary">Danh Sách Món Trong Thực Đơn</h3>
            <p className="text-xs text-on-surface-variant">Tất cả sản phẩm hiển thị trực tiếp trên giao diện Thu Ngân POS</p>
          </div>
        </div>

            {loading ? (
              <div className="p-12 text-center text-[#88512A]">Đang tải thực đơn...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#F5EFE6] text-xs font-bold text-[#88512A] uppercase tracking-wider border-b border-[#88512A]/20">
                      <th className="py-4 px-6">ID</th>
                      <th className="py-4 px-6">Tên Sản Phẩm</th>
                      <th className="py-4 px-6">Danh Mục</th>
                      <th className="py-4 px-6">Giá Bán (VNĐ)</th>
                      <th className="py-4 px-6">Giá Vốn (VNĐ)</th>
                      <th className="py-4 px-6">Trạng Thái</th>
                      <th className="py-4 px-6 text-right">Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#88512A]/10 text-sm">
                    {products.map((prod) => {
                      const cat = categories.find(c => c.id === prod.category_id);
                      return (
                        <tr key={prod.id} className="hover:bg-[#F5EFE6]/30 transition-colors">
                          <td className="py-4 px-6 font-semibold text-[#88512A]">#{prod.id}</td>
                          <td className="py-4 px-6 font-bold text-[#220F05]">
                            <div className="flex items-center space-x-2">
                              <span className="material-symbols-outlined text-base text-[#88512A]">local_cafe</span>
                              <span>{prod.name}</span>
                            </div>
                            {prod.description && <p className="text-xs text-[#88512A] mt-0.5">{prod.description}</p>}
                          </td>
                          <td className="py-4 px-6 text-[#88512A] font-medium">{cat?.name || 'Chưa phân loại'}</td>
                          <td className="py-4 px-6 font-extrabold text-[#220F05]">
                            {prod.price.toLocaleString('vi-VN')} ₫
                          </td>
                          <td className="py-4 px-6 text-[#88512A]">
                            {prod.cost_price ? `${prod.cost_price.toLocaleString('vi-VN')} ₫` : '0 ₫'}
                          </td>
                          <td className="py-4 px-6">
                            <span className="inline-flex items-center space-x-1 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold shadow-sm">
                              <span className="material-symbols-outlined text-xs">check_circle</span>
                              <span>Đang bán</span>
                            </span>
                          </td>
                          <td className="py-4 px-6 text-right">
                            <button
                              onClick={() => handleOpenEditModal(prod)}
                              className="px-3 py-1.5 bg-[#88512A]/10 hover:bg-[#88512A]/20 text-[#88512A] rounded-xl text-xs font-bold transition-all"
                            >
                              Chỉnh sửa
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

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#FDFBF7] rounded-3xl max-w-lg w-full p-8 border border-[#88512A]/30 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-[#88512A]/20 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-[#88512A] text-white flex items-center justify-center">
                  <span className="material-symbols-outlined">restaurant_menu</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg text-[#220F05]">
                    {editingProduct ? 'Chỉnh Sửa Món Nước' : 'Thêm Món Nước Mới'}
                  </h3>
                  <p className="text-xs text-[#88512A]">Cập nhật thông tin chi tiết sản phẩm</p>
                </div>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="w-8 h-8 rounded-full bg-[#88512A]/10 hover:bg-[#88512A]/20 text-[#88512A] flex items-center justify-center font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Tên Sản Phẩm</label>
                <input 
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-bold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                  required
                  placeholder="Ví dụ: Cà Phê Muối"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Danh Mục</label>
                <select 
                  value={categoryId}
                  onChange={(e) => setCategoryId(Number(e.target.value))}
                  className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-medium focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Giá Bán (VNĐ)</label>
                  <input 
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(Number(e.target.value))}
                    className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-bold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                    required
                    min={0}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Giá Vốn (VNĐ)</label>
                  <input 
                    type="number"
                    value={costPrice}
                    onChange={(e) => setCostPrice(Number(e.target.value))}
                    className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-bold focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                    required
                    min={0}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#88512A] uppercase mb-1">Mô Tả Chi Tiết</label>
                <textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#88512A]/30 bg-white text-[#220F05] font-medium focus:outline-none focus:ring-2 focus:ring-[#88512A]"
                  rows={3}
                  placeholder="Mô tả thành phần hoặc hương vị..."
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#88512A]/20">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl border border-[#88512A]/30 text-[#88512A] hover:bg-[#88512A]/10 font-semibold text-sm transition-all"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  className="px-6 py-2.5 rounded-xl bg-[#88512A] hover:bg-[#6e4121] text-white font-bold text-sm shadow-md transition-all flex items-center space-x-2"
                >
                  <span className="material-symbols-outlined text-base">check</span>
                  <span>{editingProduct ? 'Cập Nhật Món' : 'Tạo Món Mới'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
