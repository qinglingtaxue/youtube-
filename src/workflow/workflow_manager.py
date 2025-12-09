#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理器
协调三事件最小故事的完整执行流程
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from research.data_collector import DataCollector
from analysis.pattern_analyzer import PatternAnalyzer
from template.template_generator import TemplateGenerator
from creator.script_creator import ScriptCreator

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self, theme: str, output_dir: Path, 
                 max_videos: int = 1000, max_cases: int = 10,
                 time_limit: int = 120, logger=None):
        self.theme = theme
        self.output_dir = output_dir
        self.max_videos = max_videos
        self.max_cases = max_cases
        self.time_limit = time_limit  # 分钟
        self.logger = logger
        
        # 时间分配
        self.time_allocation = {
            'event1': int(time_limit * 0.5),  # 50%
            'event2': int(time_limit * 0.25), # 25%
            'event3': int(time_limit * 0.25)  # 25%
        }
        
        # 初始化模块
        self.data_collector = DataCollector(logger)
        self.pattern_analyzer = PatternAnalyzer(logger)
        self.template_generator = TemplateGenerator(logger)
        self.script_creator = ScriptCreator(logger)
        
        # 工作流状态
        self.state = {
            'start_time': None,
            'end_time': None,
            'current_event': None,
            'progress': 0.0,
            'errors': []
        }
    
    def execute(self) -> Dict[str, Any]:
        """
        执行完整的工作流
        
        Returns:
            工作流执行结果
        """
        self.logger.info(f"开始执行工作流：{self.theme}")
        self.state['start_time'] = time.time()
        
        try:
            # 事件1：调研分析
            event1_result = self._execute_event1()
            
            # 事件2：模式抽象
            event2_result = self._execute_event2(event1_result)
            
            # 事件3：实战应用
            event3_result = self._execute_event3(event2_result)
            
            # 生成最终报告
            final_result = self._generate_final_report(
                event1_result, event2_result, event3_result
            )
            
            self.state['end_time'] = time.time()
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"工作流执行失败：{str(e)}")
            self.state['errors'].append(str(e))
            raise
    
    def _execute_event1(self) -> Dict[str, Any]:
        """
        事件1：调研分析 → 产出典型案例 + 模式总结
        
        时间限制：60分钟
        """
        self.logger.info("开始执行事件1：调研分析")
        self.state['current_event'] = 'event1'
        
        event_start = time.time()
        
        # 阶段1：数据收集（20分钟）
        self._log_progress("开始数据收集", 0.0)
        videos = self.data_collector.collect_videos(
            self.theme, self.max_videos
        )
        
        # 质量筛选
        quality_videos = self.data_collector.filter_quality_videos(videos)
        self.data_collector.save_videos(
            quality_videos, 
            self.output_dir / 'data' / 'collected_videos.json'
        )
        
        # 阶段2：深度分析（30分钟）
        self._log_progress("开始模式分析", 0.4)
        pattern_analysis = self.pattern_analyzer.analyze_videos(
            quality_videos, self.max_cases
        )
        
        # 保存分析结果
        self.pattern_analyzer.save_analysis_result(
            pattern_analysis,
            self.output_dir / 'analysis' / 'pattern_analysis.json'
        )
        
        # 阶段3：模式总结（10分钟）
        self._log_progress("完成模式总结", 0.9)
        
        event_time = time.time() - event_start
        self.logger.info(f"事件1完成，耗时{event_time:.1f}秒")
        
        return {
            'event': 'event1',
            'status': 'completed',
            'duration': event_time,
            'videos_collected': len(videos),
            'videos_quality': len(quality_videos),
            'cases_selected': len(pattern_analysis['selected_cases']),
            'patterns_found': len(pattern_analysis['pattern_distribution']),
            'pattern_analysis': pattern_analysis
        }
    
    def _execute_event2(self, event1_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        事件2：模式抽象 → 生成创作模板
        
        时间限制：30分钟
        """
        self.logger.info("开始执行事件2：模式抽象")
        self.state['current_event'] = 'event2'
        
        event_start = time.time()
        
        # 获取模式分析结果
        pattern_analysis = event1_result['pattern_analysis']
        
        # 生成模板
        self._log_progress("开始生成模板", 0.0)
        templates = self.template_generator.generate_templates(
            pattern_analysis, self.theme
        )
        
        # 保存模板
        self._log_progress("保存模板库", 0.8)
        self.template_generator.save_templates(
            templates, 
            self.output_dir / 'templates'
        )
        
        event_time = time.time() - event_start
        self.logger.info(f"事件2完成，耗时{event_time:.1f}秒")
        
        return {
            'event': 'event2',
            'status': 'completed',
            'duration': event_time,
            'templates_generated': len(templates),
            'templates': templates
        }
    
    def _execute_event3(self, event2_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        事件3：实战应用 → 输出创作文案
        
        时间限制：30分钟
        """
        self.logger.info("开始执行事件3：实战应用")
        self.state['current_event'] = 'event3'
        
        event_start = time.time()
        
        # 获取模板
        templates = event2_result['templates']
        
        # 生成创作文案
        self._log_progress("开始创作文案", 0.0)
        scripts = self.script_creator.create_scripts(
            templates, self.theme
        )
        
        # 保存文案
        self._log_progress("保存创作文案", 0.8)
        self.script_creator.save_scripts(
            scripts,
            self.output_dir / 'scripts'
        )
        
        event_time = time.time() - event_start
        self.logger.info(f"事件3完成，耗时{event_time:.1f}秒")
        
        return {
            'event': 'event3',
            'status': 'completed',
            'duration': event_time,
            'scripts_created': len(scripts),
            'scripts': scripts
        }
    
    def _generate_final_report(self, event1: Dict, event2: Dict, event3: Dict) -> Dict[str, Any]:
        """生成最终报告"""
        total_time = (event1['duration'] + event2['duration'] + event3['duration']) / 60
        
        result = {
            'theme': self.theme,
            'total_time': total_time,
            'videos_collected': event1['videos_collected'],
            'cases_selected': event1['cases_selected'],
            'patterns_found': event1['patterns_found'],
            'templates_generated': event2['templates_generated'],
            'scripts_created': event3['scripts_created'],
            'event_details': {
                'event1': event1,
                'event2': event2,
                'event3': event3
            },
            'output_files': self._get_output_files(),
            'summary': self._generate_summary(event1, event2, event3)
        }
        
        # 保存最终报告
        self._save_final_report(result)
        
        return result
    
    def _generate_summary(self, event1: Dict, event2: Dict, event3: Dict) -> str:
        """生成执行摘要"""
        summary_parts = [
            f"📊 **调研主题**：{self.theme}",
            f"⏱️ **总耗时**：{(event1['duration'] + event2['duration'] + event3['duration'])/60:.1f}分钟",
            f"",
            f"**事件1 - 调研分析**：",
            f"- 收集视频：{event1['videos_collected']}个",
            f"- 精选案例：{event1['cases_selected']}个",
            f"- 识别模式：{event1['patterns_found']}个",
            f"",
            f"**事件2 - 模式抽象**：",
            f"- 生成模板：{event2['templates_generated']}个",
            f"",
            f"**事件3 - 实战应用**：",
            f"- 创作文案：{event3['scripts_created']}个",
            f"",
            f"🎯 **核心发现**：",
            f"{event1['pattern_analysis']['patterns_summary']}"
        ]
        
        return '\n'.join(summary_parts)
    
    def _get_output_files(self) -> Dict[str, str]:
        """获取输出文件列表"""
        files = {}
        
        # 数据文件
        data_file = self.output_dir / 'data' / 'collected_videos.json'
        if data_file.exists():
            files['data'] = str(data_file)
            
        # 分析文件
        analysis_file = self.output_dir / 'analysis' / 'pattern_analysis.json'
        if analysis_file.exists():
            files['analysis'] = str(analysis_file)
            
        # 模板文件
        templates_dir = self.output_dir / 'templates'
        if templates_dir.exists():
            files['templates'] = str(templates_dir)
            
        # 文案文件
        scripts_dir = self.output_dir / 'scripts'
        if scripts_dir.exists():
            files['scripts'] = str(scripts_dir)
            
        return files
    
    def _save_final_report(self, result: Dict[str, Any]):
        """保存最终报告"""
        report_file = self.output_dir / 'final_report.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"最终报告已保存：{report_file}")
        
        # 生成Markdown格式报告
        self._save_markdown_report(result)
    
    def _save_markdown_report(self, result: Dict[str, Any]):
        """保存Markdown格式报告"""
        md_file = self.output_dir / 'report.md'
        
        content = [
            f"# YouTube视频创作工作流 - 执行报告",
            f"",
            f"**调研主题**：{result['theme']}",
            f"**执行时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总耗时**：{result['total_time']:.1f}分钟",
            f"",
            f"## 执行摘要",
            f"",
            f"{result['summary']}",
            f"",
            f"## 详细结果",
            f"",
            f"### 事件1：调研分析",
            f"- 收集视频：{result['videos_collected']}个",
            f"- 精选案例：{result['cases_selected']}个",
            f"- 识别模式：{result['patterns_found']}个",
            f"",
            f"### 事件2：模式抽象",
            f"- 生成模板：{result['templates_generated']}个",
            f"",
            f"### 事件3：实战应用",
            f"- 创作文案：{result['scripts_created']}个",
            f"",
            f"## 输出文件",
            f"",
            f"- 数据文件：`{result['output_files'].get('data', 'N/A')}`",
            f"- 分析文件：`{result['output_files'].get('analysis', 'N/A')}`",
            f"- 模板文件：`{result['output_files'].get('templates', 'N/A')}`",
            f"- 文案文件：`{result['output_files'].get('scripts', 'N/A')}`",
            f"",
            f"---",
            f"*报告由YouTube视频创作工作流自动生成*"
        ]
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
            
        self.logger.info(f"Markdown报告已保存：{md_file}")
    
    def _log_progress(self, message: str, progress: float):
        """记录进度"""
        self.state['progress'] = progress
        self.logger.info(f"[{self.state['current_event']}] {message} ({progress:.0%})")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'theme': self.theme,
            'current_event': self.state['current_event'],
            'progress': self.state['progress'],
            'elapsed_time': time.time() - self.state['start_time'] if self.state['start_time'] else 0,
            'errors': self.state['errors']
        }
