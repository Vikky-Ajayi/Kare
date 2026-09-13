import React from 'react';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="py-20 px-6 md:px-8 bg-sand/40 border-t border-ink/8">
      <div className="max-w-[1400px] mx-auto flex flex-col md:flex-row justify-between items-start gap-16">
        <div className="space-y-6 max-w-xs">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-ink flex items-center justify-center">
              <Activity size={18} className="text-primary" />
            </div>
            <span className="font-display text-2xl font-bold text-ink">Kare</span>
          </Link>
          <p className="text-ink/45 text-sm leading-relaxed">
            A voice-first health companion for Nigeria — code-switched, memory-keeping, available any time.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-12 w-full md:w-auto">
          <div className="space-y-4">
            <div className="text-xs font-semibold text-primary-ink/80 uppercase tracking-wide">Platform</div>
            <div className="flex flex-col gap-3 text-sm text-ink/50">
              <Link to="/features" className="hover:text-ink transition-colors">Features</Link>
              <a href="#" className="hover:text-ink transition-colors">Security</a>
            </div>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-semibold text-primary-ink/80 uppercase tracking-wide">Company</div>
            <div className="flex flex-col gap-3 text-sm text-ink/50">
              <Link to="/about" className="hover:text-ink transition-colors">About us</Link>
              <Link to="/impact" className="hover:text-ink transition-colors">Impact</Link>
            </div>
          </div>
          <div className="space-y-4">
            <div className="text-xs font-semibold text-primary-ink/80 uppercase tracking-wide">Legal</div>
            <div className="flex flex-col gap-3 text-sm text-ink/50">
              <a href="#" className="hover:text-ink transition-colors">Privacy policy</a>
              <a href="#" className="hover:text-ink transition-colors">Terms</a>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-[1400px] mx-auto mt-16 pt-8 border-t border-ink/10 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="text-sm text-ink/35">
          © 2026 Kare Health. All rights reserved.
        </div>
        <div className="flex gap-3">
          {['TW', 'IG', 'LI'].map((social) => (
            <a key={social} href="#" className="w-10 h-10 rounded-full border border-ink/15 flex items-center justify-center text-xs font-semibold text-ink/50 hover:bg-primary hover:text-primary-ink hover:border-primary transition-all">
              {social}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
