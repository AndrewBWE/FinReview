import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/pipeline": "http://localhost:8000",
      "/schemas": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/deals": "http://localhost:8000",
      "/folders": "http://localhost:8000",
    },
  },
});
