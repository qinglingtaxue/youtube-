'use client'

import { ReactNode, Component } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
  fallback?: (error: Error, reset: () => void) => ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error('错误已捕获:', error, errorInfo)
  }

  private reset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError && this.state.error) {
      return (
        this.props.fallback?.(this.state.error, this.reset) || (
          <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950">
            <div className="max-w-md mx-auto text-center p-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold mb-2">出错了</h1>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                抱歉，页面加载出现问题
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mb-6 p-3 bg-gray-100 dark:bg-gray-900 rounded break-all">
                {this.state.error.message}
              </p>
              <div className="flex gap-3 justify-center">
                <Button onClick={this.reset}>重新加载</Button>
                <Button
                  variant="outline"
                  onClick={() => window.location.href = '/'}
                >
                  返回首页
                </Button>
              </div>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}
