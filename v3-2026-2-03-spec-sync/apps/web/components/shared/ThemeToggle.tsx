'use client'

import { useTheme } from '@/components/providers/ThemeProvider'
import { Button } from '@/components/ui/button'
import { Moon, Sun } from 'lucide-react'
import { useState, useEffect } from 'react'

export function ThemeToggle() {
  const { theme, setTheme, isDark } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // 避免 hydration mismatch
  if (!mounted) {
    return <div className="w-10 h-10" />
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => {
        setTheme(isDark ? 'light' : 'dark')
      }}
      className="rounded-full"
      title={`切换到${isDark ? '浅色' : '暗色'}模式`}
    >
      {isDark ? (
        <Sun className="w-5 h-5" />
      ) : (
        <Moon className="w-5 h-5" />
      )}
      <span className="sr-only">切换主题</span>
    </Button>
  )
}
