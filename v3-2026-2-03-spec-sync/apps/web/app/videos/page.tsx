'use client'

import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function VideosPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">视频列表</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          此页面正在开发中... (Phase 2)
        </p>
        <Button asChild>
          <Link href="/">返回首页</Link>
        </Button>
      </div>
    </div>
  )
}
