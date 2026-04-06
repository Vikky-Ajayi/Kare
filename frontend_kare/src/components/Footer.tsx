import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="py-32 px-8 border-t-4 border-white/10 bg-black">
      <div className="max-w-[1800px] mx-auto flex flex-col md:flex-row justify-between items-start gap-20">
        <div className="space-y-8">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary flex items-center justify-center border-2 border-black">
              <div className="w-6 h-6 border-2 border-black"></div>
            </div>
            <span className="font-display text-4xl font-bold tracking-tighter uppercase">Kare</span>
          </Link>
          <p className="text-white/20 text-xs font-bold uppercase tracking-[0.3em] max-w-xs leading-relaxed">
            Empowering Africa through accessible, AI-driven healthcare solutions. Available 24/7.
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-20 w-full md:w-auto">
          <div className="space-y-6">
            <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary">Platform</div>
            <div className="flex flex-col gap-4 text-[10px] font-bold uppercase tracking-widest text-white/40">
              <Link to="/features" className="hover:text-white transition-colors">Features</Link>
              <a href="#" className="hover:text-white transition-colors">Security</a>
              <a href="#" className="hover:text-white transition-colors">Mobile App</a>
            </div>
          </div>
          <div className="space-y-6">
            <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary">Company</div>
            <div className="flex flex-col gap-4 text-[10px] font-bold uppercase tracking-widest text-white/40">
              <Link to="/about" className="hover:text-white transition-colors">About Us</Link>
              <a href="#" className="hover:text-white transition-colors">Careers</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
          <div className="space-y-6">
            <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary">Legal</div>
            <div className="flex flex-col gap-4 text-[10px] font-bold uppercase tracking-widest text-white/40">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-[1800px] mx-auto mt-32 pt-12 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-8">
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">
          © 2026 KARE HEALTH TECH. ALL RIGHTS RESERVED.
        </div>
        <div className="flex gap-8">
          {['TW', 'IG', 'LI', 'FB'].map(social => (
            <a key={social} href="#" className="w-10 h-10 border border-white/10 flex items-center justify-center text-[10px] font-bold hover:bg-primary hover:text-black hover:border-primary transition-all">
              {social}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
};

export default Footer;
