# 跨平台跨地区调研工具使用指南

## 概述

这是一个基于MCP技术的跨平台跨地区调研工具，可以帮助您：
- 收集YouTube、TikTok、Facebook、Instagram等平台的真实数据
- 分析不同地区和品类的竞争情况
- 找出竞争少的领域和信息差
- 生成详细的分析报告

## 快速开始

### 1. 查看可用地区
```bash
python3 research.py regions

# 查看特定分组的地区
python3 research.py regions --group low_competition
python3 research.py regions --group english_speaking
```

### 2. 查看可用平台
```bash
python3 research.py platforms

# 查看特定分组的平台
python3 research.py platforms --group video_platforms
```

### 3. 执行真实数据调研
```bash
# 调研单个品类在低竞争地区的竞争情况
python3 research.py real "Python教程"

# 指定特定地区
python3 research.py real "JavaScript学习" --regions US SG MY TH BR

# 指定多个平台
python3 research.py real "AI人工智能" --platforms youtube tiktok
```

### 4. 执行多平台调研
```bash
# 调研单个品类在多个平台的情况
python3 research.py multi "数据分析"

# 指定地区和平台
python3 research.py multi "机器学习" --regions US SG MY TH --platforms youtube tiktok facebook
```

## 详细说明

### 真实数据调研 (real)

使用真实数据调研功能，您需要：
1. 在Claude Code中执行MCP命令收集数据
2. 系统自动分析竞争度
3. 生成基于实际数据的报告

**示例流程**：
```bash
# 1. 运行调研命令
python3 research.py real "Python教程" --regions SG MY TH

# 2. 按照提示在Claude Code中执行MCP命令
@playwright 打开 https://www.youtube.com/results?search_query=Python教程&gl=SG
@playwright 等待页面加载完成
@playwright 滚动页面到底部
@playwright 提取所有视频的标题、频道名、观看量、发布时间

# 3. 查看分析结果
cat output/real_research/Python教程_analysis_report.md
```

### 多平台调研 (multi)

多平台调研使用模拟数据，演示完整的功能流程：
```bash
python3 research.py multi "Web开发"
```

**输出文件**：
- `{品类}_raw_data.json`: 原始数据
- `{品类}_gap_analysis.json`: 机会分析
- `{品类}_opportunity_report.md`: 机会报告
- `comprehensive_opportunity_report.md`: 综合报告

## 地区分组

### 高竞争地区
- US (美国)
- CN (中国大陆)
- JP (日本)
- KR (韩国)

### 中等竞争地区
- CA (加拿大)
- TW (台湾)
- HK (香港)
- IN (印度)
- GB (英国)
- DE (德国)
- FR (法国)
- AU (澳大利亚)

### 低竞争地区
- MX (墨西哥)
- SG (新加坡)
- MY (马来西亚)
- TH (泰国)
- VN (越南)
- IT (意大利)
- ES (西班牙)
- BR (巴西)

### 英语地区
- US, CA, GB, AU, SG, MY, IN

## 平台说明

### YouTube
- URL: https://www.youtube.com
- 数据类型: 视频
- 竞争指标: 观看量、频道数、视频数、发布频率

### TikTok
- URL: https://www.tiktok.com
- 数据类型: 短视频
- 竞争指标: 观看量、点赞数、创作者数、发布频率

### Facebook
- URL: https://www.facebook.com
- 数据类型: 帖子
- 竞争指标: 互动数、页面数、发布频率

### Instagram
- URL: https://www.instagram.com
- 数据类型: 帖子
- 竞争指标: 点赞数、帖子数、标签使用

## 竞争度分析标准

### 观看量分析 (YouTube/TikTok)
- **高竞争**: 平均观看量 ≥ 100万
- **中等竞争**: 平均观看量 10万-100万
- **低竞争**: 平均观看量 < 10万

### 频道/创作者分析
- **高竞争**: 独特频道/创作者数量 > 15
- **中等竞争**: 独特频道/创作者数量 5-15
- **低竞争**: 独特频道/创作者数量 < 5

### 时效性分析
- **高竞争**: 近期发布内容比例 ≥ 70%
- **中等竞争**: 近期发布内容比例 40-70%
- **低竞争**: 近期发布内容比例 < 40%

## MCP调用示例

### YouTube数据收集
```bash
@playwright 打开 https://www.youtube.com/results?search_query=Python教程&gl=SG
@playwright 等待页面加载完成
@playwright 滚动页面到底部
@playwright 提取所有视频的标题、频道名、观看量、发布时间
@playwright 截图保存
```

### TikTok数据收集
```bash
@playwright 打开 https://www.tiktok.com/search?q=Python教程
@playwright 等待内容加载
@playwright 滚动加载更多视频
@playwright 提取视频信息
```

### Facebook数据收集
```bash
@playwright 打开 https://www.facebook.com/search/top/?q=Python教程
@playwright 等待内容加载
@playwright 提取帖子信息
```

### Instagram数据收集
```bash
@playwright 打开 https://www.instagram.com/explore/tags/python/
@playwright 等待内容加载
@playwright 提取帖子信息
```

## 输出说明

### 报告文件
- `analysis_report.md`: 详细分析报告
- `comprehensive_opportunity_report.md`: 综合机会报告
- `{品类}_research.json`: 原始调研数据

### 数据字段
- `region`: 地区代码
- `category`: 调研品类
- `competition_analysis`: 竞争度分析
  - `overall`: 总体竞争度 (high/medium/low)
  - `scores`: 各维度评分 (1-3分)
  - `video_count`: 视频数量
  - `sample_videos`: 样本视频

## 最佳实践

1. **选择合适的地区**: 从低竞争地区开始，逐步扩展
2. **多平台布局**: 不要只关注YouTube，其他平台可能有更好机会
3. **关注时效性**: 近期发布内容多说明竞争激烈
4. **定期更新**: 市场情况会变化，需要定期重新调研

## 注意事项

1. 真实数据调研需要在Claude Code中实际执行MCP命令
2. 多平台调研使用模拟数据，仅用于演示流程
3. 竞争度判断基于多个维度，需要综合分析
4. 结果仅供参考，实际决策需要结合更多因素

## 故障排除

### Q: MCP命令执行失败
A: 检查CC-Switch是否运行，确保MCP服务器已启用

### Q: 分析结果不准确
A: 确保收集到足够的数据样本（至少10个视频）

### Q: 报告生成失败
A: 检查输出目录权限，确保有写入权限

## 扩展功能

### 添加新地区
编辑 `config/regions.yaml`，添加新地区配置

### 添加新平台
编辑 `config/platforms.yaml`，添加新平台配置

### 自定义竞争度标准
修改 `src/research/real_data_collector.py` 中的分析逻辑

---

**开始您的跨平台跨地区调研之旅！** 🚀
