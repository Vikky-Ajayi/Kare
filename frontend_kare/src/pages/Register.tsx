import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ArrowRight, Activity, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { auth, errMsg } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { LANGUAGES, type LangCode } from '../types';

const Register = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [language, setLanguage] = useState<LangCode>('en');
  const [show, setShow] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) return setError('Passwords do not match');
    if (password.length < 8) return setError('Password must be at least 8 characters');
    setIsLoading(true);
    try {
      const { user, access_token, refresh_token } = await auth.register({
        email, password, first_name: firstName, last_name: lastName, preferred_language: language,
      });
      setAuth(user, access_token, refresh_token);
      navigate('/dashboard');
    } catch (err) {
      setError(errMsg(err, 'Could not create your account.'));
    } finally {
      setIsLoading(false);
    }
  };

  const field = 'brutalist-input w-full focus:border-primary transition-colors';

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-8 selection:bg-primary selection:text-black">
      <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="flex flex-col items-center mb-12">
          <Link to="/" className="w-20 h-20 bg-primary border-4 border-black flex items-center justify-center text-black mb-8 shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] hover:-translate-y-1 transition-transform">
            <Activity size={40} />
          </Link>
          <div className="text-[10px] font-bold uppercase tracking-[0.5em] text-primary mb-2">Kare Health</div>
          <h1 className="text-5xl font-display font-bold text-white uppercase tracking-tighter text-center">Create Account<span className="text-primary">.</span></h1>
        </div>

        <div className="brutalist-card bg-surface border-2 border-white/10 p-10">
          <form onSubmit={handleRegister} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">First name</label>
                <input type="text" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className={field} style={{ textTransform: 'none' }} />
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Last name</label>
                <input type="text" required value={lastName} onChange={(e) => setLastName(e.target.value)} className={field} style={{ textTransform: 'none' }} />
              </div>
            </div>
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={field} style={{ textTransform: 'none' }} />
            </div>
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Preferred language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value as LangCode)}
                className={`${field} appearance-none bg-surface`}>
                {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Password</label>
                <div className="relative">
                  <input type={show ? 'text' : 'password'} required value={password} onChange={(e) => setPassword(e.target.value)}
                    className={`${field} pr-12`} style={{ textTransform: 'none' }} />
                  <button type="button" onClick={() => setShow(!show)} className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-primary">
                    {show ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Confirm</label>
                <input type={show ? 'text' : 'password'} required value={confirm} onChange={(e) => setConfirm(e.target.value)}
                  className={field} style={{ textTransform: 'none' }} />
              </div>
            </div>
            <button type="submit" disabled={isLoading}
              className="btn-primary w-full py-5 flex items-center justify-center gap-4 group disabled:opacity-50 min-h-[44px]">
              <span className="text-sm font-bold uppercase tracking-[0.3em]">{isLoading ? 'Creating…' : 'Create Account'}</span>
              <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" />
            </button>
            {error && (
              <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                className="text-red-500 text-[10px] font-bold uppercase tracking-widest text-center">{error}</motion.p>
            )}
          </form>
        </div>

        <div className="flex flex-col items-center mt-10 space-y-5">
          <p className="text-white/20 text-[10px] font-bold uppercase tracking-widest">
            Already have an account? <Link to="/login" className="text-primary hover:underline">Sign in →</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
