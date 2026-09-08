import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

const Layout = () => (
  <div className="min-h-screen bg-black text-white">
    <Sidebar />
    <div className="ml-64">
      <TopBar />
      <main>
        <Outlet />
      </main>
    </div>
  </div>
);

export default Layout;
