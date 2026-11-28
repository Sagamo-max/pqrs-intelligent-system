import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const srcDir = decodeURIComponent(new URL('./src', import.meta.url).pathname).replace(
  /^\/([A-Za-z]:)/,
  '$1',
);

export default defineConfig({
  base: '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': srcDir,
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('recharts') || id.includes('d3-')) {
              return 'charts';
            }
            if (id.includes('@tanstack/react-query') || id.includes('axios')) {
              return 'query';
            }
            if (
              id.includes('react-hook-form') ||
              id.includes('@hookform/resolvers') ||
              id.includes('/zod/')
            ) {
              return 'forms';
            }
            if (id.includes('@radix-ui/')) {
              return 'radix';
            }
            if (
              id.includes('react-dom') ||
              id.includes('react-router') ||
              id.includes('/react/') ||
              id.includes('/scheduler/')
            ) {
              return 'react-vendor';
            }
          }
          return undefined;
        },
      },
    },
  },
});
