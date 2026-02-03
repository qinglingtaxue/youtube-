#!/usr/bin/env python3
"""
Vercel Serverless Function Entry Point

将完整的 api_server.py FastAPI 应用暴露给 Vercel
"""

import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量标识 Vercel 环境
os.environ.setdefault('VERCEL', '1')

# 尝试导入完整的 API 服务器
try:
    from src.api_server import app
except Exception as e:
    # 如果导入失败，创建一个简单的错误响应应用
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI()

    error_msg = str(e)
    error_tb = traceback.format_exc()

    @app.get("/api/health")
    async def health_error():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application import failed",
                "message": error_msg,
                "traceback": error_tb,
                "env": {
                    "DATABASE_URL_SET": bool(os.environ.get("DATABASE_URL")),
                    "VERCEL": os.environ.get("VERCEL"),
                }
            }
        )

    @app.get("/api/{path:path}")
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application import failed",
                "message": error_msg,
                "path": path
            }
        )
