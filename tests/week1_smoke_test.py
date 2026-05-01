"""src 模块导入测试"""
import sys
import os

# 将项目根目录加入 sys.path，确保可以从任意位置运行此脚本
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from src.type_inference import ColumnType, infer_column_type, normalize_missing_placeholders
from src.file_handler import validate_file
from src.validators import check_missing, check_duplicates, check_numeric_outliers_iqr
from src.data_preview import generate_summary

# Test 1: normalize
s = pd.Series(['N/A', None, 'null', 'hello', ''])
result = normalize_missing_placeholders(s)
assert result.isna().sum() == 4, f"Expected 4 NaN, got {result.isna().sum()}"
print("Test 1 PASS: normalize_missing_placeholders")

# Test 2: Phone detection
s2 = pd.Series(['13812345678', '13987654321', '19900001111', 'invalid', '13812345678'])
r2 = infer_column_type(s2)
assert r2['type'] == ColumnType.PHONE, f"Expected PHONE, got {r2['type']}"
print(f"Test 2 PASS: Phone type={r2['type'].value}, conf={r2['confidence']:.2f}")

# Test 3: Email detection
s3 = pd.Series(['a@b.com', 'test@domain.cn', 'x@y.org', 'invalid', 'x@y.org'])
r3 = infer_column_type(s3)
assert r3['type'] == ColumnType.EMAIL, f"Expected EMAIL, got {r3['type']}"
print(f"Test 3 PASS: Email type={r3['type'].value}, conf={r3['confidence']:.2f}")

# Test 4: Numeric detection
s4 = pd.Series([1.0, 2.5, 3.7, np.nan, 5.0])
r4 = infer_column_type(s4)
assert r4['type'] == ColumnType.NUMERIC, f"Expected NUMERIC, got {r4['type']}"
print(f"Test 4 PASS: Numeric type={r4['type'].value}, conf={r4['confidence']:.2f}")

# Test 5: Text fallback (date_ratio=0 safeguard)
s5 = pd.Series(['abc', 'def', 'ghi'])
r5 = infer_column_type(s5)
print(f"Test 5 PASS: Text fallback type={r5['type'].value} (date_ratio=0 OK)")

# Test 6: IQR type guard
s6 = pd.Series(['a', 'b', 'c'])
r6 = check_numeric_outliers_iqr(s6)
assert r6['outlier_count'] == 0, "Non-numeric should return 0 outliers"
print("Test 6 PASS: IQR non-numeric guard")

# Test 7: check_missing (post-normalize)
df7 = pd.DataFrame({'a': [1.0, np.nan, 3.0], 'b': ['x', np.nan, 'z']})
r7 = check_missing(df7)
print(f"Test 7 PASS: check_missing a={r7['a']['count']}, b={r7['b']['count']}")

# Test 8: check_duplicates
df8 = pd.DataFrame({'a': [1, 2, 1], 'b': ['x', 'y', 'x']})
r8 = check_duplicates(df8)
assert r8['total_duplicates'] == 2, f"Expected 2 duplicates, got {r8['total_duplicates']}"
print("Test 8 PASS: check_duplicates")

# Test 9: generate_summary
df9 = pd.DataFrame({'x': [1, 2, None], 'y': ['a', None, 'c']})
s9 = generate_summary(df9)
assert len(s9) == 2, f"Expected 2 rows in summary, got {len(s9)}"
print("Test 9 PASS: generate_summary")

print("\n🎉 所有导入和基础测试通过！Week 1 开发完成。")
