"""
数据抽取引擎
整合所有模块，执行完整的 ETL 流程
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import yaml
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .data_loader import DataLoader
from .column_mapper import ColumnMapper
from .test_mapper import TestMapper
from .value_parser import ValueParser
from .qc_reporter import QCReporter
from .utils import parse_datetime, generate_run_id


class ExtractorEngine(QObject):
    """
    数据抽取引擎（支持多线程）
    """
    progress = pyqtSignal(int, str)  # (percentage, message)
    log = pyqtSignal(str)  # log message
    finished = pyqtSignal(dict)  # result dict
    error = pyqtSignal(str)
    
    def __init__(self, profile_path: str):
        super().__init__()
        self.profile_path = profile_path
        self.profile = None
        self.run_id = generate_run_id()
        self._is_cancelled = False
    
    def load_profile(self) -> bool:
        """加载 profile 配置"""
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                self.profile = yaml.safe_load(f)
            self.log.emit(f"✓ 加载配置文件: {self.profile['id']}")
            return True
        except Exception as e:
            self.error.emit(f"加载配置文件失败: {str(e)}")
            return False
    
    def cancel(self):
        """取消运行"""
        self._is_cancelled = True
        self.log.emit("⚠️ 用户取消操作")
    
    def run(self, file_or_folder: str, output_dir: str):
        """
        执行完整的抽取流程
        
        Args:
            file_or_folder: 输入文件或文件夹路径
            output_dir: 输出目录
        """
        try:
            if not self.load_profile():
                return
            
            self.progress.emit(0, "开始处理...")
            
            # 1. 查找所有 Excel 文件
            self.log.emit("📁 扫描文件...")
            loader = DataLoader()
            excel_files = loader.find_excel_files(file_or_folder)
            self.log.emit(f"✓ 找到 {len(excel_files)} 个 Excel 文件")
            
            if not excel_files:
                self.error.emit("未找到任何 Excel 文件")
                return
            
            self.progress.emit(10, f"找到 {len(excel_files)} 个文件")
            
            # 2. 加载所有文件
            self.log.emit("📖 读取文件...")
            skip_rows = self.profile.get('signature', {}).get('skip_top_rows', 0)
            
            all_data = []
            for idx, file_path in enumerate(excel_files):
                if self._is_cancelled:
                    return
                
                try:
                    progress_pct = 10 + int((idx / len(excel_files)) * 30)
                    self.progress.emit(progress_pct, f"读取 {idx+1}/{len(excel_files)}")
                    
                    df = loader.load_full_file(file_path, skip_rows)
                    all_data.append((file_path, df))
                    self.log.emit(f"✓ {os.path.basename(file_path)}: {len(df)} 行")
                except Exception as e:
                    self.log.emit(f"✗ 跳过 {os.path.basename(file_path)}: {str(e)}")
            
            if not all_data:
                self.error.emit("所有文件读取失败")
                return
            
            # 3. 合并数据
            self.progress.emit(40, "合并数据...")
            self.log.emit("🔗 合并所有数据...")
            df_combined = pd.concat([df for _, df in all_data], ignore_index=True)
            self.log.emit(f"✓ 合并后总行数: {len(df_combined)}")
            
            # 4. 应用列映射
            self.progress.emit(50, "应用字段映射...")
            self.log.emit("🔄 应用字段映射...")
            column_mapping = self.profile.get('column_mapping', {})
            mapper = ColumnMapper(column_mapping)
            df_mapped = mapper.apply(df_combined)
            self.log.emit(f"✓ 映射字段: {list(column_mapping.keys())}")
            
            # 5. 应用检验项目映射
            self.progress.emit(60, "标准化检验项目...")
            self.log.emit("🔬 标准化检验项目...")
            test_mapping = self.profile.get('test_mapping', {})
            test_mapper = TestMapper(test_mapping)
            df_mapped = test_mapper.apply(df_mapped)
            
            # 过滤选中的项目
            selected_tests = set(test_mapping.keys())
            df_filtered = test_mapper.filter_selected_tests(df_mapped, selected_tests)
            self.log.emit(f"✓ 保留 {len(selected_tests)} 个项目，{len(df_filtered)} 行")
            
            # 6. 解析数值
            self.progress.emit(70, "解析检验结果...")
            self.log.emit("🔢 解析检验结果...")
            value_parsing = self.profile.get('value_parsing', {})
            value_parser = ValueParser(value_parsing)
            df_parsed = value_parser.apply(df_filtered)
            
            # 7. 处理日期时间
            self.log.emit("📅 处理日期时间...")
            if 'sample_datetime' in df_parsed.columns:
                # 保存原始值用于诊断
                original_values = df_parsed['sample_datetime'].copy()
                
                # 先检查原始列中有多少非空值
                original_non_null = original_values.notna().sum()
                self.log.emit(f"   原始数据中有 {original_non_null} 行包含日期")
                
                # 使用 pandas 的向量化日期解析（比 apply 快得多）
                df_parsed['sample_datetime'] = pd.to_datetime(
                    df_parsed['sample_datetime'],
                    errors='coerce',  # 无法解析的设为 NaT
                    infer_datetime_format=True,  # 自动推断格式（速度更快）
                )
                
                # 检查解析后有多少成功
                parsed_non_null = df_parsed['sample_datetime'].notna().sum()
                self.log.emit(f"   成功解析 {parsed_non_null} 个日期")
                
                # 详细诊断失败的情况
                if parsed_non_null < original_non_null:
                    failed_count = original_non_null - parsed_non_null
                    self.log.emit(f"   ⚠️ 警告：{failed_count} 个日期解析失败")
                    
                    # 显示失败的样本（用于调试）
                    failed_mask = df_parsed['sample_datetime'].isna() & original_values.notna()
                    if failed_mask.any():
                        failed_samples = original_values.loc[failed_mask].head(5).tolist()
                        self.log.emit(f"   失败样本: {failed_samples}")
                
                if parsed_non_null == 0 and original_non_null > 0:
                    self.log.emit("   ❌ 错误：所有日期解析失败！请检查日期格式")
            else:
                self.log.emit("   ⚠️ 警告：未找到 sample_datetime 列")
            
            # 8. 生成 labs_long
            self.progress.emit(80, "生成标准化输出...")
            self.log.emit("📋 生成标准化长表...")
            
            # 选择输出列
            output_columns = [
                'patient_id', 'visit_id', 'sample_datetime',
                'test_name', 'test_code', 'test_value', 'value_numeric', 'value_flag',
                'unit', 'unit_std', 'ref_range', 'result_flag', 'specimen_type'
            ]
            
            available_columns = [col for col in output_columns if col in df_parsed.columns]
            labs_long = df_parsed[available_columns].copy()
            
            # 添加元数据
            labs_long['profile_id'] = self.profile['id']
            labs_long['run_id'] = self.run_id
            
            self.log.emit(f"✓ 生成 labs_long: {len(labs_long)} 行")
            
            # 9. 生成质量报告
            self.progress.emit(90, "生成质量报告...")
            self.log.emit("📊 生成质量报告...")
            qc = QCReporter()
            report = qc.analyze(df_combined, labs_long, self.profile['id'])
            self.log.emit("✓ 质量分析完成")
            
            # 10. 导出文件
            self.progress.emit(95, "导出文件...")
            self.log.emit("💾 导出文件...")
            
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 导出 labs_long
            output_file = os.path.join(output_dir, f'labs_long_{timestamp}.xlsx')
            labs_long.to_excel(output_file, index=False, engine='openpyxl')
            self.log.emit(f"✓ 导出: {os.path.basename(output_file)}")
            
            # 导出质量报告
            qc_file = os.path.join(output_dir, f'qc_report_{timestamp}.xlsx')
            qc.export_to_excel(qc_file)
            self.log.emit(f"✓ 导出: {os.path.basename(qc_file)}")
            
            # 11. 完成
            self.progress.emit(100, "完成!")
            self.log.emit("=" * 50)
            self.log.emit("✅ 抽取完成!")
            self.log.emit(f"   输出目录: {output_dir}")
            self.log.emit(f"   数据行数: {len(labs_long)}")
            self.log.emit(f"   检验项目: {len(selected_tests)}")
            self.log.emit("=" * 50)
            
            result = {
                'success': True,
                'output_dir': output_dir,
                'labs_long_file': output_file,
                'qc_report_file': qc_file,
                'total_rows': len(labs_long),
                'total_tests': len(selected_tests),
                'report': report
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"处理失败: {str(e)}")
            import traceback
            self.log.emit(traceback.format_exc())


class ExtractorThread(QThread):
    """
    抽取引擎线程包装器
    """
    def __init__(self, engine: ExtractorEngine, file_or_folder: str, output_dir: str):
        super().__init__()
        self.engine = engine
        self.file_or_folder = file_or_folder
        self.output_dir = output_dir
    
    def run(self):
        """执行线程"""
        self.engine.run(self.file_or_folder, self.output_dir)

