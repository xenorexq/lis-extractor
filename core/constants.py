"""
常量定义模块
集中管理项目中的配置常量
"""


class LoaderConfig:
    """数据加载配置常量"""
    # 文件大小阈值
    LARGE_FILE_THRESHOLD_MB = 100  # 超过此大小显示警告

    # 行数阈值
    MEMORY_OPTIMIZATION_ROW_THRESHOLD = 100_000  # 超过此行数进行内存优化
    DEFAULT_PREVIEW_ROWS = 100  # 默认预览行数
    MAX_DISPLAY_ROWS = 500  # 表格最大显示行数

    # 预览滑块范围
    SLIDER_MIN_ROWS = 500
    SLIDER_MAX_ROWS = 10_000
    SLIDER_STEP = 500


class ValidatorConfig:
    """验证配置常量"""
    DEFAULT_MATCH_RATIO = 0.75  # 列匹配最小比例
    MIN_SAMPLE_SIZE = 10  # 最小样本数量用于统计分析


class ParserConfig:
    """解析器配置常量"""
    MAX_SAMPLES = 100  # 格式检测最大样本数
    EXTREME_VALUE_THRESHOLD = 1e10  # 极端值阈值


class UIConfig:
    """UI 配置常量"""
    THREAD_WAIT_TIMEOUT_MS = 5000  # 线程等待超时（毫秒）
    THREAD_CLEANUP_TIMEOUT_MS = 3000  # 线程清理超时
    PROGRESS_UPDATE_INTERVAL = 5  # 进度更新间隔（百分比）


class ExportConfig:
    """导出配置常量"""
    TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'
    LABS_LONG_PREFIX = 'labs_long_'
    QC_REPORT_PREFIX = 'qc_report_'
