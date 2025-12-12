"""
检验项目映射模块
标准化项目名称、单位等
"""
import pandas as pd
from typing import Dict, List, Optional, Set


class TestMapper:
    """
    检验项目映射器
    """
    
    def __init__(self, test_mapping: Optional[Dict] = None):
        """
        test_mapping: {
            'CEA': {
                'aliases': ['CEA', 'CEA(CLIA)', '癌胚抗原'],
                'unit': 'ng/mL',
                'range': [0, 5]
            }
        }
        """
        self.test_mapping = test_mapping or {}
        self._build_reverse_index()
    
    def _build_reverse_index(self):
        """构建别名反向索引"""
        self.alias_to_standard = {}
        
        for standard_name, config in self.test_mapping.items():
            aliases = config.get('aliases', [])
            for alias in aliases:
                self.alias_to_standard[alias.strip().lower()] = standard_name
    
    def standardize_test_name(self, raw_name: str) -> str:
        """
        标准化检验项目名称
        如果在映射中找到，返回标准名称
        否则返回原始名称
        """
        if pd.isna(raw_name):
            return ''
        
        raw_name_lower = str(raw_name).strip().lower()
        
        if raw_name_lower in self.alias_to_standard:
            return self.alias_to_standard[raw_name_lower]
        
        return str(raw_name).strip()
    
    def get_standard_unit(self, test_name: str) -> Optional[str]:
        """获取标准单位"""
        if test_name in self.test_mapping:
            return self.test_mapping[test_name].get('unit')
        return None
    
    def get_reference_range(self, test_name: str) -> Optional[List[float]]:
        """获取参考范围"""
        if test_name in self.test_mapping:
            return self.test_mapping[test_name].get('range')
        return None
    
    def apply(self, df: pd.DataFrame, test_name_col: str = 'test_name') -> pd.DataFrame:
        """
        应用映射到 DataFrame
        添加 test_code 列（标准化名称）
        """
        df = df.copy()
        
        df['test_code'] = df[test_name_col].apply(self.standardize_test_name)
        
        # 添加标准单位列（如果配置了）
        df['unit_std'] = df['test_code'].apply(self.get_standard_unit)
        
        return df
    
    def filter_selected_tests(self, df: pd.DataFrame, selected_tests: Set[str], 
                             test_code_col: str = 'test_code') -> pd.DataFrame:
        """
        过滤出选中的检验项目
        """
        return df[df[test_code_col].isin(selected_tests)].copy()
    
    def get_test_statistics(self, df: pd.DataFrame, test_name_col: str = 'test_name') -> pd.DataFrame:
        """
        统计每个检验项目的数量
        返回 DataFrame: [test_name, count, standard_name]
        """
        stats = df[test_name_col].value_counts().reset_index()
        stats.columns = ['test_name', 'count']
        
        # 添加标准化名称
        stats['test_code'] = stats['test_name'].apply(self.standardize_test_name)
        
        # 按数量排序
        stats = stats.sort_values('count', ascending=False)
        
        return stats
    
    @classmethod
    def from_selected_tests(cls, selected_tests: List[str], 
                           aliases: Optional[Dict[str, List[str]]] = None) -> 'TestMapper':
        """
        从选中的测试列表创建映射
        """
        test_mapping = {}
        aliases = aliases or {}
        
        for test in selected_tests:
            test_mapping[test] = {
                'aliases': aliases.get(test, [test]),
                'unit': None,
                'range': None
            }
        
        return cls(test_mapping)
    
    def to_dict(self) -> Dict:
        """转为字典（用于保存到 YAML）"""
        return self.test_mapping
    
    @classmethod
    def from_dict(cls, mapping_dict: Dict) -> 'TestMapper':
        """从字典创建（用于从 YAML 加载）"""
        return cls(mapping_dict)
    
    def add_test(self, standard_name: str, aliases: List[str], 
                 unit: Optional[str] = None, ref_range: Optional[List[float]] = None):
        """添加一个检验项目"""
        self.test_mapping[standard_name] = {
            'aliases': aliases,
            'unit': unit,
            'range': ref_range
        }
        self._build_reverse_index()
    
    def update_test(self, standard_name: str, **kwargs):
        """更新检验项目配置"""
        if standard_name in self.test_mapping:
            self.test_mapping[standard_name].update(kwargs)
            self._build_reverse_index()

