/** @type {import('next').NextConfig} */
const nextConfig = {
  // 启用严格模式
  reactStrictMode: true,

  // 图片优化
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'i.ytimg.com',
      },
      {
        protocol: 'https',
        hostname: 'yt3.googleapis.com',
      },
    ],
  },

  // 性能优化
  productionBrowserSourceMaps: false,

  // 重定向和重写
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: '/api/:path*',
        },
      ],
    }
  },

  // 自定义 Webpack - 代码分割优化
  webpack: (config, { isServer }) => {
    config.optimization = config.optimization || {}
    config.optimization.splitChunks = config.optimization.splitChunks || {}

    // 启用代码分割缓存组
    config.optimization.splitChunks.cacheGroups = {
      ...config.optimization.splitChunks.cacheGroups,
      // 第三方库分割
      vendor: {
        test: /[\\/]node_modules[\\/]/,
        name: 'vendors',
        priority: 10,
        reuseExistingChunk: true,
      },
      // UI 组件库分割
      ui: {
        test: /[\\/]node_modules[\\/](lucide-react|@radix-ui)[\\/]/,
        name: 'ui-libs',
        priority: 20,
        reuseExistingChunk: true,
      },
      // 共享组件分割
      common: {
        minChunks: 2,
        priority: 5,
        reuseExistingChunk: true,
      },
    }

    return config
  },
}

export default nextConfig
