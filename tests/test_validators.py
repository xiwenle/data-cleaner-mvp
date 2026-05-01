# tests/test_validators.py
# 计划书 v6.0 Week 2 任务3 - P0 验证规则单元测试

"""
验证规则测试。

测试范围：
    - check_missing: 缺失值检测（仅依赖 pd.isnull()）
    - check_duplicates: 重复行检测
    - check_email_format: 邮箱格式验证
    - check_phone_format: 中国手机号验证（含 +86、横杠变体）
    - check_numeric_outliers_iqr: IQR 异常值（含非数值列守卫）
"""

import numpy as np
import pandas as pd

from src.validators import (
    check_missing,
    check_duplicates,
    check_email_format,
    check_phone_format,
    check_numeric_outliers_iqr,
)


class TestCheckMissing:
    """缺失值检测测试 - 计划书 v6.0 第十项修正：仅依赖 pd.isnull()"""

    def test_detect_nan_in_numeric(self, sample_missing_data):
        """数值列中的 NaN 应被检测到"""
        result = check_missing(sample_missing_data)
        assert '数值列' in result
        assert result['数值列']['count'] == 2
        assert result['数值列']['rate'] == 40.0  # 2/5

    def test_detect_none_in_text(self, sample_missing_data):
        """文本列中的 None 应被检测到"""
        result = check_missing(sample_missing_data)
        assert '文本列' in result
        # 文本列：'a', '', 'b', None, 'N/A'
        # None → NaN（pandas 自动处理），所以 1 个缺失
        assert result['文本列']['count'] == 1

    def test_placeholder_strings_not_detected(self, sample_missing_data):
        """
        🔴 关键测试：占位符 'N/A'、'null' 等字符串不应被 check_missing 检测为缺失。
        因为 check_missing 仅依赖 pd.isnull()，占位符标准化由 normalize_missing_placeholders 负责。
        """
        result = check_missing(sample_missing_data)
        # 占位列：'null', 'NULL', 'None', 'NA', '有效值' — 全是字符串，不含 NaN
        assert '占位列' not in result, (
            "占位列中的 'null'/'NULL' 等是字符串，不是 NaN，"
            "check_missing 不应检测到它们（占位符标准化在其他步骤处理）"
        )

    def test_top_positions_limit(self):
        """top_positions 只返回前 20 个"""
        df = pd.DataFrame({'x': [np.nan] * 50})
        result = check_missing(df)
        assert len(result['x']['top_positions']) <= 20


class TestCheckDuplicates:
    """重复行检测测试"""

    def test_detect_all_duplicates(self, sample_duplicate_data):
        """
        sample_duplicate_data:
            第 0 行与第 2 行相同 → 2 条
            第 1 行与第 4 行相同 → 2 条
            共 4 条重复
        """
        result = check_duplicates(sample_duplicate_data)
        assert result['total_duplicates'] == 4

    def test_duplicate_indices_returned(self, sample_duplicate_data):
        """验证返回重复行的索引列表"""
        result = check_duplicates(sample_duplicate_data)
        assert 'all_duplicate_indices' in result['duplicate_groups']
        indices = result['duplicate_groups']['all_duplicate_indices']
        assert sorted(indices) == [0, 1, 2, 4]

    def test_no_duplicates(self):
        """无重复行时返回 0"""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        result = check_duplicates(df)
        assert result['total_duplicates'] == 0


class TestCheckEmailFormat:
    """邮箱格式验证测试"""

    def test_valid_and_invalid_counts(self, sample_format_data):
        """
        sample_format_data['邮箱']:
            'valid@test.com' → 有效
            'invalid' → 无效
            'test@' → 无效
            '@gmail.com' → 无效
            '' → 无效
            np.nan → 跳过（不参与计数）
        期望: valid=1, invalid=4
        """
        result = check_email_format(sample_format_data['邮箱'])
        assert result['valid_count'] == 1
        assert result['invalid_count'] == 4

    def test_invalid_values_list(self, sample_format_data):
        """验证返回无效值列表"""
        result = check_email_format(sample_format_data['邮箱'])
        assert 'invalid' in result['invalid_values']


class TestCheckPhoneFormat:
    """中国手机号验证测试"""

    def test_valid_phone(self, sample_format_data):
        """
        sample_format_data['手机']:
            '13812345678' → 有效
            '12345' → 无效（太短）
            '138-1234-5678' → 归一化后有效
            '+86 13812345678' → 归一化后有效
            'abc' → 无效
        期望: valid=3, invalid=2
        """
        result = check_phone_format(sample_format_data['手机'])
        assert result['valid_count'] == 3
        assert result['invalid_count'] == 2

    def test_phone_with_hyphen_accepted(self):
        """带横杠的手机号应被正确归一化"""
        s = pd.Series(['138-0000-1111'])
        result = check_phone_format(s)
        assert result['valid_count'] == 1

    def test_phone_with_country_code_accepted(self):
        """带 +86 的手机号应被正确归一化"""
        s = pd.Series(['+86 13900001111'])
        result = check_phone_format(s)
        assert result['valid_count'] == 1

    def test_invalid_phone_second_digit(self):
        """第二位不是 3-9 的手机号无效"""
        s = pd.Series(['10123456789', '11123456789', '12123456789'])
        result = check_phone_format(s)
        assert result['invalid_count'] == 3


class TestCheckNumericOutliersIQR:
    """IQR 异常值检测测试"""

    def test_detect_outliers(self, sample_outlier_series):
        """
        sample_outlier_series: [10, 12, 8, 11, -5, 30]
        Q1≈8.5, Q3≈11.75, IQR≈3.25
        lower≈3.625, upper≈16.625
        -5 和 30 为异常值 → 2 个
        """
        result = check_numeric_outliers_iqr(sample_outlier_series)
        assert result['outlier_count'] == 2
        assert result['lower_bound'] is not None
        assert result['upper_bound'] is not None

    def test_lower_than_lower_bound_is_outlier(self, sample_outlier_series):
        """低于下界的值应被标记"""
        result = check_numeric_outliers_iqr(sample_outlier_series)
        assert -5.0 in result['outlier_values']

    def test_higher_than_upper_bound_is_outlier(self, sample_outlier_series):
        """高于上界的值应被标记"""
        result = check_numeric_outliers_iqr(sample_outlier_series)
        assert 30.0 in result['outlier_values']

    def test_normal_values_not_in_outliers(self):
        """正常范围内不应有异常值"""
        s = pd.Series([10.0, 12.0, 11.0, 13.0, 10.0])
        result = check_numeric_outliers_iqr(s)
        assert result['outlier_count'] == 0

    def test_non_numeric_guard(self, sample_numeric_data):
        """
        🔴 计划书 v6.0 第八项修正：非数值列传入时返回空结果而不报错
        """
        result = check_numeric_outliers_iqr(sample_numeric_data['文本列'])
        assert result['error'] is not None
        assert result['outlier_count'] == 0
        assert result['lower_bound'] is None

    def test_different_multiplier_affects_detection(self):
        """
        更大的 IQR 倍数 → 更宽松 → 更少异常值
        """
        s = pd.Series([10.0, 12.0, 8.0, 11.0, -5.0, 30.0])
        r1 = check_numeric_outliers_iqr(s, multiplier=1.5)
        r2 = check_numeric_outliers_iqr(s, multiplier=3.0)
        assert r1['outlier_count'] >= r2['outlier_count']

    def test_full_nan_column_returns_zeros(self):
        """
        🔴 QA补充：全 NaN 数值列应返回 0.0 边界而非 NaN
        """
        s = pd.Series([np.nan, np.nan, np.nan], dtype='float64')
        result = check_numeric_outliers_iqr(s)
        assert result['lower_bound'] == 0.0
        assert result['upper_bound'] == 0.0
        assert result['outlier_count'] == 0

    def test_single_value_no_outliers(self):
        """
        🔴 QA补充：单一值列 IQR=0 应返回 0 个异常值
        """
        s = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
        result = check_numeric_outliers_iqr(s)
        assert result['outlier_count'] == 0
