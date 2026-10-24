import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const backendUrl = env.VITE_BACKEND_URL;
  const healthProxy = backendUrl
    ? {
        '/api/health': {
          target: backendUrl,
          changeOrigin: true,
          rewrite: () => '/health',
        },
      }
    : undefined;

  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      proxy: healthProxy,
    },
    preview: {
      host: '127.0.0.1',
      proxy: healthProxy,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
      css: true,
    },
  };
});
