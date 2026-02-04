'use client'

import { useState, useCallback } from 'react'
import { X } from 'lucide-react'

export type ToastType = 'info' | 'success' | 'error' | 'warning'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType, duration?: number) => void
  removeToast: (id: string) => void
}

export const useToast = (() => {
  let listeners: Array<(state: ToastContextType) => void> = []
  let state: ToastContextType = {
    toasts: [],
    addToast: function(message: string, type: ToastType = 'info', duration: number = 3000) {
      const id = `${Date.now()}-${Math.random()}`
      this.toasts = [...this.toasts, { id, message, type }]
      notifyListeners()

      if (duration > 0) {
        setTimeout(() => this.removeToast(id), duration)
      }
    },
    removeToast: function(id: string) {
      this.toasts = this.toasts.filter(t => t.id !== id)
      notifyListeners()
    },
  }

  const notifyListeners = () => {
    listeners.forEach(listener => listener(state))
  }

  return {
    subscribe: (listener: (state: ToastContextType) => void) => {
      listeners.push(listener)
      return () => {
        listeners = listeners.filter(l => l !== listener)
      }
    },
    getState: () => state,
    addToast: (message: string, type: ToastType = 'info', duration?: number) => {
      state.addToast(message, type, duration)
    },
    removeToast: (id: string) => {
      state.removeToast(id)
    },
  }
})()

export function Toast({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const bgColor = {
    info: 'bg-blue-500',
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-yellow-500',
  }[toast.type]

  return (
    <div className={`${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between gap-3 animate-slide-up`}>
      <span className="text-sm">{toast.message}</span>
      <button
        onClick={onClose}
        className="flex-shrink-0 hover:opacity-80 transition"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([])

  // 监听 toast 状态变化
  useCallback(() => {
    useToast.subscribe((state) => {
      setToasts(state.toasts)
    })
  }, [])

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none">
      {toasts.map(toast => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            toast={toast}
            onClose={() => useToast.removeToast(toast.id)}
          />
        </div>
      ))}
    </div>
  )
}
