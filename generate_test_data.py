"""
生成测试用的 LIS Excel 数据
"""
import pandas as pd
from datetime import datetime, timedelta
import random
import os


def generate_test_lis_data(output_file='test_lis_data.xlsx', num_patients=50):
    """
    生成测试用的 LIS 数据
    
    Args:
        output_file: 输出文件名
        num_patients: 患者数量
    """
    print("正在生成测试数据...")
    
    data = []
    start_date = datetime(2024, 1, 1)
    
    # 检验项目定义
    test_definitions = [
        ('CEA', (0, 10), 'ng/mL', (0, 5)),
        ('CA19-9', (0, 50), 'U/mL', (0, 37)),
        ('CA125', (0, 50), 'U/mL', (0, 35)),
        ('AFP', (0, 30), 'ng/mL', (0, 20)),
        ('SCC-Ag', (0, 5), 'ng/mL', (0, 1.5)),
        ('WBC', (3, 12), '10^9/L', (3.5, 9.5)),
        ('HGB', (100, 170), 'g/L', (115, 150)),
        ('PLT', (100, 400), '10^9/L', (125, 350)),
        ('ALT', (10, 80), 'U/L', (9, 50)),
        ('AST', (10, 80), 'U/L', (15, 40)),
    ]
    
    for i in range(num_patients):
        patient_id = f"P{10001 + i}"
        visit_id = f"V{20001 + i}"
        test_date = start_date + timedelta(days=random.randint(0, 60))
        
        # 每个患者随机选择 3-8 个检验项目
        num_tests = random.randint(3, 8)
        selected_tests = random.sample(test_definitions, num_tests)
        
        for test_name, (min_val, max_val), unit, ref_range in selected_tests:
            # 生成数值
            value = random.uniform(min_val, max_val)
            
            # 随机添加特殊格式
            rand = random.random()
            if rand < 0.05:
                # 小于号
                value_str = f"<{value:.2f}"
            elif rand < 0.10:
                # 大于号
                value_str = f">{value:.2f}"
            elif rand < 0.12:
                # 阳性
                value_str = random.choice(['阳性', '弱阳性', '+', '++'])
            elif rand < 0.14:
                # 阴性
                value_str = random.choice(['阴性', '-'])
            elif rand < 0.16:
                # 无效值
                value_str = random.choice(['溶血', '样本不足', '--', '/'])
            else:
                # 正常数值
                value_str = f"{value:.2f}"
            
            # 结果标志
            ref_min, ref_max = ref_range
            if isinstance(value_str, str) and not value_str[0].isdigit():
                result_flag = ''
            elif value < ref_min:
                result_flag = 'L'
            elif value > ref_max:
                result_flag = 'H'
            else:
                result_flag = 'N'
            
            data.append({
                '病人ID': patient_id,
                '住院病人门诊ID': visit_id,
                '检验日期': test_date.strftime('%Y-%m-%d'),
                '项目名称': test_name,
                '检验结果': value_str,
                '单位': unit,
                '参考值': f"{ref_min}-{ref_max}",
                '结果标志': result_flag,
                '标本类型': random.choice(['血清', '全血', '血浆'])
            })
    
    # 创建 DataFrame
    df = pd.DataFrame(data)
    
    # 排序
    df = df.sort_values(['病人ID', '检验日期', '项目名称'])
    
    # 导出
    df.to_excel(output_file, index=False)
    
    print(f"✓ 测试数据已生成!")
    print(f"  文件: {output_file}")
    print(f"  总行数: {len(df)}")
    print(f"  患者数: {num_patients}")
    print(f"  检验项目: {df['项目名称'].nunique()} 个")
    print(f"  日期范围: {df['检验日期'].min()} 至 {df['检验日期'].max()}")
    print()
    print("项目分布:")
    for test, count in df['项目名称'].value_counts().items():
        print(f"  - {test}: {count} 条")


if __name__ == '__main__':
    # 检查依赖
    try:
        import pandas
        import openpyxl
    except ImportError as e:
        print(f"错误: 缺少依赖包 - {e}")
        print("请先运行: pip install pandas openpyxl")
        exit(1)
    
    # 生成数据
    generate_test_lis_data('test_lis_data.xlsx', num_patients=50)
    
    print()
    print("📝 下一步:")
    print("1. 启动程序: python3 main.py")
    print("2. 点击「新建格式配置并抽取数据」")
    print("3. 选择刚生成的 test_lis_data.xlsx 文件")
    print("4. 按照向导完成配置")

