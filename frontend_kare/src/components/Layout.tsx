import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

const Layout = () => {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  React.useEffect(() => setOpen(false), [loc.pathname]);

  return (
    <div className="min-h-screen bg-black text-white">
      <div className={`fixed inset-y-0 left-0 z-50 transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar />
      </div>
      {open && <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />}

      <button onClick={() => setOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-30 w-10 h-10 bg-surface border-2 border-white/10 flex items-center justify-center text-white">
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>

      <div className="lg:ml-64">
        <TopBar />
        <main><Outlet /></main>
      </div>
    </div>
  );
};

export default Layout;
