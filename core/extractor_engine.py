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
            self.progress.emit(40, "准备合并数据...")
            self.log.emit("🔗 合并所有数据...")

            # 分批合并以提供进度反馈
            if len(all_data) > 1:
                total_files = len(all_data)
                dfs_to_concat = []

                # 收集阶段 (40-42%)
                for idx, (_, df) in enumerate(all_data):
                    dfs_to_concat.append(df)
                    if (idx + 1) % max(1, total_files // 3) == 0:
                        pct = 40 + int((idx / total_files) * 2)
                        self.progress.emit(pct, f"收集数据 {idx+1}/{total_files}...")

                # 实际合并阶段 (42-45%) - 这是耗时操作
                self.progress.emit(42, "执行合并操作...")
                df_combined = pd.concat(dfs_to_concat, ignore_index=True)
                self.progress.emit(45, f"合并完成: {len(df_combined):,} 行")
            else:
                df_combined = all_data[0][1].copy() if all_data else pd.DataFrame()
                self.progress.emit(45, f"数据准备完成: {len(df_combined):,} 行")

            self.log.emit(f"✓ 合并后总行数: {len(df_combined)}")
            
            # 4. 应用列映射
            self.progress.emit(46, "应用字段映射...")
            self.log.emit("🔄 应用字段映射...")
            column_mapping = self.profile.get('column_mapping', {})
            mapper = ColumnMapper(column_mapping)

            self.progress.emit(48, f"映射 {len(column_mapping)} 个字段...")
            df_mapped = mapper.apply(df_combined)

            self.progress.emit(50, "字段映射完成")
            self.log.emit(f"✓ 映射字段: {list(column_mapping.keys())}")
            
            # 5. 应用检验项目映射
            self.progress.emit(60, "标准化检验项目...")
            self.log.emit("🔬 标准化检验项目...")
            test_mapping = self.profile.get('test_mapping', {})
            test_mapper = TestMapper(test_mapping)

            # 在映射前，检测完整数据中的所有项目
            if 'test_name' in df_mapped.columns:
                all_tests_in_data = set(df_mapped['test_name'].dropna().unique())
                selected_tests = set(test_mapping.keys())

                # 检测是否有未在profile中选择的新项目
                new_tests = all_tests_in_data - selected_tests
                if new_tests:
                    self.log.emit(f"⚠️ 警告: 发现 {len(new_tests)} 个预览时未出现的检验项目:")
                    # 显示前10个新项目
                    for test in list(new_tests)[:10]:
                        self.log.emit(f"   - {test}")
                    if len(new_tests) > 10:
                        self.log.emit(f"   ... 还有 {len(new_tests)-10} 个")
                    self.log.emit(f"   这些项目将被过滤掉（因为drop_unknown_tests=True）")
                    self.log.emit(f"   如需包含，请重新运行向导并选择更大的预览行数")

            df_mapped = test_mapper.apply(df_mapped)

            # 过滤选中的项目
            selected_tests = set(test_mapping.keys())
            df_filtered = test_mapper.filter_selected_tests(df_mapped, selected_tests)
            self.log.emit(f"✓ 保留 {len(selected_tests)} 个项目，{len(df_filtered)} 行")
            
            # 6. 解析数值
            self.progress.emit(65, "解析检验结果...")
            self.log.emit("🔢 解析检验结果...")
            value_parsing = self.profile.get('value_parsing', {})
            value_parser = ValueParser(value_parsing)

            self.progress.emit(68, f"解析 {len(df_filtered)} 行数值...")
            df_parsed = value_parser.apply(df_filtered)
            self.progress.emit(72, "数值解析完成")
            
            # 7. 处理日期时间
            self.progress.emit(74, "处理日期时间...")
            self.log.emit("📅 处理日期时间...")
            if 'sample_datetime' in df_parsed.columns:
                # 先统计原始非空值数量（不复制整列，只计数）
                original_non_null = df_parsed['sample_datetime'].notna().sum()
                self.log.emit(f"   原始数据中有 {original_non_null} 行包含日期")

                # 如果有大量日期需要诊断失败情况，才保存样本
                if original_non_null > 0:
                    # 只保存前10个原始值样本用于诊断（而非整列复制）
                    original_samples = df_parsed['sample_datetime'].dropna().head(10).tolist()

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

                    # 显示原始样本（用于调试格式问题）
                    if original_samples:
                        self.log.emit(f"   原始数据样本: {original_samples[:5]}")

                if parsed_non_null == 0 and original_non_null > 0:
                    self.log.emit("   ❌ 错误：所有日期解析失败！请检查日期格式")
                elif parsed_non_null < original_non_null * 0.5 and original_non_null > 10:
                    # 如果失败率超过50%且有足够样本，发出警告
                    failure_rate = (original_non_null - parsed_non_null) / original_non_null * 100
                    self.log.emit(f"   ⚠️ 警告：日期解析失败率较高 ({failure_rate:.1f}%)，建议检查日期格式")
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
            
            # 动态添加 I just want it 列
            ijwi_cols = [col for col in df_parsed.columns if col.startswith('ijwi_')]
            output_columns.extend(sorted(ijwi_cols))
            
            available_columns = [col for col in output_columns if col in df_parsed.columns]
            labs_long = df_parsed[available_columns].copy()
            
            # 添加元数据
            labs_long['profile_id'] = self.profile['id']
            labs_long['run_id'] = self.run_id
            
            self.log.emit(f"✓ 生成 labs_long: {len(labs_long)} 行")
            
            # 9. 生成质量报告
            self.progress.emit(85, "生成质量报告...")
            self.log.emit("📊 生成质量报告...")
            qc = QCReporter()
            report = qc.analyze(df_combined, labs_long, self.profile['id'])
            self.log.emit("✓ 质量分析完成")

            # 10. 导出文件
            self.progress.emit(90, "导出文件...")
            self.log.emit("💾 导出文件...")

            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self.error.emit(f"无法创建输出目录 (权限不足): {output_dir}")
                return
            except OSError as e:
                self.error.emit(f"创建输出目录失败: {str(e)}")
                return

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 导出 labs_long
            self.progress.emit(92, f"导出数据 ({len(labs_long)} 行)...")
            output_file = os.path.join(output_dir, f'labs_long_{timestamp}.xlsx')

            try:
                labs_long.to_excel(output_file, index=False, engine='openpyxl')
                self.log.emit(f"✓ 导出: {os.path.basename(output_file)}")
            except PermissionError:
                self.error.emit(f"无法写入文件 (权限不足): {output_file}")
                return
            except IOError as e:
                self.error.emit(f"导出数据失败 (磁盘错误): {str(e)}")
                return
            except Exception as e:
                self.error.emit(f"导出数据失败: {str(e)}")
                return

            # 导出质量报告
            self.progress.emit(97, "导出质量报告...")
            qc_file = os.path.join(output_dir, f'qc_report_{timestamp}.xlsx')

            try:
                qc.export_to_excel(qc_file)
                self.log.emit(f"✓ 导出: {os.path.basename(qc_file)}")
            except PermissionError:
                self.log.emit(f"⚠️ 质量报告导出失败 (权限不足): {qc_file}")
                # 质量报告失败不应阻止主流程
            except Exception as e:
                self.log.emit(f"⚠️ 质量报告导出失败: {str(e)}")
            
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

