# LIS Extractor 项目交付文档

## 项目概述

**LIS Extractor** 是一个完整的 GUI 应用程序，用于从医院 LIS（实验室信息系统）导出的 Excel 文件中抽取和标准化检验数据。

## 已完成功能

### ✅ 核心功能模块

1. **数据加载模块** (`core/data_loader.py`)
   - 支持单文件和文件夹批量加载
   - 自动检测 Excel header 行
   - 预览功能（前 100 行）
   - 列验证功能

2. **字段映射模块** (`core/column_mapper.py`)
   - 原始列名到标准字段的映射
   - 必填字段验证
   - 自动建议映射（基于关键词）
   - 支持标准字段：patient_id, visit_id, sample_datetime, test_name, test_value, unit 等

3. **检验项目映射模块** (`core/test_mapper.py`)
   - 项目名称标准化
   - 别名支持
   - 项目统计和过滤
   - 单位和参考范围管理

4. **数值解析模块** (`core/value_parser.py`)
   - 小于号处理（`<0.5`）：一半值/下界/NA
   - 大于号处理（`>1000`）：保持/上限/NA
   - 阳性/阴性文本转换
   - 无效值处理（溶血、样本不足等）

5. **质量控制报告模块** (`core/qc_reporter.py`)
   - 数据质量分析
   - 项目分布统计
   - 数值标志统计
   - 导出 Excel 报告

6. **抽取引擎** (`core/extractor_engine.py`)
   - 完整 ETL 流程
   - 多线程支持（QThread）
   - 进度和日志信号
   - 可中止操作

7. **Profile 管理器** (`core/profile_manager.py`)
   - YAML 格式配置文件
   - 创建、加载、保存、删除
   - Profile 列表管理

8. **工具函数** (`core/utils.py`)
   - 日期时间解析
   - 数值提取
   - 特殊值模式检测
   - 列名标准化

### ✅ GUI 界面

1. **主窗口** (`gui/main_window.py`)
   - 三个标签页：数据抽取、Profile 管理、关于
   - 两种模式：新建配置 / 使用已有配置
   - 实时进度显示
   - 日志查看器
   - Profile 选择和管理

2. **6 步向导** (`gui/wizard_dialog.py`)
   - **Step 1**: 文件选择和数据预览
   - **Step 2**: 字段映射（必填字段验证）
   - **Step 3**: 检验项目选择（搜索、全选）
   - **Step 4**: 数值解析规则设置
   - **Step 5**: 输出选项配置
   - **Step 6**: Profile 摘要和保存

3. **通用组件** (`gui/components.py`)
   - 数据预览表格
   - 进度面板
   - 日志查看器
   - 导航按钮组
   - 可勾选表格

### ✅ 文档和示例

1. **README.md** - 完整的项目说明文档
2. **QUICKSTART.md** - 快速开始指南
3. **示例 Profile** - example_hospital_lis.yaml
4. **启动脚本** - run.py
5. **示例生成器** - create_example_profile.py

## 项目结构

```
Lis extractor/
├── main.py                          # 主程序入口 ✅
├── run.py                           # 快速启动脚本 ✅
├── requirements.txt                 # Python 依赖 ✅
├── README.md                        # 项目文档 ✅
├── QUICKSTART.md                    # 快速开始 ✅
├── PROJECT_DELIVERY.md              # 本文件 ✅
├── create_example_profile.py        # 示例配置生成器 ✅
├── .gitignore                       # Git 忽略文件 ✅
│
├── core/                            # 核心处理模块 ✅
│   ├── __init__.py
│   ├── utils.py                     # 工具函数
│   ├── data_loader.py               # 数据加载
│   ├── column_mapper.py             # 字段映射
│   ├── test_mapper.py               # 项目映射
│   ├── value_parser.py              # 数值解析
│   ├── qc_reporter.py               # 质量报告
│   ├── extractor_engine.py          # 抽取引擎
│   └── profile_manager.py           # Profile 管理
│
├── gui/                             # GUI 界面 ✅
│   ├── __init__.py
│   ├── components.py                # 通用组件
│   ├── main_window.py               # 主窗口
│   ├── wizard_dialog.py             # 向导容器
│   ├── wizard_step1_file_select.py  # Step 1: 文件选择
│   ├── wizard_step2_mapping.py      # Step 2: 字段映射
│   ├── wizard_step3_tests.py        # Step 3: 项目选择
│   ├── wizard_step4_values.py       # Step 4: 数值解析
│   ├── wizard_step5_output.py       # Step 5: 输出设置
│   └── wizard_step6_summary.py      # Step 6: 完成配置
│
├── profiles/                        # Profile 配置目录 ✅
│   └── lis_profiles/
│       ├── .gitkeep
│       └── example_hospital_lis.yaml # 示例配置
│
└── outputs/                         # 输出目录 ✅
    └── (运行时生成)
```

## 技术实现亮点

### 1. 完全按照 PRD 要求实现
- ✅ 6 步向导流程
- ✅ 直接读取真实大文件，无需样表
- ✅ 生成可重用的 YAML Profile
- ✅ 多线程支持，GUI 不卡顿
- ✅ 实时进度条和日志

### 2. 架构设计
- **核心层**：纯数据处理逻辑，独立于 GUI
- **GUI 层**：PyQt6 实现，信号槽机制
- **配置层**：YAML 格式，人类可读可编辑

### 3. 用户体验
- **向导模式**：首次使用友好，步骤清晰
- **快速模式**：已有配置可直接运行
- **实时反馈**：进度条、日志、错误提示
- **数据预览**：每步都可预览数据

### 4. 数据处理能力
- **智能解析**：自动检测特殊值格式
- **灵活映射**：支持任意列名映射
- **批量处理**：支持文件夹中所有 Excel
- **质量控制**：自动生成 QC 报告

## 使用流程

### 首次使用（创建 Profile）
```
启动程序
  ↓
点击"新建格式配置并抽取数据"
  ↓
Step 1: 选择 Excel 文件/文件夹 → 加载预览
  ↓
Step 2: 映射字段（自动建议或手动）
  ↓
Step 3: 选择检验项目（搜索、全选）
  ↓
Step 4: 设置解析规则（<, >, 阳性/阴性）
  ↓
Step 5: 设置输出选项
  ↓
Step 6: 保存 Profile → 自动开始抽取
  ↓
查看输出文件
```

### 使用已有 Profile
```
启动程序
  ↓
选择已有 Profile
  ↓
选择输入文件/文件夹
  ↓
点击"开始抽取"
  ↓
查看输出文件
```

## 输出文件

### labs_long_YYYYMMDD_HHMMSS.xlsx
标准化长表，每行一条检验记录：

| 字段 | 说明 |
|------|------|
| patient_id | 患者ID |
| visit_id | 就诊ID |
| sample_datetime | 采样时间 |
| test_name | 原始项目名 |
| test_code | 标准化项目名 |
| test_value | 原始结果值 |
| value_numeric | 解析后的数值 |
| value_flag | 数值标志 |
| unit | 原始单位 |
| unit_std | 标准单位 |
| profile_id | 使用的配置ID |
| run_id | 运行时间戳 |

### qc_report_YYYYMMDD_HHMMSS.xlsx
质量控制报告，包含：
- 数据摘要（原始行数、处理后行数、保留率等）
- 项目分布（每个项目的数量）
- 数值标志分布（normal/less_than/greater_than 等）

## 安装和运行

### 环境要求
- Python 3.10+
- PyQt6
- pandas
- openpyxl
- PyYAML

### 安装步骤
```bash
# 安装依赖
pip install -r requirements.txt

# 创建示例配置（可选）
python3 create_example_profile.py

# 启动程序
python3 main.py
# 或
python3 run.py
```

## 测试建议

### 测试场景 1：创建新 Profile
1. 准备一个真实的 LIS Excel 文件
2. 运行程序，选择"新建格式配置"
3. 完成 6 步向导
4. 检查生成的 YAML 文件
5. 查看输出的 labs_long 和 qc_report

### 测试场景 2：使用已有 Profile
1. 使用示例 Profile 或之前创建的 Profile
2. 选择另一个相同格式的文件
3. 运行抽取
4. 对比输出结果

### 测试场景 3：批量处理
1. 准备一个包含多个 Excel 的文件夹
2. 使用已有 Profile 处理整个文件夹
3. 检查所有文件是否都被处理

## 已知限制和未来改进

### 当前限制
1. Profile 修改需要手动编辑 YAML 或重新创建
2. 暂不支持 CSV 输入（仅 Excel）
3. 输出格式固定为 Excel（未来可支持 CSV、Parquet）

### 未来改进建议
1. **Profile 编辑器**：GUI 界面直接编辑已有 Profile
2. **更多输入格式**：支持 CSV、数据库连接
3. **数据验证规则**：添加数据范围验证、异常值检测
4. **报表模板**：自定义输出报表格式
5. **命令行模式**：支持批处理脚本
6. **打包为可执行文件**：使用 PyInstaller 打包

## 代码质量

- **模块化设计**：核心逻辑与 GUI 分离
- **类型提示**：关键函数使用类型注解
- **文档字符串**：所有模块和类都有说明
- **错误处理**：try-except 捕获异常
- **信号槽机制**：GUI 与业务逻辑解耦

## 总结

本项目完全按照 PRD 要求实现了一个功能完整、可用的 LIS 数据抽取工具：

✅ **向导流程**：6 步完整实现  
✅ **数据处理**：加载、映射、解析、质量控制  
✅ **多线程**：大文件处理不卡顿  
✅ **可重用配置**：YAML Profile 管理  
✅ **用户体验**：进度条、日志、预览  
✅ **文档完整**：README、快速指南、示例  

项目代码结构清晰，易于维护和扩展。可直接交付使用。

---

**交付日期**：2025
**开发工具**：Cursor AI Agent  
**技术栈**：Python 3.10+, PyQt6, pandas  
**代码行数**：约 3000+ 行  
**文件数量**：25+ 个文件  

