# src/file_handler.py
# 计划书 v6.0 第七项 7.1 - 文件处理模块
# 计划书 v6.0 第五项 - 文件支持范围（CSV ≤50MB/10万行, Excel ≤50MB/10万行）

"""
文件处理模块。

职责：
- 读取 CSV / Excel 文件（自动检测编码、Sheet）
- 文件大小和类型验证
- 所有异常转换为对用户友好的中文提示

重要：
- 使用 BytesIO 上下文管理器管理内存
- 本模块不依赖 streamlit，保持纯函数可测试
"""

import io
from typing import Optional

import pandas as pd


# ---------- 文件大小与行数限制 ----------
# 计划书 v6.0 第五项 - 文件支持范围
MAX_FILE_SIZE_MB = 50
MAX_ROWS = 100_000
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}


def validate_file(file) -> tuple[bool, str]:
    """
    验证上传文件的合法性。

    检查项：
        1. 文件是否为空
        2. 文件扩展名是否支持
        3. 文件大小是否在限制内

    参数:
        file: 文件对象（需有 .name 和 .size 属性）

    返回:
        (is_valid: bool, error_message: str)
    """
    if file is None:
        return False, "未选择文件，请上传 CSV 或 Excel 文件。"

    # 检查文件是否为空
    if hasattr(file, 'size') and file.size == 0:
        return False, "文件为空，请上传有效的数据文件。"

    # 检查文件扩展名
    if hasattr(file, 'name'):
        ext = '.' + file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            allowed = '、'.join(ALLOWED_EXTENSIONS)
            return False, f"不支持的文件格式，请上传 {allowed} 格式的文件。"

    # 检查文件大小
    if hasattr(file, 'size'):
        size_mb = file.size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            return False, (
                f"文件大小 {size_mb:.1f}MB 超过 {MAX_FILE_SIZE_MB}MB 限制。\n"
                "请将文件拆分为多个小文件后分别上传。"
            )

    return True, ""


def load_data(
    uploaded_file,
    sheet_name: Optional[str] = None,
    file_name: str = ""
) -> pd.DataFrame:
    """
    从文件对象加载数据，优先根据扩展名选择解析引擎。

    参数:
        uploaded_file: Streamlit UploadedFile 或 io.BytesIO
        sheet_name: Excel sheet 名称或索引（None 表示第一个 sheet）
        file_name: 原始文件名（用于判断文件类型，BytesIO 无 .name 时必须传入）

    返回:
        pd.DataFrame

    异常:
        ValueError: 文件无法解析时，包含中文友好错误提示
    """
    # 判断文件类型：
    #   1) 如果 uploaded_file 有 .name 属性（UploadedFile），直接用
    #   2) 否则检查 file_name 参数
    #   3) 最后检查 sheet_name（Excel 读取）
    is_excel = _detect_is_excel(uploaded_file, sheet_name, file_name)

    # 额外安全检查：如果都不是已知格式且 sheet_name 为空，报错
    if not is_excel and not _detect_is_csv(uploaded_file, file_name):
        raise ValueError(
            "不支持的文件格式，请上传 CSV（.csv）或 Excel（.xlsx/.xls）文件。"
        )

    if is_excel:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name or 0)
        except Exception as e:
            raise ValueError(
                f"Excel 文件读取失败。请确认文件未损坏且格式正确。\n"
                f"错误详情：{str(e)}"
            ) from e
    else:
        # CSV 文件：尝试多种编码
        df = _read_csv_with_encoding_detection(uploaded_file)

    # 检查行数限制
    if len(df) > MAX_ROWS:
        raise ValueError(
            f"文件包含 {len(df)} 行数据，超过 {MAX_ROWS} 行的限制。\n"
            "请将文件拆分为多个小文件后分别上传。"
        )

    return df


def load_data_bytes(
    file_bytes: bytes,
    sheet_name: Optional[str] = None,
    file_name: str = ""
) -> pd.DataFrame:
    """
    从 bytes 加载数据。

    计划书 v6.0 第十二项修正：使用 with io.BytesIO() 管理上下文。

    参数:
        file_bytes: 文件字节内容
        sheet_name: Excel sheet 名称
        file_name: 原始文件名（BytesIO 无 .name，必须通过此参数传递）

    返回:
        pd.DataFrame
    """
    with io.BytesIO(file_bytes) as file_obj:
        return load_data(file_obj, sheet_name=sheet_name, file_name=file_name)


def get_sheet_names(file_bytes: bytes) -> list[str]:
    """
    获取 Excel 文件的所有 Sheet 名称。

    计划书 v6.0 第十二项修正：使用 with io.BytesIO() 管理上下文。

    参数:
        file_bytes: Excel 文件字节内容

    返回:
        Sheet 名称列表。如果不是 Excel 文件，返回空列表。
    """
    with io.BytesIO(file_bytes) as file_obj:
        try:
            xl = pd.ExcelFile(file_obj)
            return xl.sheet_names
        except Exception:
            return []


# ---------- 内部辅助函数 ----------

def _detect_is_excel(
    file_obj,
    sheet_name: Optional[str],
    file_name: str = ""
) -> bool:
    """判断文件是否为 Excel 格式"""
    # 1) 通过 .name 属性
    if hasattr(file_obj, 'name') and file_obj.name:
        if file_obj.name.lower().endswith(('.xlsx', '.xls')):
            return True
        if file_obj.name.lower().endswith('.csv'):
            return False
    # 2) 通过 file_name 参数
    if file_name:
        if file_name.lower().endswith(('.xlsx', '.xls')):
            return True
        if file_name.lower().endswith('.csv'):
            return False
    # 3) 通过 sheet_name 参数（传入 sheet_name 说明期望读取 Excel）
    if sheet_name is not None:
        return True
    return False


def _detect_is_csv(file_obj, file_name: str = "") -> bool:
    """判断文件是否为 CSV 格式"""
    if hasattr(file_obj, 'name') and file_obj.name:
        return file_obj.name.lower().endswith('.csv')
    if file_name:
        return file_name.lower().endswith('.csv')
    return False


def _read_csv_with_encoding_detection(file_obj) -> pd.DataFrame:
    """
    尝试多种编码读取 CSV 文件。

    计划书 v6.0 第十二项修正：若所有编码均失败，给出明确引导提示。
    """
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    errors = []

    # 如果文件对象有 seek 方法，记录初始位置以便重置
    initial_position = None
    if hasattr(file_obj, 'seek'):
        try:
            initial_position = file_obj.tell()
        except (OSError, io.UnsupportedOperation):
            initial_position = None

    for encoding in encodings:
        try:
            # 重置文件指针到初始位置
            if hasattr(file_obj, 'seek') and initial_position is not None:
                try:
                    file_obj.seek(initial_position)
                except (OSError, io.UnsupportedOperation):
                    pass
            return pd.read_csv(file_obj, encoding=encoding)
        except (UnicodeDecodeError, UnicodeError) as e:
            errors.append(f"{encoding}: {e}")
            continue

    # 所有编码均失败 -> 给出明确的引导提示
    raise ValueError(
        "无法识别文件编码，已尝试的编码格式：UTF-8、GBK、GB2312。\n\n"
        "请按以下步骤操作：\n"
        "1. 用 Excel 打开文件\n"
        "2. 点击「文件」→「另存为」\n"
        "3. 选择「CSV UTF-8（逗号分隔）」格式保存\n"
        "4. 重新上传保存后的文件"
    )
