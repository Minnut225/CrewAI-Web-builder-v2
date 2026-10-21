import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<{ username: string; role: string; full_name?: string }>({
    username: 'Quản lý',
    role: localStorage.getItem('user_role') || 'MANAGER',
    full_name: 'Nguyễn Mai Lan'
  });

  useEffect(() => {
    // Try to load current user profile from /auth/me
    api.getCurrentUser()
      .then((data) => {
        if (data) {
          setUser({
            username: data.username,
            role: data.role,
            full_name: data.full_name || (data.role === 'MANAGER' ? 'Nguyễn Mai Lan' : 'Trần Thu Ngân')
          });
        }
      })
      .catch(() => {
        const storedRole = localStorage.getItem('user_role') || 'MANAGER';
        setUser({
          username: storedRole === 'MANAGER' ? 'manager' : 'cashier',
          role: storedRole,
          full_name: storedRole === 'MANAGER' ? 'Nguyễn Mai Lan' : 'Trần Thu Ngân'
        });
      });
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-space-md px-space-md py-space-sm rounded-lg transition-colors font-title-md text-title-md ${
      isActive
        ? 'bg-primary text-on-primary font-semibold shadow-sm'
        : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
    }`;

  const sidebarContent = (
    <div className="flex flex-col h-full justify-between">
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="px-space-lg py-space-lg flex items-center justify-between border-b border-outline-variant/20">
          <div className="flex items-center gap-space-md min-w-0">
            <div className="w-10 h-10 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow-md flex-shrink-0">
              <span className="material-symbols-outlined text-[24px]">local_cafe</span>
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-headline-sm text-headline-sm text-primary tracking-tight font-bold truncate">CoffeeFlow</span>
              <span className="font-label-sm text-label-sm text-on-surface-variant truncate">Chi nhánh 01 - Đặng Văn Ngữ</span>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1 rounded-lg text-on-surface-variant hover:bg-surface-container-high"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          )}
        </div>

        {/* Section 1: Vận hành & Bán hàng */}
        <div className="px-space-md py-space-xs mt-3">
          <span className="px-space-sm font-label-sm text-label-sm uppercase text-outline tracking-wider font-semibold">
            Vận hành &amp; Bán hàng
          </span>
          <nav className="mt-space-xs flex flex-col gap-space-2xs">
            <NavLink to="/dashboard" className={navItemClass}>
              <span className="material-symbols-outlined text-[20px]">dashboard</span>
              <span>Tổng quan</span>
            </NavLink>

            <NavLink to="/pos" className={navItemClass}>
              <div className="flex items-center gap-space-md min-w-0 flex-1">
                <span className="material-symbols-outlined text-[20px]">point_of_sale</span>
                <span className="truncate">Bán hàng (POS)</span>
              </div>
              <span className="bg-secondary-container text-on-secondary-container font-label-sm text-label-sm px-space-sm py-space-2xs rounded-full font-bold">
                Thu ngân
              </span>
            </NavLink>

            <NavLink to="/orders" className={navItemClass}>
              <span className="material-symbols-outlined text-[20px]">receipt_long</span>
              <span>Đơn hàng</span>
            </NavLink>
          </nav>
        </div>

        {/* Section 2: Quản trị cửa hàng */}
        <div className="px-space-md pt-space-md mt-2">
          <span className="px-space-sm font-label-sm text-label-sm uppercase text-outline tracking-wider font-semibold">
            Quản trị cửa hàng
          </span>
          <nav className="mt-space-xs flex flex-col gap-space-2xs">
            <NavLink to="/products" className={navItemClass}>
              <span className="material-symbols-outlined text-[20px]">coffee</span>
              <span>Sản phẩm &amp; Thực đơn</span>
            </NavLink>

            <NavLink to="/inventory" className={navItemClass}>
              <span className="material-symbols-outlined text-[20px]">inventory_2</span>
              <span>Kho nguyên liệu</span>
            </NavLink>

            <NavLink to="/reports" className={navItemClass}>
              <span className="material-symbols-outlined text-[20px]">bar_chart</span>
              <span>Báo cáo doanh thu</span>
            </NavLink>
          </nav>
        </div>
      </div>

      {/* Footer / User Profile & Logout */}
      <div className="p-space-md border-t border-outline-variant/30 flex flex-col gap-3 bg-surface-container-low/80">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-full bg-secondary text-on-primary flex items-center justify-center font-bold text-sm shadow-sm flex-shrink-0">
            {user.full_name ? user.full_name.charAt(0) : 'U'}
          </div>
          <div className="flex flex-col min-w-0 flex-1">
            <span className="text-sm font-semibold text-on-surface truncate">{user.full_name}</span>
            <span className="text-xs text-on-surface-variant font-medium">
              {user.role === 'MANAGER' ? 'Quản lý cửa hàng' : 'Nhân viên thu ngân'}
            </span>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-space-md py-space-xs text-sm font-medium text-error hover:bg-error-container/30 rounded-lg transition-colors w-full"
        >
          <span className="material-symbols-outlined text-[20px]">logout</span>
          <span>Đăng xuất</span>
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-72 bg-surface-container-low shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex-col justify-between overflow-y-auto border-r border-outline-variant/30">
        {sidebarContent}
      </aside>

      {/* Mobile Sidebar Overlay & Drawer */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-primary/40 backdrop-blur-sm transition-opacity"
            onClick={onClose}
          />
          <aside className="relative flex-1 flex flex-col max-w-xs w-full bg-surface-container-low h-full shadow-2xl z-50 overflow-y-auto">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
