import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ArrowRight, Activity, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { auth, errMsg } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const { user, access_token, refresh_token } = await auth.login({ email, password });
      setAuth(user, access_token, refresh_token);
      navigate('/dashboard');
    } catch (err) {
      setError(errMsg(err, 'Could not sign you in.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8 selection:bg-primary selection:text-primary-ink">
      <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="flex flex-col items-center mb-12">
          <Link to="/" className="w-16 h-16 rounded-3xl bg-ink flex items-center justify-center text-primary mb-7 hover:-translate-y-1 transition-transform">
            <Activity size={32} />
          </Link>
          <div className="text-xs font-semibold text-primary-ink/70 mb-2 tracking-wide">Kare Health</div>
          <h1 className="text-4xl text-center">Welcome back<span className="text-primary-ink">.</span></h1>
          <p className="text-ink/40 text-sm mt-3">Your health companion, always there</p>
        </div>

        <div className="card">
          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-ink/50 ml-1">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-field w-full" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-ink/50 ml-1">Password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} required value={password}
                  onChange={(e) => setPassword(e.target.value)} placeholder="••••••••"
                  className="input-field w-full pr-14" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-5 top-1/2 -translate-y-1/2 text-ink/30 hover:text-primary-ink transition-colors">
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={isLoading}
              className="btn-primary w-full py-4 group disabled:opacity-50 min-h-[44px]">
              <span className="text-sm">{isLoading ? 'Signing in…' : 'Sign in'}</span>
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
            {error && (
              <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                className="text-red-600 text-sm text-center">{error}</motion.p>
            )}
          </form>
        </div>

        <div className="flex flex-col items-center mt-10 space-y-4">
          <p className="text-ink/40 text-sm">
            New here? <Link to="/register" className="text-primary-ink font-semibold hover:underline">Create an account →</Link>
          </p>
          <Link to="/" className="text-ink/30 text-sm hover:text-ink transition-colors">Return home</Link>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
