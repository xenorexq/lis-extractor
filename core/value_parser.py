"""
数值解析模块
处理特殊格式的检验结果（<0.5, >1000, 阳性等）
"""
import re
import math
import pandas as pd
from typing import Optional, Dict, Any, Tuple

from .utils import extract_numeric, safe_float
from .constants import ParserConfig


class ValueParser:
    """
    检验结果值解析器
    """
    
    def __init__(self, parsing_rules: Optional[Dict] = None):
        """
        parsing_rules: {
            'less_than': {'rule': 'half'},  # 或 'lower_bound', 'na'
            'greater_than': {'rule': 'keep'},  # 或 'na', 'cap'
            'positive_text': {
                'mapping': {'阳性': 1, '弱阳性': 0.5}
            },
            'negative_text': {
                'mapping': {'阴性': 0}
            },
            'invalid_values': {
                'mapping': {'溶血': None, '样本不足': None}
            }
        }
        """
        self.rules = parsing_rules or self._default_rules()
    
    @staticmethod
    def _default_rules() -> Dict:
        """默认解析规则"""
        return {
            'less_than': {'rule': 'half'},
            'greater_than': {'rule': 'keep'},
            'positive_text': {
                'mapping': {
                    '阳性': 1,
                    '弱阳性': 0.5,
                    '+': 1,
                    '++': 1,
                    '+++': 1
                }
            },
            'negative_text': {
                'mapping': {
                    '阴性': 0,
                    '-': 0
                }
            },
            'invalid_values': {
                'mapping': {
                    '溶血': None,
                    '样本不足': None,
                    '标本凝集': None,
                    '未检出': None,
                    '--': None,
                    '/': None,
                    '#': None,
                    'NA': None,
                    'N/A': None
                }
            }
        }
    
    def parse_value(self, raw_value: Any) -> Tuple[Optional[float], Optional[str]]:
        """
        解析单个检验结果值
        返回: (parsed_value, flag)
        flag 可能的值:
        - 'normal': 普通数值
        - 'less_than': 小于号 (<)
        - 'greater_than': 大于号 (>)
        - 'scientific': 科学计数法
        - 'power': 幂表示
        - 'titer': 滴度
        - 'range': 区间
        - 'text_positive': 阳性文本
        - 'text_negative': 阴性文本
        - 'invalid': 无效值
        """
        if pd.isna(raw_value):
            return None, None
        
        value_str = str(raw_value).strip()
        
        # 1. 检查是否是无效值
        invalid_mapping = self.rules.get('invalid_values', {}).get('mapping', {})
        for invalid_text, replacement in invalid_mapping.items():
            if invalid_text.lower() in value_str.lower():
                return replacement, 'invalid'
        
        # 2. 检查阳性文本
        positive_mapping = self.rules.get('positive_text', {}).get('mapping', {})
        for pos_text, pos_value in positive_mapping.items():
            if pos_text.lower() in value_str.lower():
                return pos_value, 'text_positive'
        
        # 3. 检查阴性文本
        negative_mapping = self.rules.get('negative_text', {}).get('mapping', {})
        for neg_text, neg_value in negative_mapping.items():
            if neg_text.lower() == value_str.lower():
                return neg_value, 'text_negative'
        
        # 4. 处理小于号 <
        if value_str.startswith('<') or value_str.startswith('≤'):
            numeric = extract_numeric(value_str)
            if numeric is not None:
                rule = self.rules.get('less_than', {}).get('rule', 'half')
                if rule == 'half':
                    return numeric / 2, 'less_than'
                elif rule == 'lower_bound':
                    return numeric, 'less_than'
                else:  # 'na'
                    return None, 'less_than'
        
        # 5. 处理大于号 >
        if value_str.startswith('>') or value_str.startswith('≥'):
            numeric = extract_numeric(value_str)
            if numeric is not None:
                rule = self.rules.get('greater_than', {}).get('rule', 'keep')
                if rule == 'keep':
                    return numeric, 'greater_than'
                elif rule == 'cap':
                    cap_value = self.rules.get('greater_than', {}).get('cap_value', numeric)
                    return cap_value, 'greater_than'
                else:  # 'na'
                    return None, 'greater_than'
        
        # 6. 检测特殊格式（用于标记），同时进行边界值检查
        # 科学计数法
        if re.search(r'\d+\.?\d*[eE][-+]?\d+', value_str):
            numeric = extract_numeric(value_str)
            if numeric is not None:
                return self._validate_numeric(numeric, 'scientific')

        # 幂表示
        if '^' in value_str:
            numeric = extract_numeric(value_str)
            if numeric is not None:
                return self._validate_numeric(numeric, 'power')

        # 滴度
        if ':' in value_str and re.match(r'\d+:\d+', value_str):
            numeric = extract_numeric(value_str)
            if numeric is not None:
                return self._validate_numeric(numeric, 'titer')

        # 区间
        if '-' in value_str and not value_str.startswith('-'):
            if re.match(r'^\d+\.?\d*\s*-\s*\d+\.?\d*$', value_str):
                numeric = extract_numeric(value_str)
                if numeric is not None:
                    return self._validate_numeric(numeric, 'range')
        
        # 7. 尝试直接转为数值
        numeric = safe_float(value_str.replace(',', ''))
        if numeric is not None:
            return self._validate_numeric(numeric)

        # 8. 尝试提取数值
        numeric = extract_numeric(value_str)
        if numeric is not None:
            return self._validate_numeric(numeric)

        # 9. 无法解析
        return None, 'invalid'

    def _validate_numeric(self, numeric: float, original_flag: str = 'normal') -> Tuple[Optional[float], str]:
        """
        验证数值的合理性

        Args:
            numeric: 要验证的数值
            original_flag: 原始格式标记（如 'scientific', 'power' 等）

        Returns:
            (validated_value, flag)
        """
        # 检查 inf 和 nan
        if math.isinf(numeric) or math.isnan(numeric):
            return None, 'invalid'

        # 检查极端值
        if abs(numeric) > ParserConfig.EXTREME_VALUE_THRESHOLD:
            # 对于极端值，仍然返回但标记为 extreme
            return numeric, 'extreme_value'

        return numeric, original_flag
    
    def apply(self, df: pd.DataFrame, value_col: str = 'test_value') -> pd.DataFrame:
        """
        应用解析规则到 DataFrame
        添加 value_numeric（解析后的数值）和 value_flag（标志）列
        """
        df = df.copy()
        
        # 解析每一行
        parsed_results = df[value_col].apply(self.parse_value)
        
        df['value_numeric'] = parsed_results.apply(lambda x: x[0])
        df['value_flag'] = parsed_results.apply(lambda x: x[1])
        
        return df
    
    def to_dict(self) -> Dict:
        """转为字典（用于保存到 YAML）"""
        return self.rules
    
    @classmethod
    def from_dict(cls, rules_dict: Dict) -> 'ValueParser':
        """从字典创建（用于从 YAML 加载）"""
        return cls(rules_dict)
    
    def update_rule(self, rule_type: str, **kwargs):
        """更新规则"""
        if rule_type not in self.rules:
            self.rules[rule_type] = {}
        self.rules[rule_type].update(kwargs)

