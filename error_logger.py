"""
Centralized error logging module for Just Meal Planner.

Handles:
- Structured error logging to daily rotating files
- In-memory error registry (last 100 errors)
- Error ID generation (format: err_[timestamp]_[hash])
- Error response construction
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from collections import deque

# Create errors directory if it doesn't exist
ERRORS_DIR = Path(__file__).parent / "errors"
ERRORS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


class ErrorLogger:
    """Centralized error logger with file rotation and in-memory registry."""
    
    def __init__(self, max_memory_errors: int = 100):
        """
        Initialize error logger.
        
        Args:
            max_memory_errors: Maximum number of errors to keep in memory
        """
        self.max_memory_errors = max_memory_errors
        self.error_registry: deque = deque(maxlen=max_memory_errors)
        self.logger = logging.getLogger(__name__)
    
    def _generate_error_id(self, source_url: Optional[str] = None) -> str:
        """
        Generate unique error ID.
        
        Format: err_[timestamp_10digits]_[hash_6chars]
        
        Args:
            source_url: Optional URL for hash generation
            
        Returns:
            Unique error ID string
        """
        timestamp = int(datetime.now().timestamp())
        
        # Create hash from timestamp + URL if available
        hash_input = f"{timestamp}_{source_url}" if source_url else str(timestamp)
        hash_obj = hashlib.md5(hash_input.encode())
        hash_str = hash_obj.hexdigest()[:6]
        
        return f"err_{timestamp}_{hash_str}"
    
    def _get_log_file_path(self) -> Path:
        """
        Get log file path for current date.
        
        Format: errors/YYYY-MM-DD.log
        
        Returns:
            Path to log file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return ERRORS_DIR / f"{date_str}.log"
    
    def _write_to_file(self, error_data: Dict) -> None:
        """
        Write error to daily rotating log file.
        
        Args:
            error_data: Error dictionary to log
        """
        log_file = self._get_log_file_path()
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_data) + "\n")
        except IOError as e:
            self.logger.error(f"Failed to write to log file {log_file}: {e}")
    
    def log_scraper_error(
        self,
        error_type: str,
        error_message: str,
        source_url: Optional[str] = None,
        endpoint: str = "/scrape",
        stacktrace: Optional[str] = None
    ) -> str:
        """
        Log a scraper error and return error ID.
        
        Args:
            error_type: Type of error (scraper_error, empty_ingredients, 
                       connection_error, timeout, validation_error)
            error_message: Human-readable error message
            source_url: Original URL that was attempted
            endpoint: API endpoint where error occurred
            stacktrace: Optional Python stacktrace for debugging
            
        Returns:
            error_id for the logged error
        """
        error_id = self._generate_error_id(source_url)
        timestamp = datetime.now().isoformat()
        
        error_data = {
            "timestamp": timestamp,
            "error_id": error_id,
            "error_type": error_type,
            "error_message": error_message,
            "source_url": source_url,
            "endpoint": endpoint,
            "stacktrace": stacktrace
        }
        
        # Write to file
        self._write_to_file(error_data)
        
        # Add to memory registry
        self.error_registry.append(error_data)
        
        return error_id
    
    def get_error_response(
        self,
        error_type: str,
        error_message: str,
        source_url: Optional[str] = None,
        stacktrace: Optional[str] = None
    ) -> Dict:
        """
        Log error and return structured ErrorResponse.
        
        Args:
            error_type: Type of error
            error_message: Error message
            source_url: Original URL
            stacktrace: Optional stacktrace
            
        Returns:
            ErrorResponse dictionary
        """
        error_id = self.log_scraper_error(
            error_type=error_type,
            error_message=error_message,
            source_url=source_url,
            endpoint="/scrape",
            stacktrace=stacktrace
        )
        
        return {
            "error": True,
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "source_url": source_url,
            "error_type": error_type,
            "error_message": error_message,
            "recipe_id": None
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent errors from in-memory registry.
        
        Args:
            limit: Number of recent errors to return (max 100)
            
        Returns:
            List of error dictionaries (most recent first)
        """
        limit = min(limit, self.max_memory_errors)
        return list(reversed(list(self.error_registry)[-limit:]))
    
    def get_error_stats(self) -> Dict:
        """
        Get error statistics from in-memory registry.
        
        Returns:
            Dictionary with error counts by type
        """
        stats = {}
        for error in self.error_registry:
            error_type = error.get("error_type", "unknown")
            stats[error_type] = stats.get(error_type, 0) + 1
        
        return {
            "total_errors_in_memory": len(self.error_registry),
            "errors_by_type": stats
        }


# Global singleton instance
_logger_instance: Optional[ErrorLogger] = None


def get_error_logger() -> ErrorLogger:
    """
    Get (or create) global error logger instance.
    
    Returns:
        ErrorLogger singleton
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ErrorLogger()
    return _logger_instance
