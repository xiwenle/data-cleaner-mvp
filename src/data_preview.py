# src/data_preview.py
# 计划书 v6.0 第七项 7.2 - 数据预览模块

"""
数据预览模块。

职责：
- 生成数据统计摘要（列名、数据类型、缺失数、缺失率、唯一值数）
- 为每列推断语义含义（供 UI 展示用，不影响清洗逻辑）

重要：
- 本模块不依赖 streamlit，保持纯函数可测试
"""

import pandas as pd

from .type_inference import infer_column_type, normalize_missing_placeholders


def generate_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成数据统计摘要。

    计划书 v6.0 第七项 7.2

    参数:
        df: 原始 DataFrame

    返回:
        统计摘要 DataFrame，包含列：
            - 列名
            - 推断类型（数值/文本/日期/手机/邮箱/ID）
            - 缺失数量
            - 缺失率 (%)
            - 唯一值数量
    """
    rows = []

    # 先对数据进行缺失占位符标准化（用于准确的缺失值统计）
    df_normalized = df.copy()
    for col in df_normalized.columns:
        df_normalized[col] = normalize_missing_placeholders(df_normalized[col])

    for col in df_normalized.columns:
        series = df_normalized[col]
        total = len(series)
        missing_count = int(series.isna().sum())
        missing_rate = round(missing_count / total * 100, 2) if total > 0 else 0.0
        unique_count = series.nunique(dropna=True)

        # 推断列类型（用于展示）
        type_result = infer_column_type(series)
        inferred_type = type_result['type'].value if type_result else 'unknown'

        rows.append({
            '列名': col,
            '推断类型': inferred_type,
            '缺失数量': missing_count,
            '缺失率 (%)': missing_rate,
            '唯一值数量': unique_count
        })

    summary_df = pd.DataFrame(rows)
    return summary_df


def get_data_overview(df: pd.DataFrame) -> dict:
    """
    获取数据全局概览。

    返回包含行数、列数、总体缺失率等信息的字典。
    与 generate_summary 保持一致的缺失值统计口径。
    """
    # 先做占位符标准化，保持与 generate_summary 一致
    df_norm = df.copy()
    for col in df_norm.columns:
        df_norm[col] = normalize_missing_placeholders(df_norm[col])

    total_cells = df_norm.shape[0] * df_norm.shape[1]
    total_missing = int(df_norm.isna().sum().sum())
    overall_missing_rate = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0

    return {
        '行数': df.shape[0],
        '列数': df.shape[1],
        '总体数据量': total_cells,
        '缺失值总数': total_missing,
        '总体缺失率 (%)': overall_missing_rate
    }
