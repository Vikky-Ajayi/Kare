import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Link } from 'react-router-dom';
import { Menu, X, Activity } from 'lucide-react';
import InstallButton from './InstallButton';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b border-ink/8">
        <div className="max-w-[1400px] mx-auto px-6 md:px-8 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-ink flex items-center justify-center">
              <Activity size={18} className="text-primary" />
            </div>
            <span className="font-display text-xl font-bold text-ink">Kare</span>
          </Link>

          <div className="hidden md:flex items-center gap-10 text-sm font-medium text-ink/60">
            <Link to="/features" className="hover:text-ink transition-colors">Features</Link>
            <Link to="/about" className="hover:text-ink transition-colors">About</Link>
            <Link to="/impact" className="hover:text-ink transition-colors">Impact</Link>
          </div>

          <div className="hidden md:flex items-center gap-4">
            <InstallButton variant="nav" />
            <Link to="/login" className="text-sm font-semibold text-ink/70 hover:text-ink transition-colors">Log in</Link>
            <Link to="/register" className="btn-primary !py-3 !px-6 min-h-[44px]">Get started</Link>
          </div>

          <button
            onClick={() => setIsMenuOpen(true)}
            className="md:hidden w-11 h-11 rounded-full flex items-center justify-center bg-ink/5 text-ink hover:bg-ink/10 transition-colors"
          >
            <Menu size={20} />
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {isMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMenuOpen(false)}
              className="fixed inset-0 bg-ink/40 backdrop-blur-sm z-[60]"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-[300px] bg-surface z-[70] p-10 flex flex-col"
            >
              <button
                onClick={() => setIsMenuOpen(false)}
                className="self-end w-11 h-11 rounded-full flex items-center justify-center bg-ink/5 text-ink hover:bg-ink/10 transition-colors mb-14"
              >
                <X size={20} />
              </button>
              <div className="flex flex-col gap-8 text-lg font-display font-semibold text-ink">
                <Link to="/features" onClick={() => setIsMenuOpen(false)} className="hover:text-primary-ink transition-colors">Features</Link>
                <Link to="/about" onClick={() => setIsMenuOpen(false)} className="hover:text-primary-ink transition-colors">About</Link>
                <Link to="/impact" onClick={() => setIsMenuOpen(false)} className="hover:text-primary-ink transition-colors">Impact</Link>
                <div className="h-px bg-ink/10 my-2" />
                <InstallButton variant="nav" />
                <Link to="/login" onClick={() => setIsMenuOpen(false)} className="hover:text-primary-ink transition-colors">Log in</Link>
                <Link to="/register" onClick={() => setIsMenuOpen(false)} className="btn-primary justify-center">Get started</Link>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar;
