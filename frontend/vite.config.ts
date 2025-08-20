import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      build: {
        outDir: 'dist',
        sourcemap: false,
        minify: 'terser',
        rollupOptions: {
          output: {
            manualChunks: {
              vendor: ['react', 'react-dom'],
            },
          },
        },
      },
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY || ''),
        // Expose VITE_* environment variables to the client
        'import.meta.env.VITE_APP_NAME': JSON.stringify(env.VITE_APP_NAME || 'code.fisamy.work'),
        'import.meta.env.VITE_APP_VERSION': JSON.stringify(env.VITE_APP_VERSION || '1.0.0'),
        'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || ''),
        'import.meta.env.VITE_CODER_ACCESS_URL': JSON.stringify(env.VITE_CODER_ACCESS_URL || ''),
        'import.meta.env.VITE_CHECKOUT_SOLO': JSON.stringify(env.VITE_CHECKOUT_SOLO || ''),
        'import.meta.env.VITE_CHECKOUT_PRO': JSON.stringify(env.VITE_CHECKOUT_PRO || ''),
        'import.meta.env.VITE_CHECKOUT_TEAM': JSON.stringify(env.VITE_CHECKOUT_TEAM || ''),
        'import.meta.env.VITE_ENABLE_ANALYTICS':
          JSON.stringify(env.VITE_ENABLE_ANALYTICS || 'false'),
        'import.meta.env.VITE_ANALYTICS_ID': JSON.stringify(env.VITE_ANALYTICS_ID || ''),
        'import.meta.env.VITE_ENABLE_AI_FEATURES': JSON.stringify(env.VITE_ENABLE_AI_FEATURES || 'true'),
        'import.meta.env.VITE_ENABLE_TEAM_FEATURES': JSON.stringify(env.VITE_ENABLE_TEAM_FEATURES || 'true'),
        'import.meta.env.VITE_ENABLE_GPU_WORKSPACES': JSON.stringify(env.VITE_ENABLE_GPU_WORKSPACES || 'false')
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      }
    };
});
