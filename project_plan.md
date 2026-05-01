# AI驱动的数据验证与清洗服务 - MVP项目计划书

> **版本：** v6.0（正式版）
>
> **制定日期：** 2025年7月
>
> **开发周期：** 4周
>
> **文档状态：** 正式发布，所有开发活动必须严格遵循本文档规范执行

---

## 一、项目目标

### 1.1 一句话概括

构建一款面向中小企业的轻量级数据验证与清洗工具，帮助非技术用户在可掌控的范围内自动检测并修复常见数据质量问题。所有处理仅在服务器内存中进行，处理完成后数据不会持久化到数据库或文件系统，服务器会在每次请求后自动释放内存。如需完全本地处理，请下载源码在本地运行。

### 1.2 核心价值主张

- 让不懂Python/SQL的人也能处理脏数据
- 5分钟内完成数据清洗并生成报告
- 零部署成本，浏览器即可使用

---

## 二、目标用户画像

### 2.1 核心用户群体

| 用户类型 | 典型场景 | 痛点 | 支付意愿 |
|---------|---------|-----|---------|
| **电商运营人员** | 清洗商品数据、价格数据、库存数据 | 多平台数据格式不统一，重复商品多 | ¥99-299/月 |
| **中小企业数据专员** | 客户信息管理、销售数据整理 | 手动Excel处理耗时，错误率高 | ¥99/月 |
| **小型诊所/医疗机构** | 患者信息录入、药品库存管理 | 格式不规范（手机号、邮箱等） | ¥199/月 |
| **HR/行政人员** | 员工信息表、工资数据整理 | 重复录入、数据更新滞后 | ¥99/月 |
| **自由职业者/顾问** | 为客户提供数据分析报告前清洗数据 | 客户数据脏乱，无合适工具 | ¥149/月 |

### 2.2 用户特征总结

```
用户特征画像：
├── 技术能力：Excel 熟练，SQL/Python 不熟悉
├── 核心诉求：快、简单、不需要学新东西
├── 使用场景：每周1-5次数据清洗任务
├── 数据规模：通常 < 10万行，文件 < 50MB
├── 决策心理：先看免费功能，有效果再付费
└── 典型用语："能不能帮我把这份Excel清洗一下？"
```

---

## 三、核心功能列表

### 3.1 P0 - 必须功能（MVP第一版）

| 功能 | 描述 | 验收标准 |
|-----|-----|---------|
| 文件上传 | 支持CSV和Excel文件拖拽上传 | 单文件≤50MB，≤10万行 |
| Sheet选择 | Excel多Sheet时让用户选择 | 下拉框选择sheet |
| 数据预览 | 上传后自动显示前20行和基本统计 | 显示列名、数据类型、行列数 |
| 缺失值检测 | 识别并高亮显示含缺失值的单元格 | 统计每列缺失率 |
| 重复行检测 | 识别完全重复的行 | 显示重复行数量和位置 |
| 自动清洗 | 按决策表自动处理所有可修复的问题 | 生成清洗后文件下载 |
| 清洗报告 | 生成问题汇总（HTML格式） | 网页报告+可导出CSV |
| 错误处理 | 友好处理解析失败的文件 | 显示明确错误提示 |

### 3.2 P1 - 最好有功能（第二版）

| 功能 | 描述 | 验收标准 |
|-----|-----|---------|
| 邮箱格式验证 | 检测邮箱格式是否合法 | 正则表达式验证 |
| 手机号格式验证 | 检测中国手机号格式 | 支持11位手机号，自动去除+86等前缀 |
| 数值异常值检测 | 使用IQR方法识别异常值 | 显示异常值所在行，支持阈值配置 |
| 自定义规则 | 用户添加自己的验证规则 | 支持简单规则配置 |
| 清洗历史 | 保存最近10次清洗记录（当前会话有效） | 刷新页面后丢失 |

### 3.3 P2 - 将来功能（后续迭代）

| 功能 | 描述 | 备注 |
|-----|-----|-----|
| 数据库直连 | 直接读取MySQL/PostgreSQL | 需要API支持 |
| AI修复建议 | 对每个问题给出LLM修复建议 | 需要LLM API集成 |
| 多文件批量处理 | 支持多文件批量清洗 | 数据源整合 |
| PDF报告原生导出 | 生成正式PDF报告 | 需要weasyprint/reportlab |

### 3.4 明确不包含的功能（非目标）

```
本MVP不包含以下功能（避免需求蔓延）：
❌ 不支持图片、PDF中的数据提取
❌ 不支持数据库直连（MySQL/PostgreSQL）
❌ 不支持自动修复错误邮箱（无有效算法）
❌ 不支持撤销/回滚清洗操作
❌ 不支持用户登录和数据隔离
❌ 不支持原生PDF报告
❌ 不支持超过50MB的文件
❌ 不支持超过10万行的数据
❌ 不支持清洗历史持久化（仅会话级）
```

---

## 四、自动清洗决策表

### 4.1 清洗决策规则

| 问题类型 | 自动修复行为 | 不可修复的行为 | 说明 |
|---------|-------------|---------------|-----|
| 缺失值（数值列） | 填充该列均值/中位数（自动选择） | — | 用户可配置策略 |
| 缺失值（文本列） | 填充众数 | — | 用户可配置策略 |
| 缺失值（日期列） | 前向填充（ffill） | 若无法插值则标记 | — |
| 重复行 | 保留第一次出现，删除后续 | — | `keep='first'` |
| 邮箱格式错误 | 无，仅报告 | 标记为需人工处理 | 邮箱无法自动推断正确值 |
| 手机号格式错误 | 标准化（去除+86、空格、横杠等分隔符） | 若无法标准化则标记 | 需11位数字 |
| 异常值（数值，超出IQR 1.5倍） | 替换为最近边界值 | — | `< lower_bound → lower_bound`，`> upper_bound → upper_bound` |
| 日期格式不一致 | 统一转换为 YYYY-MM-DD | 若无法解析则保留原样并标记（转为NaT后视为缺失值处理） | — |
| 前后空格/不可见字符 | 去除 | — | `str.strip()` |

### 4.2 关键原则

```
宁可少修复，也不要乱修复。
无法确定正确值的，标记出来让用户人工处理。
```

---

## 五、技术选型及理由

### 5.1 前端/界面方案

**推荐方案：Streamlit + session_state**

| 考量维度 | Streamlit | 传统Web框架 |
|---------|----------|------------|
| 开发速度 | ⭐⭐⭐⭐⭐ 5分钟搭界面 | ⭐⭐ 需1-2周 |
| 学习成本 | ⭐⭐⭐⭐⭐ 低 | ⭐⭐ 中 |
| 数据可视化 | ⭐⭐⭐⭐⭐ 内置支持 | ⭐⭐ 需集成 |
| 部署难度 | ⭐⭐⭐⭐⭐ 极简 | ⭐⭐ 复杂 |
| 状态管理 | ⭐⭐⭐ 有session_state但需主动使用 | ⭐⭐⭐⭐⭐ 原生支持 |

**选择理由：**

1. Python原生，统计/数据处理生态完美整合
2. 几分钟内从想法到可运行原型
3. 内置图表组件（Altair/Pandas/Plotly）
4. 免费部署到Streamlit Cloud
5. 社区活跃，文档完善

### 5.2 后端数据处理

**核心依赖：**

| 库/模块 | 用途 | 必要性 |
|--------|-----|--------|
| `pandas` | 数据读取、清洗、转换 | ✅ 必须 |
| `numpy` | 数值计算、异常值检测 | ✅ 必须 |
| `re` | 正则表达式验证 | ✅ 必须 |
| `openpyxl` | Excel文件读写 | ✅ 必须（Pandas依赖） |
| `io` | 字节流处理 | ✅ 必须 |
| `json` | 配置序列化 | ✅ 必须 |
| `hashlib` | 配置hash计算 | ✅ 必须 |
| `python-magic` | 文件类型检测 | ❌ 不使用，仅依赖扩展名判断 |

**不使用 `python-magic` 的原因：**
- Streamlit Cloud 需要额外安装 `libmagic1` 系统库
- MVP阶段仅通过文件扩展名 + 尝试读取即可判断类型
- 增加部署复杂度得不偿失

### 5.3 文件支持范围

| 文件格式 | 支持版本 | 最大文件大小 | 最大行数 | 说明 |
|---------|---------|------------|--------|-----|
| CSV | UTF-8编码优先，自动检测GBK/GB2312 | **50MB** | 10万行 | 分隔符自动检测 |
| Excel | .xlsx / .xls | **50MB** | 10万行 | 自动识别引擎 |
| 限制说明 | 超过限制时提前拒绝，显示友好提示引导用户拆分文件 | | | |

### 5.4 部署方式

| 部署方式 | 适用场景 | 成本 | 复杂度 |
|---------|---------|-----|-------|
| 本地运行 | 开发测试、个人使用 | ¥0 | 极简 |
| Streamlit Cloud | 公开分享、小团队 | ¥0（公开仓库） | 简单 |
| Docker本地部署 | 企业/商业用途 | ¥30-100/月云服务器 | 中等 |

### 5.5 Python版本要求

Python 3.9 或更高版本

核心依赖及版本：

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
```

### 5.6 Streamlit 状态管理指南

#### session_state 与 cache_data 分工

| 数据类型 | 存储位置 | 原因 |
|---------|---------|------|
| 原始文件bytes | `session_state` | 每次上传不同，不可缓存 |
| 类型推断结果 | `@st.cache_data` | 参数相同则结果相同 |
| 清洗后的DataFrame | `@st.cache_data` | 参数（原始数据hash + 配置hash）相同则结果相同 |
| 报告HTML | `@st.cache_data` | 同上 |
| 用户配置参数 | `session_state` | 需实时响应用户交互 |

#### 性能注意事项

Streamlit在每次用户交互时会重新运行整个脚本。如果不加缓存：
1. 用户每次点击按钮都会重新读取文件
2. 大文件（40MB CSV）会导致5-10秒延迟
3. 参数变化的清洗会重复计算

#### 新文件上传时的完整状态重置

上传新文件时必须清除以下状态：

```python
# 数据状态
st.session_state.df_original = None
st.session_state.df_cleaned = None
st.session_state.cleaning_log = None

# 用户配置状态
st.session_state.user_type_overrides = {}
st.session_state.config_remove_duplicates = True
st.session_state.config_numeric_strategy = 'auto'
st.session_state.config_handle_outliers = True
st.session_state.config_outlier_multiplier = 1.5

# selectbox key
for key in list(st.session_state.keys()):
    if key.startswith('type_override_'):
        del st.session_state[key]

# 缓存
st.cache_data.clear()
```

#### app.py 中的缓存包装函数

```python
# app.py - 缓存函数（✅ 放在此处而非 src/cleaners.py，保持模块纯净性）

import json
import io

@st.cache_data(ttl=3600, show_spinner="正在清洗数据...")
def cached_cleaning(
    file_bytes: bytes,
    config_json: str,           # ✅ 序列化传入，确保参数可哈希
    user_overrides_json: str,   # ✅ 序列化传入
    sheet_name: str = None
) -> tuple[pd.DataFrame, dict]:
    """
    带缓存的清洗函数包装器
    
    所有参数均为可哈希类型（bytes, str, None），满足 @st.cache_data 要求。
    内部调用 src/cleaners.py 中的纯函数 clean_data_pipeline()。
    """
    from src.cleaners import clean_data_pipeline
    from src.file_handler import load_data_bytes
    
    config = json.loads(config_json)
    user_overrides_dict = json.loads(user_overrides_json)
    from src.type_inference import ColumnType
    user_overrides = {k: ColumnType(v) for k, v in user_overrides_dict.items()}
    
    df = load_data_bytes(file_bytes, sheet_name=sheet_name)
    return clean_data_pipeline(df, config, user_overrides=user_overrides)


# 调用方式（app.py 中）
if st.button("一键清洗"):
    config = get_user_config()
    user_overrides = {k: v.value for k, v in st.session_state.user_type_overrides.items()}
    
    df_cleaned, log = cached_cleaning(
        st.session_state.file_bytes,
        json.dumps(config, sort_keys=True),
        json.dumps(user_overrides, sort_keys=True),
        st.session_state.get('selected_sheet')
    )
    
    st.session_state.df_cleaned = df_cleaned
    st.session_state.cleaning_log = log
```

---

## 六、项目文件结构

```
data-cleaner-mvp/
│
├── 📄 app.py                          # Streamlit主应用（入口文件）
├── 📄 requirements.txt                # Python依赖
├── 📄 README.md                       # 项目说明
├── 📄 LICENSE                         # MIT许可证
├── 📄 .gitignore                      # Git忽略配置
│
├── 📁 .streamlit/
│   └── 📄 config.toml                 # Streamlit配置（maxUploadSize, headless等）
│
├── 📁 src/
│   ├── 📄 __init__.py
│   ├── 📄 config.py                  # 常量、占位符列表、敏感列名模式
│   ├── 📄 file_handler.py            # 文件加载、验证、异常处理
│   ├── 📄 data_preview.py            # 数据预览、统计摘要、类型推断
│   ├── 📄 validators.py              # 所有检测函数（含类型检查）
│   ├── 📄 cleaners.py                # 清洗逻辑、clean_data_pipeline
│   ├── 📄 report_generator.py        # HTML报告生成
│   └── 📄 type_inference.py          # 列类型推断（独立模块）
│
├── 📁 tests/
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py                # pytest配置
│   ├── 📄 test_file_handler.py
│   ├── 📄 test_validators.py
│   ├── 📄 test_cleaners.py
│   ├── 📄 test_type_inference.py     # 类型推断单元测试
│   ├── 📄 test_happy_path.py        # 集成测试（端到端验证）
│   └── 📁 data/
│       ├── 📄 happy_path_1.csv
│       ├── 📄 happy_path_2.csv
│       └── 📄 test_sample.csv
│
├── 📁 docs/
│   ├── 📄 USER_GUIDE.md              # 用户使用指南
│   ├── 📄 CLEANING_DECISIONS.md     # 自动清洗决策表文档
│   └── 📄 DEPLOYMENT.md             # 部署指南
│
└── 📁 sample_data/
    └── 📄 demo_data.csv
```

### 文件职责详解

| 文件名 | 职责 | 关键函数/内容 |
|-------|-----|-------------|
| `app.py` | Streamlit页面布局、状态管理、用户交互、隐私警告 | `st.file_uploader`, `st.button`, `st.session_state` |
| `src/config.py` | 常量定义、缺失占位符列表、敏感列名模式 | `MISSING_PLACEHOLDERS`, `SENSITIVE_PATTERNS` |
| `src/file_handler.py` | 文件读取、编码检测、类型判断、大小验证 | `load_data()`, `load_data_bytes()`, `validate_file()`, `get_sheet_names()` |
| `src/data_preview.py` | 统计摘要生成、列名语义推断 | `generate_summary()`, `infer_column_meaning()` |
| `src/validators.py` | 缺失值/重复行/格式/IQR异常值检测 | `check_missing()`, `check_duplicates()`, `check_email_format()` |
| `src/cleaners.py` | 自动清洗逻辑（纯净函数，不依赖streamlit） | `clean_data_pipeline()`, `fill_numeric_missing()` |
| `src/report_generator.py` | HTML清洗报告生成 | `generate_cleaning_report()`, `export_data()` |
| `src/type_inference.py` | 列类型智能推断 | `infer_column_type()`, `normalize_missing_placeholders()` |

---

## 七、关键函数设计

### 7.1 文件处理模块 (`src/file_handler.py`)

```python
def load_data(uploaded_file, sheet_name: str = None) -> pd.DataFrame:
    """
    输入: uploaded_file - Streamlit UploadedFile 或 io.BytesIO
    输出: pandas DataFrame
    
    逻辑:
        1. 根据文件对象类型和 sheet_name 判断文件格式
        2. CSV: 尝试编码列表 ['utf-8', 'gbk', 'gb2312', 'latin1']
        3. Excel: 调用 pd.read_excel()
        4. 返回DataFrame或抛出明确异常
    """

def load_data_bytes(file_bytes: bytes, sheet_name: str = None) -> pd.DataFrame:
    """
    输入: file_bytes - 文件字节内容
    输出: pd.DataFrame
    逻辑: 使用 with io.BytesIO() 创建文件对象，调用 load_data()
    """

def validate_file(file) -> tuple[bool, str]:
    """
    输入: file - 文件对象
    输出: (is_valid: bool, error_message: str)
    逻辑:
        1. 检查文件大小（≤50MB）
        2. 检查文件类型（csv/xlsx/xls）
        3. 检查文件是否为空
    """

def get_sheet_names(file_bytes: bytes) -> list[str]:
    """
    输入: Excel文件字节内容
    输出: sheet名称列表
    逻辑: 使用 with io.BytesIO() 读取，pd.ExcelFile 获取sheet列表
    """
```

### 7.2 数据预览模块 (`src/data_preview.py`)

```python
def generate_summary(df) -> pd.DataFrame:
    """
    输入: 原始DataFrame
    输出: 统计摘要DataFrame（列名、数据类型、缺失数、缺失率、唯一值数）
    """
```

### 7.3 类型推断模块 (`src/type_inference.py`)

```python
class ColumnType(Enum):
    UNKNOWN = "unknown"
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    ID = "id"

def normalize_missing_placeholders(series: pd.Series, aggressive: bool = False) -> pd.Series:
    """
    输入: series - 原始列数据, aggressive - 是否包含可能被误用的占位符
    输出: 标准化后的Series（占位符→NaN）

    标准占位符包括: '', ' ', 'nan', 'NaN', 'null', 'NULL', 'N/A', 'na', 'None',
                  '无', '没有', '缺失', '-', '--', '...', '.', '?', '*' 等
    
    aggressive=True时会额外处理: 'nan', 'Nan', 'NAN'（可能误伤真实文本）
    """

def infer_column_type(series: pd.Series, user_override: Optional[ColumnType] = None) -> dict:
    """
    输入: series - 原始列数据（已经过占位符标准化）, user_override - 用户手动指定的类型
    输出: dict {
        'type': ColumnType,        # 推断的列类型
        'confidence': float,       # 可信度 0-1
        'failed_count': int,       # 无法匹配推断类型的值数量
        'failed_samples': list,    # 失败值样本（最多5个）
        'warning': Optional[str]   # 警告信息
    }
    
    🔴 关键修正：此函数仅返回类型信息，不修改原始数据。
    类型转换（如日期字符串→datetime）统一在 cleaners.py 中完成。

    检测优先级（从高到低）：
        1. 用户手动指定（如存在则直接使用）
        2. 模式匹配（手机号正则 > 邮箱正则 > 身份证正则）
        3. 数值转换探测（pd.to_numeric，需结合列名语义排除电话/ID列）
        4. 日期转换探测（pd.to_datetime，format='mixed'，errors='coerce'）
        5. 兜底为文本类型

    关键约束：
        - date_ratio 必须在 try 块外预初始化为 0.0，避免 NameError
        - 日期转换必须添加 errors='coerce'，否则无效值会抛异常
        - 格式匹配（手机号/邮箱/身份证）优先于数值转换，避免电话被误判为数值
        - 数字列仅当列名暗示为ID/电话时才降低置信度，不强制改类型
        - pd.to_datetime 中 format='mixed' 时会忽略 dayfirst 参数
          （pandas 2.0+，mixed 模式自行推断日-月顺序）
    """
```

### 7.4 验证规则模块 (`src/validators.py`)

```python
# P0 核心规则
def check_missing(df) -> dict:
    """
    输入: DataFrame（已经过 normalize_missing_placeholders 预处理）
    输出: dict {
        'column_name': {
            'count': int,
            'rate': float,
            'top_positions': list  # 仅返回前20个行索引，避免大文件内存爆炸
        }
    }
    
    重要说明（🔴 关键修正）:
        - 此函数假设输入数据已经被 normalize_missing_placeholders() 处理过
        - 所有占位符（'N/A', 'null', '-' 等）已被转为 NaN
        - 因此检测逻辑极为简单：仅依赖 pd.isnull()
        - 空字符串 ''：在 normalize 阶段被转为 NaN，此处不需要额外处理
    """

def check_duplicates(df) -> dict:
    """
    输入: DataFrame
    输出: dict {
        'total_duplicates': int,
        'duplicate_groups': dict  # 每组重复行的索引
    }
    """

# P1 扩展规则
def check_email_format(series) -> dict:
    """
    输入: pandas Series
    输出: dict {
        'valid_count': int,
        'invalid_count': int,
        'invalid_positions': list,
        'invalid_values': list
    }
    正则: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    """

def check_phone_format(series, country='CN') -> dict:
    """
    输入: pandas Series, country代码
    输出: 同上格式
    正则（中国）: ^1[3-9]\d{9}$（去除分隔符后匹配）
    """

def check_numeric_outliers_iqr(series, multiplier=1.5) -> dict:
    """
    输入: pandas Series, IQR倍数(默认1.5)
    输出: dict {...}
    
    必须添加类型守卫：非数值列直接返回空结果
    """
```

### 7.5 清洗逻辑模块 (`src/cleaners.py`)

```python
def clean_data_pipeline(
    df: pd.DataFrame,
    config: dict,
    user_overrides: dict = None
) -> tuple[pd.DataFrame, dict]:
    """
    完整的数据清洗流程（纯净函数，可单元测试）
    
    参数:
        df: 原始 DataFrame
        config: 清洗配置字典
        user_overrides: 用户对列类型的覆盖，格式 {列名: ColumnType}
    
    返回: (清洗后DataFrame, 清洗日志dict)
    
    步骤:
        1. 缺失占位符标准化（文字占位符 → NaN）
        2. 列类型推断（仅返回类型信息，不修改数据）
        3. 按推断的类型进行数据转换（日期字符串 → datetime 等）
        4. 重复行处理
        5. 缺失值填充（按列类型选择策略）
        6. 异常值处理（仅数值列）
        7. 格式标准化（去除空格、手机号标准化等）
    
    关键修正：
        - 类型推断和类型转换是两个独立步骤，职责分离
        - 步骤1必须在步骤2之前执行，确保 check_missing 只用 pd.isnull()
    """

def fill_numeric_missing(df: pd.DataFrame, col: str, method: str = 'auto') -> tuple[pd.Series, dict]:
    """
    输入: DataFrame, 列名, 填充方法
    输出: (填充后的Series, 填充信息dict{method, value, count})
    
    方法: 'auto'（根据偏度选择）, 'mean', 'median', 'zero'
    auto逻辑：|skewness| > 1 用中位数，否则用均值
    """

# ⚠️ 注意：@st.cache_data 装饰器不放在此模块中（src/cleaners.py），
# 以保持清洗函数的纯净性和可单元测试性。
# 缓存逻辑统一放在 app.py 中，通过包装函数调用此处的纯函数。
```

### 7.6 报告生成模块 (`src/report_generator.py`)

```python
def generate_cleaning_report(
    df_original: pd.DataFrame,
    df_cleaned: pd.DataFrame,
    cleaning_log: dict,
    type_results: dict,
    fill_values: dict = None
) -> str:
    """
    输入: 原始DataFrame, 清洗后DataFrame, 清洗日志, 类型推断结果, 填充详情
    输出: HTML字符串（用st.markdown渲染）
    
    报告包含：
        - 数据变化摘要（行数、列数、删除数量）
        - 各清洗步骤详细结果
        - 列类型识别结果（含转换损失）
        - 缺失值填充详情（文本类填充值脱敏展示）
        - 警告与建议
    """

def export_data(df, format='csv') -> bytes:
    """
    输入: DataFrame, 导出格式
    输出: 字节流(用于下载)
    """
```

---

## 八、检测规则清单

### 8.1 P0 核心规则

#### 规则1：缺失值检测

| 项目 | 内容 |
|-----|-----|
| **判断标准** | 仅依赖 `pd.isnull()`（所有占位符已在预处理阶段标准化为 NaN） |
| **前置步骤** | 必须先在 `normalize_missing_placeholders()` 中将 `'N/A'`、`'null'`、`'-'`、`'无'` 等转为 NaN |
| **统计输出** | 每列缺失数量、缺失率（%）、总缺失率 |
| **位置信息** | 仅返回前 20 个行索引，避免大文件内存爆炸

#### 规则2：重复行检测

| 项目 | 内容 |
|-----|-----|
| **判断标准** | 所有列值完全相同的行（忽略索引） |
| **检测方法** | `pandas.duplicated(keep=False)` |
| **统计输出** | 重复行数量、涉及的数据量 |

### 8.2 P1 扩展规则

#### 规则3：邮箱格式验证

| 项目 | 内容 |
|-----|-----|
| **判断标准** | 符合RFC 5322简化格式：`本地部分@域名.顶级域名` |
| **正则表达式** | `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` |
| **合法示例** | `user@example.com`, `test.user@company.cn` |
| **非法示例** | `user@`, `@example.com`, `user@.com` |

#### 规则4：中国手机号格式验证

| 项目 | 内容 |
|-----|-----|
| **判断标准** | 11位数字，以1开头，第二位为3/4/5/6/7/8/9（去除+86、空格、横杠等分隔符后匹配）|
| **正则表达式** | `^1[3-9]\d{9}$` |
| **合法示例** | `13812345678`, `138-1234-5678`（先归一化再匹配） |
| **非法示例** | `12345678901`（第二位不对）, `1381234567`（不足11位） |

#### 规则5：数值型异常值检测（IQR方法）

| 项目 | 内容 |
|-----|-----|
| **适用列** | 数值型列（int, float） |
| **判断标准** | 值小于 Q1 - 1.5×IQR 或大于 Q3 + 1.5×IQR |
| **下界** | Q1 - multiplier × IQR |
| **上界** | Q3 + multiplier × IQR |
| **可配置项** | multiplier参数（默认1.5，可设为1.0/2.0/3.0） |
| **类型检查** | 非数值列直接返回空结果，不报错 |

#### 规则6：日期格式验证

| 项目 | 内容 |
|-----|-----|
| **判断标准** | 能被 `pd.to_datetime(format='mixed', errors='coerce')` 解析为有效日期 |
| **转换方法** | `pandas.to_datetime()` 混合格式解析 |
| **异常处理** | 解析失败时返回 NaT，作为缺失值处理 |

---

## 九、隐私合规与安全

### 9.1 隐私警告（app.py 上传组件前显示）

```python
st.warning("""
⚠️ 数据安全提示

【重要】本工具部署在云端服务器上运行，您上传的文件会被传输到服务器内存中处理。
- 处理完成后，数据不会持久化到任何数据库或文件系统
- 服务器会在请求结束后自动释放内存（通常在几秒内完成）
- 您的数据不会被保存、分享或用于任何其他目的

【使用须知】
- 请勿上传身份证号、银行卡号、密码等高风险敏感数据
- 如数据包含手机号、邮箱等常规业务信息，请确认您有权处理
- 如需处理高度敏感数据，请下载源码在本地运行：
  pip install -r requirements.txt && streamlit run app.py
""")
```

### 9.2 敏感数据分级策略（🔴 关键修正）

> **核心决策：** 本工具的核心用户场景就是清洗客户/员工数据（含手机号、邮箱），
> 因此**不能强制阻止**这类数据的处理，否则工具直接废弃。
> 改为分级处理：高风险数据阻止，中等风险数据只需用户确认。

```
敏感数据分级：
┌──────────────────────────────────────────────────────────────┐
│  等级    │  数据类型                  │  处理策略           │
├──────────────────────────────────────────────────────────────┤
│  🔴 高风险│  身份证号、银行卡号、       │  st.stop() 强制阻止 │
│          │  社保号、密码、             │  引导用户脱敏后     │
│          │  social_security、passport  │  重新上传           │
├──────────────────────────────────────────────────────────────┤
│  🟡 中风险│  手机号、邮箱、姓名、       │  弹出确认框，       │
│          │  地址、出生日期、           │  用户勾选"我已授权" │
│          │  联系电话                  │  后方可继续         │
├──────────────────────────────────────────────────────────────┤
│  🟢 低风险│  年龄、薪资、              │  无提示，           │
│          │  普通业务数据              │  正常处理           │
└──────────────────────────────────────────────────────────────┘
```

### 9.3 检测模式定义

```python
# src/config.py

HIGH_RISK_PATTERNS = {
    'chinese': ['身份证', '证件号', '身份证号', '银行卡', '卡号', 
                 '账号', '密码', '社保', '医保号'],
    'english': ['ssn', 'social_security', 'passport', 'password',
                'credit_card', 'bank_account', 'card_number']
}

MEDIUM_RISK_PATTERNS = {
    'chinese': ['手机', '电话', '联系电话', '手机号', '邮箱', '电子邮件',
                 '姓名', '名字', '地址', '住址', '出生日期', '生日'],
    'english': ['name', 'full_name', 'first_name', 'last_name',
                 'phone', 'mobile', 'tel', 'telephone',
                 'email', 'mail', 'e-mail',
                 'address', 'street', 'city', 'zip', 'postal',
                 'dob', 'date_of_birth', 'birthday']
}
```

### 9.4 分级处理实现

```python
# app.py

def classify_and_handle_sensitive(df):
    """
    对敏感数据进行分级处理
    
    返回: (should_continue: bool, message_type: str, message: str)
    """
    high_risk_cols = []
    medium_risk_cols = []
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        # 检测高风险模式
        for pattern_list in [HIGH_RISK_PATTERNS['chinese'], HIGH_RISK_PATTERNS['english']]:
            if any(pattern in col_lower for pattern in pattern_list):
                high_risk_cols.append(col)
                break
        
        # 检测中风险模式
        for pattern_list in [MEDIUM_RISK_PATTERNS['chinese'], MEDIUM_RISK_PATTERNS['english']]:
            if any(pattern in col_lower for pattern in pattern_list):
                medium_risk_cols.append(col)
                break
    
    # 高风险：强制阻止
    if high_risk_cols:
        return (False, 'error', f"""
            🚫 **检测到高风险敏感数据列：** {', '.join(f'`{c}`' for c in high_risk_cols)}
            
            **本工具不支持处理身份证号、银行卡号、密码等高风险数据。**
            
            请按以下步骤操作：
            1. 在原始文件中**删除或脱敏**上述列
            2. 重新上传处理后的文件
            
            如需处理真实敏感数据，请下载源码在本地运行：
            `pip install -r requirements.txt && streamlit run app.py`
        """)
    
    # 中风险：需用户确认
    if medium_risk_cols:
        return (True, 'warning', f"""
            ⚠️ **检测到以下可能包含个人信息的列：** {', '.join(f'`{c}`' for c in medium_risk_cols)}
            
            本工具不会存储您的数据，处理仅在服务器内存中进行。
            请确认您有权处理这些数据，并勾选下方选项继续。
        """)
    
    # 无风险
    return (True, 'info', None)


# 在文件上传后的处理流程中：

should_continue, msg_type, message = classify_and_handle_sensitive(df)

if msg_type == 'error':
    st.error(message)
    st.stop()  # 高风险：强制阻止

elif msg_type == 'warning':
    st.warning(message)
    
    # 用户必须主动勾选确认
    consent_given = st.checkbox(
        "我确认有权处理这些数据，且数据不包含身份证号、银行卡号等高风险信息",
        value=False,
        key='sensitive_consent'
    )
    
    if not consent_given:
        st.info("请勾选上述选项以继续，或下载源码在本地运行。")
        st.stop()  # 未确认前阻止
```

### 9.5 法律免责声明

```html
<div style="background-color: #f8f9fa; padding: 20px; margin-top: 50px;">
    <h5>法律声明</h5>
    <p><strong>数据处理说明</strong></p>
    <p>
        本工具通过 Streamlit Cloud 部署在云端服务器运行。
        您上传的文件将在服务器内存中临时处理，不会持久化存储或传输给第三方，
        处理完成后内存自动释放。
    </p>
    
    <p><strong>使用条款</strong></p>
    <p>使用本工具即表示您同意：</p>
    <ul>
        <li>您对所上传的数据拥有合法处理权限</li>
        <li>不上传身份证号、银行卡号、密码等<strong>高风险敏感数据</strong></li>
        <li>不上传违法或有害内容</li>
        <li>自行承担数据处理过程中的一切风险和责任</li>
    </ul>
    
    <p><strong>免责声明</strong></p>
    <p>
        本工具仅供数据清洗辅助使用。
        开发者对因使用本工具造成的任何数据损失、泄露或合规风险不承担任何责任。
        如需处理高度敏感的数据，请下载源码在您自己的基础设施上本地运行。
    </p>
    
    <p style="color: #6c757d; font-size: 0.85em; margin-top: 15px;">
        如有问题或建议，请通过
        <a href="https://github.com/YOUR_USERNAME/data-cleaner-mvp/issues">GitHub Issues</a> 联系我们。
    </p>
</div>
```

---

## 十、测试策略

### 10.1 测试数据类型

| 测试类型 | 生成方式 | 用途 |
|---------|---------|-----|
| **正常数据** | 手动构造标准数据集 | 验证正常流程 |
| **边界数据** | 包含临界值的数据 | 验证边界处理 |
| **脏数据** | 人工注入各类问题 | 验证检测准确性 |
| **随机数据** | Faker库批量生成（仅用于手动探索性测试） | 不用于自动化测试 |

### 10.2 验收测试场景（Happy Path）

#### happy_path_1.csv：缺失值 + 重复行

| 问题类型 | 列名 | 位置（行索引，从0开始） | 注入方式 |
|---------|-----|----------------------|---------|
| 缺失值 | 姓名 | 2 | np.nan |
| 缺失值 | 年龄 | 1 | np.nan |
| 重复行 | 全部列 | 第0行与第4行完全相同 | 复制第0行 |

```python
# 期望断言
assert log['original_rows'] == 5
assert log['final_rows'] == 3  # 删除2个重复
assert df_cleaned['姓名'].isna().sum() == 0
assert df_cleaned['年龄'].isna().sum() == 0
```

#### happy_path_2.csv：邮箱/手机号格式错误

```python
# 期望断言
assert results['phone']['invalid_count'] == 4
assert results['email']['invalid_count'] == 4
assert df_cleaned['手机'].dtype == object  # 手机号保持为文本
```

### 10.3 单元测试清单

| 测试文件 | 测试内容 | 通过标准 |
|---------|---------|---------|
| `test_file_handler.py` | 文件读取、编码检测、大小验证 | 100%通过 |
| `test_validators.py` | 缺失值检测（含空字符串和占位符）、重复行检测、格式验证 | 100%通过 |
| `test_cleaners.py` | 各类型缺失值填充、重复行删除、异常值处理 | 100%通过 |
| `test_type_inference.py` | 数值列、文本列、日期列、电话列、邮箱列识别 | >90%准确 |
| `test_happy_path.py` | 端到端集成测试 | 100%通过 |

### 10.4 测试数据生成

```python
# tests/conftest.py

import pandas as pd
import numpy as np
import pytest

@pytest.fixture
def sample_missing_data():
    """包含缺失值和占位符的测试数据"""
    return pd.DataFrame({
        '数值列': [1.0, np.nan, 3.0, 4.0, np.nan],
        '文本列': ['a', '', 'b', None, 'N/A'],
        '占位列': ['null', 'NULL', 'None', 'NA', '有效值']
    })

@pytest.fixture
def sample_duplicate_data():
    """包含重复行的测试数据"""
    return pd.DataFrame({
        'a': [1, 2, 1, 3, 2],
        'b': ['x', 'y', 'x', 'z', 'y']
    })

@pytest.fixture
def sample_format_data():
    """包含格式错误的数据"""
    return pd.DataFrame({
        '邮箱': ['valid@test.com', 'invalid', 'test@', '@gmail.com', '', np.nan],
        '手机': ['13812345678', '12345', '138-1234-5678', '+86 13812345678', 'abc']
    })
```

### 10.5 运行测试命令

```bash
# 运行所有测试
cd data-cleaner-mvp
pytest tests/ -v --tb=short

# 运行特定测试
pytest tests/test_validators.py -v
pytest tests/test_happy_path.py -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

---

## 十一、开发顺序与里程碑

### 11.1 里程碑规划（4周 + 测试并行）

| 周次 | 里程碑 | 交付物 | 同步测试 |
|-----|-------|-------|---------|
| Week 1 | M1: 基础框架 | 可运行的上传+预览 | `test_file_handler.py` 上传读取测试 |
| Week 2 | M2: 验证功能 | 缺失值+重复行检测 | `test_validators.py` 单元测试 |
| Week 3 | M3: 清洗功能 | 一键清洗+报告 | `test_cleaners.py` 单元测试 |
| Week 3 | M3.5: 集成测试 | Happy Path测试 | 运行 `pytest tests/` |
| Week 4 | M4: 优化发布 | Bug修复+文档 | 回归测试确保无新问题 |
| Week 4 | M5: 部署上线 | Streamlit Cloud | 上线前最终验证 |

### 11.2 每日开发检查清单

- [ ] 编写新功能代码
- [ ] 同步编写单元测试
- [ ] 运行 `pytest tests/` 确保测试通过
- [ ] 手动测试核心流程
- [ ] 更新相关文档

### 11.3 第1周详细计划

| 天数 | 任务 | 交付物 |
|-----|-----|-------|
| Day 1-2 | 环境搭建、安装依赖、项目结构创建 | 可运行的 `requirements.txt` |
| Day 1-2 | Streamlit 页面骨架 + session_state | 基本的 `app.py` |
| Day 3-4 | 实现 `file_handler.py`（含编码处理、错误处理、BytesIO上下文管理） | 支持CSV/Excel读取+友好错误提示 |
| Day 5-7 | 实现 `data_preview.py` | 数据统计摘要功能 |

**周末里程碑：**
- ✅ 用户可以上传CSV/Excel文件
- ✅ 能看到数据的基本统计信息（行列数、列名、类型）
- ✅ 如果文件无法解析，显示友好错误提示

**第1周不尝试：**
- 编码问题的完美处理（先让基本流程跑通）
- 多sheet支持（第二周再做）
- 异常值检测（第三周再做）

### 11.4 第2周详细计划

| 天数 | 任务 | 交付物 |
|-----|-----|-------|
| Day 8-9 | Excel多Sheet支持 | 用户可选择sheet |
| Day 8-9 | 实现 `validators.py` P0（缺失值、重复行） | 验证规则函数 |
| Day 10-12 | 实现 `cleaners.py` P0（删除重复、填充缺失） | 自动清洗逻辑 |
| Day 13-14 | `test_validators.py` 单元测试 | 测试用例通过 |

**周末里程碑：**
- ✅ 用户选择sheet后看到预览
- ✅ 看到缺失值和重复行的检测结果
- ✅ 点击"一键清洗"后可以下载清洗后的文件

### 11.5 第3周详细计划

| 天数 | 任务 | 交付物 |
|-----|-----|-------|
| Day 15-16 | 邮箱、手机号格式验证 | `validators.py` P1 |
| Day 17-18 | IQR异常值检测（含类型检查） | `validators.py` P1 |
| Day 19-20 | 侧边栏配置（策略选择、阈值调整） | `app.py` UI完善 |
| Day 20 | `test_cleaners.py` 单元测试 | 测试用例通过 |
| Day 21 | 清洗报告HTML版 | `report_generator.py` |
| Day 21 | `test_happy_path.py` 集成测试 | Happy Path测试通过 |

### 11.6 第4周详细计划

| 天数 | 任务 | 交付物 |
|-----|-----|-------|
| Day 22-23 | 完善所有单元测试 | `tests/` 目录完善 |
| Day 24-25 | 隐私合规：敏感检测、警告、阻止 | `app.py` 完善 |
| Day 26-27 | UI美化 + 错误提示完善 | `app.py` 优化 |
| Day 27 | 回归测试（确保无新Bug） | 全部测试通过 |
| Day 28 | 部署到Streamlit Cloud + README | 可访问的URL |

---

## 十二、潜在风险与应对方案

### 12.1 大文件处理

| 风险 | 应对方案 |
|-----|---------|
| 文件超过50MB | 提前检查文件大小（代码检查 + config.toml server.maxUploadSize），拒绝并提示 |
| 内存溢出 | 不做额外处理，保持50MB限制 |
| Streamlit Cloud超时 | 文档说明大文件建议本地运行 |

### 12.2 编码问题

| 风险 | 应对方案 |
|-----|---------|
| CSV编码错误 | 自动检测编码，尝试多种编码；全失败则明确提示用户另存为UTF-8或GBK |
| 混合编码文件 | 不追求完美覆盖，引导用户使用正确编码 |

### 12.3 类型推断误判

| 风险 | 应对方案 |
|-----|---------|
| 电话号码被误判为数值 | 提前进行模式匹配（手机号正则优先于数值转换） |
| 列名暗示ID/电话 | 降低置信度，保留警告但不强制改类型 |
| 用户不满意推断 | 侧边栏提供手动覆盖选择，Selectbox使用session_state保持选择 |

### 12.4 其他风险

| 风险 | 缓解措施 |
|-----|---------|
| 缺失占位符误伤真实文本（如"nan"） | 提供aggressive模式开关，默认关闭 |
| 清洗后数据丢失 | 操作前在日志中记录原始行数，清洗后对比 |
| 隐私数据安全 | MVP阶段所有处理在内存完成，不持久化；检测到敏感列直接阻止 |

---

## 十三、Streamlit 配置文件

```toml
# .streamlit/config.toml

[server]
maxUploadSize = 50       # 单位MB
headless = true          # 无头模式运行

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#0084FF"
backgroundColor = "#FFFFFF"
```

---

## 十四、依赖文件

### 14.1 requirements.txt

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
```

### 14.2 packages.txt

本项目无需系统依赖，可不创建此文件。

---

## 十五、部署检查清单

- `requirements.txt` 包含 `streamlit`, `pandas`, `numpy`, `openpyxl`
- `.streamlit/config.toml` 配置了 `maxUploadSize = 50` 和 `headless = true`
- 在 Streamlit Cloud 的 Advanced settings 中设置 Python 版本为 3.9 或更高
- 使用 45MB 文件测试是否能在云上正常运行
- README 中包含本地运行和部署说明
- 隐私警告和法律免责声明已添加

---

## 十六、开源协议

### 16.1 选择：MIT License

**理由：**
- 限制最少，便于学习使用和简历展示
- 可自由修改和商业化
- 开源社区接受度最高

### 16.2 协议说明

以MIT发布后，任何人已获得的MIT授权不受影响。您可以对未来新版本变更协议，但不能撤销已发布版本的MIT授权。如未来打算闭源，停止公开更新即可。

### 16.3 LICENSE 文件内容

```text
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 十七、成功标准

1. ✅ 可成功上传50MB以内的CSV/Excel文件
2. ✅ 正确识别缺失值（含空字符串和各类占位符）、重复行（准确率>95%）
3. ✅ 类型推断对常见数据类型（文本、数值、日期、邮箱、手机号）准确率>90%
4. ✅ 一键清洗后数据完整性100%（无数据丢失）
5. ✅ 每个清洗步骤有详细日志记录
6. ✅ 清洗报告清晰展示所有操作，包含填充值详情
7. ✅ 部署到Streamlit Cloud后可正常运行
8. ✅ 敏感数据检测正确触发阻止

---

## 十八、修订历史

| 版本 | 日期 | 修订内容 |
|-----|-----|---------|
| v1.0 | 2025-07 | 初始版本 |
| v2.0 | 2025-07 | 增加自动清洗决策表、隐私警告、非目标功能列表、修正check_missing逻辑 |
| v3.0 | 2025-07 | 修正"本地处理"表述、增加类型检测逻辑、完善session_state指导 |
| v4.0 | 2025-07 | 重写类型推断（模式匹配优先）、修正st.cache_data指导、增加法律声明 |
| v5.0 | 2025-07 | 修正日期转换bug、HTML拼接错误、TOML语法错误、Selectbox状态保持、缓存函数纯粹性、BytesIO上下文管理、敏感检测阻止逻辑、完整状态重置 |
| v6.0 | 2025-07 | 🔴 敏感数据改为分级策略（高风险阻止/中风险确认）；🟠 缺失值检测统一为仅依赖pd.isnull()；🟡 类型推断与转换职责分离；缓存函数移至app.py；法律声明与产品定位统一 |

---

*本计划书为项目开发的唯一官方指导文档，所有开发活动必须严格遵循本文档中的规范、要求执行。*
