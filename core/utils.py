"""
工具函数模块
"""
import re
from datetime import datetime
from typing import Optional, List, Any
import pandas as pd


def detect_header_row(df: pd.DataFrame, max_rows: int = 10) -> int:
    """
    自动检测 Excel 中的 header 行位置
    通过分析前几行，找到最可能是列名的那一行
    """
    for idx in range(min(max_rows, len(df))):
        row = df.iloc[idx]
        # 检查是否大部分值都是字符串且不为空
        non_null_count = row.notna().sum()
        str_count = sum(isinstance(val, str) for val in row)
        
        if non_null_count > len(row) * 0.5 and str_count > len(row) * 0.5:
            return idx
    return 0


def load_excel_auto_header(file_path: str, max_preview_rows: int = 100) -> tuple:
    """
    加载 Excel 文件，自动检测 header
    返回: (DataFrame, header_row_index, original_columns)
    """
    # 先读取原始数据（无 header）
    df_raw = pd.read_excel(file_path, header=None, nrows=max_preview_rows)
    
    # 检测 header 行
    header_row = detect_header_row(df_raw)
    
    # 重新读取，指定 header
    df = pd.read_excel(file_path, header=header_row, nrows=max_preview_rows)
    
    # 清理列名（去除空格、特殊字符）
    original_columns = df.columns.tolist()
    df.columns = [str(col).strip() for col in df.columns]
    
    return df, header_row, original_columns


def normalize_column_name(col_name: str) -> str:
    """标准化列名"""
    if pd.isna(col_name):
        return "unnamed"
    col_name = str(col_name).strip()
    col_name = re.sub(r'\s+', '_', col_name)
    col_name = re.sub(r'[^\w\u4e00-\u9fff_]', '', col_name)
    return col_name


def parse_datetime(value: Any) -> Optional[datetime]:
    """
    解析日期时间，支持多种格式
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    
    # 如果是日期类型
    if hasattr(value, 'date'):
        try:
            return datetime.combine(value.date(), datetime.min.time())
        except:
            pass
    
    if isinstance(value, str):
        # 清理字符串
        value = value.strip()
        if not value:
            return None
        
        # 尝试多种格式
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y.%m.%d',
            '%Y%m%d',
            '%Y年%m月%d日',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except:
                continue
        
        # 尝试使用 pandas 的智能解析
        try:
            return pd.to_datetime(value, errors='coerce').to_pydatetime()
        except:
            pass
    
    # 尝试直接转换为 pandas datetime
    try:
        dt = pd.to_datetime(value, errors='coerce')
        if pd.notna(dt):
            return dt.to_pydatetime()
    except:
        pass
    
    return None


def extract_numeric(value: str) -> Optional[float]:
    """
    从字符串中提取数值，支持多种临床格式
    
    支持格式：
    - 普通数字：123, 45.67
    - 科学计数法：1.5e-3, 2E+5
    - 幂表示：10^3, 2^10
    - 千分位：1,234.56
    - 带符号：<0.5, >1000, ≤5, ≥10
    - 滴度：1:128 → 128 (提取冒号后的数)
    - 区间：1.5-2.0 → 1.75 (取中值)
    
    例如: 
    - "<0.5" -> 0.5
    - "1.5e-3" -> 0.0015
    - "10^3" -> 1000.0
    - "1:128" -> 128.0
    - "1.5-2.0" -> 1.75
    """
    if pd.isna(value):
        return None
    
    value_str = str(value).strip()
    
    # 移除千分位逗号
    value_str = value_str.replace(',', '')
    
    # 1. 尝试直接转换（支持科学计数法）
    # 例如: "1.5e-3", "2E+5", "123.45"
    try:
        return float(value_str)
    except:
        pass
    
    # 2. 处理幂表示法: 10^3 → 1000
    if '^' in value_str:
        match = re.search(r'(\d+\.?\d*)\s*\^\s*(\d+)', value_str)
        if match:
            try:
                base = float(match.group(1))
                exp = float(match.group(2))
                return base ** exp
            except:
                pass
    
    # 3. 处理滴度: 1:128 → 128 (通常关注滴度值)
    if ':' in value_str:
        parts = value_str.split(':')
        if len(parts) == 2:
            try:
                return float(parts[1].strip())  # 返回冒号后的数值
            except:
                pass
    
    # 4. 处理区间: 1.5-2.0 → 1.75 (取中值)
    # 注意：需要区分负号和区间的连字符
    if '-' in value_str and not value_str.startswith('-'):
        # 查找形如 "数字-数字" 的模式
        match = re.match(r'^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$', value_str)
        if match:
            try:
                lower = float(match.group(1))
                upper = float(match.group(2))
                return (lower + upper) / 2  # 取中值
            except:
                pass
    
    # 5. 移除常见符号后提取数字
    # 处理 <, >, ≤, ≥ 等符号
    cleaned = re.sub(r'[<>≤≥~±]', '', value_str)
    
    # 6. 标准正则提取（支持负数、小数、科学计数法）
    match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', cleaned)
    if match:
        try:
            return float(match.group())
        except:
            return None
    
    return None


def detect_special_value_patterns(series: pd.Series) -> dict:
    """
    检测一列数据中的特殊值模式
    返回: {
        'less_than': ['<0.5', '<0.1'],
        'greater_than': ['>1000', '>500'],
        'positive': ['阳性', '弱阳性'],
        'negative': ['阴性'],
        'invalid': ['溶血', '样本不足', '--']
    }
    """
    patterns = {
        'less_than': set(),
        'greater_than': set(),
        'positive': set(),
        'negative': set(),
        'invalid': set()
    }
    
    for val in series.dropna().unique():
        val_str = str(val).strip()
        
        if val_str.startswith('<'):
            patterns['less_than'].add(val_str)
        elif val_str.startswith('>'):
            patterns['greater_than'].add(val_str)
        elif any(kw in val_str for kw in ['阳性', '阳']):
            patterns['positive'].add(val_str)
        elif any(kw in val_str for kw in ['阴性', '阴']):
            patterns['negative'].add(val_str)
        elif val_str in ['--', '/', '#', '未检出', '溶血', '样本不足', '标本凝集', 'NA', 'N/A']:
            patterns['invalid'].add(val_str)
    
    # 转为列表
    return {k: sorted(list(v)) for k, v in patterns.items()}


def detect_value_formats(series: pd.Series, max_samples: int = 100) -> dict:
    """
    检测数据列中的数值格式分布
    
    返回: {
        'format_counts': {
            'normal': 850,           # 普通数字
            'scientific': 50,        # 科学计数法
            'power': 10,             # 幂表示
            'titer': 80,             # 滴度
            'range': 20,             # 区间
            'less_than': 30,         # 小于号
            'greater_than': 15,      # 大于号
            'text_positive': 10,     # 阳性文本
            'text_negative': 5,      # 阴性文本
            'invalid': 0             # 无法识别
        },
        'samples': {
            'normal': ['123.45', '67.8'],
            'scientific': ['1.5e-3', '2E+5'],
            ...
        }
    }
    """
    format_counts = {
        'normal': 0,
        'scientific': 0,
        'power': 0,
        'titer': 0,
        'range': 0,
        'less_than': 0,
        'greater_than': 0,
        'text_positive': 0,
        'text_negative': 0,
        'invalid': 0
    }
    
    format_samples = {k: [] for k in format_counts.keys()}
    
    # 获取唯一值样本
    unique_values = series.dropna().unique()
    samples_to_check = unique_values[:max_samples] if len(unique_values) > max_samples else unique_values
    
    # 文本关键词
    positive_keywords = ['阳性', '阳', '+', '阳（', 'positive']
    negative_keywords = ['阴性', '阴', '阴（', 'negative']
    invalid_keywords = ['溶血', '样本不足', '标本凝集', '未检出', '--', '/', '#', 'NA', 'N/A']
    
    for val in samples_to_check:
        val_str = str(val).strip()
        
        # 检查无效值
        if any(kw in val_str for kw in invalid_keywords):
            format_counts['invalid'] += 1
            if len(format_samples['invalid']) < 3:
                format_samples['invalid'].append(val_str)
            continue
        
        # 检查阳性文本
        if any(kw in val_str for kw in positive_keywords):
            format_counts['text_positive'] += 1
            if len(format_samples['text_positive']) < 3:
                format_samples['text_positive'].append(val_str)
            continue
        
        # 检查阴性文本
        if any(kw in val_str for kw in negative_keywords):
            format_counts['text_negative'] += 1
            if len(format_samples['text_negative']) < 3:
                format_samples['text_negative'].append(val_str)
            continue
        
        # 检查小于号
        if val_str.startswith('<') or val_str.startswith('≤'):
            format_counts['less_than'] += 1
            if len(format_samples['less_than']) < 3:
                format_samples['less_than'].append(val_str)
            continue
        
        # 检查大于号
        if val_str.startswith('>') or val_str.startswith('≥'):
            format_counts['greater_than'] += 1
            if len(format_samples['greater_than']) < 3:
                format_samples['greater_than'].append(val_str)
            continue
        
        # 检查科学计数法
        if re.search(r'\d+\.?\d*[eE][-+]?\d+', val_str):
            format_counts['scientific'] += 1
            if len(format_samples['scientific']) < 3:
                format_samples['scientific'].append(val_str)
            continue
        
        # 检查幂表示
        if '^' in val_str and re.search(r'\d+\s*\^\s*\d+', val_str):
            format_counts['power'] += 1
            if len(format_samples['power']) < 3:
                format_samples['power'].append(val_str)
            continue
        
        # 检查滴度
        if re.match(r'\d+:\d+', val_str):
            format_counts['titer'] += 1
            if len(format_samples['titer']) < 3:
                format_samples['titer'].append(val_str)
            continue
        
        # 检查区间
        if re.match(r'^\d+\.?\d*\s*-\s*\d+\.?\d*$', val_str):
            format_counts['range'] += 1
            if len(format_samples['range']) < 3:
                format_samples['range'].append(val_str)
            continue
        
        # 尝试解析为普通数字
        try:
            float(val_str.replace(',', ''))
            format_counts['normal'] += 1
            if len(format_samples['normal']) < 3:
                format_samples['normal'].append(val_str)
        except:
            # 无法识别
            format_counts['invalid'] += 1
            if len(format_samples['invalid']) < 3:
                format_samples['invalid'].append(val_str)
    
    # 统计总数
    total = sum(format_counts.values())
    
    return {
        'format_counts': format_counts,
        'samples': format_samples,
        'total': total
    }


def generate_run_id() -> str:
    """生成运行 ID（时间戳）"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def safe_float(value: Any) -> Optional[float]:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def validate_required_fields(mapping: dict, required: List[str]) -> tuple:
    """
    验证必填字段是否都已映射
    返回: (is_valid, missing_fields)
    """
    mapped_fields = set(mapping.keys())
    required_fields = set(required)
    missing = required_fields - mapped_fields
    
    return len(missing) == 0, list(missing)

