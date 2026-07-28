/** @type {import('next').NextConfig} */
const webApiOrigin = (
  process.env.WEB_API_ORIGIN ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(webApiOrigin)) {
  throw new Error(
    "WEB_API_ORIGIN must use an explicit http://127.0.0.1:<port> loopback origin in Phase 0.6"
  );
}

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${webApiOrigin}/api/v1/:path*`
      }
    ];
  }
};

export default nextConfig;
