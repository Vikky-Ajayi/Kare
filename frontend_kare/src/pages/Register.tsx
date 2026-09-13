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

  const field = 'input-field w-full';

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8 selection:bg-primary selection:text-primary-ink">
      <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="flex flex-col items-center mb-10">
          <Link to="/" className="w-16 h-16 rounded-3xl bg-ink flex items-center justify-center text-primary mb-7 hover:-translate-y-1 transition-transform">
            <Activity size={32} />
          </Link>
          <div className="text-xs font-semibold text-primary-ink/70 mb-2 tracking-wide">Kare Health</div>
          <h1 className="text-4xl text-center">Create account<span className="text-primary-ink">.</span></h1>
        </div>

        <div className="card">
          <form onSubmit={handleRegister} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-ink/50 ml-1">First name</label>
                <input type="text" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className={field} />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-ink/50 ml-1">Last name</label>
                <input type="text" required value={lastName} onChange={(e) => setLastName(e.target.value)} className={field} />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-ink/50 ml-1">Email</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-ink/50 ml-1">Preferred language</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value as LangCode)}
                className={`${field} appearance-none`}>
                {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-ink/50 ml-1">Password</label>
                <div className="relative">
                  <input type={show ? 'text' : 'password'} required value={password} onChange={(e) => setPassword(e.target.value)}
                    className={`${field} pr-11`} />
                  <button type="button" onClick={() => setShow(!show)} className="absolute right-4 top-1/2 -translate-y-1/2 text-ink/30 hover:text-primary-ink">
                    {show ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-ink/50 ml-1">Confirm</label>
                <input type={show ? 'text' : 'password'} required value={confirm} onChange={(e) => setConfirm(e.target.value)}
                  className={field} />
              </div>
            </div>
            <button type="submit" disabled={isLoading}
              className="btn-primary w-full py-4 group disabled:opacity-50 min-h-[44px]">
              <span className="text-sm">{isLoading ? 'Creating…' : 'Create account'}</span>
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
            {error && (
              <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                className="text-red-600 text-sm text-center">{error}</motion.p>
            )}
          </form>
        </div>

        <div className="flex flex-col items-center mt-8 space-y-4">
          <p className="text-ink/40 text-sm">
            Already have an account? <Link to="/login" className="text-primary-ink font-semibold hover:underline">Sign in →</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
