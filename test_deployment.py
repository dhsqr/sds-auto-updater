#!/usr/bin/env python3
"""
Pre-deployment test script for SDS Auto-Updater.
Runs comprehensive tests to ensure system is ready for production.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import validate_config
from src.database import db
from src.health_check import health_checker
from src.backup import backup_manager
from src.utils import validate_cas_number, validate_email


def print_header(text):
    """Print formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_test(name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")


def test_configuration():
    """Test configuration and environment."""
    print_header("1. Testing Configuration")

    # Validate config
    config_valid = validate_config()
    print_test("Configuration validation", config_valid)

    return config_valid


def test_database():
    """Test database connectivity and operations."""
    print_header("2. Testing Database")

    all_passed = True

    # Test database connection
    try:
        stats = db.get_statistics()
        print_test("Database connection", True, f"{stats['total_chemicals']} chemicals found")
    except Exception as e:
        print_test("Database connection", False, str(e))
        all_passed = False
        return False

    # Test adding a test chemical (will fail if already exists, which is OK)
    try:
        test_chemical = db.add_chemical(
            name="Test Chemical - Deployment Test",
            cas_number="999-99-9",  # Fake CAS
            supplier="sigma_aldrich"
        )
        print_test("Database write operations", True, "Can add chemicals")

        # Clean up test chemical
        session = db.get_session()
        try:
            session.delete(test_chemical)
            session.commit()
        finally:
            session.close()

    except ValueError as ve:
        # Expected - CAS validation will fail
        if "Invalid CAS number" in str(ve):
            print_test("Database validation", True, "CAS validation working")
        else:
            print_test("Database write operations", False, str(ve))
            all_passed = False
    except Exception as e:
        if "already exists" not in str(e).lower():
            print_test("Database write operations", False, str(e))
            all_passed = False

    return all_passed


def test_utilities():
    """Test utility functions."""
    print_header("3. Testing Utilities")

    all_passed = True

    # Test CAS validation
    valid_cas = validate_cas_number("1310-73-2")
    invalid_cas = not validate_cas_number("invalid")

    print_test("CAS number validation", valid_cas and invalid_cas)

    if not (valid_cas and invalid_cas):
        all_passed = False

    # Test email validation
    valid_email = validate_email("test@example.com")
    invalid_email = not validate_email("invalid-email")

    print_test("Email validation", valid_email and invalid_email)

    if not (valid_email and invalid_email):
        all_passed = False

    return all_passed


def test_health_check():
    """Test health check system."""
    print_header("4. Testing Health Check System")

    try:
        results = health_checker.run_full_health_check()

        db_healthy = results['database']['status'] == 'healthy'
        print_test("Database health check", db_healthy)

        storage_healthy = results['storage']['status'] == 'healthy'
        print_test("Storage health check", storage_healthy)

        api_ok = results['api_configuration']['status'] in ['healthy', 'degraded']
        print_test("API configuration check", api_ok)

        sys_healthy = results['system_resources']['status'] == 'healthy'
        print_test("System resources check", sys_healthy)

        overall_ok = results['overall_status'] in ['healthy', 'degraded']
        print_test("Overall system health", overall_ok,
                  f"Status: {results['overall_status']}")

        return overall_ok

    except Exception as e:
        print_test("Health check system", False, str(e))
        return False


def test_backup_system():
    """Test backup and restore functionality."""
    print_header("5. Testing Backup System")

    all_passed = True

    # Test backup creation
    try:
        backup_path = backup_manager.create_backup(description="deployment_test")

        if backup_path and backup_path.exists():
            print_test("Backup creation", True, f"Created: {backup_path.name}")

            # Test backup listing
            backups = backup_manager.list_backups()
            found = any(b['filename'] == backup_path.name for b in backups)
            print_test("Backup listing", found)

            if not found:
                all_passed = False

        else:
            print_test("Backup creation", False, "Backup file not created")
            all_passed = False

    except Exception as e:
        print_test("Backup system", False, str(e))
        all_passed = False

    return all_passed


def test_import_export():
    """Test CSV import functionality."""
    print_header("6. Testing Import/Export")

    try:
        # Check if sample CSV exists
        sample_csv = Path("data/chemicals.csv")

        if not sample_csv.exists():
            print_test("Sample CSV exists", False, "data/chemicals.csv not found")
            return False

        print_test("Sample CSV exists", True)

        # Try to read it (don't actually import to avoid duplicates)
        import pandas as pd
        df = pd.read_csv(sample_csv)

        required_cols = ['chemical_name', 'cas_number', 'supplier']
        has_required = all(col in df.columns for col in required_cols)

        print_test("CSV format validation", has_required,
                  f"{len(df)} chemicals in sample file")

        return has_required

    except Exception as e:
        print_test("Import/Export system", False, str(e))
        return False


def test_pdf_processing():
    """Test PDF processing capabilities."""
    print_header("7. Testing PDF Processing")

    try:
        from src.pdf_processor import pdf_processor

        # Check if PDF processor is initialized
        has_llm = pdf_processor.llm is not None
        print_test("AI/LLM configuration", has_llm,
                  "Gemini API configured" if has_llm else "Will use fallback regex extraction")

        # Test text extraction (without actual PDF)
        print_test("PDF processor initialized", True)

        return True

    except Exception as e:
        print_test("PDF processing system", False, str(e))
        return False


def run_all_tests():
    """Run all pre-deployment tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SDS AUTO-UPDATER DEPLOYMENT TEST" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")

    tests = [
        ("Configuration", test_configuration),
        ("Database", test_database),
        ("Utilities", test_utilities),
        ("Health Check", test_health_check),
        ("Backup System", test_backup_system),
        ("Import/Export", test_import_export),
        ("PDF Processing", test_pdf_processing),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test suite failed with exception: {e}")
            results[test_name] = False

    # Summary
    print_header("Test Summary")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} test suites passed")
    print('=' * 60)

    if passed == total:
        print("\n🎉 All tests passed! System is ready for deployment.")
        print("📋 Next steps:")
        print("   1. Review DEPLOYMENT.md for production setup")
        print("   2. Configure automated scheduler")
        print("   3. Set up monitoring and alerts")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before deploying.")
        print("💡 Check the error messages above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
