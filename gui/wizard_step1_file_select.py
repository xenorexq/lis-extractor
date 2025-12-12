"""
向导 Step 1: 选择文件/文件夹
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFileDialog, QMessageBox,
                             QGroupBox, QSlider, QProgressDialog, QApplication)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
import pandas as pd

from core import DataLoader, UserMessage
from core.constants import LoaderConfig
from .components import DataPreviewTable, NavigationButtons


class PreviewLoadThread(QThread):
    """后台加载预览数据的线程"""
    finished = pyqtSignal(object, int, list)  # (df, header_row, columns)
    progress = pyqtSignal(int, str)  # (percentage, message)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, max_rows: int):
        super().__init__()
        self.file_path = file_path
        self.max_rows = max_rows
        self._is_cancelled = False

    def cancel(self):
        """取消加载"""
        self._is_cancelled = True

    def run(self):
        """执行加载"""
        try:
            loader = DataLoader()
            loader.progress.connect(self.progress.emit)
            loader.error.connect(self.error.emit)

            self.progress.emit(10, "正在读取文件...")

            if self._is_cancelled:
                return

            df, header_row, columns = loader.load_preview(
                self.file_path,
                max_rows=self.max_rows
            )

            if self._is_cancelled:
                return

            self.progress.emit(100, "加载完成")
            self.finished.emit(df, header_row, columns)

        except Exception as e:
            self.error.emit(str(e))


class WizardStep1FileSelect(QWidget):
    """
    Step 1: 选择真实文件/文件夹并预览
    """
    next_step = pyqtSignal(dict)  # 发送数据到下一步
    cancel = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loader = DataLoader()
        self.df_preview = None
        self.header_row = 0
        self.file_path = ""

        # 线程和进度对话框
        self.load_thread = None
        self.progress_dialog = None

        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("<h2>步骤 1: 选择数据文件</h2>")
        layout.addWidget(title)
        
        desc = QLabel("请选择 LIS 导出的 Excel 文件或包含多个 Excel 的文件夹")
        layout.addWidget(desc)
        
        # 文件选择区
        file_group = QGroupBox("数据源")
        file_layout = QVBoxLayout()
        
        # 单个文件
        file_row = QHBoxLayout()
        file_label = QLabel("选择文件:")
        file_label.setMinimumWidth(80)
        file_row.addWidget(file_label)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("点击按钮选择 Excel 文件...")
        file_row.addWidget(self.file_edit, stretch=1)
        self.file_btn = QPushButton("浏览文件...")
        self.file_btn.setMinimumWidth(100)
        self.file_btn.clicked.connect(self.select_file)
        file_row.addWidget(self.file_btn)
        file_layout.addLayout(file_row)
        
        # 文件夹
        folder_row = QHBoxLayout()
        folder_label = QLabel("或选择文件夹:")
        folder_label.setMinimumWidth(80)
        folder_row.addWidget(folder_label)
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("点击按钮选择包含 Excel 的文件夹...")
        folder_row.addWidget(self.folder_edit, stretch=1)
        self.folder_btn = QPushButton("浏览文件夹...")
        self.folder_btn.setMinimumWidth(100)
        self.folder_btn.clicked.connect(self.select_folder)
        folder_row.addWidget(self.folder_btn)
        file_layout.addLayout(folder_row)
        
        # 预览行数设置
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("预览行数:"))

        self.row_slider = QSlider(Qt.Orientation.Horizontal)
        self.row_slider.setRange(LoaderConfig.SLIDER_MIN_ROWS, LoaderConfig.SLIDER_MAX_ROWS)
        self.row_slider.setSingleStep(LoaderConfig.SLIDER_STEP)
        self.row_slider.setPageStep(LoaderConfig.SLIDER_STEP)
        self.row_slider.setTickInterval(LoaderConfig.SLIDER_STEP)
        self.row_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.row_slider.setValue(LoaderConfig.SLIDER_MIN_ROWS)
        self.row_slider.valueChanged.connect(self.update_slider_label)
        slider_row.addWidget(self.row_slider)

        self.row_count_label = QLabel(f"{LoaderConfig.SLIDER_MIN_ROWS} 行")
        self.row_count_label.setMinimumWidth(60)
        slider_row.addWidget(self.row_count_label)
        
        file_layout.addLayout(slider_row)
        
        # 加载预览按钮
        self.preview_btn = QPushButton("加载预览")
        self.preview_btn.clicked.connect(self.load_preview)
        self.preview_btn.setEnabled(False)
        file_layout.addWidget(self.preview_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 数据预览区
        self.preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout()
        
        self.info_label = QLabel("未加载数据")
        preview_layout.addWidget(self.info_label)
        
        self.preview_table = DataPreviewTable()
        preview_layout.addWidget(self.preview_table)
        
        self.preview_group.setLayout(preview_layout)
        layout.addWidget(self.preview_group)
        
        # 导航按钮
        self.nav_buttons = NavigationButtons(show_previous=False)
        self.nav_buttons.next_clicked.connect(self.on_next)
        self.nav_buttons.cancel_clicked.connect(self.cancel.emit)
        self.nav_buttons.enable_next(False)
        layout.addWidget(self.nav_buttons)
        
        self.setLayout(layout)
        
        # 连接信号
        self.file_edit.textChanged.connect(self.on_path_changed)
        self.folder_edit.textChanged.connect(self.on_path_changed)
    
    def select_file(self):
        """选择单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            self.folder_edit.clear()
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含 Excel 文件的文件夹"
        )
        if folder_path:
            self.folder_edit.setText(folder_path)
            self.file_edit.clear()
    
    def update_slider_label(self, value):
        """更新滑块标签"""
        self.row_count_label.setText(f"{value} 行")
    
    def on_path_changed(self):
        """路径变化时启用预览按钮"""
        has_path = bool(self.file_edit.text() or self.folder_edit.text())
        self.preview_btn.setEnabled(has_path)
        self.nav_buttons.enable_next(False)
    
    def load_preview(self):
        """加载预览数据（使用后台线程）"""
        # 确定输入路径
        if self.file_edit.text():
            input_path = self.file_edit.text()
        elif self.folder_edit.text():
            input_path = self.folder_edit.text()
            # 如果是文件夹，找第一个文件用于预览
            files = self.loader.find_excel_files(input_path)
            if not files:
                QMessageBox.warning(
                    self,
                    UserMessage.format_title(UserMessage.Action.SCAN, UserMessage.Type.ERROR),
                    UserMessage.format_error(
                        "查找文件",
                        "所选文件夹中未找到 Excel 文件",
                        suggestion="请确认文件夹中包含 .xlsx 或 .xls 文件"
                    )
                )
                return
            input_path = files[0]
        else:
            return

        self.file_path = input_path

        # 获取滑块值
        max_rows = self.row_slider.value()

        # 禁用按钮
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("加载中...")
        self.nav_buttons.enable_next(False)

        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            f"正在加载 {max_rows} 行数据...",
            "取消",
            0, 100,
            self
        )
        self.progress_dialog.setWindowTitle("加载数据")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)  # 立即显示
        self.progress_dialog.setValue(0)
        self.progress_dialog.canceled.connect(self._on_load_cancelled)

        # 创建并启动后台线程
        self.load_thread = PreviewLoadThread(input_path, max_rows)
        self.load_thread.progress.connect(self._on_load_progress)
        self.load_thread.finished.connect(self._on_load_finished)
        self.load_thread.error.connect(self._on_load_error)
        self.load_thread.start()

    def _on_load_progress(self, percentage: int, message: str):
        """处理加载进度更新"""
        if self.progress_dialog and not self.progress_dialog.wasCanceled():
            self.progress_dialog.setValue(percentage)
            self.progress_dialog.setLabelText(message)
            QApplication.processEvents()

    def _on_load_cancelled(self):
        """处理用户取消加载"""
        self._cleanup_thread()
        self._reset_preview_button()
        self.info_label.setText("加载已取消")

    def _cleanup_thread(self):
        """清理线程资源"""
        if self.load_thread:
            if self.load_thread.isRunning():
                self.load_thread.cancel()
                self.load_thread.quit()
                self.load_thread.wait(2000)
            self.load_thread = None

        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _on_load_finished(self, df, header_row, columns):
        """处理加载完成"""
        # 清理线程和进度对话框
        self._cleanup_thread()

        self.df_preview = df
        self.header_row = header_row

        # 限制表格显示行数（即使加载了更多）
        display_rows = min(len(self.df_preview), 500)  # 最多显示500行

        # 更新信息标签（在填充表格之前）
        self.info_label.setText(f"正在填充表格 ({display_rows} 行)...")
        QApplication.processEvents()

        # 填充表格
        self.preview_table.load_dataframe(self.df_preview, max_rows=display_rows)

        # 更新标题
        if len(self.df_preview) > display_rows:
            self.preview_group.setTitle(f"数据预览 (加载 {len(self.df_preview)} 行，显示前 {display_rows} 行)")
        else:
            self.preview_group.setTitle(f"数据预览 (前 {len(self.df_preview)} 行)")

        # 更新信息
        info = f"✓ 已加载: {len(self.df_preview)} 行, {len(self.df_preview.columns)} 列 (Header 行: {self.header_row})"

        # 添加警告信息：如果显示行数少于加载行数
        if len(self.df_preview) > display_rows:
            info += f"\n⚠️ 注意: 字段映射和项目选择将基于全部 {len(self.df_preview)} 行数据"

        # 添加警告信息：如果只加载了部分数据
        max_rows = self.row_slider.value()
        if max_rows < 50000:  # 如果预览行数相对较少
            info += f"\n💡 提示: 实际处理时会扫描完整文件的所有数据"

        self.info_label.setText(info)

        # 启用下一步
        self.nav_buttons.enable_next(True)
        self._reset_preview_button()

    def _on_load_error(self, error_msg: str):
        """处理加载错误"""
        # 清理线程和进度对话框
        self._cleanup_thread()

        QMessageBox.critical(
            self,
            UserMessage.format_title(UserMessage.Action.LOAD, UserMessage.Type.ERROR),
            UserMessage.format_file_error("读取", self.file_path, error_msg)
        )
        self._reset_preview_button()

    def _reset_preview_button(self):
        """重置预览按钮状态"""
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("加载预览")
    
    def on_next(self):
        """下一步"""
        if self.df_preview is None:
            QMessageBox.warning(
                self,
                UserMessage.Type.WARNING,
                UserMessage.format_validation_error(["预览数据"], "")
            )
            return
        
        # 准备数据传递给下一步
        data = {
            'input_path': self.file_edit.text() or self.folder_edit.text(),
            'df_preview': self.df_preview,
            'header_row': self.header_row,
            'columns': self.df_preview.columns.tolist()
        }
        
        self.next_step.emit(data)

