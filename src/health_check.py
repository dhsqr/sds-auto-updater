"""
Health check and system monitoring module.
Provides functionality to check system health and status.
"""

import logging
import psutil
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from .config import DATABASE_PATH, SDS_STORAGE_PATH, GOOGLE_API_KEY, GMAIL_SENDER_EMAIL
from .database import db

logger = logging.getLogger(__name__)


class HealthChecker:
    """System health checker."""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """
        Check database health and accessibility.

        Returns:
            Dictionary with database health information
        """
        try:
            # Check if database file exists
            if not DATABASE_PATH.exists():
                return {
                    'status': 'error',
                    'message': 'Database file not found',
                    'path': str(DATABASE_PATH)
                }

            # Try to query the database
            stats = db.get_statistics()

            return {
                'status': 'healthy',
                'path': str(DATABASE_PATH),
                'size': os.path.getsize(DATABASE_PATH),
                'statistics': stats,
                'accessible': True
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'accessible': False
            }

    @staticmethod
    def check_storage() -> Dict[str, Any]:
        """
        Check file storage health and disk space.

        Returns:
            Dictionary with storage health information
        """
        try:
            # Check if storage directory exists
            if not SDS_STORAGE_PATH.exists():
                SDS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

            # Count files
            pdf_files = list(SDS_STORAGE_PATH.glob('*.pdf'))
            total_size = sum(f.stat().st_size for f in pdf_files if f.is_file())

            # Check disk space
            disk_usage = psutil.disk_usage(str(SDS_STORAGE_PATH))

            return {
                'status': 'healthy',
                'path': str(SDS_STORAGE_PATH),
                'pdf_count': len(pdf_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'disk_free_gb': round(disk_usage.free / (1024 ** 3), 2),
                'disk_percent_used': disk_usage.percent
            }

        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @staticmethod
    def check_api_configuration() -> Dict[str, Any]:
        """
        Check API configuration status.

        Returns:
            Dictionary with API configuration status
        """
        checks = {
            'google_api': {
                'configured': bool(GOOGLE_API_KEY),
                'required': True,
                'status': 'configured' if GOOGLE_API_KEY else 'missing'
            },
            'gmail': {
                'configured': bool(GMAIL_SENDER_EMAIL),
                'required': False,
                'status': 'configured' if GMAIL_SENDER_EMAIL else 'optional_not_configured'
            }
        }

        all_required_configured = all(
            check['configured'] for check in checks.values()
            if check['required']
        )

        return {
            'status': 'healthy' if all_required_configured else 'degraded',
            'checks': checks,
            'all_required_configured': all_required_configured
        }

    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """
        Check system resource usage (CPU, memory).

        Returns:
            Dictionary with system resource information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024 ** 3), 2),
                'memory_total_gb': round(memory.total / (1024 ** 3), 2)
            }

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @classmethod
    def run_full_health_check(cls) -> Dict[str, Any]:
        """
        Run a full health check of all components.

        Returns:
            Dictionary with complete health check results
        """
        timestamp = datetime.utcnow().isoformat()

        results = {
            'timestamp': timestamp,
            'database': cls.check_database(),
            'storage': cls.check_storage(),
            'api_configuration': cls.check_api_configuration(),
            'system_resources': cls.check_system_resources()
        }

        # Determine overall status
        statuses = [
            results['database']['status'],
            results['storage']['status'],
            results['api_configuration']['status'],
            results['system_resources']['status']
        ]

        if 'error' in statuses:
            overall_status = 'unhealthy'
        elif 'degraded' in statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'

        results['overall_status'] = overall_status

        return results

    @staticmethod
    def get_uptime_info() -> Dict[str, Any]:
        """
        Get system uptime information.

        Returns:
            Dictionary with uptime information
        """
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            return {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_hours': round(uptime.total_seconds() / 3600, 2),
                'uptime_days': round(uptime.total_seconds() / 86400, 2)
            }

        except Exception as e:
            logger.error(f"Uptime check failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# Global instance
health_checker = HealthChecker()
