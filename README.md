# LIS Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

## 简介

**LIS Extractor** 是一款用于从医院 LIS（实验室信息系统）导出的 Excel 文件中抽取检验数据的工具。它能够自动识别数据格式、映射字段、选择检验项目，并输出标准化的长表格式。

> 🎉 **开源项目** - 欢迎贡献！查看 [贡献指南](CONTRIBUTING.md)

## 主要功能

### 🔧 向导式配置
- **6 步向导**：从真实数据文件出发，无需制作样表
- **自动检测**：智能识别 header 行、列名、示例数据
- **字段映射**：将原始列名映射为标准字段
- **项目选择**：从数据中扫描所有检验项目，支持搜索和筛选
- **规则配置**：灵活处理特殊值（`<0.5`、`>1000`、阳性/阴性等）
- **可重用配置**：生成 YAML 配置文件，未来相同格式可直接使用

### 📊 数据处理
- **批量处理**：支持单个文件或整个文件夹
- **智能解析**：
  - 小于号规则：`<0.5` → 取一半/下界/NA
  - 大于号规则：`>1000` → 保持原值/自定义上限/NA
  - 文本值：阳性/阴性 → 1/0
  - 无效值：溶血、样本不足等 → NA
- **数据标准化**：统一输出标准字段
- **质量控制**：自动生成 QC 报告

### 🚀 性能优化
- **多线程处理**：大文件不卡顿
- **实时进度**：进度条和日志实时更新
- **可中止操作**：随时停止运行

### 📁 输出格式
- **labs_long**：标准化长表（每行一条检验记录）
- **qc_report**：质量控制报告
- 支持 Excel 格式

## 快速开始 🚀

### 方式 1：一键启动（推荐）

#### Windows 用户
双击运行 `start.bat`

#### macOS/Linux 用户
双击运行 `start.sh` 或在终端执行：
```bash
./start.sh
```

启动脚本会自动：
- ✅ 检查 Python 环境
- ✅ 安装必要依赖
- ✅ 启动程序

### 方式 2：手动安装

#### 环境要求
- Python 3.10 或更高版本
- Windows / macOS / Linux

#### 安装步骤

1. 克隆或下载本项目
```bash
git clone https://github.com/your-username/lis-extractor.git
cd lis-extractor
```

2. 安装依赖：
```bash
pip install -r requirements.txt
# 或
pip3 install -r requirements.txt
```

3. 启动程序：
```bash
python main.py
# 或
python3 main.py
```

## 使用方法

### 启动程序
```bash
python main.py
```

### 首次使用（新格式）

1. 点击 **"新建格式配置并抽取数据"**
2. 按照 6 步向导完成配置：
   - **Step 1**：选择真实的 Excel 文件或文件夹
   - **Step 2**：映射字段（必填：patient_id, sample_datetime, test_name, test_value）
   - **Step 3**：选择需要抽取的检验项目
   - **Step 4**：设置数值解析规则
   - **Step 5**：设置输出选项
   - **Step 6**：保存配置并开始抽取

3. 配置保存后可重复使用

### 使用已有配置

1. 从下拉框选择已保存的配置
2. 选择输入文件/文件夹
3. 选择输出目录
4. 点击 **"开始抽取"**

## Profile 配置文件

配置文件保存在 `profiles/lis_profiles/` 目录，为 YAML 格式：

```yaml
id: "hospital_lis_2024"
description: "XX医院 LIS 住院检验格式"

signature:
  required_columns:
    - "病人ID"
    - "检验日期"
    - "项目名称"
    - "检验结果"
  min_match_ratio: 0.75
  skip_top_rows: 0

column_mapping:
  patient_id: "病人ID"
  sample_datetime: "检验日期"
  test_name: "项目名称"
  test_value: "检验结果"
  unit: "单位"

test_mapping:
  CEA:
    aliases: ["CEA", "癌胚抗原"]
    unit: "ng/mL"
    range: [0, 5]

value_parsing:
  less_than:
    rule: "half"
  greater_than:
    rule: "keep"
```

## 项目结构

```
LISExtractor/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包
├── README.md
├── core/                   # 核心处理模块
│   ├── data_loader.py     # 数据加载
│   ├── column_mapper.py   # 字段映射
│   ├── test_mapper.py     # 项目映射
│   ├── value_parser.py    # 数值解析
│   ├── extractor_engine.py # 抽取引擎
│   ├── qc_reporter.py     # 质量报告
│   ├── profile_manager.py # 配置管理
│   └── utils.py           # 工具函数
├── gui/                   # GUI 界面
│   ├── main_window.py     # 主窗口
│   ├── wizard_dialog.py   # 向导容器
│   ├── wizard_step1_file_select.py
│   ├── wizard_step2_mapping.py
│   ├── wizard_step3_tests.py
│   ├── wizard_step4_values.py
│   ├── wizard_step5_output.py
│   ├── wizard_step6_summary.py
│   └── components.py      # 通用组件
├── profiles/              # 配置文件目录
│   └── lis_profiles/
└── outputs/               # 输出目录
```

## 技术栈

- **语言**：Python 3.10+
- **GUI 框架**：PyQt6
- **数据处理**：pandas, openpyxl
- **配置格式**：YAML
- **多线程**：QThread

## 标准字段说明

| 字段 | 说明 | 是否必填 |
|------|------|----------|
| patient_id | 患者ID | ✓ |
| visit_id | 就诊ID | |
| sample_datetime | 采样/检验日期时间 | ✓ |
| test_name | 检验项目名称 | ✓ |
| test_value | 检验结果值 | ✓ |
| unit | 单位 | |
| specimen_type | 标本类型 | |
| ref_range | 参考范围 | |
| result_flag | 结果标志 | |
| department | 科室 | |
| diagnosis | 诊断 | |

## 常见问题

### Q: 向导中看不到我的数据？
A: 请确保：
1. 文件是有效的 Excel 格式（.xlsx 或 .xls）
2. 文件没有被其他程序占用
3. 文件包含数据（不是空文件）

### Q: 映射时找不到某个必填字段？
A: 请检查原始数据是否包含该字段。必填字段为：
- patient_id（患者ID）
- sample_datetime（检验日期）
- test_name（项目名称）
- test_value（检验结果）

### Q: 处理大文件时程序卡住了？
A: 程序使用了多线程，UI 不应该卡顿。如果出现问题，可以点击"中止"按钮。

### Q: 如何修改已有的 Profile？
A: 目前需要手动编辑 YAML 文件，或者重新运行向导创建新配置。

## 开发信息

- **版本**：1.1.0
- **开发**：Cursor AI Agent
- **许可**：MIT License

## 更新日志

### v1.1.0 (2025-12-01)
- 性能优化：iterrows() 替换为向量化操作
- 新增配置常量管理
- 边界值检查增强
- 线程安全改进
- 统一消息格式化

### v1.0.0 (2025-11-29)
- 首次发布
- 实现 6 步向导
- 支持字段映射、项目选择、数值解析
- 多线程处理
- 质量控制报告

## 贡献 🤝

我们欢迎所有形式的贡献！

- 🐛 [报告 Bug](https://github.com/your-username/lis-extractor/issues)
- 💡 [提出新功能](https://github.com/your-username/lis-extractor/issues)
- 📝 改进文档
- 🔧 提交代码

查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 许可协议 📄

本项目采用 [MIT License](LICENSE) 开源协议。

您可以自由地：
- ✅ 使用本软件
- ✅ 修改本软件
- ✅ 分发本软件
- ✅ 商业使用

## 致谢 🙏

感谢所有贡献者的支持！

特别感谢：
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 强大的 GUI 框架
- [pandas](https://pandas.pydata.org/) - 数据处理利器
- [Cursor AI](https://cursor.sh/) - 开发辅助

## 联系方式 📧

- 💬 [GitHub Issues](https://github.com/xenorexq/lis-extractor/issues)
- 🌐 项目主页: https://github.com/xenorexq/lis-extractor

## Star History ⭐

如果这个项目对您有帮助，请给我们一个 Star！

[![Star History Chart](https://api.star-history.com/svg?repos=xenorexq/lis-extractor&type=Date)](https://star-history.com/#xenorexq/lis-extractor&Date)

---

**注意**：本工具仅供数据处理使用，请确保遵守相关数据隐私和安全规定。

**版权所有** © 2025 LIS Extractor Contributors

