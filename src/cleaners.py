# src/cleaners.py
# 计划书 v6.0 第七项 7.5 - 清洗逻辑模块（Week 2-3 完整实现）

"""
数据清洗逻辑模块。

提供 clean_data_pipeline() 及各类清洗函数。

重要：
- 本模块为纯函数，不依赖 streamlit，确保可单元测试
- @st.cache_data 装饰器不放在此模块中（统一在 app.py 中包装）
- 类型推断和类型转换是两个独立步骤（参考计划书 v6.0 修正）

清洗流水线（7 步）：
    1. 缺失占位符标准化（文字占位符 → NaN）
    2. 列类型推断（仅返回类型信息，不修改数据）
    3. 按推断的类型进行数据转换（日期字符串 → datetime 等）
    4. 重复行处理
    5. 缺失值填充（按列类型选择策略）
    6. 异常值处理（仅数值列）
    7. 格式标准化（去除空格、手机号标准化等）
"""

import numpy as np
import pandas as pd
from typing import Optional

from .type_inference import infer_column_type, normalize_missing_placeholders, ColumnType


def clean_data_pipeline(
    df: pd.DataFrame,
    config: dict,
    user_overrides: Optional[dict] = None
) -> tuple[pd.DataFrame, dict]:
    """
    完整的数据清洗流程（纯净函数，可单元测试）。

    计划书 v6.0 第七项 7.5

    参数:
        df: 原始 DataFrame
        config: 清洗配置字典
        user_overrides: 用户对列类型的覆盖，格式 {列名: ColumnType}

    返回:
        (清洗后DataFrame, 清洗日志dict)
    """
    if user_overrides is None:
        user_overrides = {}

    df_working = df.copy()
    log = {
        'original_rows': len(df),
        'original_cols': len(df.columns),
        'steps': []
    }

    # ---- 步骤 1: 缺失占位符标准化 ----
    placeholder_stats = {}
    for col in df_working.columns:
        original_null = df_working[col].isna().sum()
        df_working[col] = normalize_missing_placeholders(df_working[col])
        new_null = df_working[col].isna().sum()
        if new_null > original_null:
            placeholder_stats[col] = new_null - original_null

    log['steps'].append({
        'name': '缺失占位符标准化',
        'details': f"识别到 {sum(placeholder_stats.values())} 个文本占位符被转为空值",
        'by_column': placeholder_stats
    })

    # ---- 步骤 2: 列类型推断（仅推断，不修改数据）----
    type_results = {}
    for col in df_working.columns:
        user_override = user_overrides.get(col)
        result = infer_column_type(df_working[col], user_override)
        type_results[col] = result

    log['steps'].append({
        'name': '列类型推断',
        'details': '类型推断完成（未修改数据）',
        'results': {col: {
            'type': r['type'].value,
            'confidence': round(r['confidence'], 2)
        } for col, r in type_results.items()}
    })

    # ---- 步骤 3: 按推断的类型进行数据转换 ----
    converted_cols = 0
    for col in df_working.columns:
        col_type = type_results[col]['type']
        if col_type == ColumnType.DATE:
            before = df_working[col].isna().sum()
            df_working[col] = pd.to_datetime(df_working[col], format='mixed', errors='coerce')
            after = df_working[col].isna().sum()
            if after > before:
                converted_cols += 1
        elif col_type == ColumnType.NUMERIC:
            # 强制将推断为NUMERIC的列转为数值类型，处理字符串数值列（如'25', '5000'）被误存为object的情况
            if not pd.api.types.is_numeric_dtype(df_working[col]):
                df_working[col] = pd.to_numeric(df_working[col], errors='coerce')

    log['steps'].append({
        'name': '类型转换',
        'details': f'日期和数值列已转换' + (f'，{converted_cols} 列含无法解析的值（已转为空）' if converted_cols > 0 else ''),
        'converted_cols': converted_cols
    })

    # ---- 步骤 4: 重复行处理 ----
    duplicate_count = 0
    if config.get('remove_duplicates', True):
        before = len(df_working)
        df_working = df_working.drop_duplicates(keep='first')
        duplicate_count = before - len(df_working)

    log['steps'].append({
        'name': '重复行处理',
        'details': f"删除 {duplicate_count} 行重复数据",
        'removed': duplicate_count
    })

    # ---- 步骤 5: 缺失值填充 ----
    fill_values = {}
    text_fill_value = config.get('text_fill_value', '')
    for col in df_working.columns:
        if df_working[col].isna().sum() == 0:
            continue

        col_type = type_results[col]['type']
        strategy = config.get('numeric_missing_strategy', 'auto')

        if col_type == ColumnType.NUMERIC:
            series, info = _fill_numeric_missing(df_working[col], strategy)
            df_working[col] = series
            fill_values[col] = info
        elif col_type in [ColumnType.TEXT, ColumnType.PHONE, ColumnType.EMAIL, ColumnType.ID, ColumnType.UNKNOWN]:
            # UNKNOWN 类型（如全NaN列无法推断）按文本列处理
            series, info = _fill_text_missing(df_working[col], text_fill_value)
            df_working[col] = series
            fill_values[col] = info
        elif col_type == ColumnType.DATE:
            df_working[col] = df_working[col].ffill()
            fill_values[col] = {
                'method': '前向填充',
                'value': '前一行日期',
                'count': int(df_working[col].isna().sum())
            }

    log['steps'].append({
        'name': '缺失值填充',
        'details': f"填充了 {len(fill_values)} 列的缺失值",
        'fill_values': fill_values
    })

    # ---- 步骤 6: 异常值处理 ----
    outlier_log = {}
    if config.get('handle_outliers', True):
        multiplier = config.get('outlier_multiplier', 1.5)
        for col in df_working.columns:
            if type_results[col]['type'] != ColumnType.NUMERIC:
                continue

            Q1 = df_working[col].quantile(0.25)
            Q3 = df_working[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR

            outlier_mask = (df_working[col] < lower) | (df_working[col] > upper)
            outlier_count = int(outlier_mask.sum())

            if outlier_count > 0:
                df_working[col] = df_working[col].clip(lower=lower, upper=upper)
                outlier_log[col] = outlier_count

    log['steps'].append({
        'name': '异常值处理',
        'details': f"处理了 {sum(outlier_log.values())} 个异常值",
        'by_column': outlier_log
    })

    # ---- 步骤 7: 格式标准化 ----
    import re as _re
    phone_normalized = 0
    for col in df_working.columns:
        col_type = type_results[col]['type']
        if col_type == ColumnType.TEXT:
            df_working[col] = df_working[col].astype(str).str.strip()
        elif col_type == ColumnType.PHONE:
            original = df_working[col].copy()
            df_working[col] = df_working[col].astype(str).apply(
                lambda x: _re.sub(r'[\s\-.\+\(\)（）]+', '', str(x))
            )
            # 去除国家代码前缀（与 validators.py 的 _normalize_phone 行为一致）
            df_working[col] = df_working[col].apply(
                lambda x: x[2:] if x.startswith('86') and len(x) > 11 else x
            )
            phone_normalized += int((original != df_working[col]).sum())

    detail = '文本列前后空格已去除'
    if phone_normalized > 0:
        detail += f'，{phone_normalized} 个手机号已标准化'

    log['steps'].append({
        'name': '格式标准化',
        'details': detail
    })

    # ---- 最终统计 ----
    log['final_rows'] = len(df_working)
    log['final_cols'] = len(df_working.columns)
    log['total_removed'] = log['original_rows'] - log['final_rows']

    return df_working, log


# ---------- 内部填充函数 ----------

def _fill_numeric_missing(series: pd.Series, method: str = 'auto') -> tuple[pd.Series, dict]:
    """填充数值列的缺失值"""
    missing_count = int(series.isna().sum())
    if missing_count == 0:
        return series, {}

    # 全为 NaN 时直接填 0，避免 mean/median 返回 NaN 导致 fillna(NaN) 无效
    if missing_count == len(series):
        return series.fillna(0.0), {
            'method': '全空填充为零',
            'value': 0.0,
            'count': missing_count
        }

    if method == 'no_fill':
        return series, {
            'method': '不填充',
            'value': 'N/A',
            'count': missing_count
        }

    if method == 'auto':
        skewness = series.skew()
        method = 'median' if abs(skewness) > 1 else 'mean'

    if method == 'mean':
        fill_value = series.mean()
        # 全 NaN 列 fallback：mean() 返回 NaN，此时无法填充，用 0.0 兜底
        if pd.isna(fill_value):
            fill_value = 0.0
    elif method == 'median':
        fill_value = series.median()
        if pd.isna(fill_value):
            fill_value = 0.0
    elif method == 'zero':
        fill_value = 0.0
    else:
        fill_value = series.mean()

    info = {
        'method': method,
        'value': round(float(fill_value), 4),
        'count': missing_count
    }

    result = series.fillna(fill_value)

    # 自动精度处理：均值/中位数填充可能产生过长小数，对用户不友好
    # 基于原始非空值判断列的精度级别，然后应用到整列
    result = _apply_numeric_precision(result, series)

    return result, info


def _apply_numeric_precision(result: pd.Series, original: pd.Series) -> pd.Series:
    """
    自动精度处理：均值/中位数填充可能产生过长小数，对"年龄""数量"等整数列不友好。

    基于原始非空值判断精度，然后应用到填充后的整列。

    规则：
        - 全 NaN 列跳过
        - 原始非空值全为整数 → result.round(0)
        - 否则计算原始数据最大小数位数（至少 2 位），统一四舍五入
    """
    clean_vals = original.dropna()
    if len(clean_vals) == 0:
        return result

    is_all_int = True
    max_decimals = 0
    for v in clean_vals:
        try:
            fv = float(v)
            if fv != int(fv):
                is_all_int = False
            dec_str = f"{fv:.10f}".rstrip('0').split('.')
            if len(dec_str) == 2:
                max_decimals = max(max_decimals, len(dec_str[1]))
        except (ValueError, TypeError):
            is_all_int = False

    if is_all_int:
        return result.round(0)
    else:
        decimals = max(2, min(max_decimals, 6))
        return result.round(decimals)


def _fill_text_missing(series: pd.Series, text_fill_value: str = '') -> tuple[pd.Series, dict]:
    """
    填充文本列的缺失值。

    计划书 v6.0 Week 2 修正：
        - text_fill_value 为空时使用众数
        - text_fill_value 非空时使用该固定值
    """
    missing_count = int(series.isna().sum())
    if missing_count == 0:
        return series, {}

    if text_fill_value:
        fill_value = text_fill_value
        method = '指定值'
    else:
        mode_vals = series.mode()
        fill_value = mode_vals[0] if len(mode_vals) > 0 else '未知'
        method = '众数'

    return series.fillna(fill_value), {
        'method': method,
        'value': str(fill_value),
        'count': missing_count
    }
