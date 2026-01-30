"""
Database backup and restore functionality.
"""

import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from .config import DATABASE_PATH, DATA_DIR

logger = logging.getLogger(__name__)


class BackupManager:
    """Manager for database backups."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory to store backups (default: data/backups)
        """
        self.backup_dir = backup_dir or DATA_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 10  # Keep last 10 backups

    def create_backup(self, description: str = "") -> Optional[Path]:
        """
        Create a backup of the database.

        Args:
            description: Optional description for the backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            if not DATABASE_PATH.exists():
                logger.error("Database file not found, cannot create backup")
                return None

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            desc_part = f"_{description}" if description else ""
            backup_filename = f"sds_database_backup_{timestamp}{desc_part}.db"
            backup_path = self.backup_dir / backup_filename

            # Copy database file
            shutil.copy2(DATABASE_PATH, backup_path)

            logger.info(f"Database backup created: {backup_path}")

            # Clean up old backups
            self._cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore database from a backup.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Create a backup of current database before restoring
            if DATABASE_PATH.exists():
                current_backup = self.create_backup(description="pre_restore")
                logger.info(f"Created safety backup before restore: {current_backup}")

            # Restore from backup
            shutil.copy2(backup_path, DATABASE_PATH)

            logger.info(f"Database restored from backup: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def list_backups(self) -> List[dict]:
        """
        List all available backups.

        Returns:
            List of backup information dictionaries
        """
        try:
            backups = []

            for backup_file in sorted(self.backup_dir.glob("*.db"), reverse=True):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'created_str': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent ones."""
        try:
            backups = sorted(
                self.backup_dir.glob("*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove backups beyond max_backups limit
            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def get_backup_info(self, backup_path: Path) -> Optional[dict]:
        """
        Get information about a specific backup.

        Args:
            backup_path: Path to backup file

        Returns:
            Dictionary with backup information, or None if not found
        """
        try:
            if not backup_path.exists():
                return None

            stat = backup_path.stat()

            return {
                'filename': backup_path.name,
                'path': str(backup_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_mtime),
                'created_str': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return None

    def auto_backup_if_needed(self, days_threshold: int = 7) -> Optional[Path]:
        """
        Automatically create a backup if the last backup is older than threshold.

        Args:
            days_threshold: Number of days since last backup to trigger new backup

        Returns:
            Path to new backup if created, None otherwise
        """
        try:
            backups = self.list_backups()

            if not backups:
                # No backups exist, create one
                return self.create_backup(description="auto")

            last_backup = backups[0]
            days_since_backup = (datetime.now() - last_backup['created']).days

            if days_since_backup >= days_threshold:
                logger.info(f"Last backup was {days_since_backup} days ago, creating new backup")
                return self.create_backup(description="auto")

            logger.info(f"Recent backup exists ({days_since_backup} days old), skipping auto-backup")
            return None

        except Exception as e:
            logger.error(f"Auto-backup check failed: {e}")
            return None


# Global instance
backup_manager = BackupManager()
