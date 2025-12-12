"""
日志模块
提供统一的日志记录功能
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_log_dir() -> Path:
    """获取日志目录"""
    # 优先使用环境变量
    if log_dir := os.getenv('LIS_LOG_DIR'):
        path = Path(log_dir)
    else:
        # 默认使用用户目录下的 .lis-extractor/logs
        path = Path.home() / '.lis-extractor' / 'logs'

    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logger(
    name: str = 'lis_extractor',
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    设置并返回 logger

    Args:
        name: logger 名称
        level: 日志级别
        log_to_file: 是否写入文件
        log_to_console: 是否输出到控制台

    Returns:
        配置好的 logger
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # 控制台输出
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件输出
    if log_to_file:
        log_dir = get_log_dir()
        log_file = log_dir / f"lis_extractor_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger（如果不存在则创建）

    Args:
        name: logger 名称，如果为 None 则返回根 logger

    Returns:
        logger 实例
    """
    if name is None:
        name = 'lis_extractor'

    logger = logging.getLogger(name)

    # 如果还没有配置，进行默认配置
    if not logger.handlers:
        setup_logger(name)

    return logger


# 预定义的错误类型常量
class ErrorType:
    """错误类型常量"""
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    DATA_PARSE = "DATA_PARSE"
    DATA_VALIDATE = "DATA_VALIDATE"
    PROFILE_LOAD = "PROFILE_LOAD"
    EXPORT = "EXPORT"
    THREAD = "THREAD"
    UI = "UI"


def log_error(
    logger: logging.Logger,
    error_type: str,
    message: str,
    context: str = "",
    exc_info: bool = False
) -> str:
    """
    统一的错误日志记录

    Args:
        logger: logger 实例
        error_type: 错误类型 (使用 ErrorType 常量)
        message: 错误消息
        context: 额外上下文信息
        exc_info: 是否包含异常堆栈

    Returns:
        格式化后的错误消息
    """
    full_msg = f"[{error_type}] {message}"
    if context:
        full_msg += f" | 上下文: {context}"

    logger.error(full_msg, exc_info=exc_info)
    return full_msg


def log_warning(
    logger: logging.Logger,
    warning_type: str,
    message: str,
    context: str = ""
) -> str:
    """
    统一的警告日志记录

    Args:
        logger: logger 实例
        warning_type: 警告类型
        message: 警告消息
        context: 额外上下文信息

    Returns:
        格式化后的警告消息
    """
    full_msg = f"[{warning_type}] {message}"
    if context:
        full_msg += f" | 上下文: {context}"

    logger.warning(full_msg)
    return full_msg


def log_info(
    logger: logging.Logger,
    message: str,
    context: str = ""
) -> str:
    """
    统一的信息日志记录

    Args:
        logger: logger 实例
        message: 消息
        context: 额外上下文信息

    Returns:
        格式化后的消息
    """
    full_msg = message
    if context:
        full_msg += f" | {context}"

    logger.info(full_msg)
    return full_msg


# ============== 用户界面消息格式化 ==============

class UserMessage:
    """
    统一的用户界面消息格式化类

    用于 QMessageBox 和 error signal 的消息格式统一
    """

    # 消息类型
    class Type:
        ERROR = "错误"
        WARNING = "警告"
        INFO = "提示"
        SUCCESS = "成功"

    # 操作类型（用于组合标题）
    class Action:
        LOAD = "加载"
        SAVE = "保存"
        EXPORT = "导出"
        IMPORT = "导入"
        SCAN = "扫描"
        PARSE = "解析"
        MAP = "映射"
        VALIDATE = "验证"
        CREATE = "创建"
        DELETE = "删除"
        PROCESS = "处理"

    @staticmethod
    def format_title(action: str, msg_type: str = "错误") -> str:
        """
        格式化消息标题

        Args:
            action: 操作类型 (如 "加载", "导出")
            msg_type: 消息类型 (如 "错误", "警告")

        Returns:
            格式化的标题，如 "加载失败" 或 "导出成功"
        """
        if msg_type == UserMessage.Type.ERROR:
            return f"{action}失败"
        elif msg_type == UserMessage.Type.SUCCESS:
            return f"{action}成功"
        elif msg_type == UserMessage.Type.WARNING:
            return f"{action}警告"
        else:
            return f"{action}提示"

    @staticmethod
    def format_error(
        action: str,
        reason: str,
        detail: str = "",
        suggestion: str = ""
    ) -> str:
        """
        格式化错误消息内容

        Args:
            action: 操作描述 (如 "加载文件", "导出数据")
            reason: 错误原因 (如 "文件不存在", "权限不足")
            detail: 详细信息 (可选，如文件路径)
            suggestion: 建议操作 (可选)

        Returns:
            格式化的错误消息
        """
        msg = f"无法{action}"
        if reason:
            msg += f"\n原因: {reason}"
        if detail:
            msg += f"\n详情: {detail}"
        if suggestion:
            msg += f"\n建议: {suggestion}"
        return msg

    @staticmethod
    def format_warning(
        message: str,
        detail: str = "",
        suggestion: str = ""
    ) -> str:
        """
        格式化警告消息

        Args:
            message: 警告信息
            detail: 详细信息 (可选)
            suggestion: 建议操作 (可选)

        Returns:
            格式化的警告消息
        """
        msg = message
        if detail:
            msg += f"\n详情: {detail}"
        if suggestion:
            msg += f"\n建议: {suggestion}"
        return msg

    @staticmethod
    def format_success(
        action: str,
        detail: str = ""
    ) -> str:
        """
        格式化成功消息

        Args:
            action: 操作描述
            detail: 详细信息 (可选)

        Returns:
            格式化的成功消息
        """
        msg = f"{action}完成"
        if detail:
            msg += f"\n{detail}"
        return msg

    @staticmethod
    def format_validation_error(
        missing_fields: list,
        field_type: str = "字段"
    ) -> str:
        """
        格式化验证错误消息

        Args:
            missing_fields: 缺少的字段列表
            field_type: 字段类型描述

        Returns:
            格式化的验证错误消息
        """
        if not missing_fields:
            return ""
        fields_str = ", ".join(missing_fields)
        return f"缺少必填{field_type}: {fields_str}"

    @staticmethod
    def format_file_error(
        operation: str,
        file_path: str,
        error: str
    ) -> str:
        """
        格式化文件操作错误

        Args:
            operation: 操作类型 (如 "读取", "写入")
            file_path: 文件路径
            error: 错误信息

        Returns:
            格式化的文件错误消息
        """
        filename = os.path.basename(file_path) if file_path else "未知文件"
        return f"无法{operation}文件\n文件: {filename}\n错误: {error}"

    @staticmethod
    def format_permission_error(
        operation: str,
        path: str
    ) -> str:
        """
        格式化权限错误

        Args:
            operation: 操作类型
            path: 路径

        Returns:
            格式化的权限错误消息
        """
        return f"无法{operation}\n路径: {path}\n原因: 权限不足\n建议: 请检查文件/文件夹权限或选择其他位置"
