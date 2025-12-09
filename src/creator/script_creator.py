#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文案创作模块
基于模板创作实际视频文案
"""

import json
from typing import List, Dict, Any
from pathlib import Path

class ScriptCreator:
    """文案创作器"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def create_scripts(self, templates: Dict[str, Any], theme: str) -> List[Dict[str, Any]]:
        """
        基于模板创作文案
        
        Args:
            templates: 模板字典
            theme: 调研主题
            
        Returns:
            创作的文案列表
        """
        self.logger.info("开始基于模板创作文案")
        
        scripts = []
        
        for pattern_key, template in templates.items():
            # 为每个模板创作1-2个文案示例
            script_examples = self._create_script_examples(template, theme)
            scripts.extend(script_examples)
            
        self.logger.info(f"创作了{len(scripts)}个文案")
        return scripts
    
    def _create_script_examples(self, template: Dict[str, Any], theme: str) -> List[Dict[str, Any]]:
        """为单个模板创作文案示例"""
        examples = []
        pattern_key = template['pattern_key']
        
        # 根据模式创作不同数量的示例
        example_count = 2 if pattern_key == 'cognitive_impact' else 1
        
        for i in range(example_count):
            script = self._generate_single_script(template, theme, i+1)
            examples.append(script)
            
        return examples
    
    def _generate_single_script(self, template: Dict[str, Any], theme: str, example_num: int) -> Dict[str, Any]:
        """生成单个文案"""
        script_id = f"{template['id']}_example_{example_num}"
        
        # 根据主题和模式生成具体内容
        content = self._generate_script_content(template, theme)
        
        # 生成文案详情
        script = {
            'id': script_id,
            'template_id': template['id'],
            'pattern_name': template['name'],
            'theme': theme,
            'title': self._generate_title(template, theme, example_num),
            'content': content,
            'structure': self._analyze_structure(content),
            'estimated_duration': self._estimate_duration(content),
            'target_audience': template['usage_guide']['target_audience'],
            'usage_scenario': template['usage_guide']['when_to_use'],
            'quality_score': template['quality_score'],
            'creation_time': self._get_creation_time()
        }
        
        return script
    
    def _generate_script_content(self, template: Dict[str, Any], theme: str) -> str:
        """生成文案内容"""
        sections = template['sections']
        content_parts = []
        
        for section in sections:
            section_content = self._fill_section_content(section, theme)
            content_parts.append(f"**{section['name']}**\n{section_content}\n")
            
        return '\n'.join(content_parts)
    
    def _fill_section_content(self, section: Dict[str, Any], theme: str) -> str:
        """填充段落内容"""
        section_type = section['type']
        base_content = section['content']
        
        # 根据主题调整内容
        theme_adjustments = {
            '老人养生': {
                'hook': f"你以为{theme}就是每天散步喝水？真相是：90%的老人都在用错误方法！",
                'proof': "根据中华医学会调查，坚持正确方法的老人，身体状态比实际年龄年轻10-15岁",
                'authority': "北京协和医院老专家李教授表示：养生关键在这5件事",
                'cta': "你觉得哪种方法最有效？评论区分享你的经验"
            },
            'AI工具': {
                'hook': f"你以为AI工具只是高科技人的专利？真相是：90%的职场新人都在偷偷用AI！",
                'proof': "根据某招聘平台调研，使用AI工具的员工工作效率平均提升200%",
                'authority': "人力资源专家王经理表示：'不会用AI的员工将在3年内被淘汰'",
                'cta': "你用过哪些AI工具？评论区分享一下，让更多人受益"
            },
            '美食制作': {
                'hook': f"你以为{theme}很复杂？学会这招，新手也能做出大厨水准！",
                'proof': "我测试了100个家庭，98%都成功了",
                'authority': "知名厨师张师傅点评：'这个方法确实专业'",
                'cta': "学会了记得点赞收藏，分享给更多人"
            }
        }
        
        adjustments = theme_adjustments.get(theme, {})
        return adjustments.get(section_type, base_content)
    
    def _generate_title(self, template: Dict[str, Any], theme: str, example_num: int) -> str:
        """生成标题"""
        pattern_key = template['pattern_key']
        
        title_templates = {
            'cognitive_impact': [
                f"你以为{theme}很简单？真相让人震惊！",
                f"90%的人都在用错误方法{theme}，专家终于说实话了",
                f"{theme}的5个惊人真相，第3个太颠覆了"
            ],
            'storytelling': [
                f"我用这个方法{theme}，3个月后发生的事让全家人都震惊了",
                f"朋友坚持{theme}一年，身体变化让我不敢相信",
                f"从失败到成功：我的{theme}之路太曲折了"
            ],
            'knowledge_sharing': [
                f"{theme}的3个秘诀，学会了受用终生",
                f"教你正确{theme}，简单易学一看就会",
                f"掌握这{theme}方法，你也能成为高手"
            ],
            'interaction_guide': [
                f"关于{theme}，我想听听你们的看法",
                f"你觉得{theme}最重要的是什么？评论区聊聊",
                f"投票：你最想了解{theme}的哪个方面？"
            ]
        }
        
        titles = title_templates.get(pattern_key, [f"关于{theme}，我有话要说"])
        return titles[(example_num-1) % len(titles)]
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """分析文案结构"""
        sections = content.split('**')
        section_count = len([s for s in sections if s.strip()])
        
        # 估算字数
        word_count = len(content.replace(' ', '').replace('\n', ''))
        
        # 估算句数
        sentences = content.count('。') + content.count('!') + content.count('？')
        
        return {
            'sections_count': section_count,
            'word_count': word_count,
            'sentence_count': sentences,
            'avg_words_per_section': word_count // max(section_count, 1)
        }
    
    def _estimate_duration(self, content: str) -> int:
        """估算视频时长（秒）"""
        # 按语速估算：每分钟200字
        word_count = len(content.replace(' ', '').replace('\n', ''))
        duration_seconds = (word_count / 200) * 60
        
        return int(duration_seconds)
    
    def _get_creation_time(self) -> str:
        """获取创建时间"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def save_scripts(self, scripts: List[Dict[str, Any]], output_dir: Path):
        """保存文案"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存完整文案
        scripts_file = output_dir / 'scripts.json'
        with open(scripts_file, 'w', encoding='utf-8') as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
            
        # 生成文案说明文档
        readme_file = output_dir / 'scripts_readme.md'
        self._generate_scripts_readme(scripts, readme_file)
        
        self.logger.info(f"文案已保存到：{output_dir}")
    
    def _generate_scripts_readme(self, scripts: List[Dict[str, Any]], readme_file: Path):
        """生成文案说明文档"""
        content = ["# 创作文案库\n"]
        
        for script in scripts:
            content.append(f"## {script['title']}\n")
            content.append(f"**模式**：{script['pattern_name']}\n")
            content.append(f"**主题**：{script['theme']}\n")
            content.append(f"**预估时长**：{script['estimated_duration']}秒\n")
            content.append(f"**目标受众**：{script['target_audience']}\n")
            content.append(f"**适用场景**：{script['usage_scenario']}\n")
            content.append(f"**质量评分**：{script['quality_score']:.2f}/1.00\n\n")
            
            content.append("### 文案内容\n")
            content.append(f"```\n{script['content']}\n```\n")
            
            content.append("### 结构分析\n")
            structure = script['structure']
            content.append(f"- 段落数：{structure['sections_count']}")
            content.append(f"- 字数：{structure['word_count']}")
            content.append(f"- 句数：{structure['sentence_count']}")
            content.append(f"- 平均段落字数：{structure['avg_words_per_section']}\n")
            
            content.append("---\n")
            
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
