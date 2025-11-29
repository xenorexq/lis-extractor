"""
质量控制报告模块
生成数据质量分析报告
"""
import pandas as pd
from typing import Dict, List
from datetime import datetime


class QCReporter:
    """
    质量控制报告生成器
    """
    
    def __init__(self):
        self.report = {}
    
    def analyze(self, df_raw: pd.DataFrame, df_processed: pd.DataFrame, 
                profile_name: str) -> Dict:
        """
        分析数据质量
        
        Args:
            df_raw: 原始数据
            df_processed: 处理后的数据
            profile_name: 配置文件名称
        
        Returns:
            质量报告字典
        """
        report = {
            'profile': profile_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'raw_data': self._analyze_raw(df_raw),
            'processed_data': self._analyze_processed(df_processed),
            'quality_metrics': self._calculate_metrics(df_raw, df_processed)
        }
        
        self.report = report
        return report
    
    def _analyze_raw(self, df: pd.DataFrame) -> Dict:
        """分析原始数据"""
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum()
        }
    
    def _analyze_processed(self, df: pd.DataFrame) -> Dict:
        """分析处理后的数据"""
        if df.empty:
            return {
                'total_rows': 0,
                'total_tests': 0,
                'test_distribution': {},
                'value_flags': {}
            }
        
        test_dist = {}
        if 'test_code' in df.columns:
            test_dist = df['test_code'].value_counts().to_dict()
        
        value_flags = {}
        if 'value_flag' in df.columns:
            value_flags = df['value_flag'].value_counts().to_dict()
        
        return {
            'total_rows': len(df),
            'total_tests': len(test_dist),
            'test_distribution': test_dist,
            'value_flags': value_flags,
            'missing_values': df.isnull().sum().to_dict()
        }
    
    def _calculate_metrics(self, df_raw: pd.DataFrame, df_processed: pd.DataFrame) -> Dict:
        """计算质量指标"""
        metrics = {
            'data_retention_rate': 0.0,
            'value_parse_success_rate': 0.0,
            'warnings': []
        }
        
        # 数据保留率
        if len(df_raw) > 0:
            metrics['data_retention_rate'] = len(df_processed) / len(df_raw)
        
        # 数值解析成功率
        if 'value_numeric' in df_processed.columns:
            non_null_values = df_processed['value_numeric'].notna().sum()
            if len(df_processed) > 0:
                metrics['value_parse_success_rate'] = non_null_values / len(df_processed)
        
        # 警告
        if metrics['data_retention_rate'] < 0.5:
            metrics['warnings'].append('数据保留率低于 50%，请检查配置是否正确')
        
        if metrics['value_parse_success_rate'] < 0.8:
            metrics['warnings'].append('数值解析成功率低于 80%，可能存在未处理的特殊格式')
        
        return metrics
    
    def generate_summary_text(self) -> str:
        """生成文本格式的摘要报告"""
        if not self.report:
            return "暂无报告数据"
        
        lines = []
        lines.append("=" * 60)
        lines.append("LIS 数据抽取质量报告")
        lines.append("=" * 60)
        lines.append(f"配置文件: {self.report['profile']}")
        lines.append(f"生成时间: {self.report['timestamp']}")
        lines.append("")
        
        lines.append("【原始数据】")
        raw = self.report['raw_data']
        lines.append(f"  总行数: {raw['total_rows']}")
        lines.append(f"  总列数: {raw['total_columns']}")
        lines.append(f"  重复行: {raw['duplicate_rows']}")
        lines.append("")
        
        lines.append("【处理后数据】")
        processed = self.report['processed_data']
        lines.append(f"  总行数: {processed['total_rows']}")
        lines.append(f"  检验项目数: {processed['total_tests']}")
        lines.append("")
        
        lines.append("【质量指标】")
        metrics = self.report['quality_metrics']
        lines.append(f"  数据保留率: {metrics['data_retention_rate']:.2%}")
        lines.append(f"  数值解析成功率: {metrics['value_parse_success_rate']:.2%}")
        
        if metrics['warnings']:
            lines.append("")
            lines.append("【警告】")
            for warning in metrics['warnings']:
                lines.append(f"  ⚠️  {warning}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def export_to_excel(self, output_path: str):
        """导出报告到 Excel"""
        if not self.report:
            return
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 摘要
            summary_data = {
                '指标': ['原始数据行数', '处理后行数', '检验项目数', '数据保留率', '数值解析成功率'],
                '值': [
                    self.report['raw_data']['total_rows'],
                    self.report['processed_data']['total_rows'],
                    self.report['processed_data']['total_tests'],
                    f"{self.report['quality_metrics']['data_retention_rate']:.2%}",
                    f"{self.report['quality_metrics']['value_parse_success_rate']:.2%}"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='摘要', index=False)
            
            # 项目分布
            if self.report['processed_data']['test_distribution']:
                test_dist = pd.DataFrame([
                    {'检验项目': k, '数量': v}
                    for k, v in self.report['processed_data']['test_distribution'].items()
                ])
                test_dist = test_dist.sort_values('数量', ascending=False)
                test_dist.to_excel(writer, sheet_name='项目分布', index=False)
            
            # 数值标志分布
            if self.report['processed_data']['value_flags']:
                flag_dist = pd.DataFrame([
                    {'标志类型': k, '数量': v}
                    for k, v in self.report['processed_data']['value_flags'].items()
                ])
                flag_dist.to_excel(writer, sheet_name='数值标志', index=False)

