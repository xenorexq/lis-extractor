"""
向导容器 - 管理 6 步向导流程
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal

from .wizard_step1_file_select import WizardStep1FileSelect
from .wizard_step2_mapping import WizardStep2Mapping
from .wizard_step3_tests import WizardStep3Tests
from .wizard_step4_values import WizardStep4Values
from .wizard_step5_output import WizardStep5Output
from .wizard_step6_summary import WizardStep6Summary


class WizardDialog(QDialog):
    """
    向导对话框
    管理 6 步流程
    """
    wizard_finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建 LIS 配置向导")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)  # 设置初始大小
        
        self.wizard_data = {}
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建堆叠窗口
        self.stack = QStackedWidget()
        
        # 创建所有步骤
        self.step1 = WizardStep1FileSelect()
        self.step2 = WizardStep2Mapping()
        self.step3 = WizardStep3Tests()
        self.step4 = WizardStep4Values()
        self.step5 = WizardStep5Output()
        self.step6 = WizardStep6Summary()
        
        # 添加到堆叠窗口
        self.stack.addWidget(self.step1)
        self.stack.addWidget(self.step2)
        self.stack.addWidget(self.step3)
        self.stack.addWidget(self.step4)
        self.stack.addWidget(self.step5)
        self.stack.addWidget(self.step6)
        
        # 连接信号
        # Step 1
        self.step1.next_step.connect(self.on_step1_next)
        self.step1.cancel.connect(self.reject)
        
        # Step 2
        self.step2.next_step.connect(self.on_step2_next)
        self.step2.previous_step.connect(lambda: self.go_to_step(0))
        self.step2.cancel.connect(self.reject)
        
        # Step 3
        self.step3.next_step.connect(self.on_step3_next)
        self.step3.previous_step.connect(lambda: self.go_to_step(1))
        self.step3.cancel.connect(self.reject)
        
        # Step 4
        self.step4.next_step.connect(self.on_step4_next)
        self.step4.previous_step.connect(lambda: self.go_to_step(2))
        self.step4.cancel.connect(self.reject)
        
        # Step 5
        self.step5.next_step.connect(self.on_step5_next)
        self.step5.previous_step.connect(lambda: self.go_to_step(3))
        self.step5.cancel.connect(self.reject)
        
        # Step 6
        self.step6.finish.connect(self.on_wizard_finish)
        self.step6.previous_step.connect(lambda: self.go_to_step(4))
        self.step6.cancel.connect(self.reject)
        
        layout.addWidget(self.stack)
        self.setLayout(layout)
    
    def go_to_step(self, step_index: int):
        """跳转到指定步骤"""
        self.stack.setCurrentIndex(step_index)
    
    def on_step1_next(self, data: dict):
        """Step 1 完成"""
        self.wizard_data.update(data)
        self.step2.load_data(self.wizard_data)
        self.go_to_step(1)
    
    def on_step2_next(self, data: dict):
        """Step 2 完成"""
        self.wizard_data.update(data)
        self.step3.load_data(self.wizard_data)
        self.go_to_step(2)
    
    def on_step3_next(self, data: dict):
        """Step 3 完成"""
        self.wizard_data.update(data)
        self.step4.load_data(self.wizard_data)
        self.go_to_step(3)
    
    def on_step4_next(self, data: dict):
        """Step 4 完成"""
        self.wizard_data.update(data)
        self.step5.load_data(self.wizard_data)
        self.go_to_step(4)
    
    def on_step5_next(self, data: dict):
        """Step 5 完成"""
        self.wizard_data.update(data)
        self.step6.load_data(self.wizard_data)
        self.go_to_step(5)
    
    def on_wizard_finish(self, result: dict):
        """向导完成"""
        self.wizard_finished.emit(result)
        self.accept()

