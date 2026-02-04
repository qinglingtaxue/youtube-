'use client'

import Link from 'next/link'
import dynamic from 'next/dynamic'
import { Button } from '@/components/ui/button'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'

// 动态导入 ThemeToggle，不进行 SSR，避免 context 错误
const ThemeToggle = dynamic(() => import('./ThemeToggle').then(mod => ({ default: mod.ThemeToggle })), {
  ssr: false,
  loading: () => <div className="w-10 h-10" />
})

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <span className="text-primary">📊</span>
            <span className="hidden sm:inline">YouTube 竞品分析</span>
          </Link>

          {/* 桌面导航 */}
          <div className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="text-gray-600 dark:text-gray-400 hover:text-primary transition"
            >
              首页
            </Link>
          </div>

          {/* 右侧按钮 */}
          <div className="flex items-center gap-2">
            <ThemeToggle />

            {/* 移动菜单按钮 */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden"
            >
              {isOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </Button>
          </div>
        </div>

        {/* 移动菜单 */}
        {isOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-gray-800 py-4 space-y-2 animate-slide-up">
            <Link
              href="/"
              className="block px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-primary hover:bg-gray-50 dark:hover:bg-gray-800 rounded transition"
              onClick={() => setIsOpen(false)}
            >
              首页
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
