import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-[1800px] mx-auto px-8 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary flex items-center justify-center border-2 border-black">
              <div className="w-5 h-5 border-2 border-black"></div>
            </div>
            <span className="font-display text-2xl font-bold tracking-tighter uppercase">Kare</span>
          </Link>
          
          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-12 text-[10px] font-bold uppercase tracking-[0.3em]">
            <Link to="/features" className="hover:text-primary transition-colors relative group">
              Features
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
            </Link>
            <Link to="/about" className="hover:text-primary transition-colors relative group">
              About
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
            </Link>
            <Link to="/impact" className="hover:text-primary transition-colors relative group">
              Impact
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
            </Link>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <Link to="/login" className="text-[10px] font-bold uppercase tracking-[0.3em] hover:text-primary transition-colors">Login</Link>
            <Link to="/register" className="bg-white text-black px-8 py-3 text-[10px] font-bold uppercase tracking-[0.3em] hover:bg-primary transition-all border-2 border-black hover:-translate-y-1 active:translate-y-0 min-h-[44px] flex items-center">Get Started</Link>
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            onClick={() => setIsMenuOpen(true)}
            className="md:hidden w-12 h-12 flex items-center justify-center border-2 border-white/10 hover:border-primary transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>
      </nav>

      {/* Mobile Menu Drawer */}
      <AnimatePresence>
        {isMenuOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMenuOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
            />
            <motion.div 
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-[300px] bg-black border-l-4 border-white/10 z-[70] p-12 flex flex-col"
            >
              <button 
                onClick={() => setIsMenuOpen(false)}
                className="self-end w-12 h-12 flex items-center justify-center border-2 border-white/10 hover:border-primary transition-colors mb-16"
              >
                <X className="w-6 h-6" />
              </button>
              <div className="flex flex-col gap-12 text-sm font-bold uppercase tracking-[0.4em]">
                <Link to="/features" onClick={() => setIsMenuOpen(false)} className="hover:text-primary transition-colors">Features</Link>
                <Link to="/about" onClick={() => setIsMenuOpen(false)} className="hover:text-primary transition-colors">About</Link>
                <Link to="/impact" onClick={() => setIsMenuOpen(false)} className="hover:text-primary transition-colors">Impact</Link>
                <div className="h-px bg-white/10 my-4"></div>
                <Link to="/login" onClick={() => setIsMenuOpen(false)} className="hover:text-primary transition-colors">Login</Link>
                <Link to="/register" onClick={() => setIsMenuOpen(false)} className="bg-white text-black p-6 text-center hover:bg-primary transition-all border-2 border-black">Get Started</Link>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar;
