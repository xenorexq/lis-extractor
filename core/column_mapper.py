"""
字段映射模块
将原始列映射为标准字段
"""
import pandas as pd
from typing import Dict, List, Optional


class ColumnMapper:
    """
    列映射器
    """
    
    # 标准字段定义
    STANDARD_FIELDS = [
        'patient_id',       # 患者ID（必填）
        'visit_id',         # 就诊ID
        'sample_datetime',  # 采样/检验日期时间（必填）
        'test_name',        # 检验项目名称（必填）
        'test_value',       # 检验结果值（必填）
        'unit',             # 单位
        'specimen_type',    # 标本类型
        'ref_range',        # 参考范围
        'result_flag',      # 结果标志（H/L等）
        'department',       # 科室
        'diagnosis',        # 诊断
        'ignore'            # 忽略此列
    ]
    
    REQUIRED_FIELDS = ['patient_id', 'sample_datetime', 'test_name', 'test_value']
    
    def __init__(self, mapping: Dict[str, str]):
        """
        mapping: {standard_field: original_column_name}
        例如: {'patient_id': '病人ID', 'test_name': '项目名称'}
        """
        self.mapping = mapping
        self.reverse_mapping = {v: k for k, v in mapping.items() if v}
    
    def validate(self) -> tuple:
        """
        验证映射是否包含所有必填字段
        返回: (is_valid, missing_fields)
        """
        mapped_fields = set(self.mapping.keys())
        required_fields = set(self.REQUIRED_FIELDS)
        
        missing = required_fields - mapped_fields
        
        return len(missing) == 0, list(missing)
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用映射到 DataFrame
        将原始列名重命名为标准字段名
        """
        # 只保留映射的列
        columns_to_keep = [col for col in df.columns if col in self.reverse_mapping]
        
        df_mapped = df[columns_to_keep].copy()
        
        # 重命名
        rename_dict = {orig_col: std_field 
                      for std_field, orig_col in self.mapping.items() 
                      if orig_col in df.columns and std_field != 'ignore'}
        
        df_mapped = df_mapped.rename(columns=rename_dict)
        
        return df_mapped
    
    def get_example_values(self, df: pd.DataFrame, n: int = 3) -> Dict[str, List]:
        """
        获取每个原始列的示例值
        用于 UI 展示
        """
        examples = {}
        for col in df.columns:
            # 获取非空的前 n 个值
            non_null_values = df[col].dropna().head(n).tolist()
            examples[col] = [str(v)[:50] for v in non_null_values]  # 限制长度
        
        return examples
    
    @classmethod
    def suggest_mapping(cls, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        自动建议列映射（基于关键词匹配）
        返回: {standard_field: suggested_column}
        """
        suggestions = {}
        
        # 关键词映射规则
        keywords = {
            'patient_id': ['病人', '患者', 'patient', 'pid', '病案号', '住院号'],
            'visit_id': ['就诊', '门诊', 'visit', '住院病人门诊'],
            'sample_datetime': ['日期', '时间', 'date', 'time', '检验日期', '采样时间'],
            'test_name': ['项目', '检验项目', 'test', 'item', '项目名称'],
            'test_value': ['结果', '检验结果', 'value', 'result', '测定结果'],
            'unit': ['单位', 'unit'],
            'specimen_type': ['标本', 'specimen', '样本类型'],
            'ref_range': ['参考', 'reference', '参考范围', '参考值'],
            'result_flag': ['标志', 'flag', '结果标志', '异常标志'],
            'department': ['科室', 'department', '送检科室'],
            'diagnosis': ['诊断', 'diagnosis']
        }
        
        for std_field, kws in keywords.items():
            matched = None
            for col in columns:
                col_lower = col.lower()
                if any(kw.lower() in col_lower for kw in kws):
                    matched = col
                    break
            suggestions[std_field] = matched
        
        return suggestions
    
    def to_dict(self) -> Dict:
        """转为字典（用于保存到 YAML）"""
        return {k: v for k, v in self.mapping.items() if v and k != 'ignore'}
    
    @classmethod
    def from_dict(cls, mapping_dict: Dict) -> 'ColumnMapper':
        """从字典创建（用于从 YAML 加载）"""
        return cls(mapping_dict)

