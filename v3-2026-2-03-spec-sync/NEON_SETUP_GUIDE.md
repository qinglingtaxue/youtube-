# 🌐 Neon PostgreSQL 配置指南

**目的**: 为 v3 项目创建 Neon PostgreSQL 数据库实例
**时间**: 10-15 分钟

---

## 步骤 1: 创建 Neon 账户 (如果还没有)

### 访问 Neon 官方网站
1. 打开浏览器，访问: https://console.neon.tech/
2. 点击 "Sign up" 注册新账户
   - 可以用 Google/GitHub 账号快速登录
   - 或输入邮箱创建账户

3. 完成邮箱验证
4. 设置组织名和密码

---

## 步骤 2: 创建新项目

### 在 Neon 控制台中:

1. **登录后**，点击左上角 "New Project" 按钮

2. **填写项目信息**:
   ```
   Project Name: youtube-v3-prod
   Database name: youtube_db  (保持默认)
   Region: 美国东部 (us-east-1) 推荐
   PostgreSQL Version: 15 (或更新)
   ```

3. **点击 "Create project"**
   - 等待 1-2 分钟，项目创建完成

---

## 步骤 3: 获取连接字符串

### 在项目详情页面:

1. **点击 "Connect" 按钮**（绿色按钮）

2. **选择连接方式**:
   - 下拉菜单选择: "Connection string"
   - 或直接选择编程语言: "Node.js"

3. **复制连接字符串**:
   ```
   postgresql://user:password@host/dbname?sslmode=require
   ```

   🔍 **连接字符串示例**:
   ```
   postgresql://username:encrypted_password@ep-xxxx-xx.us-east-1.neon.tech/youtube_db?sslmode=require
   ```

4. **保存这个连接字符串** ⚠️ 很重要！

---

## 步骤 4: 配置 .env 文件

### 创建本地 .env 文件

```bash
# 进入项目目录
cd /Users/su/Downloads/3d_games/5-content-creation-tools/youtube-minimal-video-story/v3-2026-2-03-spec-sync

# 复制 .env.example
cp .env.example .env

# 编辑 .env 文件
# 使用您喜欢的编辑器，例如: code .env
```

### 编辑 .env 内容

打开 `.env` 文件，找到这几行:

```env
# 修改前:
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/youtube.db

# 修改后:
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://username:encrypted_password@ep-xxxx-xx.us-east-1.neon.tech/youtube_db?sslmode=require
```

⚠️ **关键**:
- 替换 `postgresql://...` 为您从 Neon 复制的完整连接字符串
- 不要修改其他环境变量
- 保存文件

---

## 步骤 5: 验证连接

### 测试 PostgreSQL 连接

```bash
# 使用 psql 命令行客户端（如果已安装）
psql "postgresql://username:password@ep-xxxx-xx.us-east-1.neon.tech/youtube_db?sslmode=require" -c "SELECT version();"
```

### 或者用 Node.js 测试

```bash
# 创建测试脚本
cat > test_connection.js << 'EOF'
import pg from 'pg';

const connectionString = process.env.DATABASE_URL;
const client = new pg.Client({ connectionString });

await client.connect();
console.log('✅ PostgreSQL 连接成功！');
const result = await client.query('SELECT version()');
console.log(result.rows[0].version);
await client.end();
EOF

# 运行测试
bun test_connection.js
```

**预期输出**:
```
✅ PostgreSQL 连接成功！
PostgreSQL 15.x on ... (Neon)
```

---

## 步骤 6: 在 Neon 中创建必要的 Role（可选）

如果想为迁移脚本使用专门的 PostgreSQL 角色：

```sql
-- 在 Neon SQL Editor 中运行这些命令

-- 创建新角色
CREATE ROLE migration_user WITH LOGIN PASSWORD 'secure_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE youtube_db TO migration_user;
GRANT ALL ON SCHEMA public TO migration_user;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO migration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO migration_user;
```

然后在 `.env` 中使用这个新角色的连接字符串:
```env
DATABASE_URL=postgresql://migration_user:secure_password@ep-xxxx-xx.us-east-1.neon.tech/youtube_db?sslmode=require
```

---

## 故障排除

### ❌ 连接被拒绝: "connect ECONNREFUSED"

**原因**: .env 中的 DATABASE_URL 不正确

**解决**:
1. 重新复制 Neon 的连接字符串
2. 确保没有拷贝错误（特别是 @host 部分）
3. 检查密码中是否有特殊字符需要转义

### ❌ SSL 证书错误

**原因**: SSL 模式设置不对

**解决**: 连接字符串必须包含 `?sslmode=require`
```env
# ✅ 正确
DATABASE_URL=postgresql://...?sslmode=require

# ❌ 错误
DATABASE_URL=postgresql://...
```

### ❌ 认证失败: "password authentication failed"

**原因**: 用户名或密码错误

**解决**:
1. 在 Neon 控制台检查默认用户名（通常是 `postgres`）
2. 重新复制完整的连接字符串
3. 不要手动修改其中的字符

### ✅ 网络防火墙问题

Neon 使用 SSL 连接，大多数防火墙允许。如果仍有问题:
- 尝试从不同的网络连接（例如手机热点）
- 询问网络管理员是否阻止了 PostgreSQL 端口

---

## 💡 安全建议

1. **保护 .env 文件**
   ```bash
   # .env 不应该提交到 git
   # 检查 .gitignore
   cat .gitignore | grep ".env"
   ```

2. **轮换密码** (定期)
   ```bash
   # 在 Neon 控制台中更新密码后
   # 更新 .env 文件中的连接字符串
   ```

3. **限制连接**
   - Neon 默认允许所有 IP，建议在生产环境中限制 IP 范围

4. **备份数据**
   - 启用 Neon 的自动备份功能（在项目设置中）

---

## 下一步

配置完成后，继续迁移流程:

```bash
# Step 1: 创建 v3 Schema
bun run db:push

# Step 2: 执行数据迁移
bun run migration:execute

# Step 3: 验证结果
bun run migration:validate
```

---

## 常用 Neon 功能

### 查看数据库监控
- 访问: https://console.neon.tech/ → 项目 → "Monitor" 标签
- 可以查看查询性能、连接数等

### 访问 SQL 编辑器
- 在 Neon 控制台点击 "SQL Editor"
- 可以直接运行 SQL 查询

### 创建额外的分支（可选）
- 用于开发/测试，与生产隔离

### 启用自动备份
- 在项目设置中启用
- Neon 会每天自动备份

---

## 相关文档

- 📖 Neon 官方文档: https://neon.tech/docs
- 🔐 连接管理: https://neon.tech/docs/connect/connection-details
- 🛡️ 安全最佳实践: https://neon.tech/docs/security/authentication

---

**准备好了吗？**

完成上述步骤后，在 .env 文件中配置好 DATABASE_URL，然后继续运行迁移命令！

```bash
# 确认 .env 已配置
echo $DATABASE_URL

# 创建 Schema
bun run db:push

# 迁移数据
bun run migration:execute
```
