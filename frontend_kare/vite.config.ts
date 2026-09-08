import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_');
  return {
    plugins: [react(), tailwindcss()],
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
        env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
      ),
    },
    resolve: { alias: { '@': path.resolve(__dirname, './src') } },
    server: { port: 3000, host: '0.0.0.0' },
    preview: { port: 3000, host: '0.0.0.0' },
  };
});
