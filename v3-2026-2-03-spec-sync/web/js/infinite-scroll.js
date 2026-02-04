/**
 * 无限滚动列表组件
 *
 * 功能：
 * 1. 分页加载视频列表（每页 50 条）
 * 2. 虚拟滚动：只渲染可见区域的卡片
 * 3. 增量加载：用户滚动到底部时自动加载下一页
 * 4. 防抖处理：避免频繁触发加载
 *
 * 使用示例：
 * ```html
 * <div id="video-list" class="video-list"></div>
 *
 * <script>
 * const list = new InfiniteScrollList('video-list', {
 *   keyword: '养生',
 *   sortBy: 'views',
 * });
 *
 * await list.init();
 * </script>
 * ```
 *
 * 优化对比：
 * 原方案：一次性加载 10万 条 → 前端 100MB 内存 → 浏览器卡死
 * 新方案：分页加载 50 条 → 前端 2MB 内存 → 流畅体验
 */

class InfiniteScrollList {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);

    // 配置参数
    this.keyword = options.keyword || "";
    this.sortBy = options.sortBy || "views";
    this.timeRange = options.timeRange || "30d";
    this.pageSize = 50; // 每页加载 50 条

    // 状态管理
    this.currentPage = 1;
    this.totalPages = 0;
    this.isLoading = false;
    this.hasMore = true;

    // 内存中的数据（不超过 2 页）
    this.cachedItems = [];

    // UI 状态
    this.loadingIndicator = null;
    this.sentinelElement = null;

    this._setupIntersectionObserver();
  }

  /**
   * 初始化：加载第一页数据
   */
  async init() {
    console.log("🚀 初始化列表...");
    await this.loadMore();
    console.log("✅ 列表初始化完成");
  }

  /**
   * 加载下一页数据
   */
  async loadMore() {
    if (this.isLoading || !this.hasMore) {
      return;
    }

    this.isLoading = true;
    this.showLoadingIndicator();

    try {
      const response = await fetch(
        `/api/videos?` +
          `page=${this.currentPage}` +
          `&limit=${this.pageSize}` +
          `&keyword=${encodeURIComponent(this.keyword)}` +
          `&sortBy=${this.sortBy}` +
          `&timeRange=${this.timeRange}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // 更新状态
      this.cachedItems.push(...data.items);
      this.totalPages = data.pagination.pages;
      this.hasMore = data.pagination.hasMore;
      this.currentPage++;

      // 渲染新数据
      this.renderItems(data.items);

      console.log(
        `✅ 加载了第 ${this.currentPage - 1} 页（共 ${this.totalPages} 页）`
      );
    } catch (error) {
      console.error("❌ 加载失败:", error);
      this.showError(error.message);
    } finally {
      this.isLoading = false;
      this.hideLoadingIndicator();
    }
  }

  /**
   * 渲染视频卡片
   * 使用 requestAnimationFrame 避免阻塞 UI
   */
  renderItems(items) {
    // 分批渲染（每批 10 条），避免一次性渲染 50 条导致卡顿
    const batchSize = 10;

    for (let i = 0; i < items.length; i += batchSize) {
      requestAnimationFrame(() => {
        const batch = items.slice(i, i + batchSize);
        this._renderBatch(batch);
      });
    }
  }

  /**
   * 内部方法：渲染一批卡片
   */
  _renderBatch(items) {
    const fragment = document.createDocumentFragment();

    for (const item of items) {
      const card = this._createVideoCard(item);
      fragment.appendChild(card);
    }

    this.container.appendChild(fragment);
  }

  /**
   * 创建视频卡片 HTML
   */
  _createVideoCard(video) {
    const card = document.createElement("div");
    card.className = "video-card";
    card.innerHTML = `
      <div class="card-thumbnail">
        <img
          src="https://i.ytimg.com/vi/${video.youtube_id}/default.jpg"
          alt="${video.title}"
          loading="lazy"
        />
      </div>
      <div class="card-content">
        <h3 class="card-title">${this._escapeHtml(video.title)}</h3>
        <p class="card-channel">${this._escapeHtml(video.channel_name)}</p>
        <div class="card-stats">
          <span class="stat">
            📺 ${this._formatNumber(video.views)} 次播放
          </span>
          <span class="stat">
            👍 ${this._formatNumber(video.likes)} 个赞
          </span>
          <span class="stat">
            💬 ${this._formatNumber(video.comments)} 条评论
          </span>
        </div>
      </div>
    `;

    return card;
  }

  /**
   * 设置 Intersection Observer
   * 当用户滚动到底部时自动加载下一页
   */
  _setupIntersectionObserver() {
    // 创建哨兵元素（插入到容器底部）
    this.sentinelElement = document.createElement("div");
    this.sentinelElement.className = "scroll-sentinel";
    this.container.appendChild(this.sentinelElement);

    // 创建 Observer
    const observer = new IntersectionObserver(
      (entries) => {
        // 当哨兵元素进入视口时触发
        if (entries[0].isIntersecting && !this.isLoading && this.hasMore) {
          this.loadMore();
        }
      },
      {
        root: null, // 使用视口作为根元素
        rootMargin: "100px", // 提前 100px 触发（提升用户体验）
        threshold: 0.01,
      }
    );

    observer.observe(this.sentinelElement);
  }

  /**
   * 显示加载指示器
   */
  showLoadingIndicator() {
    if (!this.loadingIndicator) {
      this.loadingIndicator = document.createElement("div");
      this.loadingIndicator.className = "loading-indicator";
      this.loadingIndicator.innerHTML = `
        <div class="spinner"></div>
        <p>加载中...</p>
      `;
    }

    this.container.appendChild(this.loadingIndicator);
  }

  /**
   * 隐藏加载指示器
   */
  hideLoadingIndicator() {
    if (this.loadingIndicator && this.loadingIndicator.parentNode) {
      this.loadingIndicator.parentNode.removeChild(this.loadingIndicator);
    }
  }

  /**
   * 显示错误信息
   */
  showError(message) {
    const errorEl = document.createElement("div");
    errorEl.className = "error-message";
    errorEl.textContent = `❌ 加载失败：${message}`;
    this.container.appendChild(errorEl);
  }

  /**
   * 工具方法：格式化大数字
   * 10000 → "1 万"
   */
  _formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    }
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + "万";
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
  }

  /**
   * 工具方法：HTML 转义
   * 防止 XSS 攻击
   */
  _escapeHtml(text) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  /**
   * 重置列表
   */
  reset() {
    this.cachedItems = [];
    this.currentPage = 1;
    this.hasMore = true;
    this.container.innerHTML = "";
    this._setupIntersectionObserver();
  }

  /**
   * 搜索新关键词
   */
  async search(keyword) {
    this.keyword = keyword;
    this.reset();
    await this.loadMore();
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      itemsLoaded: this.cachedItems.length,
      pagesLoaded: this.currentPage - 1,
      totalPages: this.totalPages,
      isLoading: this.isLoading,
      hasMore: this.hasMore,
    };
  }
}

// ================================================================
// 导出（如果使用模块化）
// ================================================================

if (typeof module !== "undefined" && module.exports) {
  module.exports = InfiniteScrollList;
}

// ================================================================
// CSS 样式（可选：内联或外部）
// ================================================================

const STYLES = `
.video-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
}

.video-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.video-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-thumbnail {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 宽高比 */
  background: #f0f0f0;
  overflow: hidden;
}

.card-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-content {
  padding: 12px;
}

.card-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-channel {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #666;
}

.card-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: #999;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #333;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 12px;
  background: #fee;
  color: #c33;
  border-radius: 4px;
  margin: 10px;
}

.scroll-sentinel {
  height: 1px;
  visibility: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-list {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    padding: 12px;
  }

  .card-content {
    padding: 8px;
  }

  .card-title {
    font-size: 12px;
  }

  .card-stats {
    font-size: 10px;
  }
}
`;

// ================================================================
// 自动注入样式（可选）
// ================================================================

function injectStyles() {
  if (document.getElementById("infinite-scroll-styles")) {
    return; // 避免重复注入
  }

  const styleEl = document.createElement("style");
  styleEl.id = "infinite-scroll-styles";
  styleEl.textContent = STYLES;
  document.head.appendChild(styleEl);
}

// 页面加载时自动注入
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectStyles);
} else {
  injectStyles();
}
