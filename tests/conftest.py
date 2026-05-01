# tests/conftest.py
# 计划书 v6.0 第十项 10.4 - 测试数据生成
# pytest 配置和共享 fixtures

"""
pytest 配置文件。

提供共享的测试 fixtures：
    - sample_missing_data: 包含缺失值和占位符的测试数据
    - sample_duplicate_data: 包含重复行的测试数据
    - sample_format_data: 包含格式错误的数据
    - sample_numeric_data: 包含数值和异常值的数据
    - sample_outlier_data: 包含明显异常值的数值 Series
    - sample_full_pipeline_data: 混合了缺失、重复、格式错误的小型数据集
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_missing_data() -> pd.DataFrame:
    """
    包含缺失值和占位符的测试数据。

    计划书 v6.0 第十项 10.4：
        - 数值列：包含 np.nan
        - 文本列：包含空字符串和 None
        - 占位列：包含各类文本占位符（'null', 'NULL', 'None', 'NA', 'N/A'）
    """
    return pd.DataFrame({
        '数值列': [1.0, np.nan, 3.0, 4.0, np.nan],
        '文本列': ['a', '', 'b', None, 'N/A'],
        '占位列': ['null', 'NULL', 'None', 'NA', '有效值']
    })


@pytest.fixture
def sample_duplicate_data() -> pd.DataFrame:
    """
    包含重复行的测试数据。

    计划书 v6.0 第十项 10.4：
        - 第 0 行与第 2 行完全相同
        - 第 1 行与第 4 行完全相同
    """
    return pd.DataFrame({
        'a': [1, 2, 1, 3, 2],
        'b': ['x', 'y', 'x', 'z', 'y']
    })


@pytest.fixture
def sample_format_data() -> pd.DataFrame:
    """
    包含格式错误的数据。

    计划书 v6.0 第十项 10.4：
        - 邮箱列：有效、无效、空、None
        - 手机列：有效、超短、带分隔符、带国家代码、字母
    """
    return pd.DataFrame({
        '邮箱': [
            'valid@test.com',
            'invalid',
            'test@',
            '@gmail.com',
            '',         # 空字符串
        ],
        '手机': [
            '13812345678',
            '12345',
            '138-1234-5678',
            '+86 13812345678',
            'abc',
        ]
    })


@pytest.fixture
def sample_numeric_data() -> pd.DataFrame:
    """
    包含数值和异常值的测试数据。

    用于测试 IQR 异常值检测。
    """
    return pd.DataFrame({
        '正常值': [10.0, 12.0, 11.0, 13.0, 10.0, 11.5],
        '含异常值': [10.0, 12.0, 100.0, 13.0, -50.0, 11.5],
        '文本列': ['a', 'b', 'c', 'd', 'e', 'f']
    })


@pytest.fixture
def sample_outlier_series() -> pd.Series:
    """
    包含明显异常值的数值 Series。

    计划书 Week 2 任务4 - 用于 IQR 测试
    Q1=7.5, Q3=12.5, IQR=5.0
    lower = 7.5 - 1.5*5.0 = 0.0
    upper = 12.5 + 1.5*5.0 = 20.0
    异常值：-5.0（低于下界）、30.0（高于上界）
    """
    return pd.Series([10.0, 12.0, 8.0, 11.0, -5.0, 30.0], name='数值')


@pytest.fixture
def sample_full_pipeline_data() -> pd.DataFrame:
    """
    混合了缺失、重复、格式错误的小型数据集。

    用于 clean_data_pipeline 集成测试。

    特征：
        - 5 行数据
        - 第 0 行与第 4 行完全相同（重复行）
        - 第 1 行姓名缺失
        - 第 1 行薪资缺失（数值列）
        - 第 2 行年龄缺失（数值列）
        清洗后期望：3 行，缺失值被填充，重复行被删除
    """
    return pd.DataFrame({
        '姓名': ['张三', None, '王五', '张三'],
        '年龄': [25.0, 30.0, None, 25.0],
        '薪资': [5000.0, None, 8000.0, 5000.0],
        '部门': ['技术', '销售', '技术', '技术']
    })
