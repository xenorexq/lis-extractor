"""
示例：创建测试用的 LIS Profile
"""
import yaml
import os

def create_example_profile():
    """创建一个示例 Profile"""
    
    example_profile = {
        'id': 'example_hospital_lis',
        'description': '示例医院 LIS 检验格式（用于演示）',
        'created_at': '2024-01-01 00:00:00',
        'signature': {
            'required_columns': [
                '病人ID',
                '检验日期',
                '项目名称',
                '检验结果'
            ],
            'min_match_ratio': 0.75,
            'skip_top_rows': 0
        },
        'column_mapping': {
            'patient_id': '病人ID',
            'visit_id': '住院病人门诊ID',
            'sample_datetime': '检验日期',
            'test_name': '项目名称',
            'test_value': '检验结果',
            'unit': '单位',
            'ref_range': '参考值',
            'result_flag': '结果标志',
            'specimen_type': '标本类型'
        },
        'test_mapping': {
            'CEA': {
                'aliases': ['CEA', 'CEA(CLIA)', '癌胚抗原'],
                'unit': 'ng/mL',
                'range': [0, 5]
            },
            'CA199': {
                'aliases': ['CA19-9', 'CA199', '糖类抗原19-9'],
                'unit': 'U/mL',
                'range': [0, 37]
            },
            'AFP': {
                'aliases': ['AFP', '甲胎蛋白'],
                'unit': 'ng/mL',
                'range': [0, 20]
            },
            'WBC': {
                'aliases': ['WBC', '白细胞', '白细胞计数'],
                'unit': '10^9/L',
                'range': [3.5, 9.5]
            },
            'HGB': {
                'aliases': ['HGB', 'Hb', '血红蛋白'],
                'unit': 'g/L',
                'range': [115, 150]
            }
        },
        'value_parsing': {
            'less_than': {
                'rule': 'half'
            },
            'greater_than': {
                'rule': 'keep'
            },
            'positive_text': {
                'mapping': {
                    '阳性': 1,
                    '弱阳性': 0.5,
                    '+': 1,
                    '++': 1,
                    '+++': 1
                }
            },
            'negative_text': {
                'mapping': {
                    '阴性': 0,
                    '-': 0
                }
            },
            'invalid_values': {
                'mapping': {
                    '溶血': None,
                    '样本不足': None,
                    '标本凝集': None,
                    '未检出': None,
                    '--': None,
                    '/': None,
                    '#': None
                }
            }
        },
        'output_options': {
            'drop_unknown_tests': True,
            'drop_failed_rows': False
        }
    }
    
    # 确保目录存在
    os.makedirs('profiles/lis_profiles', exist_ok=True)
    
    # 保存
    output_path = 'profiles/lis_profiles/example_hospital_lis.yaml'
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(example_profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✓ 示例 Profile 已创建: {output_path}")
    print("\n配置内容:")
    print(f"  - ID: {example_profile['id']}")
    print(f"  - 描述: {example_profile['description']}")
    print(f"  - 字段映射: {len(example_profile['column_mapping'])} 个")
    print(f"  - 检验项目: {len(example_profile['test_mapping'])} 个")
    

if __name__ == '__main__':
    create_example_profile()

