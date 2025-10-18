#!/usr/bin/env python3
"""
Example usage of the Orphaned Data Audit Tool

This script demonstrates how to use the audit tool programmatically
and shows different scenarios for cleanup operations.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the auditor
from scripts.cleanup.orphans_audit import OrphanedDataAuditor


def demonstrate_basic_audit():
    """Demonstrate basic audit functionality."""
    print("=== Basic Audit Demo ===")
    
    # Create auditor with default settings (dry-run, 30 days)
    auditor = OrphanedDataAuditor(
        dry_run=True,
        days_threshold=30,
        verbose=True
    )
    
    # Run the audit
    results = auditor.run_audit()
    
    # Export report
    report_path = auditor.export_report()
    
    print(f"Audit completed! Report saved to: {report_path}")
    print(f"Total orphaned items found: {results['summary']['total_orphaned_items']}")
    
    return results


def demonstrate_custom_threshold():
    """Demonstrate audit with custom threshold."""
    print("\n=== Custom Threshold Demo ===")
    
    # Create auditor with 60-day threshold
    auditor = OrphanedDataAuditor(
        dry_run=True,
        days_threshold=60,
        verbose=False
    )
    
    # Run the audit
    results = auditor.run_audit()
    
    print(f"Audit with 60-day threshold completed!")
    print(f"Total orphaned items found: {results['summary']['total_orphaned_items']}")
    
    return results


def demonstrate_report_analysis():
    """Demonstrate how to analyze the audit report."""
    print("\n=== Report Analysis Demo ===")
    
    # Run audit first
    auditor = OrphanedDataAuditor(dry_run=True, verbose=False)
    results = auditor.run_audit()
    report_path = auditor.export_report()
    
    # Load and analyze the report
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    print("Report Analysis:")
    print(f"  Timestamp: {report_data['timestamp']}")
    print(f"  Dry run: {report_data['dry_run']}")
    print(f"  Days threshold: {report_data['days_threshold']}")
    print(f"  Cutoff date: {report_data['cutoff_date']}")
    
    summary = report_data['summary']
    print(f"\nSummary:")
    print(f"  Total orphaned items: {summary['total_orphaned_items']}")
    print(f"  Orphaned blobs: {summary['orphaned_blobs']}")
    print(f"  Orphaned documents: {summary['orphaned_documents']}")
    print(f"  Orphaned contacts: {summary['orphaned_contacts']}")
    print(f"  Orphaned Redis keys: {summary['orphaned_redis_keys']}")
    print(f"  Orphaned search documents: {summary['orphaned_search_documents']}")
    
    # Analyze details if any orphaned items found
    details = report_data['details']
    if summary['total_orphaned_items'] > 0:
        print(f"\nDetailed Analysis:")
        
        if details['orphaned_blobs']:
            print(f"  Blobs to clean:")
            for blob in details['orphaned_blobs'][:3]:  # Show first 3
                print(f"    - {blob['name']} ({blob['size']} bytes)")
        
        if details['orphaned_documents']:
            print(f"  Documents to clean:")
            for doc in details['orphaned_documents'][:3]:  # Show first 3
                print(f"    - {doc['title']} (ID: {doc['id']})")
        
        if details['orphaned_contacts']:
            print(f"  Contacts to clean:")
            for contact in details['orphaned_contacts'][:3]:  # Show first 3
                print(f"    - {contact['name']} (ID: {contact['id']})")
    
    return report_data


def demonstrate_safe_cleanup_preparation():
    """Demonstrate how to prepare for safe cleanup."""
    print("\n=== Safe Cleanup Preparation Demo ===")
    
    # Step 1: Run initial audit
    print("Step 1: Running initial audit...")
    auditor = OrphanedDataAuditor(dry_run=True, verbose=True)
    initial_results = auditor.run_audit()
    
    if initial_results['summary']['total_orphaned_items'] == 0:
        print("No orphaned items found. No cleanup needed.")
        return
    
    # Step 2: Analyze what would be cleaned
    print(f"\nStep 2: Analysis of {initial_results['summary']['total_orphaned_items']} orphaned items:")
    
    details = initial_results['details']
    
    # Calculate potential space savings
    total_size = sum(blob.get('size', 0) for blob in details['orphaned_blobs'])
    print(f"  Potential space savings: {total_size / (1024*1024):.2f} MB")
    
    # Show breakdown by type
    for data_type, items in details.items():
        if items:
            print(f"  {data_type}: {len(items)} items")
    
    # Step 3: Show what would be deleted (first few items)
    print(f"\nStep 3: Sample items that would be deleted:")
    
    for data_type, items in details.items():
        if items:
            print(f"\n  {data_type.upper()}:")
            for item in items[:2]:  # Show first 2 items
                if data_type == 'orphaned_blobs':
                    print(f"    - {item['name']} ({item['size']} bytes)")
                elif data_type == 'orphaned_documents':
                    print(f"    - {item['title']} (ID: {item['id']})")
                elif data_type == 'orphaned_contacts':
                    print(f"    - {item['name']} (ID: {item['id']})")
                elif data_type == 'orphaned_redis_keys':
                    print(f"    - {item['key']}")
    
    # Step 4: Export detailed report for manual review
    report_path = auditor.export_report("logs/cleanup_preparation_report.json")
    print(f"\nStep 4: Detailed report exported to: {report_path}")
    print("Review this report before proceeding with actual cleanup.")
    
    return initial_results


def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n=== Error Handling Demo ===")
    
    # Test with invalid configuration
    print("Testing error handling with limited configuration...")
    
    try:
        auditor = OrphanedDataAuditor(dry_run=True, verbose=True)
        results = auditor.run_audit()
        
        print("Audit completed successfully despite configuration issues.")
        print("The script handles missing services gracefully.")
        
    except Exception as e:
        print(f"Error during audit: {e}")
    
    return True


def main():
    """Main demonstration function."""
    print("Orphaned Data Audit Tool - Usage Examples")
    print("=" * 50)
    
    try:
        # Run all demonstrations
        demonstrate_basic_audit()
        demonstrate_custom_threshold()
        demonstrate_report_analysis()
        demonstrate_safe_cleanup_preparation()
        demonstrate_error_handling()
        
        print("\n" + "=" * 50)
        print("All demonstrations completed successfully!")
        print("\nNext steps:")
        print("1. Review the generated reports in the logs/ directory")
        print("2. Follow the cleanup plan in docs/diagnostico/cleanup_plan.md")
        print("3. Run actual cleanup only after thorough review")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
