import { mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";
import { defineConfig } from "vitest/config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    },
  }),
);
