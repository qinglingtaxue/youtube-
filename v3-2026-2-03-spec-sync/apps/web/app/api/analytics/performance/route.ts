import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const data = await request.json()

    // 记录性能数据（在生产环境中应该存储到数据库）
    console.log('Performance metric received:', {
      timestamp: new Date().toISOString(),
      ...data,
      userAgent: request.headers.get('user-agent'),
      url: data.url || request.referrer,
    })

    // 在生产环境中，可以将这些数据发送到：
    // 1. 数据库存储
    // 2. 分析服务 (Google Analytics, Datadog, New Relic 等)
    // 3. 自定义 BI 系统

    return NextResponse.json(
      { success: true, message: 'Performance metric recorded' },
      { status: 200 }
    )
  } catch (error) {
    console.error('Failed to record performance metric:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to record metric' },
      { status: 500 }
    )
  }
}
