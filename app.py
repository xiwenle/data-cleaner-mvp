# app.py
# 计划书 v6.0 - Week 4 最终版
# 数据清洗工具 Data Cleaner MVP

"""
Streamlit 主应用（本地版）。

功能：
    - 数据处理说明
    - 文件上传（CSV/Excel，≤50MB），Excel 多 Sheet 支持
    - 数据预览（统计摘要 + 前 20 行）
    - 敏感列检测（温和提示，不阻断）
    - 侧边栏清洗配置（去重 + 填充策略 + 异常值 + 文本填充值）
    - 侧边栏列类型手动覆盖
    - P0 验证结果展示（缺失值、重复行）
    - P1 验证结果展示（邮箱/手机号格式、IQR异常值）
    - 一键清洗 + 清洗结果下载
    - HTML 清洗报告展示（可折叠）
    - Session State 管理（新文件 / 切换 Sheet 时正确处理）
    - macOS 风格 UI（克制的配色、圆角、充足留白）
    - 全中文界面

重要：
    所有 @st.cache_data 装饰器只在本文件中使用，
    src/ 目录下的模块保持为不依赖 streamlit 的纯函数。
"""

import io
import json
import traceback

import streamlit as st
import pandas as pd

from src.config import HIGH_RISK_PATTERNS, MEDIUM_RISK_PATTERNS
from src.file_handler import load_data, validate_file, get_sheet_names
from src.data_preview import generate_summary, get_data_overview
from src.validators import (
    check_missing, check_duplicates,
    check_email_format, check_phone_format, check_numeric_outliers_iqr
)
from src.type_inference import infer_column_type, ColumnType
from src.report_generator import generate_cleaning_report


# ---------- 缓存函数（必须在所有调用点之前定义）----------
# 计划书 v6.0 第五节 5.6 — 缓存函数放在 app.py
@st.cache_data(ttl=3600, show_spinner="正在清洗数据...")
def cached_cleaning(
    file_bytes: bytes,
    config_json: str,
    user_overrides_json: str,
    sheet_name: "str | None" = None,
    file_name: str = ""
) -> tuple:
    """带缓存的清洗函数。所有参数均为可哈希类型。"""
    from src.cleaners import clean_data_pipeline
    from src.file_handler import load_data_bytes
    from src.type_inference import ColumnType as CT

    config = json.loads(config_json)
    user_overrides_dict = json.loads(user_overrides_json)
    user_overrides = {k: CT(v) for k, v in user_overrides_dict.items()}

    df = load_data_bytes(file_bytes, sheet_name=sheet_name, file_name=file_name)
    return clean_data_pipeline(df, config, user_overrides=user_overrides)


# ---------- macOS 风格 CSS 注入 ----------
st.markdown("""
<style>
    /* 全局字体与基调 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
        color: #1d1d1f;
    }
    /* 主标题 */
    .main-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 0.25rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e5e5e5;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
    /* 卡片容器 */
    .card-container {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #fafafa;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    /* 圆角输入框 */
    [data-testid="stFileUploader"] section {
        border-radius: 8px !important;
    }
    /* 隐藏 Streamlit 自带的菜单 / Deploy 等英文按钮 */
    [data-testid="stHeader"] {
        display: none;
    }
    [data-testid="stToolbar"] {
        display: none;
    }
    /* 隐藏页脚的 "Made with Streamlit" */
    .stApp footer {
        display: none;
    }
    /* 消除隐藏菜单后顶部的空白间距 */
    .stApp {
        margin-top: -30px;
    }
    /* 替换文件上传组件英文文本为中文（只替换 small 提示文字，不动按钮） */
    [data-testid="stFileUploader"] small {
        visibility: hidden;
    }
    [data-testid="stFileUploader"] small::after {
        content: "支持 .csv、.xlsx、.xls 格式，最大 50MB，不超过 10 万行";
        visibility: visible;
        display: block;
        font-size: 0.875rem;
        color: #888;
    }
    /* 按钮 */
    button[kind="primary"] {
        border-radius: 8px !important;
    }
    /* 侧边栏 */
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem;
        font-weight: 600;
    }
    /* 分割线 */
    hr {
        border-color: #e5e5e5;
    }
</style>
""", unsafe_allow_html=True)

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="数据清洗工具",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# macOS 风格标题
st.markdown('<div class="main-title">🧹 数据清洗工具</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">面向中小企业的轻量级数据验证与清洗工具 · '
    '所有处理在服务器内存中完成，不留痕迹</div>',
    unsafe_allow_html=True
)

# ---------- 隐私提示（上传组件之前）----------
st.info("""
🔒 **数据处理说明**

您正在本地运行本工具，所有数据处理均在本机内存中完成，不会上传到任何服务器。
- 数据不会被保存、分享或传输到任何第三方
- 关闭程序后所有数据自动清除

使用本工具前，请确认您遵守所在地区的数据合规要求，自行对数据处理的合法性负责。
""")

# ---------- Session State 初始化 ----------
# 所有 key 在此统一初始化，确保在组件创建之前完成
# 注意：初始化必须在侧边栏/组件创建之前，否则 Streamlit 会报
# "cannot be modified after the widget is instantiated"

# 数据与状态 key
for key, default in [
    ('current_file_name', None),
    ('file_bytes', None),
    ('df_original', None),
    ('df_cleaned', None),
    ('cleaning_log', None),
    ('validation_results', None),
    ('user_type_overrides', {}),
    ('prev_selected_sheet', None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# 侧边栏配置组件 key（必须在组件创建前初始化默认值）
if 'config_remove_duplicates' not in st.session_state:
    st.session_state.config_remove_duplicates = True
if 'config_numeric_strategy_label' not in st.session_state:
    st.session_state.config_numeric_strategy_label = "自动选择（偏度>1用中位数）"
if 'config_text_fill_value' not in st.session_state:
    st.session_state.config_text_fill_value = ''
if 'config_handle_outliers' not in st.session_state:
    st.session_state.config_handle_outliers = True
if 'config_outlier_multiplier' not in st.session_state:
    st.session_state.config_outlier_multiplier = 1.5

# ---------- 侧边栏：清洗配置 ----------
with st.sidebar:
    st.markdown("#### 📊 清洗配置")
    st.caption("调整清洗策略，配置变更后需点击清洗按钮方可生效")

    st.checkbox(
        "删除完全重复的行",
        value=st.session_state.config_remove_duplicates,
        key='config_remove_duplicates',
        help="检测到完全相同的行时，保留第一行并删除后续重复行"
    )

    st.divider()

    numeric_strategy_map = {
        "自动选择（偏度>1用中位数）": "auto",
        "均值": "mean",
        "中位数": "median",
        "填零": "zero",
        "不填充": "no_fill"
    }
    current_label = st.session_state.config_numeric_strategy_label
    st.selectbox(
        "数值列缺失值填充策略",
        options=list(numeric_strategy_map.keys()),
        index=list(numeric_strategy_map.keys()).index(current_label) if current_label in numeric_strategy_map else 0,
        key='config_numeric_strategy_label',
        help="auto：|偏度|>1 用中位数，否则用均值"
    )
    config_numeric_strategy = numeric_strategy_map[st.session_state.config_numeric_strategy_label]

    st.text_input(
        "文本列填充值（留空 = 用众数）",
        value=st.session_state.config_text_fill_value,
        key='config_text_fill_value',
        help="留空则自动使用该列中出现最多的值填充；填入特定值则统一使用该值"
    )

    st.divider()

    st.checkbox(
        "检测并调整数值异常值",
        value=st.session_state.config_handle_outliers,
        key='config_handle_outliers',
        help="使用 IQR 方法检测异常值，超出边界的值会被裁剪到边界"
    )

    if st.session_state.config_handle_outliers:
        st.number_input(
            "IQR 倍数",
            min_value=1.0,
            max_value=3.0,
            value=float(st.session_state.config_outlier_multiplier),
            step=0.1,
            key='config_outlier_multiplier',
            help="1.0 = 严格（更多异常值），3.0 = 宽松（更少异常值）"
        )
    else:
        config_outlier_multiplier = 1.5

    st.divider()

    # ---- 列类型手动覆盖（Week 4 修复 audit 问题2）----
    # 计划书 v6.0 第十二项 - 侧边栏类型覆盖
    st.markdown("#### 🏷️ 列类型覆盖（可选）")
    st.caption("若自动推断的类型不准确，可在下方手动指定")

    if st.session_state.df_original is not None:
        df_for_override = st.session_state.df_original
        # 自动推断每列类型
        for col in df_for_override.columns:
            result = infer_column_type(df_for_override[col])
            current_type = result['type'].value
            confidence = result['confidence']

            type_options = ['auto'] + [t.value for t in ColumnType]

            override_key = f"type_override_{col}"
            if override_key not in st.session_state:
                st.session_state[override_key] = 'auto'

            selected = st.selectbox(
                f"{col}",
                options=type_options,
                index=type_options.index(st.session_state[override_key]),
                key=override_key,
                help=f"自动推断：{current_type}（可信度 {confidence:.0%}）"
            )

            if selected != 'auto':
                st.session_state.user_type_overrides[col] = ColumnType(selected)
            elif col in st.session_state.user_type_overrides:
                del st.session_state.user_type_overrides[col]

# ---------- 文件上传 ----------
st.subheader("📤 上传数据文件")

uploaded_file = st.file_uploader(
    "点击或拖拽 CSV / Excel 文件到此处",
    type=['csv', 'xlsx', 'xls'],
    help="支持 CSV（UTF-8/GBK 编码）和 Excel（.xlsx/.xls），文件 ≤50MB，数据 ≤10 万行"
)
st.caption("支持 .csv、.xlsx、.xls 格式，单个文件最大 50MB，不超过 10 万行。")

if uploaded_file is not None:
    # ---- 验证文件 ----
    is_valid, error_msg = validate_file(uploaded_file)
    if not is_valid:
        st.error(error_msg)
        st.stop()

    # ---- 检测是否为新文件 ----
    is_new_file = (st.session_state.current_file_name != uploaded_file.name)

    if is_new_file:
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.file_bytes = uploaded_file.getvalue()

        # 数据状态
        st.session_state.df_original = None
        st.session_state.df_cleaned = None
        st.session_state.cleaning_log = None
        st.session_state.validation_results = None

        # 用户类型覆盖
        st.session_state.user_type_overrides = {}

        # 清除 selectbox key（type_override_ 开头）
        for key in list(st.session_state.keys()):
            if key.startswith('type_override_'):
                del st.session_state[key]

        # 清除缓存
        st.cache_data.clear()

        # 注意：不重置侧边栏配置组件的值（Streamlit 不允许在组件创建后修改 widget key）。
        # 用户上传新文件时保留之前的配置设置，如需恢复默认配置请刷新页面。

    # ---- Excel 多 Sheet 处理 + 加载数据 ----
    file_ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ''

    if file_ext in ('xlsx', 'xls'):
        sheets = get_sheet_names(st.session_state.file_bytes)
        if len(sheets) > 1:
            selected_sheet = st.selectbox(
                "📑 检测到多个 Sheet，请选择要处理的 Sheet：",
                options=sheets,
                key='selected_sheet'
            )
        else:
            selected_sheet = sheets[0] if sheets else 0
            if 'selected_sheet' in st.session_state:
                st.session_state.selected_sheet = selected_sheet
    else:
        selected_sheet = None

    sheet_changed = False
    if file_ext in ('xlsx', 'xls'):
        current_sheet = st.session_state.get('selected_sheet', None)
        if (st.session_state.prev_selected_sheet is not None
                and current_sheet is not None
                and st.session_state.prev_selected_sheet != current_sheet):
            sheet_changed = True
        st.session_state.prev_selected_sheet = current_sheet

    if sheet_changed:
        st.session_state.df_original = None
        st.session_state.df_cleaned = None
        st.session_state.cleaning_log = None
        st.session_state.validation_results = None
        st.cache_data.clear()

    # ---- 加载数据 ----
    if st.session_state.df_original is None:
        try:
            with st.spinner("正在读取文件..."):
                with io.BytesIO(st.session_state.file_bytes) as file_obj:
                    df = load_data(
                        file_obj,
                        sheet_name=(
                            st.session_state.get('selected_sheet')
                            if file_ext in ('xlsx', 'xls') else None
                        ),
                        file_name=uploaded_file.name
                    )
                st.session_state.df_original = df
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}\n\n请确认文件为 CSV 或 Excel 格式，推荐使用 UTF-8 编码，也支持 GBK。")
            st.stop()

    df = st.session_state.df_original
    st.success(f"成功读取 {len(df)} 行 × {len(df.columns)} 列")

    # ---- 敏感数据分级检测 ----
    high_risk_cols = []
    medium_risk_cols = []

    for col in df.columns:
        col_lower = str(col).lower().strip()
        for lang_patterns in [HIGH_RISK_PATTERNS['chinese'], HIGH_RISK_PATTERNS['english']]:
            if any(pattern in col_lower for pattern in lang_patterns):
                high_risk_cols.append(col)
                break
        for lang_patterns in [MEDIUM_RISK_PATTERNS['chinese'], MEDIUM_RISK_PATTERNS['english']]:
            if any(pattern in col_lower for pattern in lang_patterns):
                medium_risk_cols.append(col)
                break

    if high_risk_cols:
        st.info(f"""
        📋 **检测到以下敏感列：** {', '.join(f'`{c}`' for c in high_risk_cols)}

        请确认您有权处理这些数据。本工具在本地运行，所有数据仅在本机内存中处理，不会外传。
        """)

    if medium_risk_cols:
        st.warning(f"""
        ⚠️ **检测到以下可能包含个人信息的列：** {', '.join(f'`{c}`' for c in medium_risk_cols)}

        本工具在本地运行，所有数据仅在本机内存中处理。请确认您有权处理这些数据。
        """)

        consent_given = st.checkbox(
            "我确认有权处理这些数据",
            value=False,
            key='sensitive_consent'
        )

        if not consent_given:
            st.info("请勾选确认以继续。")
            st.stop()

    # ---- 数据预览 ----
    st.divider()
    st.subheader("📊 数据预览")
    st.caption(f"前 20 行数据 · 共 {len(df)} 行 × {len(df.columns)} 列")

    with st.container():
        st.dataframe(df.head(20), width='stretch')

    # ---- 统计摘要 ----
    st.divider()
    st.subheader("📋 数据统计摘要")

    try:
        overview = get_data_overview(df)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("行数", overview['行数'])
        with col2:
            st.metric("列数", overview['列数'])
        with col3:
            st.metric("总体缺失率", f"{overview['总体缺失率 (%)']}%")

        summary_df = generate_summary(df)
        st.dataframe(summary_df, width='stretch')
    except Exception as e:
        st.warning(f"统计摘要生成时出现问题：{e}")

    # ---- P0 验证结果展示 ----
    st.divider()
    st.subheader("🔍 数据质量检测")

    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("**缺失值检测**")
        missing_results = check_missing(df)
        if missing_results:
            for col_name, info in missing_results.items():
                st.warning(f"**{col_name}**：{info['count']} 个缺失 ({info['rate']}%)")
        else:
            st.success("未检测到缺失值")

    with col_v2:
        st.markdown("**重复行检测**")
        dup_results = check_duplicates(df)
        dup_count = dup_results.get('total_duplicates', 0)
        if dup_count > 0:
            dup_groups = dup_results.get('duplicate_groups', {})
            unique_dup_rows = len(set(dup_groups.get('all_duplicate_indices', [])))
            st.warning(f"检测到 **{unique_dup_rows}** 个重复行（共涉及 {dup_count} 个单元格）")
        else:
            st.success("未检测到重复行")

    # ---- P1 验证结果展示 ----
    with st.expander("🔬 详细检测（邮箱/手机号格式、异常值）", expanded=True):
        type_results_p1 = {}
        for col in df.columns:
            type_results_p1[col] = infer_column_type(df[col])

        has_p1_content = False

        email_cols = [c for c in df.columns if type_results_p1[c]['type'] == ColumnType.EMAIL]
        if email_cols:
            has_p1_content = True
            st.markdown("##### 📧 邮箱格式检测")
            for col in email_cols:
                result = check_email_format(df[col])
                if result['invalid_count'] > 0:
                    samples = result['invalid_values'][:5]
                    st.warning(
                        f"**{col}**：{result['invalid_count']} 个格式错误 "
                        f"（有效 {result['valid_count']}）\n错误示例：{', '.join(str(s) for s in samples)}"
                    )
                else:
                    st.success(f"**{col}**：全部 {result['valid_count']} 个格式正确")

        phone_cols = [c for c in df.columns if type_results_p1[c]['type'] == ColumnType.PHONE]
        if phone_cols:
            has_p1_content = True
            st.markdown("##### 📱 手机号格式检测")
            for col in phone_cols:
                result = check_phone_format(df[col])
                if result['invalid_count'] > 0:
                    samples = result['invalid_values'][:5]
                    st.warning(
                        f"**{col}**：{result['invalid_count']} 个格式错误 "
                        f"（有效 {result['valid_count']}）\n错误示例：{', '.join(str(s) for s in samples)}"
                    )
                else:
                    st.success(f"**{col}**：全部 {result['valid_count']} 个格式正确")

        outlier_multiplier = st.session_state.get('config_outlier_multiplier', 1.5)
        numeric_cols = [c for c in df.columns if type_results_p1[c]['type'] == ColumnType.NUMERIC]
        if numeric_cols:
            has_p1_content = True
            st.markdown(f"##### 📈 数值异常值检测（IQR × {outlier_multiplier}）")
            for col in numeric_cols:
                result = check_numeric_outliers_iqr(df[col], multiplier=outlier_multiplier)
                lb = result.get('lower_bound')
                ub = result.get('upper_bound')
                if lb is None or ub is None:
                    st.info(f"**{col}**：此列不适用异常值检测")
                    continue
                if result['outlier_count'] > 0:
                    positions = result['outlier_positions'][:20]
                    st.warning(
                        f"**{col}**：{result['outlier_count']} 个异常值 "
                        f"（下界 {lb:.2f}，上界 {ub:.2f}）\n"
                        f"异常位置：{positions}"
                    )
                else:
                    st.success(
                        f"**{col}**：未检测到异常值 "
                        f"（范围 [{lb:.2f}, {ub:.2f}]）"
                    )

        if not has_p1_content:
            st.info("当前数据中未检测到邮箱、手机号或数值类型列。")

    # ---- 一键清洗 ----
    st.divider()
    st.subheader("🧹 数据清洗")

    should_clean = st.button("一键清洗", type="primary", width='stretch')

    if should_clean:
        config = {
            'remove_duplicates': st.session_state.get('config_remove_duplicates', True),
            'numeric_missing_strategy': numeric_strategy_map.get(
                st.session_state.get('config_numeric_strategy_label', "自动选择（偏度>1用中位数）"),
                'auto'
            ),
            'text_fill_value': st.session_state.get('config_text_fill_value', ''),
            'handle_outliers': st.session_state.get('config_handle_outliers', True),
            'outlier_multiplier': st.session_state.get('config_outlier_multiplier', 1.5),
        }

        user_overrides = {
            k: v.value if hasattr(v, 'value') else str(v)
            for k, v in st.session_state.get('user_type_overrides', {}).items()
        }

        file_bytes = st.session_state.file_bytes
        sheet = st.session_state.get('selected_sheet') if file_ext in ('xlsx', 'xls') else None

        with st.spinner("🔄 正在清洗数据，请稍候…"):
            try:
                df_cleaned, log = cached_cleaning(
                    file_bytes,
                    json.dumps(config, sort_keys=True),
                    json.dumps(user_overrides, sort_keys=True),
                    sheet_name=sheet,
                    file_name=uploaded_file.name
                )
                st.session_state.df_cleaned = df_cleaned
                st.session_state.cleaning_log = log
                st.success(f"✅ 清洗完成！{log['original_rows']} 行 → {log.get('final_rows', log['original_rows'])} 行")
            except Exception as e:
                st.error("清洗过程中发生错误，请检查数据格式或调整侧边栏配置。")
                print(f"[清洗异常] {traceback.format_exc()}", flush=True)
                st.stop()

    # ---- 清洗报告 ----
    if st.session_state.df_cleaned is not None and st.session_state.cleaning_log is not None:
        df_cleaned = st.session_state.df_cleaned
        cleaning_log = st.session_state.cleaning_log

        st.divider()

        with st.expander("📋 查看清洗报告", expanded=True):
            type_results_for_report = {}
            for step in cleaning_log.get('steps', []):
                if step.get('name') == '列类型推断' and step.get('results'):
                    type_results_for_report = step['results']
                    break

            report_html = generate_cleaning_report(
                df_original=st.session_state.df_original,
                df_cleaned=df_cleaned,
                cleaning_log=cleaning_log,
                type_results=type_results_for_report,
            )
            st.markdown(report_html, unsafe_allow_html=True)

        st.divider()
        st.subheader("📥 导出结果")

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            csv_data = df_cleaned.to_csv(index=False).encode('utf-8')
            fname_base = (st.session_state.current_file_name or 'data').rsplit('.', 1)[0]
            st.download_button(
                label="📄 下载清洗后 CSV",
                data=csv_data,
                file_name=f"cleaned_{fname_base}.csv",
                mime="text/csv",
                width='stretch'
            )

        with col_dl2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_cleaned.to_excel(writer, index=False, sheet_name='清洗后数据')
            excel_data = output.getvalue()
            st.download_button(
                label="📊 下载清洗后 Excel",
                data=excel_data,
                file_name=f"cleaned_{fname_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )

else:
    st.info("👆 请上传 CSV 或 Excel 文件开始数据清洗")
    st.markdown("""
    ### 使用说明

    1. **上传文件** — CSV、Excel（.xlsx/.xls），最大 50MB
    2. **配置参数** — 在左侧边栏调整清洗策略和列类型
    3. **查看检测** — 自动检测缺失值、重复行、格式错误、异常值
    4. **一键清洗** — 自动修复常见数据质量问题
    5. **下载结果** — 导出 CSV 或 Excel

    ### 支持的功能

    - ✅ 缺失值检测与填充（数值/文本分别处理）
    - ✅ 重复行检测与删除
    - ✅ 异常值检测（IQR 方法，可调阈值）
    - ✅ 邮箱/手机号格式验证与标准化
    - ✅ 敏感列自动识别与提醒
    - ✅ HTML 清洗报告
    - ✅ 列类型手动覆盖
    """)


# ---------- 法律免责声明（Week 4 修复 audit 问题1）----------
# 计划书 v6.0 第九项 9.5 - 页脚法律声明
st.divider()
st.markdown("""
<div style="background-color: #fafafa; padding: 24px; margin-top: 30px; border-radius: 12px; border: 1px solid #e5e5e5; font-size: 0.85rem; color: #666; line-height: 1.7;">
    <p style="font-weight: 600; color: #333; margin-bottom: 10px;">使用声明</p>
    <p><strong>运行环境</strong><br>
    本工具在您本地计算机上运行，所有数据处理仅在本机内存中完成，
    不会上传到任何服务器或第三方。</p>
    <p><strong>使用须知</strong><br>
    使用本工具即表示您确认：对所处理的数据拥有合法权限；
    遵守所在地区的数据保护法规；自行承担数据处理过程中的一切风险和责任。</p>
    <p><strong>免责声明</strong><br>
    本工具仅供数据清洗辅助使用。开发者对因使用本工具造成的任何数据损失或合规风险不承担任何责任。</p>
</div>
""", unsafe_allow_html=True)
