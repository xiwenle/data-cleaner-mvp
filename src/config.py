# src/config.py
# 计划书 v6.0 第九项 - 隐私合规与安全（检测模式定义）
# 计划书 v6.0 第五大项修正 - 占位符列表

"""
全局配置常量，包括：
- 缺失占位符列表
- 敏感数据模式（高风险 / 中风险）
- 重要：本模块不依赖 streamlit，可被其他纯函数模块安全导入。
"""

# ---------- 缺失值占位符列表 ----------
# 计划书 v6.0 第九项 - 占位符标准化
# 所有被识别为占位符的值将在 normalize_missing_placeholders() 中转为 NaN

MISSING_PLACEHOLDERS = {
    # 空值变体
    '', ' ', 'nan', 'NaN', 'NAN',
    # 编程语言 null
    'null', 'NULL', 'Null', 'none', 'None', 'NIL', 'nil',
    # 表格/数据分析常用
    'N/A', 'n/a', 'NA', 'na', '#N/A', '#N/A N/A',
    # 中文占位符
    '无', '没有', '缺失', '空', '空值',
    # 符号占位符
    '-', '--', '—', '.', '..', '...', '*', '?', '/', 'x'
}

# aggressive 模式额外处理的占位符（默认关闭，避免误伤真实文本 "nan"）
AGGRESSIVE_PLACEHOLDERS = {
    'nan', 'Nan', 'NAN'
}


# ---------- 敏感数据检测模式 ----------
# 计划书 v6.0 第九项 - 敏感数据分级策略

HIGH_RISK_PATTERNS = {
    'chinese': [
        '身份证', '证件号', '身份证号',
        '银行卡', '卡号', '账号',
        '密码', '社保', '医保号'
    ],
    'english': [
        'ssn', 'social_security', 'passport',
        'password', 'credit_card', 'bank_account', 'card_number'
    ]
}

MEDIUM_RISK_PATTERNS = {
    'chinese': [
        '手机', '电话', '联系电话', '手机号',
        '邮箱', '电子邮件',
        '姓名', '名字',
        '地址', '住址',
        '出生日期', '生日'
    ],
    'english': [
        'name', 'full_name', 'first_name', 'last_name',
        'phone', 'mobile', 'tel', 'telephone',
        'email', 'mail', 'e-mail',
        'address', 'street', 'city', 'zip', 'postal',
        'dob', 'date_of_birth', 'birthday'
    ]
}
