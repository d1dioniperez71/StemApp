import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Servidor de desarrollo atado a 127.0.0.1 (privacidad por diseño).
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173 },
});
