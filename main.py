"""
LIS Extractor 主程序入口
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("LIS Extractor")
    app.setOrganizationName("Medical Data Tools")
    app.setApplicationVersion("1.0.0")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

