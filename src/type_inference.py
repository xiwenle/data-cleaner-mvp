# src/type_inference.py
# 计划书 v6.0 第七项 7.3 - 类型推断模块
# 🔴 关键修正：此模块仅推断类型并返回信息，不修改原始数据
# 类型转换统一在 cleaners.py 中完成

"""
列类型智能推断模块。

职责：
- 将缺失占位符标准化为 NaN
- 推断每列的语义类型（数值/文本/日期/手机/邮箱/ID）

重要：
- 本模块不依赖 streamlit，保持纯函数可测试
- infer_column_type() 仅返回类型信息，不修改传入的 Series
- 正则匹配（手机号/邮箱）优先于数值尝试，防止电话被误判为数值
"""

import re
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from .config import MISSING_PLACEHOLDERS, AGGRESSIVE_PLACEHOLDERS


class ColumnType(Enum):
    """列类型枚举"""
    UNKNOWN = "unknown"
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    ID = "id"


# ---------- 正则模式（预编译，避免每次调用时重复编译）----------

# 中国手机号：1 开头 + 3-9 + 9 位数字（去除分隔符后匹配）
PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')

# 邮箱格式：本地部分@域名.顶级域名
EMAIL_PATTERN = re.compile(r'^[\w.\-+]+@[\w.\-]+\.\w{2,}$')

# 身份证号：15 位数字 或 17 位数字 + X/x
ID_PATTERN = re.compile(r'^\d{15}$|^\d{17}[\dXx]$')


def normalize_missing_placeholders(series: pd.Series, aggressive: bool = False) -> pd.Series:
    """
    将列中的各类文本占位符统一转为 NaN。

    计划书 v6.0 第十二项修正：aggressive 模式默认关闭，
    避免将真实文本 "nan" 误转为缺失值。

    参数:
        series: 原始列数据
        aggressive: 是否额外处理易误伤的占位符（如 'nan', 'Nan'）

    返回:
        标准化后的 Series（占位符 → NaN，其他值不变）
    """
    placeholders = MISSING_PLACEHOLDERS.copy()
    if aggressive:
        placeholders.update(AGGRESSIVE_PLACEHOLDERS)

    def to_missing(value):
        """将占位符转为 NaN，其他值原样返回"""
        if pd.isna(value):
            return np.nan
        val_str = str(value).strip()
        if val_str in placeholders:
            return np.nan
        return value

    return series.apply(to_missing)


def _normalize_number(val: str) -> str:
    """去除数字串中的常见分隔符（空格、横杠、点号、加号）"""
    return re.sub(r'[\s\-.\+]+', '', str(val))


def infer_column_type(
    series: pd.Series,
    user_override: Optional[ColumnType] = None
) -> dict:
    """
    智能推断列类型。

    计划书 v6.0 第七项 7.3 - 检测优先级（从高到低）：
        1. 用户手动指定（如存在则直接使用）
        2. 模式匹配（手机号正则 > 邮箱正则 > 身份证正则）
        3. 数值转换探测（pd.to_numeric，结合列名语义）
        4. 日期转换探测（pd.to_datetime，errors='coerce'）
        5. 兜底为文本类型

    🔴 关键修正：
        - 仅返回类型信息，不修改原始数据（不再返回 converted_series）
        - 日期探测前必须先初始化 date_ratio = 0.0
        - 正则匹配必须优先于数值尝试

    参数:
        series: 原始列数据（应已通过 normalize_missing_placeholders 预处理）
        user_override: 用户手动指定的类型（None 表示由系统推断）

    返回:
        dict: {
            'type': ColumnType,
            'confidence': float,        # 可信度 0-1
            'failed_count': int,        # 无法匹配推断类型的值数量
            'failed_samples': list,     # 失败值样本（最多 5 个）
            'warning': Optional[str]    # 警告信息
        }
    """
    # 如果用户指定了类型，直接返回
    if user_override is not None:
        return {
            'type': user_override,
            'confidence': 1.0,
            'failed_count': 0,
            'failed_samples': [],
            'warning': '用户手动指定的类型'
        }

    # 获取非空样本
    valid_mask = ~series.isna()
    valid_values = series[valid_mask]

    if len(valid_values) == 0:
        return {
            'type': ColumnType.UNKNOWN,
            'confidence': 0.0,
            'failed_count': 0,
            'failed_samples': [],
            'warning': '该列无有效数据'
        }

    # ---------- 第 2 层：正则模式匹配（优先于数值/日期转换）----------
    # 计划书 v6.0 核心约束：正则匹配必须优先于数值尝试

    # 2.1 检测手机号格式
    normalized_for_phone = valid_values.astype(str).apply(_normalize_number)
    phone_matches = normalized_for_phone.apply(lambda x: bool(PHONE_PATTERN.match(x)))
    phone_ratio = phone_matches.sum() / len(valid_values)
    if phone_ratio >= 0.8:
        return {
            'type': ColumnType.PHONE,
            'confidence': phone_ratio,
            'failed_count': len(valid_values) - phone_matches.sum(),
            'failed_samples': valid_values[~phone_matches].head(5).tolist(),
            'warning': None
        }

    # 2.2 检测邮箱格式
    email_matches = valid_values.astype(str).apply(lambda x: bool(EMAIL_PATTERN.match(x.strip())))
    email_ratio = email_matches.sum() / len(valid_values)
    if email_ratio >= 0.8:
        return {
            'type': ColumnType.EMAIL,
            'confidence': email_ratio,
            'failed_count': len(valid_values) - email_matches.sum(),
            'failed_samples': valid_values[~email_matches].head(5).tolist(),
            'warning': None
        }

    # 2.3 检测身份证号格式
    id_matches = valid_values.astype(str).apply(
        lambda x: bool(ID_PATTERN.match(x.strip().upper()))
    )
    id_ratio = id_matches.sum() / len(valid_values)
    if id_ratio >= 0.8:
        return {
            'type': ColumnType.ID,
            'confidence': id_ratio,
            'failed_count': len(valid_values) - id_matches.sum(),
            'failed_samples': valid_values[~id_matches].head(5).tolist(),
            'warning': None
        }

    # ---------- 第 3 层：数值转换探测 ----------
    numeric_converted = pd.to_numeric(valid_values, errors='coerce')
    numeric_ratio = numeric_converted.notna().sum() / len(valid_values)

    if numeric_ratio >= 0.8:
        col_name_lower = str(series.name).lower()

        # 列名暗示可能是 ID / 电话？降低置信度但不强制改类型
        likely_id_phone_name = any(kw in col_name_lower for kw in [
            'phone', 'mobile', 'tel', '电话', '手机',
            'id', 'no', 'number', '编号', '号码',
            'card', '证件', '账号', 'account'
        ])

        if likely_id_phone_name:
            return {
                'type': ColumnType.NUMERIC,
                'confidence': numeric_ratio * 0.8,
                'failed_count': len(valid_values) - numeric_converted.notna().sum(),
                'failed_samples': valid_values[numeric_converted.isna()].head(5).tolist(),
                'warning': '列名暗示可能为 ID/电话，保留为数值类型。如需按文本处理，请手动修改。'
            }

        return {
            'type': ColumnType.NUMERIC,
            'confidence': numeric_ratio,
            'failed_count': len(valid_values) - numeric_converted.notna().sum(),
            'failed_samples': valid_values[numeric_converted.isna()].head(5).tolist(),
            'warning': None
        }

    # ---------- 第 4 层：日期转换探测 ----------
    # 🔴 关键修正：date_ratio 必须在 try 块外预初始化为 0.0
    date_ratio = 0.0
    date_failed_samples = []

    try:
        # format='mixed' 让 pandas 自动推断每行的日期格式（pandas >= 2.0）
        # errors='coerce' 确保无效值返回 NaT 而非抛异常
        date_converted = pd.to_datetime(
            valid_values,
            format='mixed',
            errors='coerce'    # 计划书 v5.0 修正：必须添加此参数
        )
        date_ratio = date_converted.notna().sum() / len(valid_values)

        if date_ratio >= 0.8:
            return {
                'type': ColumnType.DATE,
                'confidence': date_ratio,
                'failed_count': len(valid_values) - date_converted.notna().sum(),
                'failed_samples': valid_values[date_converted.isna()].head(5).tolist(),
                'warning': None
            }
    except Exception:
        # 日期转换完全失败（如 pandas 版本过旧），继续到下一步
        pass

    # ---------- 第 5 层：兜底为文本类型 ----------
    return {
        'type': ColumnType.TEXT,
        'confidence': 1.0 - max(numeric_ratio, date_ratio),
        'failed_count': 0,
        'failed_samples': [],
        'warning': None
    }
