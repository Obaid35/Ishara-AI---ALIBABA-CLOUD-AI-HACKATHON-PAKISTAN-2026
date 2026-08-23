/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // The API runs on localhost:8000. Proxying keeps the browser on one
    // origin and keeps the whole demo free of any cross-origin surprises.
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" },
      { source: "/media/:path*", destination: "http://127.0.0.1:8000/media/:path*" },
    ];
  },
};
export default nextConfig;
