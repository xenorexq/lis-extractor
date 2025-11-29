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
            self.progress.emit(0, f"正在加载文件: {os.path.basename(file_path)}")
            
            df, header_row, columns = load_excel_auto_header(file_path, max_rows)
            
            self.progress.emit(100, f"加载完成，共 {len(df)} 行")
            
            return df, header_row, columns
        
        except Exception as e:
            self.error.emit(f"加载文件失败: {str(e)}")
            raise
    
    def load_full_file(self, file_path: str, skip_rows: int = 0) -> pd.DataFrame:
        """
        加载完整文件
        """
        try:
            self.progress.emit(0, f"正在读取: {os.path.basename(file_path)}")
            
            df = pd.read_excel(file_path, header=skip_rows)
            
            # 清理列名
            df.columns = [str(col).strip() for col in df.columns]
            
            self.progress.emit(100, f"读取完成，共 {len(df)} 行")
            
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

