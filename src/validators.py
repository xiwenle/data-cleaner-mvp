# src/validators.py
# 计划书 v6.0 第七项 7.4 - 验证规则模块（Week 2 完整实现）

"""
数据验证规则模块。

提供各类数据质量检测函数：
- 缺失值检测（check_missing）
- 重复行检测（check_duplicates）
- 格式验证（邮箱、手机号）
- 异常值检测（IQR 方法）

重要：
- 本模块不依赖 streamlit，保持纯函数可测试
- check_missing 假设输入数据已经过 normalize_missing_placeholders 预处理
  （参考计划书 v6.0 第十项修正：检测逻辑仅依赖 pd.isnull()）
"""

import re
import numpy as np
import pandas as pd


# 预编译正则
PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
EMAIL_PATTERN = re.compile(r'^[-a-zA-Z0-9._%+]+@[-a-zA-Z0-9.]+\.[a-zA-Z]{2,}$')


def _normalize_phone(value: str) -> str:
    """去除手机号中的分隔符，用于匹配前预处理"""
    if not isinstance(value, str):
        return ''
    cleaned = re.sub(r'[\s\-.\+\(\)（\）]+', '', value)
    if cleaned.startswith('86'):
        cleaned = cleaned[2:]
    return cleaned


def check_missing(df: pd.DataFrame) -> dict:
    """
    检测缺失值。

    计划书 v6.0 第十项修正：
        - 输入数据已经过占位符标准化，仅依赖 pd.isnull()
        - 仅返回前 20 个行索引，避免大文件内存爆炸
    """
    result = {}
    for col in df.columns:
        missing_mask = df[col].isna()
        count = int(missing_mask.sum())
        rate = round(count / len(df) * 100, 2) if len(df) > 0 else 0.0

        if count > 0:
            positions = df.index[missing_mask].tolist()
            result[col] = {
                'count': count,
                'rate': rate,
                'top_positions': positions[:20]
            }
    return result


def check_duplicates(df: pd.DataFrame) -> dict:
    """检测完全重复的行"""
    duplicate_mask = df.duplicated(keep=False)
    total_duplicates = int(duplicate_mask.sum())

    result = {
        'total_duplicates': total_duplicates,
        'duplicate_groups': {}
    }

    if total_duplicates > 0:
        dup_indices = df.index[duplicate_mask].tolist()
        result['duplicate_groups'] = {'all_duplicate_indices': dup_indices[:100]}

    return result


def check_email_format(series: pd.Series) -> dict:
    r"""
    检测邮箱格式。

    计划书 v6.0 第八项 规则3 - 邮箱格式验证
    正则：^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    """
    valid_mask = series.notna() & series.astype(str).str.strip().apply(
        lambda x: bool(EMAIL_PATTERN.match(x)) if x else False
    )
    invalid_mask = series.notna() & ~valid_mask

    valid_count = int(valid_mask.sum())
    invalid_count = int(invalid_mask.sum())

    return {
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'invalid_positions': series.index[invalid_mask].tolist()[:20],
        'invalid_values': series[invalid_mask].tolist()[:20]
    }


def check_phone_format(series: pd.Series, country: str = 'CN') -> dict:
    """
    检测手机号格式。

    计划书 v6.0 第八项 规则4 - 先归一化再匹配
    规则：去除分隔符后 11 位数字，1 开头，第二位 3-9

    参数:
        series: 手机号列
        country: 国家代码（当前仅支持 'CN'）
    """
    # 仅支持中国手机号格式
    _ = country
    valid_mask = series.notna() & series.astype(str).apply(
        lambda x: bool(PHONE_PATTERN.match(_normalize_phone(str(x))))
    )
    invalid_mask = series.notna() & ~valid_mask

    valid_count = int(valid_mask.sum())
    invalid_count = int(invalid_mask.sum())

    return {
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'invalid_positions': series.index[invalid_mask].tolist()[:20],
        'invalid_values': series[invalid_mask].tolist()[:20]
    }


def check_numeric_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> dict:
    """
    使用 IQR 方法检测数值异常值。

    计划书 v6.0 第八项 - 必须添加类型守卫
    """
    if not pd.api.types.is_numeric_dtype(series):
        return {
            'error': '非数值列，无法进行异常值检测',
            'lower_bound': None,
            'upper_bound': None,
            'outlier_count': 0,
            'outlier_positions': [],
            'outlier_values': []
        }

    # 全 NaN 列保护：quantile 在全 NaN 时返回 NaN，导致边界也为 NaN
    clean = series.dropna()
    if len(clean) == 0:
        return {
            'lower_bound': 0.0,
            'upper_bound': 0.0,
            'outlier_count': 0,
            'outlier_positions': [],
            'outlier_values': []
        }

    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR

    outlier_mask = (series < lower) | (series > upper)
    outlier_count = int(outlier_mask.sum())

    return {
        'lower_bound': float(lower),
        'upper_bound': float(upper),
        'outlier_count': outlier_count,
        'outlier_positions': series.index[outlier_mask].tolist()[:20] if outlier_count > 0 else [],
        'outlier_values': series[outlier_mask].tolist()[:20] if outlier_count > 0 else []
    }
