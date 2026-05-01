# 🧹 数据清洗工具 Data Cleaner MVP

> 面向中小企业非技术用户的轻量级数据验证与清洗工具。上传 CSV/Excel，自动检测并修复数据质量问题——无需任何编程知识。

---

## ✨ 功能亮点

- 🚀 **一键清洗** — 上传文件后自动检测缺失值、重复行、异常值、格式错误，一键修复
- 🔍 **智能检测** — 自动识别列类型（数值/文本/日期/邮箱/手机号），按类型选择合理的填充策略
- 🛡️ **敏感数据保护** — 三级分级检测：高风险（身份证/银行卡）强制阻止、中风险（手机/邮箱）需用户确认
- 📊 **完整报告** — 清洗后自动生成 HTML 报告，含数据变化对比、填充详情、类型识别、警告建议
- 🎨 **macOS 风格 UI** — 克制配色、充足留白、圆角设计、非技术用户也能秒懂
- ⚙️ **灵活配置** — 侧边栏调整去重、填充策略（自动/均值/中位数/填零）、异常值阈值
- 📥 **多格式导出** — CSV + Excel 双格式下载

## 🌐 在线演示

> *(即将部署到 Streamlit Cloud，届时此处将填入公开链接)*

## 🚀 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/data-cleaner-mvp.git
cd data-cleaner-mvp

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
streamlit run app.py
```

浏览器打开 [http://localhost:8501](http://localhost:8501) 即可使用。

## 📖 使用流程

```
上传文件 → 查看检测结果 → 配置清洗策略 → 一键清洗 → 查看报告 → 下载文件
```

1. **上传文件** — 拖拽 CSV 或 Excel 到上传区域
2. **确认数据** — 自动预览前 20 行、显示统计摘要和列类型推断
3. **查看检测** — 缺失值、重复行自动检测；邮箱/手机号格式、异常值可折叠查看
4. **调整配置** — 左侧边栏修改去重、填充策略、异常值阈值和列类型覆盖
5. **一键清洗** — 点击大按钮，数秒内完成清洗；成功后自动生成报告
6. **导出结果** — 下载清洗后的 CSV 或 Excel 文件

详见 [用户操作指南](docs/USER_GUIDE.md)。

## ⚙️ 文件限制

| 项目 | 限制 |
|-----|-----|
| 文件格式 | CSV（UTF-8/GBK）、Excel（.xlsx/.xls） |
| 文件大小 | ≤ 50MB |
| 数据行数 | ≤ 10 万行 |
| 超出处理 | 友好的错误提示，引导用户拆分后重新上传 |

## 🔒 隐私安全

- **数据处理**：所有处理在服务器内存中完成，不持久化到任何数据库或文件系统
- **自动释放**：请求结束后服务器自动释放内存（通常在数秒内）
- **无痕使用**：您的数据不会被保存、分享或用于任何其他目的
- **敏感分级**：
  - 🔴 高风险（身份证号、银行卡号）→ 强制阻止，需脱敏后重新上传
  - 🟡 中风险（手机号、邮箱、姓名）→ 弹出确认框，用户勾选授权后方可继续
  - 🟢 低风险 → 正常处理
- **本地优先**：如需处理高度敏感数据，下载源码在本地运行即可

## 🧱 技术栈

| 组件 | 技术 |
|-----|-----|
| 前端界面 | Streamlit 1.50 |
| 数据处理 | Pandas 2.3, NumPy 2.0 |
| 文件读写 | openpyxl 3.1（Excel） |
| 测试框架 | pytest 8.4（48 个测试用例） |
| 部署平台 | Streamlit Cloud |

## 📂 项目结构

```
data-cleaner-mvp/
├── app.py                    # Streamlit 主入口
├── requirements.txt          # Python 依赖
├── src/                      # 纯函数核心模块（不依赖 streamlit）
│   ├── config.py            # 常量、占位符、敏感模式
│   ├── file_handler.py      # 文件读取、验证
│   ├── type_inference.py    # 列类型推断
│   ├── data_preview.py      # 统计摘要
│   ├── validators.py        # 检测规则
│   ├── cleaners.py          # 清洗流水线
│   └── report_generator.py  # HTML 报告生成
├── tests/                    # 48 个单元测试 + 集成测试
├── docs/                     # 用户指南、部署文档、路线图
└── .streamlit/config.toml   # Streamlit 配置
```

## 🤝 技术支持

- **Issues**：在 GitHub 仓库提交 [Issue](https://github.com/YOUR_USERNAME/data-cleaner-mvp/issues)
- **反馈**：欢迎提交功能建议和 bug 报告
- **贡献**：MIT 开源协议，欢迎 PR

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件
