#!/usr/bin/env python3
"""YouTube 内容创作流水线 CLI 入口"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# 确保可以导入项目模块
sys.path.insert(0, str(Path(__file__).parent))

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="YouTube Content Pipeline")
def cli():
    """YouTube 内容创作全流程自动化工具

    \b
    使用示例:
      python cli.py status                           # 查看项目状态
      python cli.py research collect --theme 老人养生  # 采集视频数据
      python cli.py analytics market                  # 生成市场分析
      python cli.py analytics opportunities           # 挖掘创作机会
    """
    pass


@cli.command()
def status():
    """显示项目状态"""
    from src.shared.repositories import CompetitorVideoRepository

    console.print(Panel.fit(
        "[bold green]YouTube Content Pipeline[/bold green]\n"
        "版本: 1.0.0",
        title="项目信息"
    ))

    # 数据库统计
    try:
        repo = CompetitorVideoRepository()
        videos = repo.find_all(limit=10000)
        total = len(videos)
        with_details = sum(1 for v in videos if v.description)
        with_dates = sum(1 for v in videos if v.published_at)
        total_views = sum(v.view_count for v in videos)

        table = Table(title="数据库统计")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="green")
        table.add_row("总视频数", f"{total:,}")
        table.add_row("有详情的", f"{with_details:,}")
        table.add_row("有发布时间的", f"{with_dates:,}")
        table.add_row("总播放量", f"{total_views:,}")
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]数据库未初始化: {e}[/yellow]")


# ============================================================
# 调研模块命令
# ============================================================

@cli.group()
def research():
    """调研模块 - 视频数据采集"""
    pass


@research.command('collect')
@click.option('--theme', '-t', required=True, help='采集主题，如"老人养生"')
@click.option('--count', '-n', default=200, help='目标采集数量（默认200）')
@click.option('--detail-limit', '-d', default=50, help='获取详情的数量上限（默认50）')
@click.option('--min-views', '-v', default=5000, help='获取详情的最低播放量阈值（默认5000）')
def research_collect(theme: str, count: int, detail_limit: int, min_views: int):
    """采集 YouTube 视频数据

    \b
    示例:
      python cli.py research collect --theme 老人养生
      python cli.py research collect -t 健康饮食 -n 500 -d 100
    """
    from src.research.data_collector import DataCollector

    console.print(f"[bold]开始采集: {theme}[/bold]")
    console.print(f"  目标数量: {count}")
    console.print(f"  详情上限: {detail_limit}")
    console.print(f"  最低播放量: {min_views:,}")
    console.print()

    collector = DataCollector()

    with console.status("[bold green]采集中..."):
        result = collector.collect_large_scale(
            theme=theme,
            target_count=count,
            detail_min_views=min_views,
            detail_limit=detail_limit,
        )

    # 显示结果
    console.print()
    console.print(Panel.fit(
        f"[green]采集完成![/green]\n\n"
        f"主题: {result['theme']}\n"
        f"关键词: {', '.join(result['keywords'])}\n\n"
        f"[bold]阶段1 - 快速搜索[/bold]\n"
        f"  新增视频: {result['phase1']['new_videos']}\n"
        f"  跳过(已存在): {result['phase1']['skipped']}\n\n"
        f"[bold]阶段2 - 详情获取[/bold]\n"
        f"  成功: {result['phase2']['success']}\n"
        f"  失败: {result['phase2']['failed']}\n\n"
        f"[bold]数据库统计[/bold]\n"
        f"  总视频数: {result['database']['total']:,}\n"
        f"  有详情的: {result['database']['with_details']:,}\n"
        f"  总播放量: {result['database']['total_views']:,}\n\n"
        f"耗时: {result['elapsed_seconds']} 秒",
        title="采集结果"
    ))


@research.command('stats')
def research_stats():
    """显示采集数据统计"""
    from src.shared.repositories import CompetitorVideoRepository

    repo = CompetitorVideoRepository()
    videos = repo.find_all(limit=10000)

    if not videos:
        console.print("[yellow]数据库为空[/yellow]")
        return

    # 基础统计
    total = len(videos)
    with_details = sum(1 for v in videos if v.description)
    with_dates = sum(1 for v in videos if v.published_at)
    total_views = sum(v.view_count for v in videos)
    avg_views = total_views // total if total else 0

    # 频道统计
    channels = set(v.channel_name for v in videos if v.channel_name)

    table = Table(title="采集数据统计")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    table.add_row("总视频数", f"{total:,}")
    table.add_row("有详情的", f"{with_details:,} ({with_details/total*100:.1f}%)")
    table.add_row("有发布时间的", f"{with_dates:,} ({with_dates/total*100:.1f}%)")
    table.add_row("总频道数", f"{len(channels):,}")
    table.add_row("总播放量", f"{total_views:,}")
    table.add_row("平均播放量", f"{avg_views:,}")
    console.print(table)


# ============================================================
# 分析模块命令
# ============================================================

@cli.group()
def analytics():
    """分析模块 - 数据分析与洞察"""
    pass


@analytics.command('market')
@click.option('--format', '-f', 'output_format', type=click.Choice(['json', 'table', 'both']),
              default='both', help='输出格式（默认both）')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径（可选）')
@click.option('--enrich-dates/--no-enrich-dates', default=False,
              help='是否补充发布时间（较慢）')
def analytics_market(output_format: str, output: str, enrich_dates: bool):
    """生成市场分析报告

    \b
    分析内容:
      - 市场规模（总视频数、总播放量、覆盖频道数）
      - 竞争格局（头部集中度、长尾分布）
      - 发布频率（日均/月均发布量）
      - 时间趋势（年增长率、近期趋势）
      - 进入壁垒（爆款门槛、成功率）

    \b
    示例:
      python cli.py analytics market
      python cli.py analytics market -f json -o report.json
      python cli.py analytics market --enrich-dates
    """
    from src.analysis.market_analyzer import MarketAnalyzer

    analyzer = MarketAnalyzer()

    with console.status("[bold green]加载数据..."):
        count = analyzer.load_data()
    console.print(f"加载了 {count:,} 个视频")

    if enrich_dates:
        with console.status("[bold green]补充发布时间..."):
            enriched = analyzer.enrich_publish_dates(limit=200)
            analyzer.load_data()  # 重新加载
        console.print(f"补充了 {enriched} 个视频的发布时间")

    with console.status("[bold green]分析中..."):
        report = analyzer.analyze()

    # 输出表格
    if output_format in ['table', 'both']:
        _print_market_report(report)

    # 保存 JSON
    if output_format in ['json', 'both']:
        if output:
            path = analyzer.save_report(report, output)
        else:
            path = analyzer.save_report(report)
        console.print(f"\n[green]报告已保存: {path}[/green]")


def _print_market_report(report):
    """打印市场报告表格"""
    # 时间上下文
    tc = report.time_context
    if tc.get('data_has_dates'):
        console.print(Panel.fit(
            f"分析日期: {tc['analysis_date']}\n"
            f"数据范围: {tc['date_range']['earliest']} ~ {tc['date_range']['latest']}\n"
            f"时间跨度: {tc['date_range']['span_description']}\n"
            f"有日期视频: {tc['videos_with_date_count']} ({tc['date_coverage_rate']}%)",
            title="数据时间范围"
        ))

    # 市场规模
    ms = report.market_size
    table = Table(title="市场规模")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    table.add_row("样本视频数", f"{ms['sample_videos']:,}")
    table.add_row("总播放量", f"{ms['total_views']:,}")
    table.add_row("平均播放量", f"{ms['avg_views']:,}")
    table.add_row("中位数播放量", f"{ms['median_views']:,}")
    console.print(table)

    # 竞争格局
    cc = report.channel_competition
    table = Table(title="竞争格局")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    table.add_row("总频道数", f"{cc['total_channels']}")
    table.add_row("单视频频道", f"{cc['size_distribution']['single_video']}")
    table.add_row("Top10 集中度", f"{cc['concentration']['top10_share']}%")
    table.add_row("Top20 集中度", f"{cc['concentration']['top20_share']}%")
    console.print(table)

    # 头部频道
    table = Table(title="头部频道 Top 5")
    table.add_column("#", style="dim")
    table.add_column("频道", style="cyan")
    table.add_column("视频数", style="green")
    table.add_column("总播放", style="green")
    for i, ch in enumerate(cc['top_channels'][:5], 1):
        table.add_row(
            str(i),
            ch['channel'][:25],
            str(ch['video_count']),
            f"{ch['total_views']:,}"
        )
    console.print(table)

    # 进入壁垒
    eb = report.entry_barriers
    table = Table(title="进入壁垒")
    table.add_column("层级", style="cyan")
    table.add_column("数量", style="green")
    table.add_column("占比", style="green")
    for tier, count in eb['performance_tiers'].items():
        pct = count / report.sample_size * 100
        table.add_row(tier, str(count), f"{pct:.1f}%")
    console.print(table)


@analytics.command('opportunities')
@click.option('--window', '-w', type=click.Choice(['7d', '30d', '90d', '6m']),
              default='30d', help='时间窗口（默认30d）')
@click.option('--format', '-f', 'output_format', type=click.Choice(['json', 'table', 'both']),
              default='both', help='输出格式')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
def analytics_opportunities(window: str, output_format: str, output: str):
    """挖掘 AI 视频创作机会

    \b
    分析内容:
      - 近期爆款（按时间窗口分类）
      - 高日增长视频（日均 500+ 播放）
      - 小频道黑马（1-3 视频但有爆款）
      - 高互动率模板（适合 AI 配音）

    \b
    示例:
      python cli.py analytics opportunities
      python cli.py analytics opportunities -w 7d
      python cli.py analytics opportunities -w 90d -f json
    """
    from src.analysis.market_analyzer import MarketAnalyzer

    analyzer = MarketAnalyzer()

    with console.status("[bold green]加载数据..."):
        count = analyzer.load_data()
    console.print(f"加载了 {count:,} 个视频")

    with console.status("[bold green]分析机会..."):
        report = analyzer.analyze()

    opp = report.ai_creator_opportunities

    if opp.get('note'):
        console.print(f"[yellow]{opp['note']}[/yellow]")
        return

    # 时间窗口映射
    window_map = {'7d': '7天内', '30d': '30天内', '90d': '90天内', '6m': '6个月内'}
    target_window = window_map[window]

    if output_format in ['table', 'both']:
        _print_opportunities(opp, target_window)

    if output_format in ['json', 'both']:
        output_path = output or f"data/analysis/opportunities_{window}.json"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(opp, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]报告已保存: {output_path}[/green]")


def _print_opportunities(opp, target_window):
    """打印机会分析结果"""
    console.print(Panel.fit(
        f"分析时间: {opp['analysis_time']}\n"
        f"数据范围: {opp['data_time_range']['earliest']} ~ {opp['data_time_range']['latest']}\n"
        f"有日期视频: {opp['data_time_range']['videos_with_date']}",
        title="AI 创作者机会分析"
    ))

    # 近期爆款
    if target_window in opp['recent_viral_by_window']:
        rv = opp['recent_viral_by_window'][target_window]
        console.print(f"\n[bold cyan]【{target_window} 近期爆款】[/bold cyan]")
        console.print(f"  视频数: {rv['video_count']} | 平均播放: {rv['avg_views']:,}")

        table = Table(title=f"{target_window} Top 视频")
        table.add_column("#", style="dim", width=3)
        table.add_column("标题", style="cyan", max_width=40)
        table.add_column("发布", style="green", width=12)
        table.add_column("播放", style="green", width=10)
        table.add_column("日增", style="yellow", width=8)

        for i, v in enumerate(rv['top_performers'][:10], 1):
            table.add_row(
                str(i),
                v['title'][:40],
                v['published_at'],
                f"{v['views']:,}",
                f"{v['daily_growth']:,}"
            )
        console.print(table)

    # 高日增长
    hg = opp['high_daily_growth']
    console.print(f"\n[bold cyan]【高日增长视频】[/bold cyan]")
    console.print(f"  共 {hg['count']} 个: {hg['description']}")

    table = Table(title="高增长 Top 10")
    table.add_column("#", style="dim", width=3)
    table.add_column("时间段", style="magenta", width=10)
    table.add_column("标题", style="cyan", max_width=35)
    table.add_column("日增", style="yellow", width=8)

    for i, v in enumerate(hg['top_performers'][:10], 1):
        table.add_row(
            str(i),
            v['time_bucket'],
            v['title'][:35],
            f"{v['daily_growth']:,}"
        )
    console.print(table)

    # 小频道黑马
    sch = opp['small_channel_hits']
    console.print(f"\n[bold cyan]【小频道黑马】[/bold cyan]")
    console.print(f"  共 {sch['count']} 个: {sch['description']}")

    table = Table(title="小频道爆款 Top 10")
    table.add_column("#", style="dim", width=3)
    table.add_column("时间段", style="magenta", width=10)
    table.add_column("标题", style="cyan", max_width=35)
    table.add_column("播放", style="green", width=10)

    for i, v in enumerate(sch['top_performers'][:10], 1):
        table.add_row(
            str(i),
            v['time_bucket'],
            v['title'][:35],
            f"{v['views']:,}"
        )
    console.print(table)

    # 机会总结
    summary = opp['opportunity_summary']
    console.print(f"\n[bold cyan]【机会总结】[/bold cyan]")
    console.print(f"  最佳时间窗口: {summary['best_time_window']}")
    console.print("\n  建议:")
    for rec in summary['recommendations']:
        console.print(f"    [green]✓[/green] {rec}")
    console.print("\n  行动项:")
    for item in summary['action_items']:
        console.print(f"    [yellow]→[/yellow] {item}")


# ============================================================
# 其他模块占位
# ============================================================

@cli.group()
def planning():
    """策划模块 - 内容策划（待开发）"""
    pass


@cli.group()
def production():
    """制作模块 - 视频制作（待开发）"""
    pass


@cli.group()
def publishing():
    """发布模块 - 视频发布（待开发）"""
    pass


if __name__ == "__main__":
    cli()
