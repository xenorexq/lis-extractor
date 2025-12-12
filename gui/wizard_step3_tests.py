"""
向导 Step 3: 选择检验项目
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QMessageBox,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QApplication, QProgressDialog)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
import pandas as pd

from core import TestMapper, ColumnMapper, DataLoader, UserMessage
from .components import CheckableTableWidget, NavigationButtons


class FullScanThread(QThread):
    """后台扫描线程"""
    finished = pyqtSignal(dict)  # {test_name: count}
    progress = pyqtSignal(int, str)  # (percentage, message)
    error = pyqtSignal(str)

    def __init__(self, input_path: str, test_name_column: str, skip_rows: int = 0):
        super().__init__()
        self.input_path = input_path
        self.test_name_column = test_name_column
        self.skip_rows = skip_rows
        self._is_cancelled = False

    def cancel(self):
        """取消操作"""
        self._is_cancelled = True

    def run(self):
        """执行扫描"""
        try:
            if self._is_cancelled:
                return

            loader = DataLoader()
            loader.progress.connect(self.progress.emit)
            loader.error.connect(self.error.emit)

            result = loader.scan_test_names(
                self.input_path,
                self.test_name_column,
                self.skip_rows
            )

            # 检查取消状态，避免在取消后发射信号
            if self._is_cancelled:
                return

            self.finished.emit(result)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))


class WizardStep3Tests(QWidget):
    """
    Step 3: 选择检验项目
    """
    next_step = pyqtSignal(dict)
    previous_step = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df_preview = None
        self.mapper = None
        self.test_stats = None
        self.selected_tests = set()
        self.input_path = None
        self.header_row = 0
        self.test_name_column = None  # 原始列名
        self.full_scan_result = None  # 完整扫描结果
        self.scan_thread = None

        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 3: 选择检验项目</h2>")
        layout.addWidget(title)
        
        desc = QLabel("从数据中扫描到的所有检验项目，请勾选需要抽取的项目")
        layout.addWidget(desc)
        
        # 搜索和全选区
        control_layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索:")
        search_label.setMinimumWidth(50)
        control_layout.addWidget(search_label)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入项目名称进行搜索...")
        self.search_edit.textChanged.connect(self.filter_tests)
        control_layout.addWidget(self.search_edit, stretch=1)
        
        # 全选/全不选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setMinimumWidth(80)
        self.select_all_btn.clicked.connect(lambda: self.test_table.check_all(True))
        control_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.setMinimumWidth(80)
        self.deselect_all_btn.clicked.connect(lambda: self.test_table.check_all(False))
        control_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(control_layout)

        # 扫描完整数据按钮（核心功能：从根源解决数据遗漏问题）
        scan_layout = QHBoxLayout()
        self.full_scan_btn = QPushButton("🔍 扫描完整数据")
        self.full_scan_btn.setToolTip("扫描完整文件中的所有检验项目，确保不遗漏任何项目")
        self.full_scan_btn.clicked.connect(self.start_full_scan)
        scan_layout.addWidget(self.full_scan_btn)

        self.scan_status_label = QLabel("")
        scan_layout.addWidget(self.scan_status_label, stretch=1)

        layout.addLayout(scan_layout)
        
        # 项目表格
        test_group = QGroupBox("检验项目列表")
        test_layout = QVBoxLayout()
        
        self.info_label = QLabel("未加载数据")
        test_layout.addWidget(self.info_label)
        
        self.test_table = CheckableTableWidget()
        self.test_table.setMinimumHeight(300)
        self.test_table.selection_changed.connect(self.update_selection_count)
        test_layout.addWidget(self.test_table)
        
        self.selection_label = QLabel("已选择: 0 个项目")
        test_layout.addWidget(self.selection_label)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=True)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.previous_clicked.connect(self.previous_step.emit)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
    
    def load_data(self, data: dict):
        """加载数据"""
        self.df_preview = data['df_preview']
        self.mapper = data['mapper']
        self.input_path = data.get('input_path', '')
        self.header_row = data.get('header_row', 0)

        # 获取test_name对应的原始列名
        mapping = data.get('mapping', {})
        self.test_name_column = mapping.get('test_name', None)

        # 应用映射
        df_mapped = self.mapper.apply(self.df_preview)

        # 统计检验项目
        if 'test_name' not in df_mapped.columns:
            QMessageBox.warning(
                self,
                UserMessage.format_title(UserMessage.Action.VALIDATE, UserMessage.Type.ERROR),
                UserMessage.format_validation_error(["test_name"], "字段")
            )
            return

        temp_mapper = TestMapper()
        self.test_stats = temp_mapper.get_test_statistics(df_mapped, 'test_name')

        # 填充表格
        self._populate_table_from_stats()

        # 更新信息
        preview_rows = len(self.df_preview)
        info_text = f"✓ 扫描到 {len(self.test_stats)} 个不同的检验项目 (基于预览的 {preview_rows:,} 行数据)"

        # 添加提示：点击按钮可扫描完整数据
        info_text += "\n💡 点击「扫描完整数据」可确保不遗漏任何检验项目"

        self.info_label.setText(info_text)
        self.update_selection_count()

        # 启用扫描按钮
        self.full_scan_btn.setEnabled(bool(self.input_path and self.test_name_column))

    def _populate_table_from_stats(self):
        """从统计数据填充表格"""
        # 使用向量化操作代替 iterrows()，性能提升约100倍
        items = list(zip(
            self.test_stats['test_name'].tolist(),
            self.test_stats['count'].tolist()
        ))

        self.test_table.load_items(items, ['项目名称', '出现次数'])

    def start_full_scan(self):
        """开始完整扫描"""
        if not self.input_path or not self.test_name_column:
            QMessageBox.warning(
                self,
                UserMessage.format_title(UserMessage.Action.SCAN, UserMessage.Type.ERROR),
                UserMessage.format_validation_error(
                    ["文件路径"] if not self.input_path else [] +
                    ["检验项目列"] if not self.test_name_column else [],
                    "信息"
                )
            )
            return

        # 禁用按钮，显示进度
        self.full_scan_btn.setEnabled(False)
        self.full_scan_btn.setText("扫描中...")
        self.scan_status_label.setText("正在扫描完整数据...")

        # 创建并启动扫描线程
        self.scan_thread = FullScanThread(
            self.input_path,
            self.test_name_column,
            self.header_row
        )
        self.scan_thread.progress.connect(self._on_scan_progress)
        self.scan_thread.finished.connect(self._on_scan_finished)
        self.scan_thread.error.connect(self._on_scan_error)
        self.scan_thread.start()

    def _on_scan_progress(self, percentage: int, message: str):
        """扫描进度更新"""
        self.scan_status_label.setText(f"{message} ({percentage}%)")
        QApplication.processEvents()

    def _on_scan_finished(self, result: dict):
        """扫描完成"""
        self.full_scan_result = result
        self.full_scan_btn.setText("🔍 扫描完整数据")
        self.full_scan_btn.setEnabled(True)

        # 将结果转换为DataFrame格式
        if result:
            # 保存当前选中的项目
            previously_selected = set(self.test_table.get_checked_items(column_index=1))

            # 创建新的统计数据
            data = [{'test_name': name, 'count': count} for name, count in result.items()]
            self.test_stats = pd.DataFrame(data).sort_values('count', ascending=False)

            # 重新填充表格
            self._populate_table_from_stats()

            # 恢复之前选中的项目
            for i in range(self.test_table.rowCount()):
                test_name = self.test_table.item(i, 1).text()
                if test_name in previously_selected:
                    self.test_table.item(i, 0).setCheckState(Qt.CheckState.Checked)

            # 计算新发现的项目
            preview_tests = set(self.df_preview['test_name'].dropna().unique()) if 'test_name' in self.mapper.apply(self.df_preview).columns else set()
            # 重新从mapper获取
            df_mapped = self.mapper.apply(self.df_preview)
            if 'test_name' in df_mapped.columns:
                preview_tests = set(df_mapped['test_name'].dropna().astype(str).str.strip().unique())

            full_tests = set(result.keys())
            new_tests = full_tests - preview_tests

            # 更新信息
            total_rows = sum(result.values())
            info_text = f"✅ 完整扫描完成: {len(result)} 个检验项目 (共 {total_rows:,} 行)"

            if new_tests:
                info_text += f"\n🆕 发现 {len(new_tests)} 个预览中未出现的新项目!"
                self.scan_status_label.setText(f"✅ 发现 {len(new_tests)} 个新项目")
            else:
                info_text += "\n✓ 预览数据已包含所有检验项目"
                self.scan_status_label.setText("✅ 扫描完成，无新项目")

            self.info_label.setText(info_text)
            self.update_selection_count()
        else:
            self.scan_status_label.setText("扫描完成，无结果")

    def _on_scan_error(self, error_msg: str):
        """扫描错误"""
        self._cleanup_scan_thread()
        self.full_scan_btn.setText("🔍 扫描完整数据")
        self.full_scan_btn.setEnabled(True)
        self.scan_status_label.setText(f"❌ 扫描失败: {error_msg}")
        QMessageBox.warning(
            self,
            UserMessage.format_title(UserMessage.Action.SCAN, UserMessage.Type.ERROR),
            UserMessage.format_error("扫描完整数据", error_msg)
        )

    def _cleanup_scan_thread(self):
        """清理扫描线程资源"""
        if self.scan_thread:
            if self.scan_thread.isRunning():
                self.scan_thread.cancel()
                self.scan_thread.quit()
                self.scan_thread.wait(2000)
            self.scan_thread = None
    
    def filter_tests(self):
        """过滤/搜索检验项目"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.test_table.rowCount()):
            test_name = self.test_table.item(i, 1).text().lower()
            
            if search_text in test_name:
                self.test_table.setRowHidden(i, False)
            else:
                self.test_table.setRowHidden(i, True)
    
    def update_selection_count(self):
        """更新选择计数"""
        selected = self.test_table.get_checked_items(column_index=1)
        self.selection_label.setText(f"已选择: {len(selected)} 个项目")
        
        # 至少选择一个项目才能继续
        self.nav_buttons.enable_next(len(selected) > 0)
    
    def on_next(self):
        """下一步"""
        selected = self.test_table.get_checked_items(column_index=1)
        
        if not selected:
            QMessageBox.warning(
                self,
                UserMessage.Type.WARNING,
                UserMessage.format_validation_error(["至少一个检验项目"], "选择")
            )
            return
        
        # 创建 test_mapping（此时还没有别名和单位，Step 3 只是选择）
        test_mapping = {}
        for test_name in selected:
            test_mapping[test_name] = {
                'aliases': [test_name.strip()],  # 确保aliases也被strip
                'unit': None,
                'range': None
            }
        
        data = {
            'test_mapping': test_mapping,
            'selected_tests': selected
        }
        
        self.next_step.emit(data)

