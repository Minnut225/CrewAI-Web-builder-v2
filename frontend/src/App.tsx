import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import CashierPOS from './pages/CashierPOS';
import ManagerDashboard from './pages/ManagerDashboard';
import OrdersManagement from './pages/OrdersManagement';
import ProductsMenu from './pages/ProductsMenu';
import InventoryStock from './pages/InventoryStock';
import ReportsRevenue from './pages/ReportsRevenue';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Login Route */}
        <Route path="/login" element={<Login />} />
        
        {/* Dedicated High-Performance Cashier POS */}
        <Route path="/pos" element={<CashierPOS />} />
        
        {/* Core Management & Operations Routes with Shared Sidebar & Layout */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<ManagerDashboard />} />
          <Route path="/orders" element={<OrdersManagement />} />
          <Route path="/products" element={<ProductsMenu />} />
          <Route path="/menu" element={<Navigate to="/products" replace />} />
          <Route path="/inventory" element={<InventoryStock />} />
          <Route path="/reports" element={<ReportsRevenue />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
