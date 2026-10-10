import os
import logging
import logging.handlers
import threading
from pathlib import Path
from django.conf import settings
from contextvars import ContextVar
from typing import Dict, List
from .progress_registry import set_progress
from .sse_bus import publish_log

# ========= Task Context and Mirror to Progress (used by LogManager below) ========

# Task ID context (set once per task entry)
task_id_var: ContextVar[str | None] = ContextVar('task_id', default=None)

# Global task ID registry for cross-thread access
_task_id_registry: Dict[int, str] = {}
_task_id_lock = threading.Lock()

def set_task_context(task_id: str | None):
    """Set task_id of current execution context (called on task entry)."""
    task_id_var.set(task_id)
    # Also set into global registry
    if task_id:
        with _task_id_lock:
            _task_id_registry[threading.get_ident()] = task_id

def clear_task_context():
    """Clear task_id (called when task finishes)."""
    task_id_var.set(None)
    # Also remove from global registry
    with _task_id_lock:
        _task_id_registry.pop(threading.get_ident(), None)


class TaskContextFilter(logging.Filter):
    """Inject task_id into LogRecord.task_id; supports multi-task and task type info"""
    def filter(self, record: logging.LogRecord) -> bool:
        # First try to obtain from ContextVar
        task_id = task_id_var.get()
        # If not in ContextVar, try global registry
        if task_id is None:
            with _task_id_lock:
                task_id = _task_id_registry.get(threading.get_ident())
        if task_id is not None:
            setattr(record, 'task_id', task_id)
        # Allow business logic to attach multiple task IDs or task types to record (optional)
        if not hasattr(record, 'task_ids'):
            setattr(record, 'task_ids', None)
        if not hasattr(record, 'task_type'):
            setattr(record, 'task_type', None)
        return True


class ProgressMirrorHandler(logging.Handler):
    """Mirror logs with task_id/ids to progress registry and SSE queue, supporting multi-task and multi-type"""
    def emit(self, record: logging.LogRecord) -> None:
        # Support multiple task IDs; if not present, use single task_id
        task_ids = getattr(record, 'task_ids', None)
        if not task_ids:
            single_id = getattr(record, 'task_id', None)
            if not single_id:
                return
            task_ids = [single_id]
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        # Task type (optional)
        task_type = getattr(record, 'task_type', None) or 'generation'
        for tid in task_ids:
            try:
                set_progress(tid, {'log': msg})
            except Exception:
                pass
            try:
                publish_log(
                    task_id=tid,
                    level=record.levelname,
                    msg=msg,
                    name=record.name,
                    thread=f"{record.thread} {record.threadName}",
                    task_type=task_type,
                    module=record.name,
                )
            except Exception:
                pass

# Log level mapping
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class LogManager:
    """Unified Log Manager"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LogManager._initialized:
            return
            
        # Get log config from Django settings, fallback to defaults
        self.log_level = LOG_LEVELS.get(
            getattr(settings, 'LOG_LEVEL', 'INFO'),
            logging.INFO
        )
        
        self.log_dir = getattr(settings, 'LOG_DIR', 'logs')
        self.max_bytes = getattr(settings, 'LOG_MAX_BYTES', 10 * 1024 * 1024)  # 10MB
        self.backup_count = getattr(settings, 'LOG_BACKUP_COUNT', 5)
        
        # Create log directory
        Path(self.log_dir).mkdir(exist_ok=True)
        
        # Configure root logger
        self._configure_root_logger()
        
        # Create loggers for each module
        self.loggers = {
            'core': self._get_logger('core'),
            'llm': self._get_logger('llm'),
            'ai_agents': self._get_logger('ai_agents'),
            'knowledge': self._get_logger('knowledge'),
            'api': self._get_logger('api'),
        }
        
        LogManager._initialized = True
        
    def _configure_root_logger(self):
        """Configure root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [thread=%(thread)d %(threadName)s] - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler - all logs
        all_log_file = os.path.join(self.log_dir, 'all.log')
        file_handler = logging.handlers.RotatingFileHandler(
            all_log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [thread=%(thread)d %(threadName)s] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Add file handler - error logs only
        error_log_file = os.path.join(self.log_dir, 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        # Inject task context filter and mirror handler
        task_filter = TaskContextFilter()
        root_logger.addFilter(task_filter)
        mirror_handler = ProgressMirrorHandler(level=self.log_level)
        # Match console/file format with extra task_id for frontend troubleshooting
        mirror_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [thread=%(thread)d %(threadName)s] - [task_id=%(task_id)s] - %(message)s'
        ))
        root_logger.addHandler(mirror_handler)
    
    def _get_logger(self, name):
        """Get logger for specified name"""
        logger = logging.getLogger(name)
        
        # Create log file for specific module
        log_file = os.path.join(self.log_dir, f'{name}.log')
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        handler.setLevel(self.log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [thread=%(thread)d %(threadName)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Clear existing handlers
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            
        logger.addHandler(handler)
        
        # Add task context filter
        task_filter = TaskContextFilter()
        logger.addFilter(task_filter)
        
        # Also add filter to handler
        handler.addFilter(task_filter)
        
        return logger
    
    def get_logger(self, name):
        """Get logger"""
        if name in self.loggers:
            return self.loggers[name]
        
        # Handle submodule loggers, e.g. llm.deepseek
        for module, logger in self.loggers.items():
            if name.startswith(f"{module}."):
                return logging.getLogger(name)
        
        # If not predefined module, create logger with TaskContextFilter via _get_logger
        return self._get_logger(name)

# Create singleton instance
log_manager = LogManager()

def get_logger(name):
    """Convenience function to get logger"""
    return log_manager.get_logger(name)

