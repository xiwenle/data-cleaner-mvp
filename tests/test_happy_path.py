# tests/test_happy_path.py
# 计划书 v6.0 §10.2 - Happy Path 端到端集成测试（Week 3 任务3）

"""
端到端集成测试。

模拟计划书定义的 happy path 场景：
    - happy_path_1: 缺失值 + 重复行
    - happy_path_2: 邮箱/手机号格式错误

所有测试数据通过 io.StringIO 内联创建，不依赖外部文件。
"""

import io
import pandas as pd

from src.cleaners import clean_data_pipeline
from src.validators import check_missing, check_email_format, check_phone_format
from src.type_inference import ColumnType, normalize_missing_placeholders


class TestHappyPath1MissingAndDuplicates:
    """
    计划书 §10.2 Happy Path 1：缺失值 + 重复行

    数据特征：
        - 5 行 2 列（姓名、年龄）
        - 第 2 行姓名缺失，第 1 行年龄缺失
        - 第 0 行与第 4 行完全相同
        清洗后期望：3 行，无缺失值，年龄为数值
    """

    @staticmethod
    def _build_df():
        csv_content = "姓名,年龄\n张三,25\n李四,\n,30\n王五,35\n张三,25\n"
        return pd.read_csv(io.StringIO(csv_content))

    def test_original_five_rows(self):
        df = self._build_df()
        assert len(df) == 5, f"原始数据应为 5 行，实际 {len(df)} 行"

    def test_final_three_rows_after_cleaning(self):
        """清洗后行数应为 4（1 行重复被删除）"""
        df = self._build_df()
        config = {
            'remove_duplicates': True,
            'numeric_missing_strategy': 'median',
            'handle_outliers': False,
        }
        df_cleaned, log = clean_data_pipeline(df, config)

        assert log['original_rows'] == 5, f"原始行数应为 5，实际 {log['original_rows']}"
        assert log['final_rows'] == 4, f"清洗后行数应为 4（1组重复），实际 {log['final_rows']}"
        assert log['total_removed'] == 1, f"应删除 1 行重复，实际删除 {log['total_removed']}"

    def test_no_missing_values_after_cleaning(self):
        """清洗后姓名和年龄列应无缺失值"""
        df = self._build_df()
        config = {
            'remove_duplicates': True,
            'numeric_missing_strategy': 'median',
            'handle_outliers': False,
        }
        df_cleaned, _ = clean_data_pipeline(df, config)

        assert df_cleaned['姓名'].isna().sum() == 0, "姓名列清洗后不应有缺失值"
        assert df_cleaned['年龄'].isna().sum() == 0, "年龄列清洗后不应有缺失值"

    def test_age_is_numeric(self):
        """年龄列清洗后应为数值类型"""
        df = self._build_df()
        config = {
            'remove_duplicates': True,
            'numeric_missing_strategy': 'median',
            'handle_outliers': False,
        }
        df_cleaned, _ = clean_data_pipeline(df, config)

        assert pd.api.types.is_numeric_dtype(df_cleaned['年龄']), (
            f"年龄列应为数值类型，实际为 {df_cleaned['年龄'].dtype}"
        )

    def test_log_contains_expected_steps(self):
        """日志应包含所有核心步骤"""
        df = self._build_df()
        config = {'remove_duplicates': True}
        _, log = clean_data_pipeline(df, config)

        step_names = [s['name'] for s in log['steps']]
        assert '缺失占位符标准化' in step_names
        assert '重复行处理' in step_names
        assert '缺失值填充' in step_names


class TestHappyPath2EmailPhoneValidation:
    """
    计划书 §10.2 Happy Path 2：邮箱/手机号格式错误

    数据特征：
        - 4 行 2 列（邮箱、手机）
        - 邮箱：1 个有效，4 个无效（含空和错误格式）
        - 手机：1 个有效（带横杠），4 个无效
    """

    @staticmethod
    def _build_df():
        csv_content = (
            "邮箱,手机\n"
            "valid@test.com,138-1234-5678\n"
            "invalid,12345\n"
            "test@,abc\n"
            "@gmail.com,+86 13900001111\n"
            ",13812345678\n"
        )
        return pd.read_csv(io.StringIO(csv_content))

    def test_email_invalid_count(self):
        """
        邮箱检测：valid@test.com 有效，其余 4 个无效（包括 NaN）
        """
        df = self._build_df()
        # 先标准化缺失占位符（将空字符串转为 NaN）
        df['邮箱'] = normalize_missing_placeholders(df['邮箱'])
        result = check_email_format(df['邮箱'])
        assert result['invalid_count'] == 3, (
            f"邮箱无效数应为 3，实际 {result['invalid_count']}"
        )

    def test_phone_invalid_count(self):
        """
        手机号检测：138-1234-5678（归一化后有效）、+86 13900001111（归一化后有效）、
        13812345678（有效），12345（不足11位）和 abc（字母）无效 → 2 个无效
        """
        df = self._build_df()
        result = check_phone_format(df['手机'])
        assert result['invalid_count'] == 2, (
            f"手机号无效数应为 2，实际 {result['invalid_count']}"
        )

    def test_phone_column_remains_object_after_cleaning(self):
        """
        清洗后手机列应保持为 object（文本）类型，不会被误转为数值
        """
        df = self._build_df()
        # 指定列为 EMAIL 和 PHONE 类型确保检测生效
        user_overrides = {
            '邮箱': ColumnType.EMAIL,
            '手机': ColumnType.PHONE,
        }
        config = {'remove_duplicates': True}
        df_cleaned, log = clean_data_pipeline(df, config, user_overrides=user_overrides)

        assert df_cleaned['手机'].dtype == object, (
            f"手机列应为 object 类型，实际为 {df_cleaned['手机'].dtype}"
        )

    def test_email_column_remains_object_after_cleaning(self):
        """清洗后邮箱列应保持为 object（文本）类型"""
        df = self._build_df()
        user_overrides = {
            '邮箱': ColumnType.EMAIL,
            '手机': ColumnType.PHONE,
        }
        config = {'remove_duplicates': True}
        df_cleaned, _ = clean_data_pipeline(df, config, user_overrides=user_overrides)

        assert df_cleaned['邮箱'].dtype == object, (
            f"邮箱列应为 object 类型，实际为 {df_cleaned['邮箱'].dtype}"
        )

    def test_type_inference_in_log(self):
        """
        日志中的类型推断结果应反映 user_overrides 指定的类型
        """
        df = self._build_df()
        user_overrides = {
            '邮箱': ColumnType.EMAIL,
            '手机': ColumnType.PHONE,
        }
        config = {'remove_duplicates': True}
        _, log = clean_data_pipeline(df, config, user_overrides=user_overrides)

        type_step = [s for s in log['steps'] if s['name'] == '列类型推断'][0]
        results = type_step['results']

        assert results['邮箱']['type'] == 'email', (
            f"邮箱类型应为 email，实际为 {results['邮箱']['type']}"
        )
        assert results['手机']['type'] == 'phone', (
            f"手机类型应为 phone，实际为 {results['手机']['type']}"
        )
