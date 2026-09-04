/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Pin the file-tracing root. Next 15 otherwise infers it from the nearest
  // lockfile, which can resolve outside the repo and produce a wrong
  // standalone bundle.
  outputFileTracingRoot: __dirname,
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
