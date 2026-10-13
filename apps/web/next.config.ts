import type { NextConfig } from "next";

const config: NextConfig = {
  output: "standalone", poweredByHeader: false,
  async headers() {
    return [{
      source: "/:locale/admin/:path*",
      headers: [
        { key: "Cache-Control", value: "no-store, private" },
        { key: "Pragma", value: "no-cache" },
        { key: "Referrer-Policy", value: "no-referrer" },
      ],
    }];
  },
};
export default config;
