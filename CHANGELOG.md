# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-12-01

### Performance Improvements
- **iterrows() 优化**: 使用 `zip()` 替代 `iterrows()` 进行表格填充，性能提升约 100 倍
- **DataFrame 内存优化**: 日期解析时只保存 10 个样本用于诊断，而非复制整列数据
- **进度条准确性**: 分离数据收集和合并阶段，提供更准确的进度反馈

### Code Quality
- **常量管理**: 新增 `core/constants.py`，集中管理所有配置常量
  - `LoaderConfig`: 文件加载相关配置
  - `ValidatorConfig`: 验证相关配置
  - `ParserConfig`: 解析相关配置
  - `UIConfig`: 界面相关配置
  - `ExportConfig`: 导出相关配置
- **边界值检查**: `ValueParser` 新增对 inf、nan 和极端值的验证
- **代码去重**: 提取 `_make_ijwi_column_name()` 方法，消除重复代码
- **日志规范化**: 将 `print()` 语句替换为 `logger` 调用

### Bug Fixes
- **线程安全**: 为 `FullScanThread` 添加取消机制和清理方法
- **科学计数法验证**: 修复科学计数法等特殊格式未经过边界值检查的问题

### New Features
- **UserMessage 类**: 统一的用户界面消息格式化工具
  - `format_title()`: 格式化消息标题
  - `format_error()`: 格式化错误消息
  - `format_success()`: 格式化成功消息
  - `format_validation_error()`: 格式化验证错误
  - `format_file_error()`: 格式化文件错误
  - `format_permission_error()`: 格式化权限错误

## [1.0.0] - 2025-11-29

### Initial Release
- 完整的 LIS 数据抽取向导流程
- 支持 Excel 文件批量处理
- 灵活的字段映射配置
- 检验项目选择和标准化
- 数值解析（支持 <、>、阳性/阴性等格式）
- 质量报告生成
- Profile 配置保存和复用
