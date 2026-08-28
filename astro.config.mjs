import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://yananzhou.me",
  base: "/stereopatch",
  trailingSlash: "always",
  output: "static",
  build: {
    assets: "assets",
  },
});
