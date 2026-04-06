import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Mail, Lock, ArrowRight, Activity, Github, Eye, EyeOff, User, Globe } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';

const Register = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [language, setLanguage] = useState('English');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setAuth = useAuthStore(state => state.setAuth);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    try {
      const response = await api.post('/auth/register', { 
        email, 
        password, 
        first_name: firstName, 
        last_name: lastName, 
        preferred_language: language 
      });
      const { user, access_token, refresh_token } = response.data;

      setAuth(user, access_token, refresh_token);
      navigate('/dashboard');
    } catch (err: any) {
      const message = err.response?.data?.detail || err.response?.data?.message || err.message || 'An unexpected error occurred. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-8 selection:bg-primary selection:text-black">
      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-xl"
      >
        <div className="flex flex-col items-center mb-16">
          <Link to="/" className="w-20 h-20 bg-primary border-4 border-black flex items-center justify-center text-black mb-8 shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] hover:-translate-y-1 transition-transform">
            <Activity size={40} />
          </Link>
          <div className="text-[10px] font-bold uppercase tracking-[0.5em] text-primary mb-2">Kare Health</div>
          <h1 className="text-6xl font-display font-bold text-white uppercase tracking-tighter">Create Identity<span className="text-primary">.</span></h1>
          <p className="text-white/20 text-xs font-bold uppercase tracking-[0.3em] mt-4">Join the future of healthcare</p>
        </div>

        <div className="brutalist-card bg-surface border-2 border-white/10 p-12">
          <form onSubmit={handleRegister} className="space-y-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">First Name</label>
                <div className="relative">
                  <input 
                    type="text" 
                    required
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="FIRST"
                    className="brutalist-input w-full focus:border-primary transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-4">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Last Name</label>
                <div className="relative">
                  <input 
                    type="text" 
                    required
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="LAST"
                    className="brutalist-input w-full focus:border-primary transition-colors"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Email Identifier</label>
              <div className="relative">
                <input 
                  type="email" 
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="USER@KARE.HEALTH"
                  className="brutalist-input w-full focus:border-primary transition-colors"
                />
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Preferred Language</label>
              <div className="relative">
                <select 
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="brutalist-input w-full appearance-none focus:border-primary transition-colors bg-surface"
                >
                  <option value="English">English</option>
                  <option value="Yoruba">Yoruba</option>
                  <option value="Hausa">Hausa</option>
                  <option value="Igbo">Igbo</option>
                  <option value="French">French</option>
                  <option value="Nigerian Pidgin">Nigerian Pidgin</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Security Key</label>
              <div className="relative">
                <input 
                  type={showPassword ? "text" : "password"} 
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="brutalist-input w-full pr-16 focus:border-primary transition-colors"
                  style={{ textTransform: 'none' }}
                />
                <button 
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-6 top-1/2 -translate-y-1/2 text-white/20 hover:text-primary transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-bold text-white/40 uppercase tracking-[0.3em] ml-1">Confirm Security Key</label>
              <div className="relative">
                <input 
                  type={showConfirmPassword ? "text" : "password"} 
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="brutalist-input w-full pr-16 focus:border-primary transition-colors"
                  style={{ textTransform: 'none' }}
                />
                <button 
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-6 top-1/2 -translate-y-1/2 text-white/20 hover:text-primary transition-colors"
                >
                  {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div className="space-y-6">
              <button 
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full py-6 flex items-center justify-center gap-4 group disabled:opacity-50 min-h-[44px]"
              >
                <span className="text-sm font-bold uppercase tracking-[0.3em]">
                  {isLoading ? "Creating Identity..." : "Create My Kare Account"}
                </span>
                <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" />
              </button>

              {error && (
                <motion.p 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-red-500 text-[10px] font-bold uppercase tracking-widest text-center"
                >
                  {error}
                </motion.p>
              )}
            </div>
          </form>

          <div className="mt-16 pt-12 border-t-2 border-white/5">
            <p className="text-center text-[10px] font-bold text-white/20 uppercase tracking-[0.5em] mb-10">External Providers</p>
            <div className="grid grid-cols-2 gap-6">
              <button className="flex items-center justify-center gap-4 py-4 bg-black border-2 border-white/10 hover:border-primary transition-all group min-h-[44px]">
                <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5 grayscale group-hover:grayscale-0" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">Google</span>
              </button>
              <button className="flex items-center justify-center gap-4 py-4 bg-black border-2 border-white/10 hover:border-primary transition-all group min-h-[44px]">
                <Github size={20} className="text-white grayscale group-hover:grayscale-0" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">GitHub</span>
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center mt-16 space-y-6">
          <p className="text-white/20 text-[10px] font-bold uppercase tracking-widest">
            Already have an account? <Link to="/login" className="text-primary hover:underline">Sign in →</Link>
          </p>
          <Link to="/" className="text-white/10 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-colors">
            Return Home
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default Register;
