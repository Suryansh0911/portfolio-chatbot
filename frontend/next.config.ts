/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // This tells Next.js to intercept any requests that start with /api-backend/
        source: '/api-backend/:path*',
        // And secretly forward them to your AWS server!
        destination: 'http://13.233.55.238:8000/:path*', // <-- Your exact AWS IP!
      },
    ]
  },
};

export default nextConfig;