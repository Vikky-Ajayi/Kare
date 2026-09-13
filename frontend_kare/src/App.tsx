import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import VoiceDoctor from './pages/VoiceDoctor';
import SymptomCheck from './pages/SymptomCheck';
import Medications from './pages/Medications';
import MedicalHistory from './pages/MedicalHistory';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Pregnancy from './pages/Pregnancy';
import Login from './pages/Login';
import Register from './pages/Register';
import Landing from './pages/Landing';
import About from './pages/About';
import Impact from './pages/Impact';
import Features from './pages/Features';
import { useAuthStore } from './store/useAuthStore';
import { auth } from './services/api';
import { registerServiceWorker } from './services/notifications';
import ScrollToTop from './components/ScrollToTop';
import UpdateToast from './components/UpdateToast';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setUser = useAuthStore((s) => s.setUser);

  useEffect(() => {
    registerServiceWorker();
  }, []);

  useEffect(() => {
    if (isAuthenticated) auth.me().then(setUser).catch(() => {});
  }, [isAuthenticated, setUser]);

  return (
    <BrowserRouter>
      <ScrollToTop />
      <UpdateToast />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/about" element={<About />} />
        <Route path="/impact" element={<Impact />} />
        <Route path="/features" element={<Features />} />

        <Route path="/dashboard" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="voice" element={<VoiceDoctor />} />
          <Route path="pregnancy" element={<Pregnancy />} />
          <Route path="symptoms" element={<SymptomCheck />} />
          <Route path="medications" element={<Medications />} />
          <Route path="history" element={<MedicalHistory />} />
          <Route path="profile" element={<Profile />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
