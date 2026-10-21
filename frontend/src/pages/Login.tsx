import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Login({ onLoginSuccess }: { onLoginSuccess?: (token: string, role: string) => void }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState('cashier1');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(username, password);
      if (res && res.access_token) {
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('coffeeflow_token', res.access_token);
        localStorage.setItem('user_role', res.role || 'CASHIER');
        localStorage.setItem('coffeeflow_role', res.role || 'CASHIER');
        if (onLoginSuccess) {
          onLoginSuccess(res.access_token, res.role || 'CASHIER');
        }
        if (res.role === 'MANAGER') {
          navigate('/dashboard');
        } else {
          navigate('/pos');
        }
      } else {
        setError('Đăng nhập không thành công. Vui lòng kiểm tra lại thông tin.');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      const detailMsg = err.response?.data?.detail || err.message || 'Sai tài khoản hoặc mật khẩu.';
      setError(detailMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-background px-4 font-sans">
      <div className="w-full max-w-md bg-surface-container-lowest rounded-3xl shadow-2xl border border-outline-variant/30 p-8 flex flex-col gap-8">
        {/* Header & Logo */}
        <div className="flex flex-col items-center text-center gap-3">
          <div className="w-16 h-16 rounded-2xl bg-primary text-on-primary flex items-center justify-center shadow-lg">
            <span className="material-symbols-outlined text-[36px]">local_cafe</span>
          </div>
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold text-on-surface tracking-tight">CoffeeFlow POS</h1>
            <p className="text-xs text-on-surface-variant">Hệ thống quản lý quán cà phê Artisan Operational Craft</p>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-on-surface-variant">Tên đăng nhập (Username)</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">person</span>
              <input
                type="text"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-surface-container-low border border-outline-variant/40 rounded-xl text-on-surface text-sm focus:outline-none focus:border-primary transition"
                placeholder="Nhập tên đăng nhập..."
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-on-surface-variant">Mật khẩu (Password)</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">lock</span>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-surface-container-low border border-outline-variant/40 rounded-xl text-on-surface text-sm focus:outline-none focus:border-primary transition"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <div className="bg-error-container/20 border border-error/30 text-error p-3 rounded-xl text-xs font-medium text-center">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl font-bold text-sm bg-primary text-on-primary shadow-lg hover:opacity-90 transition flex items-center justify-center gap-2 mt-2"
          >
            {loading && <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>}
            <span>Đăng nhập hệ thống</span>
          </button>
        </form>

        {/* Quick Demo Creds Helper */}
        <div className="flex flex-col gap-2 pt-4 border-t border-outline-variant/20 text-center">
          <span className="text-[11px] text-on-surface-variant font-medium">Tài khoản mẫu nhanh:</span>
          <div className="flex justify-center gap-3">
            <button
              type="button"
              onClick={() => { setUsername('cashier1'); setPassword('password123'); }}
              className="px-3 py-1.5 rounded-lg bg-surface-container text-xs font-semibold text-primary hover:bg-surface-container-high transition"
            >
              Thu ngân (Cashier)
            </button>
            <button
              type="button"
              onClick={() => { setUsername('manager1'); setPassword('password123'); }}
              className="px-3 py-1.5 rounded-lg bg-surface-container text-xs font-semibold text-primary hover:bg-surface-container-high transition"
            >
              Quản lý (Manager)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
