#!/usr/bin/env python3
"""
SDS Auto-Updater - Command Line Interface

Usage:
    python main.py --import-csv data/chemicals.csv   # Import chemicals from CSV
    python main.py --check-all                        # Check all chemicals for updates
    python main.py --check --cas 1310-73-2           # Check specific chemical
    python main.py --test-email                       # Send test email
    python main.py --scheduler                        # Start the scheduler
    python main.py --stats                            # Show database statistics
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db
from src.scheduler import scheduler
from src.alerts.email_alerts import email_service
from src.config import validate_config
from src.health_check import health_checker
from src.backup import backup_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sds_updater.log")
    ]
)
logger = logging.getLogger(__name__)


def import_chemicals(csv_path: str):
    """Import chemicals from a CSV file."""
    print(f"\n📥 Importing chemicals from: {csv_path}")
    
    try:
        count = db.import_chemicals_from_csv(csv_path)
        print(f"✅ Successfully imported {count} new chemicals")
        
        stats = db.get_statistics()
        print(f"📊 Total chemicals in database: {stats['total_chemicals']}")
        
    except Exception as e:
        print(f"❌ Error importing chemicals: {e}")
        sys.exit(1)


def check_all_chemicals():
    """Run a check on all chemicals."""
    print("\n🔍 Starting SDS check for all chemicals...")
    
    results = scheduler.run_daily_check()
    
    print(f"\n📊 Check Complete:")
    print(f"   Total chemicals: {results['total']}")
    print(f"   Checked: {results['checked']}")
    print(f"   Updated: {results['updated']}")
    print(f"   Errors: {results['errors']}")
    
    if results['chemicals_with_changes']:
        print(f"\n⚠️ Chemicals with changes:")
        for chem in results['chemicals_with_changes']:
            print(f"   - {chem['name']} ({chem['cas']})")
            for change in chem['changes']:
                print(f"      [{change['severity']}] {change['section']}: {change['summary']}")


def check_single_chemical(cas_number: str):
    """Check a single chemical by CAS number."""
    print(f"\n🔍 Checking chemical with CAS: {cas_number}")
    
    chemical = db.get_chemical_by_cas(cas_number)
    if not chemical:
        print(f"❌ Chemical not found with CAS: {cas_number}")
        print("   Use --import-csv to add chemicals first")
        sys.exit(1)
    
    result = scheduler.check_single_chemical(chemical.id)
    
    print(f"\n📋 {result['chemical_name']} ({result['cas_number']})")
    
    if result.get('error'):
        print(f"   ❌ Error: {result['error']}")
    elif result.get('is_updated'):
        print("   ✅ Updated! New version downloaded.")
        if result.get('changes'):
            print("   Changes detected:")
            for change in result['changes']:
                print(f"      [{change['severity']}] {change['section']}")
                print(f"         {change['summary']}")
    else:
        print("   ℹ️ No updates found")


def test_email():
    """Send a test email."""
    print("\n📧 Sending test email...")
    
    if not email_service.is_configured():
        print("❌ Email not configured!")
        print("   Set GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD in .env")
        sys.exit(1)
    
    success = email_service.send_test_email()
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email. Check your credentials.")


def start_scheduler():
    """Start the background scheduler."""
    print("\n⏰ Starting SDS Auto-Updater Scheduler...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped.")
        scheduler.stop()


def show_stats():
    """Show database statistics."""
    stats = db.get_statistics()

    print("\n📊 SDS Auto-Updater Statistics")
    print("=" * 40)
    print(f"   Total Chemicals:     {stats['total_chemicals']}")
    print(f"   SDS Versions:        {stats['total_sds_versions']}")
    print(f"   Total Changes:       {stats['total_changes']}")
    print(f"   Unreviewed Changes:  {stats['unreviewed_changes']}")
    print(f"   Critical Changes:    {stats['critical_changes']}")
    print("=" * 40)


def health_check():
    """Run system health check."""
    print("\n🏥 Running System Health Check...")
    print("=" * 50)

    results = health_checker.run_full_health_check()

    # Overall status
    status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}
    print(f"\nOverall Status: {status_emoji.get(results['overall_status'], '❓')} {results['overall_status'].upper()}")

    # Database
    print(f"\n📁 Database: {status_emoji.get(results['database']['status'], '❓')}")
    if results['database']['status'] == 'healthy':
        stats = results['database']['statistics']
        print(f"   Chemicals: {stats['total_chemicals']}")
        print(f"   SDS Versions: {stats['total_sds_versions']}")
    elif 'message' in results['database']:
        print(f"   Error: {results['database']['message']}")

    # Storage
    print(f"\n💾 Storage: {status_emoji.get(results['storage']['status'], '❓')}")
    if results['storage']['status'] == 'healthy':
        print(f"   PDF Files: {results['storage']['pdf_count']}")
        print(f"   Total Size: {results['storage']['total_size_mb']} MB")
        print(f"   Disk Free: {results['storage']['disk_free_gb']} GB")

    # API Configuration
    print(f"\n🔑 API Configuration: {status_emoji.get(results['api_configuration']['status'], '❓')}")
    for api, info in results['api_configuration']['checks'].items():
        status = "✅" if info['configured'] else ("❌" if info['required'] else "⚠️")
        print(f"   {api}: {status} {info['status']}")

    # System Resources
    print(f"\n💻 System Resources: {status_emoji.get(results['system_resources']['status'], '❓')}")
    if results['system_resources']['status'] == 'healthy':
        print(f"   CPU: {results['system_resources']['cpu_percent']}%")
        print(f"   Memory: {results['system_resources']['memory_percent']}%")
        print(f"   Available RAM: {results['system_resources']['memory_available_gb']} GB")

    print("=" * 50)


def create_backup():
    """Create database backup."""
    print("\n💾 Creating database backup...")
    backup_path = backup_manager.create_backup()

    if backup_path:
        print(f"✅ Backup created successfully: {backup_path}")
    else:
        print("❌ Failed to create backup")


def list_backups():
    """List all database backups."""
    print("\n📦 Available Backups:")
    print("=" * 70)

    backups = backup_manager.list_backups()

    if not backups:
        print("   No backups found")
    else:
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup['filename']}")
            print(f"   Created: {backup['created_str']}")
            print(f"   Size: {backup['size_mb']} MB")
            print()

    print("=" * 70)


def restore_backup(backup_file: str):
    """Restore database from backup."""
    from pathlib import Path

    backup_path = Path(backup_file)
    if not backup_path.is_absolute():
        backup_path = backup_manager.backup_dir / backup_file

    print(f"\n⚠️  Restoring database from: {backup_path}")
    print("   This will overwrite the current database!")

    success = backup_manager.restore_backup(backup_path)

    if success:
        print("✅ Database restored successfully")
    else:
        print("❌ Failed to restore database")


def main():
    parser = argparse.ArgumentParser(
        description="SDS Auto-Updater - Automated Safety Data Sheet monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--import-csv",
        metavar="FILE",
        help="Import chemicals from a CSV file"
    )
    
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check all chemicals for SDS updates"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check a single chemical (use with --cas)"
    )
    
    parser.add_argument(
        "--cas",
        metavar="NUMBER",
        help="CAS number of chemical to check"
    )
    
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send a test email to verify configuration"
    )
    
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Start the background scheduler"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )
    
    parser.add_argument(
        "--weekly-digest",
        action="store_true",
        help="Send weekly digest email now"
    )

    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run system health check"
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create database backup"
    )

    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List all database backups"
    )

    parser.add_argument(
        "--restore-backup",
        metavar="FILE",
        help="Restore database from backup file"
    )

    args = parser.parse_args()
    
    # Validate configuration
    print("\n🔧 SDS Auto-Updater")
    print("=" * 40)
    validate_config()
    
    # Execute command
    if args.import_csv:
        import_chemicals(args.import_csv)
    elif args.check_all:
        check_all_chemicals()
    elif args.check and args.cas:
        check_single_chemical(args.cas)
    elif args.test_email:
        test_email()
    elif args.scheduler:
        start_scheduler()
    elif args.stats:
        show_stats()
    elif args.weekly_digest:
        print("\n📧 Sending weekly digest...")
        success = email_service.send_weekly_digest()
        print("✅ Sent!" if success else "❌ Failed")
    elif args.health_check:
        health_check()
    elif args.backup:
        create_backup()
    elif args.list_backups:
        list_backups()
    elif args.restore_backup:
        restore_backup(args.restore_backup)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
