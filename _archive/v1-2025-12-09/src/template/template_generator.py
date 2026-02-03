#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板生成模块
将识别的模式转化为可复用的创作模板
"""

import json
from typing import List, Dict, Any
from pathlib import Path

class TemplateGenerator:
    """模板生成器"""
    
    def __init__(self, logger):
        self.logger = logger
        
        # 预定义模板结构
        self.template_structures = {
            'cognitive_impact': {
                'name': '认知冲击型',
                'sections': [
                    {'name': '冲击观点', 'type': 'hook', 'required': True},
                    {'name': '数据支撑', 'type': 'proof', 'required': True},
                    {'name': '权威背书', 'type': 'authority', 'required': False},
                    {'name': '行动引导', 'type': 'cta', 'required': True}
                ]
            },
            'storytelling': {
                'name': '故事叙述型',
                'sections': [
                    {'name': '故事背景', 'type': 'background', 'required': True},
                    {'name': '冲突设置', 'type': 'conflict', 'required': True},
                    {'name': '解决过程', 'type': 'solution', 'required': True},
                    {'name': '升华总结', 'type': 'insight', 'required': True}
                ]
            },
            'knowledge_sharing': {
                'name': '干货输出型',
                'sections': [
                    {'name': '痛点切入', 'type': 'pain_point', 'required': True},
                    {'name': '方法论', 'type': 'methodology', 'required': True},
                    {'name': '案例验证', 'type': 'example', 'required': True},
                    {'name': '总结行动', 'type': 'action', 'required': True}
                ]
            },
            'interaction_guide': {
                'name': '互动引导型',
                'sections': [
                    {'name': '悬念开头', 'type': 'hook', 'required': True},
                    {'name': '内容展示', 'type': 'content', 'required': True},
                    {'name': '互动设置', 'type': 'interaction', 'required': True},
                    {'name': '引导关注', 'type': 'follow', 'required': True}
                ]
            }
        }
        
        # 模板示例库
        self.template_examples = {
            'cognitive_impact': {
                'hook_examples': [
                    "你以为{常识观点}？真相是{颠覆数据}的人都在{做某事}",
                    "医生绝不会告诉你：{核心真相}",
                    "99%的人都误解了{话题}，真正有效的是{正确做法}"
                ],
                'proof_examples': [
                    "根据{权威机构}调查，{具体数字}的人发现{真相}",
                    "我分析了{数量}个案例，发现{规律}",
                    "最新研究显示：{研究结论}"
                ],
                'cta_examples': [
                    "你觉得呢？评论区说说你的经历",
                    "关注我，每天分享{相关}知识",
                    "觉得有用的话点个赞，让更多人看到"
                ]
            },
            'storytelling': {
                'background_examples': [
                    "去年这个时候，我{遇到某事}，没想到{转折}",
                    "我有个朋友{背景描述}，他{遇到问题}",
                    "记得{时间}，我第一次{经历某事}"
                ],
                'conflict_examples': [
                    "原本以为{预期}，没想到{意外情况}",
                    "试了很多方法都不行，{问题持续}",
                    "正当我{状态}的时候，突然{突发事件}"
                ],
                'solution_examples': [
                    "后来我{尝试方法}，终于{结果}",
                    "后来用了{解决方案}，效果特别好",
                    "最后通过{关键行动}，成功{达成目标}"
                ]
            },
            'knowledge_sharing': {
                'pain_point_examples': [
                    "很多人都在问：如何{解决问题}？",
                    "我发现{目标群体}最大的问题是{核心痛点}",
                    "你是不是也遇到过{具体问题}？"
                ],
                'methodology_examples': [
                    "我总结了{数量}个步骤：\n1. 首先{步骤1}\n2. 然后{步骤2}\n3. 最后{步骤3}",
                    "核心方法就是{方法论}：\n- 要点1：{内容}\n- 要点2：{内容}\n- 要点3：{内容}",
                    "只需要记住这个公式：{公式}"
                ],
                'example_examples': [
                    "拿{具体例子}举个例子：{描述}",
                    "比如{场景}，{具体做法}",
                    "按照这个方法，{案例}成功{结果}"
                ]
            }
        }
        
    def generate_templates(self, pattern_analysis: Dict[str, Any], 
                          theme: str) -> Dict[str, Any]:
        """
        生成创作模板
        
        Args:
            pattern_analysis: 模式分析结果
            theme: 调研主题
            
        Returns:
            生成的模板
        """
        self.logger.info("开始生成创作模板")
        
        templates = {}
        typical_features = pattern_analysis.get('typical_features', {})
        
        for pattern_key, feature_info in typical_features.items():
            if pattern_key in self.template_structures:
                template = self._generate_single_template(
                    pattern_key, feature_info, theme
                )
                templates[pattern_key] = template
                
        self.logger.info(f"生成了{len(templates)}个创作模板")
        return templates
    
    def _generate_single_template(self, pattern_key: str, 
                                 feature_info: Dict[str, Any],
                                 theme: str) -> Dict[str, Any]:
        """生成单个模板"""
        structure = self.template_structures[pattern_key]
        examples = self.template_examples.get(pattern_key, {})
        
        # 生成模板内容
        sections = []
        for section in structure['sections']:
            section_content = self._generate_section_content(
                section, feature_info, theme, examples
            )
            sections.append(section_content)
            
        # 生成完整模板
        template = {
            'id': f"{pattern_key}_{theme}",
            'name': structure['name'],
            'theme': theme,
            'pattern_key': pattern_key,
            'sections': sections,
            'full_template': self._compose_full_template(sections),
            'usage_guide': self._generate_usage_guide(pattern_key, theme),
            'variations': self._generate_variations(pattern_key, theme),
            'quality_score': feature_info.get('avg_engagement', 0.5)
        }
        
        return template
    
    def _generate_section_content(self, section: Dict[str, Any],
                                 feature_info: Dict[str, Any],
                                 theme: str,
                                 examples: Dict[str, Any]) -> Dict[str, Any]:
        """生成单个段落内容"""
        section_type = section['type']
        section_name = section['name']
        
        # 获取该段落的示例
        section_examples = examples.get(f'{section_type}_examples', [])
        
        # 根据主题生成具体内容
        content = self._generate_content_by_theme(section_type, theme, section_examples)
        
        return {
            'name': section_name,
            'type': section_type,
            'required': section['required'],
            'content': content,
            'examples': section_examples[:3] if section_examples else [],
            'tips': self._generate_section_tips(section_type, theme)
        }
    
    def _generate_content_by_theme(self, section_type: str, 
                                  theme: str,
                                  examples: List[str]) -> str:
        """根据主题生成具体内容"""
        if not examples:
            return f"[{section_type}内容]"
            
        # 根据主题类型调整示例
        theme_content = {
            '老人养生': {
                'hook': f"你以为{theme}很简单？真相是90%的人都在用错误方法",
                'proof': f"根据中医协会调查，{theme}的正确方法只有3种",
                'authority': f"国医大师表示：{theme}的关键在于...",
                'cta': f"你觉得{theme}最重要的是什么？评论区分享"
            },
            'AI工具': {
                'hook': f"你以为AI工具只是高科技人的专利？真相是90%的职场新人都在用",
                'proof': f"根据某招聘平台调研，使用AI工具的员工工作效率提升200%",
                'authority': f"人力资源专家李经理表示：'不会用AI的员工将被淘汰'",
                'cta': f"你用过哪些AI工具？评论区分享一下"
            }
        }
        
        content_map = theme_content.get(theme, {})
        return content_map.get(section_type, examples[0] if examples else f"[{section_type}内容]")
    
    def _generate_section_tips(self, section_type: str, theme: str) -> List[str]:
        """生成段落写作技巧"""
        tips_map = {
            'hook': [
                "开头3秒内抓住注意力",
                "使用颠覆性观点或疑问句",
                "避免冗长铺垫"
            ],
            'proof': [
                "使用具体数字和对比",
                "引用权威机构或研究",
                "数据要真实可信"
            ],
            'authority': [
                "提及专家姓名和头衔",
                "引用权威机构",
                "增强可信度"
            ],
            'cta': [
                "明确行动指令",
                "降低参与门槛",
                "增加互动价值"
            ]
        }
        
        return tips_map.get(section_type, ["保持内容相关性"])
    
    def _compose_full_template(self, sections: List[Dict[str, Any]]) -> str:
        """组合完整模板"""
        template_parts = []
        
        for i, section in enumerate(sections, 1):
            section_title = f"{i}. 【{section['name']}】"
            section_content = section['content']
            template_parts.append(f"{section_title}\n{section_content}\n")
            
        return '\n'.join(template_parts)
    
    def _generate_usage_guide(self, pattern_key: str, theme: str) -> Dict[str, Any]:
        """生成使用指南"""
        return {
            'when_to_use': self._get_when_to_use(pattern_key, theme),
            'target_audience': self._get_target_audience(pattern_key, theme),
            'best_practices': self._get_best_practices(pattern_key, theme),
            'common_mistakes': self._get_common_mistakes(pattern_key, theme)
        }
    
    def _get_when_to_use(self, pattern_key: str, theme: str) -> str:
        """获取适用场景"""
        scenarios = {
            'cognitive_impact': '新号快速起量、需要颠覆认知的话题',
            'storytelling': '需要建立情感连接、提升观看完播率',
            'knowledge_sharing': '打造专业形象、知识付费内容',
            'interaction_guide': '提升算法权重、增加用户粘性'
        }
        return scenarios.get(pattern_key, '通用创作场景')
    
    def _get_target_audience(self, pattern_key: str, theme: str) -> str:
        """获取目标受众"""
        audiences = {
            'cognitive_impact': '对传统观念有疑问的用户',
            'storytelling': '喜欢听故事、注重情感体验的用户',
            'knowledge_sharing': '追求实用价值、愿意学习的用户',
            'interaction_guide': '活跃的社交媒体用户'
        }
        return audiences.get(pattern_key, '通用用户群体')
    
    def _get_best_practices(self, pattern_key: str, theme: str) -> List[str]:
        """获取最佳实践"""
        practices = {
            'cognitive_impact': [
                '确保颠覆观点有事实支撑',
                '数据要具体且有冲击力',
                '避免过度夸张'
            ],
            'storytelling': [
                '故事要真实可信',
                '情节要有起伏',
                '情感要真挚'
            ],
            'knowledge_sharing': [
                '方法要实用可操作',
                '案例要典型有说服力',
                '逻辑要清晰'
            ]
        }
        return practices.get(pattern_key, ['保持内容相关性', '确保逻辑清晰'])
    
    def _get_common_mistakes(self, pattern_key: str, theme: str) -> List[str]:
        """获取常见错误"""
        mistakes = {
            'cognitive_impact': [
                '观点过于极端',
                '缺乏数据支撑',
                '标题党严重'
            ],
            'storytelling': [
                '故事过于平淡',
                '情节逻辑不通',
                '情感渲染过度'
            ],
            'knowledge_sharing': [
                '方法过于复杂',
                '案例不够典型',
                '实用性不强'
            ]
        }
        return mistakes.get(pattern_key, ['内容不够聚焦', '逻辑不够清晰'])
    
    def _generate_variations(self, pattern_key: str, theme: str) -> List[Dict[str, str]]:
        """生成模板变体"""
        variations = []
        
        if pattern_key == 'cognitive_impact':
            variations = [
                {'name': '数据对比型', 'description': '强调数字对比的冲击效果'},
                {'name': '案例冲击型', 'description': '用真实案例制造反差'},
                {'name': '观点颠覆型', 'description': '直接颠覆常识观点'}
            ]
        elif pattern_key == 'storytelling':
            variations = [
                {'name': '个人经历型', 'description': '分享个人真实经历'},
                {'name': '他人故事型', 'description': '讲述他人成功案例'},
                {'name': '对比故事型', 'description': '通过对比突出转变'}
            ]
        elif pattern_key == 'knowledge_sharing':
            variations = [
                {'name': '步骤分解型', 'description': '按步骤详细说明'},
                {'name': '公式总结型', 'description': '提炼核心公式'},
                {'name': '案例验证型', 'description': '用案例验证方法'}
            ]
            
        return variations
    
    def save_templates(self, templates: Dict[str, Any], output_dir: Path):
        """保存模板"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存完整模板
        templates_file = output_dir / 'templates.json'
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
            
        # 生成模板说明文档
        readme_file = output_dir / 'template_readme.md'
        self._generate_template_readme(templates, readme_file)
        
        self.logger.info(f"模板已保存到：{output_dir}")
    
    def _generate_template_readme(self, templates: Dict[str, Any], readme_file: Path):
        """生成模板说明文档"""
        content = ["# 创作模板库\n"]
        
        for pattern_key, template in templates.items():
            content.append(f"## {template['name']}\n")
            content.append(f"**适用主题**：{template['theme']}\n")
            content.append(f"**适用场景**：{template['usage_guide']['when_to_use']}\n")
            content.append(f"**目标受众**：{template['usage_guide']['target_audience']}\n\n")
            
            content.append("### 模板结构\n")
            for section in template['sections']:
                content.append(f"- **{section['name']}**：{section['content']}\n")
            
            content.append("\n### 完整模板\n")
            content.append(f"```\n{template['full_template']}\n```\n")
            
            content.append("### 使用技巧\n")
            for tip in template['usage_guide']['best_practices']:
                content.append(f"- {tip}\n")
            
            content.append("\n### 常见错误\n")
            for mistake in template['usage_guide']['common_mistakes']:
                content.append(f"- {mistake}\n")
            
            content.append("---\n")
            
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
