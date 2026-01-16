/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    // Proxy API calls to backend - uses internal Docker network name 'api'
    const apiDestination = process.env.API_INTERNAL_URL || 'http://api:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiDestination}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
