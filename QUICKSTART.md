# LIS Extractor 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 启动程序

### 方式 1: 直接运行
```bash
python main.py
```

### 方式 2: 使用启动脚本
```bash
python run.py
```

## 3. 第一次使用

### 创建示例配置（可选）
如果想先测试程序功能，可以创建一个示例配置：

```bash
python create_example_profile.py
```

### 使用向导创建配置

1. **启动程序**后，点击 **"新建格式配置并抽取数据"** 按钮

2. **Step 1 - 选择文件**
   - 点击"浏览文件"选择一个 Excel 文件
   - 或点击"浏览文件夹"选择包含多个 Excel 的文件夹
   - 点击"加载预览"查看数据
   - 确认数据正确后，点击"下一步"

3. **Step 2 - 字段映射**
   - 程序会显示所有原始列名和示例值
   - 点击"自动建议映射"让程序自动匹配
   - 或手动选择每列对应的标准字段
   - 必填字段（必须映射）：
     - patient_id（患者ID）
     - sample_datetime（检验日期）
     - test_name（项目名称）
     - test_value（检验结果）
   - 点击"下一步"

4. **Step 3 - 选择检验项目**
   - 程序会扫描数据中所有不同的检验项目
   - 使用搜索框快速查找项目
   - 勾选需要抽取的项目
   - 可以使用"全选"/"全不选"按钮
   - 点击"下一步"

5. **Step 4 - 数值解析规则**
   - 程序会自动检测特殊值格式
   - 设置小于号规则（如 `<0.5`）：
     - 使用一半值：0.25
     - 使用下界值：0.5
     - 设为 NA
   - 设置大于号规则（如 `>1000`）：
     - 保持原值：1000
     - 使用自定义上限
     - 设为 NA
   - 设置阳性/阴性文本转换
   - 点击"下一步"

6. **Step 5 - 输出设置**
   - 选择输出目录（默认：outputs/）
   - 勾选需要的输出内容
   - 设置数据过滤选项
   - 点击"下一步"

7. **Step 6 - 完成配置**
   - 输入 Profile ID（例如：hospital_lis_2024）
   - 输入描述信息
   - 查看配置摘要
   - 勾选"保存 Profile 后立即处理当前文件"
   - 点击"完成并保存"

8. **自动开始抽取**
   - 如果勾选了立即处理，程序会自动开始抽取
   - 查看进度条和日志
   - 完成后会弹出提示框

## 4. 使用已有配置

如果已经创建了 Profile 配置：

1. 在主界面的"使用已有配置"区域
2. 从下拉框选择一个配置
3. 点击"选择文件"或"选择文件夹"选择输入
4. 选择输出目录
5. 点击"开始抽取"

## 5. 输出文件

处理完成后，会在输出目录生成以下文件：

- `labs_long_YYYYMMDD_HHMMSS.xlsx`：标准化长表
  - 每行一条检验记录
  - 包含所有映射的字段
  - 添加了 test_code、value_numeric、value_flag 等列

- `qc_report_YYYYMMDD_HHMMSS.xlsx`：质量控制报告
  - 数据摘要
  - 项目分布
  - 数值标志分布
  - 质量指标

## 6. 常见问题

### Q: 如何处理多个不同格式的 LIS 文件？
A: 为每种格式创建一个 Profile，然后分别使用对应的配置处理。

### Q: 可以修改已保存的 Profile 吗？
A: 可以手动编辑 `profiles/lis_profiles/` 目录下的 YAML 文件。

### Q: 程序支持哪些 Excel 格式？
A: 支持 .xlsx 和 .xls 格式。

### Q: 如何处理非常大的文件？
A: 程序使用多线程处理，可以处理几百 MB 的文件。如果遇到内存问题，建议将大文件拆分。

### Q: 输出的字段有哪些？
A: 标准输出包括：
- patient_id：患者ID
- visit_id：就诊ID
- sample_datetime：采样时间
- test_name：原始项目名
- test_code：标准化项目名
- test_value：原始结果值
- value_numeric：解析后的数值
- value_flag：数值标志（normal/less_than/greater_than等）
- unit：单位
- unit_std：标准单位
- 其他映射的字段

## 7. 目录结构

```
Lis extractor/
├── main.py                 # 主程序
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖
├── README.md              # 说明文档
├── QUICKSTART.md          # 本文件
├── create_example_profile.py  # 创建示例配置
├── core/                  # 核心模块
├── gui/                   # GUI 界面
├── profiles/              # 配置文件（自动生成）
│   └── lis_profiles/
└── outputs/               # 输出文件（自动生成）
```

## 8. 技巧和建议

1. **首次使用建议先用小文件测试**
   - 选择包含 1000 行左右的小文件
   - 验证映射和解析规则是否正确
   - 确认无误后再处理大文件

2. **Profile 命名规范**
   - 建议使用有意义的 ID，如：`hospital_name_department_year`
   - 例如：`zhengda_inpatient_2020`

3. **数值解析规则的选择**
   - 对于临床数据，小于号通常选择"使用一半值"
   - 大于号通常选择"保持原值"
   - 根据具体需求调整

4. **定期备份 Profile**
   - Profile 文件保存了重要的配置信息
   - 建议定期备份 `profiles/` 目录

## 9. 下一步

- 了解详细功能：查看 README.md
- 查看示例配置：`profiles/lis_profiles/example_hospital_lis.yaml`
- 如有问题，查看日志输出

---

祝使用愉快！

