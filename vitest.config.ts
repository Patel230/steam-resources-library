import { defineConfig } from "vitest/config";
import path from "path";

const templateRoot = path.resolve(import.meta.dirname);

export default defineConfig({
  root: templateRoot,
  resolve: {
    alias: {
      "@": path.resolve(templateRoot, "apps/web/src"),
      "@shared": path.resolve(templateRoot, "packages/shared"),
    },
  },
  test: {
    environment: "node",
    include: [
      "apps/api/**/*.test.ts",
      "apps/api/**/*.spec.ts",
      "apps/web/**/*.test.ts",
      "apps/web/**/*.spec.ts",
    ],
  },
});
