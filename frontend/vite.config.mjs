import react from '@vitejs/plugin-react';

/** @type { import('vite').UserConfig } */
export default {
  root: ".",
  publicDir: "public",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
  },
  plugins: [
    react(), // Now this is a standard function call
  ],
};