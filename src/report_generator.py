# src/report_generator.py
# 计划书 v6.0 第七项 7.6 - HTML 清洗报告生成（Week 3 完整实现）

"""
清洗报告生成模块。

生成 HTML 格式的清洗报告，包含：
- 数据变化摘要（行数、列数、缺失单元格数变化）
- 各步骤详细结果
- 列类型识别结果（含可信度和转换损失）
- 缺失值填充详情（文本类填充值脱敏展示）
- 警告与建议（高缺失率列、低置信度类型推断等）

重要：
- 本模块不依赖 streamlit，保持纯函数可测试
"""

import html
from datetime import datetime


def generate_cleaning_report(
    df_original,
    df_cleaned,
    cleaning_log: dict,
    type_results: dict = None,
) -> str:
    """
    生成 HTML 清洗报告。

    计划书 v6.0 第十一项 §11.5 任务2

    参数:
        df_original: 原始 DataFrame
        df_cleaned: 清洗后 DataFrame
        cleaning_log: clean_data_pipeline() 返回的日志
        type_results: 列类型推断结果（{列名: infer_column_type() 返回值}）

    返回:
        HTML 字符串
    """
    report_parts = []
    if type_results is None:
        type_results = {}

    # ---- 页头 ----
    report_parts.append(f"""
    <div class="report-header" style="margin-bottom: 20px;">
        <h2>📊 数据清洗报告</h2>
        <p style="color: #666;">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """)

    # ---- 数据变化摘要 ----
    original_missing = int(df_original.isna().sum().sum())
    cleaned_missing = int(df_cleaned.isna().sum().sum())
    missing_change = original_missing - cleaned_missing

    report_parts.append(f"""
    <div class="report-section" style="margin-bottom: 25px;">
        <h3>📋 数据变化摘要</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; text-align: left;">指标</th>
                <th style="padding: 8px; text-align: right;">清洗前</th>
                <th style="padding: 8px; text-align: right;">清洗后</th>
                <th style="padding: 8px; text-align: right;">变化</th>
            </tr>
            <tr>
                <td style="padding: 8px;">行数</td>
                <td style="padding: 8px; text-align: right;">{cleaning_log.get('original_rows', '?')}</td>
                <td style="padding: 8px; text-align: right;">{cleaning_log.get('final_rows', '?')}</td>
                <td style="padding: 8px; text-align: right;">{_format_change(cleaning_log.get('total_removed', 0), '行')}</td>
            </tr>
            <tr>
                <td style="padding: 8px;">缺失单元格数</td>
                <td style="padding: 8px; text-align: right;">{original_missing}</td>
                <td style="padding: 8px; text-align: right;">{cleaned_missing}</td>
                <td style="padding: 8px; text-align: right;">{_format_improvement(missing_change)}</td>
            </tr>
            <tr>
                <td style="padding: 8px;">列数</td>
                <td style="padding: 8px; text-align: right;">{cleaning_log.get('original_cols', '?')}</td>
                <td style="padding: 8px; text-align: right;">{cleaning_log.get('final_cols', cleaning_log.get('original_cols', '?'))}</td>
                <td style="padding: 8px; text-align: right;">不变</td>
            </tr>
        </table>
    </div>
    """)

    # ---- 清洗步骤详情 ----
    report_parts.append('<div class="report-section" style="margin-bottom: 25px;"><h3>🔍 清洗步骤详情</h3>')

    for step in cleaning_log.get('steps', []):
        report_parts.append(f"""
        <div style="background-color: #f9f9f9; padding: 12px; margin-bottom: 10px; border-radius: 5px;">
            <h4 style="margin-top: 0;">✅ {html.escape(str(step.get('name', '')))}</h4>
            <p>{html.escape(str(step.get('details', '')))}</p>
        """)

        if 'by_column' in step and step['by_column']:
            report_parts.append('<ul>')
            for col, count in step['by_column'].items():
                report_parts.append(f'<li><strong>{html.escape(str(col))}</strong>: {count} 处</li>')
            report_parts.append('</ul>')

        if 'removed' in step:
            report_parts.append(f'<p>共删除：<strong>{step["removed"]}</strong> 行</p>')

        report_parts.append('</div>')

    report_parts.append('</div>')

    # ---- 缺失值填充详情 ----
    fill_values = None
    for step in cleaning_log.get('steps', []):
        if step.get('name') == '缺失值填充' and step.get('fill_values'):
            fill_values = step['fill_values']
            break

    if fill_values:
        report_parts.append("""
        <div class="report-section" style="margin-bottom: 25px;">
            <h3>🔧 缺失值填充详情</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; text-align: left;">列名</th>
                    <th style="padding: 8px; text-align: left;">填充方法</th>
                    <th style="padding: 8px; text-align: left;">填充值</th>
                    <th style="padding: 8px; text-align: right;">填充数量</th>
                </tr>
        """)

        for col_name, info in fill_values.items():
            display_value = _safe_display_value(info.get('value', ''), info.get('method', ''))
            report_parts.append(f"""
                <tr>
                    <td style="padding: 8px;"><strong>{html.escape(str(col_name))}</strong></td>
                    <td style="padding: 8px;">{html.escape(str(info.get('method', '')))}</td>
                    <td style="padding: 8px;">{display_value}</td>
                    <td style="padding: 8px; text-align: right;">{info.get('count', 0)}</td>
                </tr>
            """)

        report_parts.append('</table></div>')

    # ---- 列类型识别结果 ----
    if type_results:
        report_parts.append("""
        <div class="report-section" style="margin-bottom: 25px;">
            <h3>🏷️ 列类型识别结果</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; text-align: left;">列名</th>
                    <th style="padding: 8px; text-align: left;">识别类型</th>
                    <th style="padding: 8px; text-align: right;">可信度</th>
                    <th style="padding: 8px; text-align: left;">备注</th>
                </tr>
        """)

        for col_name, result in type_results.items():
            if isinstance(result, dict):
                type_name = result.get('type', type_results[col_name].get('type'))
                if hasattr(type_name, 'value'):
                    type_name = type_name.value
                confidence = result.get('confidence', 0)
                failed = result.get('failed_count', 0)
                lost = f"{failed} 个值失败" if failed > 0 else "—"
                confidence_class = "color: green;" if confidence >= 0.9 else ("color: orange;" if confidence >= 0.8 else "color: red;")
                report_parts.append(f"""
                    <tr>
                        <td style="padding: 8px;"><strong>{html.escape(str(col_name))}</strong></td>
                        <td style="padding: 8px;">{type_name}</td>
                        <td style="padding: 8px; text-align: right; {confidence_class}">{confidence:.0%}</td>
                        <td style="padding: 8px;">{lost}</td>
                    </tr>
                """)
            elif hasattr(type_results[col_name], 'get'):
                type_name = type_results[col_name].get('type', '?')
                confidence = type_results[col_name].get('confidence', 0)
        report_parts.append('</table></div>')

    # ---- 警告与建议 ----
    warnings = []

    # 1. 高缺失率列
    for step in cleaning_log.get('steps', []):
        if step.get('name') == '缺失值填充' and step.get('fill_values'):
            for col, info in step['fill_values'].items():
                col_total = cleaning_log.get('final_rows', 0)
                if col_total > 0 and info.get('count', 0) / col_total > 0.5:
                    warnings.append(
                        f'<li>⚠️ <strong>{html.escape(str(col))}</strong>：缺失率超过 50%'
                        f'（{info["count"]} 处），建议检查原始数据是否完整</li>'
                    )

    # 2. 类型推断低置信度
    if type_results:
        for col_name, result in type_results.items():
            if isinstance(result, dict):
                conf = result.get('confidence', 1.0)
                if conf < 0.8:
                    type_name = result.get('type', '?')
                    if hasattr(type_name, 'value'):
                        type_name = type_name.value
                    warnings.append(
                        f'<li>🔍 <strong>{html.escape(str(col_name))}</strong>：类型推断置信度较低'
                        f'（{conf:.0%}，推断为 {type_name}），建议手动确认</li>'
                    )

    # 3. 类型推断中的警告信息
    if type_results:
        for col_name, result in type_results.items():
            if isinstance(result, dict) and result.get('warning'):
                warnings.append(f'<li>💡 <strong>{html.escape(str(col_name))}</strong>：{html.escape(str(result["warning"]))}</li>')

    # 4. 电话号码列的提醒
    if type_results:
        for col_name, result in type_results.items():
            if isinstance(result, dict) and result.get('type'):
                type_val = result['type'].value if hasattr(result['type'], 'value') else str(result['type'])
                if type_val == 'phone':
                    warnings.append(
                        f'<li>📱 <strong>{html.escape(str(col_name))}</strong>：已被识别为电话号码列，'
                        '未进行数值计算或均值填充</li>'
                    )

    if warnings:
        report_parts.append("""
        <div class="report-section" style="margin-bottom: 25px; background-color: #fff9c4; padding: 15px; border-radius: 5px;">
            <h3>⚠️ 警告与建议</h3>
            <ul style="line-height: 1.8;">
        """)
        for w in warnings:
            report_parts.append(w)
        report_parts.append('</ul></div>')

    return '\n'.join(report_parts)


# ---------- 内部辅助 ----------

def _format_change(count: int, unit: str) -> str:
    """格式化增减显示"""
    if count > 0:
        return f'<span style="color: red;">-{count} {unit}</span>'
    return '<span style="color: green;">不变</span>'


def _format_improvement(change: int) -> str:
    """格式化改善显示（正数表示改善了）"""
    if change > 0:
        return f'<span style="color: green;">已修复 {change} 个</span>'
    elif change < 0:
        return f'<span style="color: orange;">新增 {abs(change)} 个</span>'
    return '<span style="color: green;">不变</span>'


def _safe_display_value(value, method: str = '') -> str:
    """
    安全展示填充值。

    计划书 Week 3 任务2：
        - 文本众数：长度 >20 时截断为前 10 字符 + "..."
        - 自定义固定值：直接展示
        - 数值：正常展示
    """
    val_str = str(value)

    # 数值型填充值（mean/median/zero）：正常展示
    if method in ('mean', 'median', 'auto', 'zero'):
        try:
            float_val = float(value)
            return f'<code>{float_val:.4f}</code>'
        except (ValueError, TypeError):
            pass

    # 文本众数：脱敏展示
    if method in ('众数', 'mode'):
        if len(val_str) > 20:
            return f'<code>{val_str[:10]}…（{len(val_str)}字符）</code>'
        elif len(val_str) > 5:
            return f'<code>{val_str[:2]}***</code>'
        return '<code>***</code>'

    # 指定值 / 前向填充 / 其他
    if len(val_str) > 50:
        return f'<code>{val_str[:20]}…（{len(val_str)}字符）</code>'
    return f'<code>{val_str}</code>'
