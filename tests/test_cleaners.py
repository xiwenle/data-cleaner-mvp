# tests/test_cleaners.py
# 计划书 v6.0 Week 2 任务3 - P0 清洗逻辑单元测试

"""
清洗逻辑测试。

测试范围：
    - clean_data_pipeline: 完整流水线（缺失填充、重复删除、异常值裁剪）
    - _fill_numeric_missing: 各策略（auto/mean/median/zero/no_fill）
    - _fill_text_missing: 众数 / 指定值
    - 异常值裁剪（clip 到边界值）
"""

import numpy as np
import pandas as pd

from src.cleaners import clean_data_pipeline, _fill_numeric_missing, _fill_text_missing
from src.type_inference import ColumnType


class TestCleanDataPipeline:
    """完整清洗流水线测试"""

    def test_duplicates_removed(self, sample_full_pipeline_data):
        """
        sample_full_pipeline_data: 4 行
        第 0 行(张三,25,5000,技术) 与第 3 行(张三,25,5000,技术) 完全相同
        期望：清洗后 3 行，1 行被删除
        """
        config = {'remove_duplicates': True}
        df_cleaned, log = clean_data_pipeline(sample_full_pipeline_data, config)

        assert log['original_rows'] == 4
        assert log['final_rows'] == 3
        assert log['total_removed'] == 1

    def test_missing_values_filled(self, sample_full_pipeline_data):
        """
        验证缺失值被填充：
            - 姓名（文本）：None → 众数 '张三'
            - 年龄（数值）：NaN → 均值 27.5
            - 薪资（数值）：NaN → 均值 6500.0
        """
        config = {'remove_duplicates': True}
        df_cleaned, log = clean_data_pipeline(sample_full_pipeline_data, config)

        # 清洗后不应有缺失值（日期列除外）
        assert df_cleaned['姓名'].isna().sum() == 0
        assert df_cleaned['年龄'].isna().sum() == 0
        assert df_cleaned['薪资'].isna().sum() == 0

    def test_log_contains_all_steps(self, sample_full_pipeline_data):
        """验证清洗日志包含所有 7 个步骤"""
        config = {'remove_duplicates': True}
        _, log = clean_data_pipeline(sample_full_pipeline_data, config)

        step_names = [step['name'] for step in log['steps']]
        expected_steps = [
            '缺失占位符标准化',
            '列类型推断',
            '类型转换',
            '重复行处理',
            '缺失值填充',
            '异常值处理',
            '格式标准化',
        ]
        for expected in expected_steps:
            assert expected in step_names, f"日志中缺少步骤: {expected}"

    def test_log_includes_fill_details(self, sample_full_pipeline_data):
        """清洗日志应包含缺失值填充的详细信息"""
        config = {'remove_duplicates': True}
        _, log = clean_data_pipeline(sample_full_pipeline_data, config)

        fill_step = [s for s in log['steps'] if s['name'] == '缺失值填充'][0]
        assert 'fill_values' in fill_step

    def test_duplicates_not_removed_when_config_false(self, sample_full_pipeline_data):
        """配置 remove_duplicates=False 时不删除重复行"""
        config = {'remove_duplicates': False}
        df_cleaned, log = clean_data_pipeline(sample_full_pipeline_data, config)
        assert log['total_removed'] == 0

    def test_text_fill_with_custom_value(self, sample_full_pipeline_data):
        """用户指定文本填充值时使用该固定值"""
        config = {
            'remove_duplicates': True,
            'text_fill_value': '未知姓名'
        }
        df_cleaned, _ = clean_data_pipeline(sample_full_pipeline_data, config)
        # 姓名列缺失值应被填充为 '未知姓名'
        assert '未知姓名' in df_cleaned['姓名'].values

    def test_numeric_no_fill_strategy(self, sample_full_pipeline_data):
        """不填充策略下数值缺失值保持为 NaN"""
        config = {
            'remove_duplicates': True,
            'numeric_missing_strategy': 'no_fill'
        }
        df_cleaned, _ = clean_data_pipeline(sample_full_pipeline_data, config)
        # 年龄和薪资列均应仍有 NaN（在去重后的行中）
        assert df_cleaned['年龄'].isna().any() or df_cleaned['薪资'].isna().any()


class TestfillNumericMissing:
    """数值列缺失值填充测试"""

    def test_auto_with_skew(self):
        """
        auto 策略：偏度 > 1 时用中位数
        构造右偏数据：[1, 2, 3, 4, 100] → skew > 1 → 用 median=3
        """
        s = pd.Series([1.0, 2.0, np.nan, 4.0, 100.0])
        result, info = _fill_numeric_missing(s, method='auto')
        # median of [1,2,4,100] = 3.0
        assert info['method'] == 'median'
        assert result.iloc[2] == 3.0

    def test_mean_strategy(self):
        """mean 策略：填充均值"""
        s = pd.Series([10.0, 20.0, np.nan])
        result, info = _fill_numeric_missing(s, method='mean')
        assert info['method'] == 'mean'
        assert result.iloc[2] == 15.0

    def test_median_strategy(self):
        """median 策略：填充中位数"""
        s = pd.Series([10.0, 20.0, np.nan, 30.0])
        result, info = _fill_numeric_missing(s, method='median')
        assert info['method'] == 'median'
        assert result.iloc[2] == 20.0

    def test_zero_strategy(self):
        """zero 策略：填充 0"""
        s = pd.Series([10.0, np.nan, 30.0])
        result, info = _fill_numeric_missing(s, method='zero')
        assert info['method'] == 'zero'
        assert info['value'] == 0.0
        assert result.iloc[1] == 0.0

    def test_no_fill_strategy(self):
        """no_fill 策略：不填充"""
        s = pd.Series([10.0, np.nan, 30.0])
        result, info = _fill_numeric_missing(s, method='no_fill')
        assert info['method'] == '不填充'
        assert np.isnan(result.iloc[1])

    def test_no_missing_values(self):
        """无缺失值时返回原始数据"""
        s = pd.Series([1.0, 2.0, 3.0])
        result, info = _fill_numeric_missing(s, method='auto')
        assert info == {}
        assert list(result) == [1.0, 2.0, 3.0]

    def test_info_contains_count(self):
        """info 应包含填充的缺失值数量"""
        s = pd.Series([10.0, np.nan, np.nan, 40.0])
        _, info = _fill_numeric_missing(s, method='mean')
        assert info['count'] == 2


class TestFillTextMissing:
    """文本列缺失值填充测试"""

    def test_mode_when_no_custom_value(self):
        """不指定填充值时使用众数"""
        s = pd.Series(['a', 'b', np.nan, 'a', 'b'])
        result, info = _fill_text_missing(s, '')
        assert info['method'] == '众数'
        # mode 可能是 'a' 或 'b'（任一均可）
        assert result.iloc[2] in ['a', 'b']
        assert info['count'] == 1

    def test_custom_value_when_specified(self):
        """指定填充值时使用该固定值"""
        s = pd.Series(['x', np.nan, 'y'])
        result, info = _fill_text_missing(s, '自定义值')
        assert info['method'] == '指定值'
        assert info['value'] == '自定义值'
        assert result.iloc[1] == '自定义值'

    def test_no_missing_values(self):
        """无缺失值时返回原始数据和空 info"""
        s = pd.Series(['a', 'b', 'c'])
        result, info = _fill_text_missing(s, '')
        assert info == {}


class TestOutlierClipping:
    """异常值裁剪测试"""

    def test_outliers_clipped_to_bounds(self):
        """
        清洗流水线应将异常值裁剪到 IQR 边界。
        构造数据：[10, 12, 8, 11, -100, 200]
        Q1≈8.5, Q3≈11.75, IQR≈3.25
        lower≈3.625, upper≈16.625
        -100 应被 clip 到 3.625
        200 应被 clip 到 16.625
        """
        df = pd.DataFrame({
            'x': [10.0, 12.0, 8.0, 11.0, -100.0, 200.0]
        })
        config = {
            'remove_duplicates': False,
            'handle_outliers': True,
            'outlier_multiplier': 1.5
        }
        df_cleaned, log = clean_data_pipeline(df, config)

        # 检查异常值步骤日志
        outlier_step = [s for s in log['steps'] if s['name'] == '异常值处理'][0]
        assert 'x' in outlier_step['by_column']
        assert outlier_step['by_column']['x'] == 2  # 2 个异常值

        # 验证被裁剪的值不再超出范围
        Q1 = df['x'].quantile(0.25)
        Q3 = df['x'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        assert df_cleaned['x'].min() >= lower - 1e-6
        assert df_cleaned['x'].max() <= upper + 1e-6

    def test_outlier_disabled(self):
        """handle_outliers=False 时不裁剪异常值"""
        df = pd.DataFrame({'x': [10.0, 12.0, 100.0]})
        config = {
            'remove_duplicates': False,
            'handle_outliers': False,
            'outlier_multiplier': 1.5
        }
        df_cleaned, log = clean_data_pipeline(df, config)
        # 100.0 应保持不变
        assert df_cleaned['x'].max() == 100.0

    def test_string_numeric_conversion(self):
        """
        🔴 QA补充：字符串数值列应被正确转换为数值类型，
        避免 '25'/'5000' 在调用 .mean() 时 TypeError
        """
        df = pd.DataFrame({
            '年龄': ['25', '30', 'N/A', '35', ''],
            '薪资': ['5000', '8000', '', '12000', 'null'],
            '姓名': ['张三', '李四', None, '王五', '赵六']
        })
        config = {'remove_duplicates': True, 'handle_outliers': False}
        df_c, log = clean_data_pipeline(df, config)
        # 不应崩溃，且数值列应被正确填充
        assert df_c['年龄'].isna().sum() == 0, "年龄列缺失应被填充"
        assert df_c['薪资'].isna().sum() == 0, "薪资列缺失应被填充"
        assert pd.api.types.is_numeric_dtype(df_c['年龄']), "年龄应为数值类型"
        assert pd.api.types.is_numeric_dtype(df_c['薪资']), "薪资应为数值类型"

    def test_all_nan_numeric_column_handled(self):
        """
        🔴 QA补充：全 NaN 数值列在清洗流水线中不应崩溃
        """
        df = pd.DataFrame({'x': [np.nan, np.nan, np.nan]})
        config = {'remove_duplicates': False, 'handle_outliers': True}
        df_c, log = clean_data_pipeline(df, config)
        assert len(df_c) == 3
        assert df_c['x'].isna().sum() == 0, "全NaN列缺失应被填充"
