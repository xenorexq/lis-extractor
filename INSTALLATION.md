# LIS Extractor - 安装和测试指南

## 📦 安装步骤

### 1. 确认 Python 版本
```bash
python3 --version
# 或
python --version
```
需要 Python 3.10 或更高版本

### 2. 安装依赖包

#### 方式 A：使用 pip（推荐）
```bash
# 进入项目目录
cd "/your_path/Lis extractor"

# 安装依赖
pip3 install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

#### 方式 B：逐个安装
```bash
pip3 install PyQt6==6.6.1
pip3 install pandas==2.1.4
pip3 install openpyxl==3.1.2
pip3 install PyYAML==6.0.1
pip3 install xlrd==2.0.1
pip3 install pyarrow==14.0.2
```

### 3. 验证安装
```bash
python3 -c "import PyQt6; print('PyQt6 OK')"
python3 -c "import pandas; print('pandas OK')"
python3 -c "import yaml; print('PyYAML OK')"
python3 -c "import openpyxl; print('openpyxl OK')"
```

如果所有命令都输出 "OK"，说明安装成功！

## 🚀 启动程序

### 方式 1：直接运行
```bash
python3 main.py
```

### 方式 2：使用启动脚本
```bash
python3 run.py
```

## 🧪 测试程序

### 测试 1：创建示例配置
```bash
# 创建一个示例 Profile（需要先安装依赖）
python3 create_example_profile.py
```

这会在 `profiles/lis_profiles/` 目录创建 `example_hospital_lis.yaml`

### 测试 2：检查目录结构
```bash
# 查看项目结构
ls -la

# 应该看到以下目录和文件：
# - core/          （核心模块）
# - gui/           （GUI 界面）
# - profiles/      （配置文件）
# - outputs/       （输出目录）
# - main.py        （主程序）
# - requirements.txt
# - README.md
```

### 测试 3：启动 GUI
```bash
python3 main.py
```

应该会弹出主窗口，包含：
- "新建格式配置并抽取数据" 按钮
- "使用已有配置" 区域
- Profile 下拉框
- 日志查看器

## 📝 准备测试数据

### 创建测试 Excel 文件

如果您没有真实的 LIS Excel 文件，可以创建一个测试文件：

```python
# 创建 test_lis_data.py
import pandas as pd
from datetime import datetime, timedelta
import random

# 生成测试数据
data = []
start_date = datetime(2024, 1, 1)

for i in range(100):
    patient_id = f"P{1000 + i}"
    visit_id = f"V{2000 + i}"
    test_date = start_date + timedelta(days=random.randint(0, 30))
    
    # 不同的检验项目
    tests = [
        ('CEA', random.uniform(0, 10), 'ng/mL'),
        ('CA19-9', random.uniform(0, 50), 'U/mL'),
        ('AFP', random.uniform(0, 30), 'ng/mL'),
        ('WBC', random.uniform(3, 10), '10^9/L'),
        ('HGB', random.uniform(110, 160), 'g/L'),
    ]
    
    for test_name, value, unit in tests:
        # 随机添加一些特殊值
        if random.random() < 0.1:
            value_str = f"<{value:.2f}"
        elif random.random() < 0.1:
            value_str = f">{value:.2f}"
        else:
            value_str = f"{value:.2f}"
        
        data.append({
            '病人ID': patient_id,
            '住院病人门诊ID': visit_id,
            '检验日期': test_date.strftime('%Y-%m-%d'),
            '项目名称': test_name,
            '检验结果': value_str,
            '单位': unit,
            '参考值': '',
            '结果标志': 'N' if random.random() > 0.2 else 'H',
            '标本类型': '血清'
        })

df = pd.DataFrame(data)
df.to_excel('test_lis_data.xlsx', index=False)
print(f"✓ 测试数据已生成: test_lis_data.xlsx ({len(df)} 行)")
```

运行：
```bash
python3 test_lis_data.py
```

## ✅ 功能测试清单

### [ ] 测试 1：启动程序
- [ ] 程序正常启动
- [ ] 主窗口显示正常
- [ ] 三个标签页都可以切换

### [ ] 测试 2：向导流程
- [ ] 点击"新建格式配置"按钮
- [ ] Step 1: 选择测试文件，数据预览正常
- [ ] Step 2: 自动建议映射功能正常
- [ ] Step 3: 显示所有检验项目，可以勾选
- [ ] Step 4: 显示特殊值示例
- [ ] Step 5: 设置输出选项
- [ ] Step 6: 输入 Profile 信息，保存成功

### [ ] 测试 3：使用已有配置
- [ ] Profile 下拉框显示刚创建的配置
- [ ] 选择配置后显示描述
- [ ] 选择输入文件
- [ ] 点击"开始抽取"
- [ ] 进度条更新
- [ ] 日志实时显示
- [ ] 完成后显示成功提示

### [ ] 测试 4：检查输出文件
- [ ] outputs/ 目录有输出文件
- [ ] labs_long_*.xlsx 可以打开
- [ ] qc_report_*.xlsx 可以打开
- [ ] 数据格式正确

### [ ] 测试 5：Profile 管理
- [ ] 切换到"Profile 管理"标签
- [ ] 点击"刷新列表"
- [ ] 显示所有 Profile 信息

## 🐛 常见问题排查

### 问题 1：ModuleNotFoundError
```
ModuleNotFoundError: No module named 'PyQt6'
```
**解决**：确保已安装所有依赖
```bash
pip3 install -r requirements.txt
```

### 问题 2：程序无法启动
```
ImportError: cannot import name 'MainWindow'
```
**解决**：检查文件结构是否完整
```bash
ls core/
ls gui/
```

### 问题 3：文件选择后无反应
**解决**：
1. 检查文件是否是有效的 Excel 文件
2. 查看日志窗口的错误信息
3. 确认文件没有被其他程序占用

### 问题 4：中文显示乱码（Windows）
**解决**：确保 Excel 文件是 UTF-8 编码

### 问题 5：macOS 上程序闪退
**解决**：
```bash
# 可能需要额外权限
python3 -m pip install --upgrade PyQt6
```

## 📊 性能测试建议

### 小文件测试（推荐首次测试）
- 行数：100-1000 行
- 列数：10-20 列
- 预期时间：< 5 秒

### 中等文件测试
- 行数：10,000-50,000 行
- 列数：10-20 列
- 预期时间：10-30 秒

### 大文件测试
- 行数：100,000+ 行
- 列数：10-20 列
- 预期时间：1-3 分钟
- 注意：观察内存使用

## 🔧 开发模式

如果需要修改代码：

```bash
# 1. 安装开发依赖（如果需要）
pip3 install pytest black mypy

# 2. 格式化代码
black core/ gui/

# 3. 类型检查
mypy core/ gui/

# 4. 运行程序
python3 main.py
```

## 📦 打包为可执行文件（未来）

```bash
# 安装 PyInstaller
pip3 install pyinstaller

# 打包
pyinstaller --windowed --name="LIS Extractor" main.py

# 可执行文件在 dist/ 目录
```

## ✨ 下一步

1. **完成安装**：确保所有依赖已安装
2. **生成测试数据**：使用上面的脚本或准备真实数据
3. **测试向导**：完整走一遍创建 Profile 流程
4. **测试抽取**：使用创建的 Profile 处理数据
5. **查看输出**：检查生成的 Excel 文件

## 📞 获取帮助

如遇到问题：
1. 查看日志窗口的错误信息
2. 检查 outputs/ 目录的文件
3. 查看 PROJECT_DELIVERY.md 了解项目详情
4. 阅读 QUICKSTART.md 快速开始指南

---

祝测试顺利！ 🎉

