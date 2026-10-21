import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface HeaderProps {
  onToggleMobileMenu?: () => void;
}

export default function Header({ onToggleMobileMenu }: HeaderProps) {
  const location = useLocation();

  const getPageInfo = () => {
    switch (location.pathname) {
      case '/dashboard':
        return { title: 'Tổng quan', subtitle: 'Bảng điều khiển hoạt động quán' };
      case '/orders':
        return { title: 'Đơn hàng', subtitle: 'Quản lý đơn hàng & giao dịch' };
      case '/products':
      case '/menu':
        return { title: 'Sản phẩm', subtitle: 'Thực đơn & thiết lập món' };
      case '/inventory':
        return { title: 'Kho nguyên liệu', subtitle: 'Theo dõi tồn kho & định lượng' };
      case '/reports':
        return { title: 'Báo cáo', subtitle: 'Thống kê doanh thu & hiệu suất' };
      default:
        return { title: 'Hệ thống', subtitle: 'CoffeeFlow Management' };
    }
  };

  const { title } = getPageInfo();

  return (
    <header className="fixed top-0 left-0 lg:left-72 right-0 h-16 bg-surface/85 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-outline-variant/30 z-40 flex items-center justify-between px-4 sm:px-6">
      {/* Left: Mobile Toggle & Breadcrumb */}
      <div className="flex items-center gap-3 sm:gap-4">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-lg text-on-surface hover:bg-surface-container-high transition-colors"
          aria-label="Mở menu"
        >
          <span className="material-symbols-outlined text-[24px]">menu</span>
        </button>

        <div className="flex items-center gap-2 text-body-sm">
          <span className="text-outline font-medium hidden sm:inline">CoffeeFlow</span>
          <span className="text-outline-variant hidden sm:inline">/</span>
          <span className="font-semibold text-primary">{title}</span>
        </div>

        <div className="hidden md:block h-4 w-px bg-outline-variant"></div>

        <div className="hidden md:inline-flex items-center gap-2 bg-surface-container-high px-3 py-1 rounded-full">
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
          <span className="font-label-sm text-label-sm text-on-surface font-medium">
            Ca sáng (06:30 - 14:30) • Đang mở
          </span>
        </div>
      </div>

      {/* Right: Quick actions & POS Shortcut */}
      <div className="flex items-center gap-3">
        <Link
          to="/pos"
          className="inline-flex items-center gap-2 bg-primary text-on-primary hover:bg-primary-container px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-sm sm:text-title-md font-semibold transition-all shadow-sm active:scale-95"
        >
          <span className="material-symbols-outlined text-[18px]">point_of_sale</span>
          <span className="hidden sm:inline">Bán hàng (POS)</span>
          <span className="sm:hidden">POS</span>
          <span className="hidden md:inline bg-surface-container-high/20 px-1.5 py-0.5 rounded text-[10px] text-primary-fixed-dim font-bold ml-1">
            F1
          </span>
        </Link>
      </div>
    </header>
  );
}
