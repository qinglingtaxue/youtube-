# 全站框架技术栈分析

## 推荐架构
- **前端框架**：Next.js - https://github.com/vercel/next.js
- **样式框架**：Tailwind CSS - https://github.com/tailwindlabs/tailwindcss
- **UI 组件库**：shadcn/ui - https://github.com/shadcn-ui/ui
- **包管理器**：bun - https://bun.com
- **数据库**：PostgreSQL (本地) + Neon (云端) - https://neon.com
- **ORM**：Drizzle ORM - https://github.com/drizzle-team/drizzle-orm
- **认证**：Better Auth - https://www.better-auth.com
- **AI 框架**：Vercel AI SDK - https://ai-sdk.dev

## 当前项目缺口
项目当前使用 Fastify + 原生 Node.js，缺少：
1. 前端框架（无 Next.js）
2. UI 组件库（无 shadcn/ui）
3. 样式框架（无 Tailwind）
4. 前端认证集成
5. API 与前端的统一认证流

## 迁移建议
1. 保留后端 Fastify 或改用 Next.js API Routes
2. 新建 `apps/web` (Next.js) + `apps/api` (如需分离)
3. 集成 Better Auth for 认证层
4. 用 Vercel AI SDK 的函数调用支持数据分析/洞察生成
5. 所有数据可视化用 Recharts 或 D3 集成 shadcn/ui
