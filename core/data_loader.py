"""
数据加载模块
支持单文件、多文件、文件夹加载
"""
import os
from pathlib import Path
from typing import List, Union, Tuple
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal

from .utils import load_excel_auto_header
from .constants import LoaderConfig


class DataLoader(QObject):
    """
    数据加载器
    支持进度信号
    """
    progress = pyqtSignal(int, str)  # (percentage, message)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.files = []
    
    def find_excel_files(self, path: Union[str, Path]) -> List[str]:
        """
        查找 Excel 文件
        如果是文件，直接返回
        如果是文件夹，递归查找所有 Excel
        """
        path = Path(path)
        excel_files = []
        
        if path.is_file():
            if path.suffix.lower() in ['.xlsx', '.xls']:
                excel_files.append(str(path))
        elif path.is_dir():
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(('.xlsx', '.xls')) and not file.startswith('~'):
                        excel_files.append(os.path.join(root, file))
        
        self.files = excel_files
        return excel_files
    
    def load_preview(self, file_path: str, max_rows: int = 100) -> Tuple[pd.DataFrame, int, List[str]]:
        """
        加载预览数据（前 N 行）
        返回: (DataFrame, header_row, column_names)
        """
        try:
            self.progress.emit(0, f"正在打开文件: {os.path.basename(file_path)}")

            # 分阶段报告进度
            self.progress.emit(20, "读取Excel数据...")
            df, header_row, columns = load_excel_auto_header(file_path, max_rows)

            self.progress.emit(60, "处理列名...")
            # 列名已在 load_excel_auto_header 中处理

            self.progress.emit(80, "验证数据...")
            row_count = len(df)
            col_count = len(columns)

            self.progress.emit(100, f"加载完成: {row_count} 行, {col_count} 列")

            return df, header_row, columns

        except Exception as e:
            self.error.emit(f"加载文件失败: {str(e)}")
            raise
    
    def load_full_file(self, file_path: str, skip_rows: int = 0) -> pd.DataFrame:
        """
        加载完整文件

        优化措施:
        - 使用 string 类型减少内存使用
        - 检测大文件并发出警告
        """
        try:
            filename = os.path.basename(file_path)
            self.progress.emit(0, f"正在打开: {filename}")

            # 检查文件大小
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > LoaderConfig.LARGE_FILE_THRESHOLD_MB:
                self.progress.emit(10, f"⚠️ 大文件 ({file_size_mb:.1f}MB): {filename}")

            self.progress.emit(20, f"读取数据: {filename}")

            # 使用优化的 dtype 来减少内存使用
            # string 类型比 object 类型更节省内存
            df = pd.read_excel(
                file_path,
                header=skip_rows,
                dtype_backend='numpy_nullable',  # 使用新的 nullable dtypes
                engine='openpyxl'
            )

            self.progress.emit(70, f"处理列名: {filename}")
            # 清理列名
            df.columns = [str(col).strip() for col in df.columns]

            # 对于大数据集，尝试优化内存
            if len(df) > LoaderConfig.MEMORY_OPTIMIZATION_ROW_THRESHOLD:
                self.progress.emit(85, "优化内存使用...")
                # 将 object 列转换为 string 以节省内存
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].astype('string')

            self.progress.emit(100, f"读取完成: {len(df)} 行")

            return df

        except Exception as e:
            self.error.emit(f"读取文件失败 {file_path}: {str(e)}")
            raise
    
    def load_multiple_files(self, file_paths: List[str], skip_rows: int = 0) -> List[Tuple[str, pd.DataFrame]]:
        """
        加载多个文件
        返回: [(file_path, DataFrame), ...]
        """
        results = []
        total = len(file_paths)
        
        for idx, file_path in enumerate(file_paths):
            try:
                progress_pct = int((idx / total) * 100)
                self.progress.emit(progress_pct, f"正在处理 {idx+1}/{total}: {os.path.basename(file_path)}")
                
                df = self.load_full_file(file_path, skip_rows)
                results.append((file_path, df))
                
            except Exception as e:
                self.error.emit(f"跳过文件 {file_path}: {str(e)}")
                continue
        
        self.progress.emit(100, f"全部加载完成，共 {len(results)} 个文件")
        
        return results
    
    def validate_columns(self, df: pd.DataFrame, required_columns: List[str], min_match_ratio: float = 0.75) -> Tuple[bool, List[str]]:
        """
        验证文件列是否符合 profile 要求
        返回: (is_valid, missing_columns)
        """
        df_columns = set(df.columns)
        required_set = set(required_columns)

        matched = df_columns & required_set
        match_ratio = len(matched) / len(required_set) if required_set else 0

        is_valid = match_ratio >= min_match_ratio
        missing = list(required_set - matched)

        return is_valid, missing

    def scan_column_values(self, file_or_folder: str, column_name: str,
                          skip_rows: int = 0) -> Tuple[set, int]:
        """
        快速扫描指定列的所有唯一值（不加载完整数据）

        这个方法只读取指定的列，内存效率高，适合扫描大文件的所有检验项目名称。

        Args:
            file_or_folder: 文件或文件夹路径
            column_name: 要扫描的列名
            skip_rows: 跳过的行数（header位置）

        Returns:
            (unique_values: set, total_rows: int)
        """
        unique_values = set()
        total_rows = 0

        # 获取所有文件
        files = self.find_excel_files(file_or_folder)

        if not files:
            return unique_values, total_rows

        for idx, file_path in enumerate(files):
            try:
                self.progress.emit(
                    int((idx / len(files)) * 100),
                    f"扫描 {idx+1}/{len(files)}: {os.path.basename(file_path)}"
                )

                # 只读取指定的列，大幅减少内存使用
                # 使用usecols参数只加载需要的列
                df = pd.read_excel(
                    file_path,
                    header=skip_rows,
                    usecols=lambda x: str(x).strip() == column_name
                )

                if df.empty:
                    # 如果没找到列，尝试读取第一行获取列名
                    df_headers = pd.read_excel(file_path, header=skip_rows, nrows=0)
                    available_cols = [str(c).strip() for c in df_headers.columns]
                    self.error.emit(f"在 {os.path.basename(file_path)} 中未找到列 '{column_name}'。"
                                   f"可用列: {available_cols[:5]}...")
                    continue

                # 获取唯一值
                col_values = df.iloc[:, 0].dropna().astype(str).str.strip()
                unique_values.update(col_values.unique())
                total_rows += len(df)

            except Exception as e:
                self.error.emit(f"扫描文件失败 {os.path.basename(file_path)}: {str(e)}")
                continue

        self.progress.emit(100, f"扫描完成: {len(unique_values)} 个唯一值, {total_rows} 行")

        return unique_values, total_rows

    def scan_test_names(self, file_or_folder: str, test_name_column: str,
                       skip_rows: int = 0) -> dict:
        """
        扫描所有检验项目名称及其出现次数

        这是scan_column_values的增强版本，返回每个项目的出现次数。

        Args:
            file_or_folder: 文件或文件夹路径
            test_name_column: 检验项目名称列
            skip_rows: 跳过的行数

        Returns:
            {test_name: count, ...}
        """
        test_counts = {}
        files = self.find_excel_files(file_or_folder)

        if not files:
            return test_counts

        for idx, file_path in enumerate(files):
            try:
                self.progress.emit(
                    int((idx / len(files)) * 100),
                    f"扫描项目 {idx+1}/{len(files)}: {os.path.basename(file_path)}"
                )

                # 只读取test_name列
                df = pd.read_excel(
                    file_path,
                    header=skip_rows,
                    usecols=lambda x: str(x).strip() == test_name_column
                )

                if df.empty:
                    continue

                # 统计每个项目的出现次数
                col = df.iloc[:, 0].dropna().astype(str).str.strip()
                value_counts = col.value_counts()

                for test_name, count in value_counts.items():
                    test_counts[test_name] = test_counts.get(test_name, 0) + count

            except Exception as e:
                self.error.emit(f"扫描失败 {os.path.basename(file_path)}: {str(e)}")
                continue

        self.progress.emit(100, f"扫描完成: {len(test_counts)} 个检验项目")

        return test_counts

