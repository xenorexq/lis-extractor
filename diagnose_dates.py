"""
诊断脚本：检查 Excel 文件中的日期列
用于排查 sample_datetime 为空的问题
"""
import pandas as pd
import sys
from datetime import datetime


def diagnose_date_column(file_path, date_column_name='检验日期'):
    """
    诊断日期列的问题
    """
    print("=" * 60)
    print("LIS 日期列诊断工具")
    print("=" * 60)
    print(f"\n正在读取文件: {file_path}")
    
    try:
        # 读取文件
        df = pd.read_excel(file_path, nrows=100)
        print(f"✓ 文件读取成功，共 {len(df)} 行（前100行）")
        
        # 显示所有列名
        print(f"\n【文件中的所有列】")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # 查找可能的日期列
        print(f"\n【查找日期列】")
        date_keywords = ['日期', '时间', 'date', 'time', '检验', '采样']
        possible_date_cols = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in date_keywords):
                possible_date_cols.append(col)
        
        if possible_date_cols:
            print(f"✓ 找到可能的日期列:")
            for col in possible_date_cols:
                print(f"  - {col}")
        else:
            print(f"✗ 未找到明显的日期列")
        
        # 检查指定的日期列
        if date_column_name not in df.columns:
            print(f"\n⚠️ 警告: 列 '{date_column_name}' 不存在！")
            
            # 尝试查找相似的列名
            similar_cols = [col for col in df.columns if '日期' in str(col) or 'date' in str(col).lower()]
            if similar_cols:
                print(f"\n是否是以下列之一？")
                for col in similar_cols:
                    print(f"  - {col}")
                    date_column_name = col  # 使用第一个匹配的列
                    break
            else:
                print(f"\n请手动指定正确的日期列名")
                return
        
        print(f"\n【分析日期列: {date_column_name}】")
        
        date_col = df[date_column_name]
        
        # 统计信息
        total = len(date_col)
        non_null = date_col.notna().sum()
        null_count = date_col.isna().sum()
        
        print(f"  总行数: {total}")
        print(f"  非空行: {non_null} ({non_null/total*100:.1f}%)")
        print(f"  空值行: {null_count} ({null_count/total*100:.1f}%)")
        
        if non_null == 0:
            print(f"\n❌ 错误：日期列完全为空！")
            return
        
        # 显示样本值
        print(f"\n【日期列样本值】（前10个非空值）")
        samples = date_col.dropna().head(10)
        for i, val in enumerate(samples, 1):
            val_type = type(val).__name__
            print(f"  {i}. {val} (类型: {val_type})")
        
        # 检测数据类型
        print(f"\n【数据类型分析】")
        dtypes = date_col.dropna().apply(type).value_counts()
        for dtype, count in dtypes.items():
            print(f"  {dtype.__name__}: {count} 个")
        
        # 尝试解析日期
        print(f"\n【尝试解析日期】")
        from core.utils import parse_datetime
        
        parsed = date_col.apply(parse_datetime)
        parsed_success = parsed.notna().sum()
        
        print(f"  解析成功: {parsed_success}/{non_null} ({parsed_success/non_null*100:.1f}%)")
        
        if parsed_success == 0:
            print(f"\n❌ 所有日期解析都失败了！")
            print(f"\n可能的原因:")
            print(f"  1. 日期格式不被支持")
            print(f"  2. 数据类型异常")
            print(f"  3. 包含特殊字符")
            
            # 显示无法解析的样本
            print(f"\n【无法解析的样本】")
            failed_samples = date_col[parsed.isna() & date_col.notna()].head(5)
            for i, val in enumerate(failed_samples, 1):
                print(f"  {i}. {repr(val)} (类型: {type(val).__name__})")
        else:
            print(f"✓ 日期解析成功！")
            print(f"\n【解析后的样本】")
            parsed_samples = parsed.dropna().head(5)
            for i, val in enumerate(parsed_samples, 1):
                print(f"  {i}. {val}")
        
        print("\n" + "=" * 60)
        print("诊断完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 diagnose_dates.py <excel文件路径> [日期列名]")
        print("\n示例:")
        print("  python3 diagnose_dates.py test_lis_data.xlsx")
        print("  python3 diagnose_dates.py data.xlsx 检验日期")
        sys.exit(1)
    
    file_path = sys.argv[1]
    date_col = sys.argv[2] if len(sys.argv) > 2 else '检验日期'
    
    diagnose_date_column(file_path, date_col)

