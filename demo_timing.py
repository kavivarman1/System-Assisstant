#!/usr/bin/env python3
"""
Simple demonstration of timing functionality integration.
This script shows how the enhanced system can handle timing-based file operations.
"""

import json
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from operation_executor_window import parse_time_input, execute_operation_with_timing

def demo_timing_parsing():
    """Demonstrate timing parsing functionality."""
    print("🕒 Timing Parsing Demonstration")
    print("=" * 40)
    
    test_timings = [
        "today",
        "yesterday", 
        "last week",
        "last month",
        "this morning",
        "this afternoon",
        "this evening",
        "recent",
        "old",
        "new",
        "from June 2024 to July 2024",
        "files on 8 January 2025",
        "all files on 8th 2024",
        "files created in December 2024",
        "files from 5 days ago",
        "files modified in the last 2 hours"
    ]
    
    for timing in test_timings:
        print(f"\n📝 Testing: '{timing}'")
        result = parse_time_input(timing)
        
        if isinstance(result, tuple) and all(isinstance(i, datetime) for i in result):
            start, end = result
            if start and end:
                print(f"   ✅ Parsed: {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"   ❌ Invalid date range")
        elif isinstance(result, list):
            print(f"   ✅ Parsed: {len(result)} date ranges")
            for i, (start, end) in enumerate(result[:3], 1):  # Show first 3
                if start and end:
                    print(f"      Range {i}: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
                else:
                    print(f"      Range {i}: Invalid date range")
            if len(result) > 3:
                print(f"      ... and {len(result) - 3} more ranges")
        else:
            print(f"   ❌ Failed to parse timing")

def demo_operation_with_timing():
    """Demonstrate file operations with timing."""
    print("\n🔍 File Operations with Timing Demonstration")
    print("=" * 50)
    
    # Test cases with timing
    test_cases = [
        {
            "operation": "search",
            "filename": "*.txt",
            "timing": "today",
            "description": "Search for text files from today"
        },
        {
            "operation": "search", 
            "filename": "report",
            "timing": "yesterday",
            "description": "Search for files named 'report' from yesterday"
        },
        {
            "operation": "search",
            "filename": ".py",
            "timing": "last week", 
            "description": "Search for Python files from last week"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Operation: {test_case['operation']}")
        print(f"   Filename: {test_case['filename']}")
        print(f"   Timing: {test_case['timing']}")
        
        try:
            result = execute_operation_with_timing(
                test_case['operation'],
                test_case['filename'], 
                test_case['timing']
            )
            
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            if result.get('matches'):
                print(f"   Matches found: {len(result['matches'])}")
                for j, match in enumerate(result['matches'][:3], 1):
                    print(f"      {j}. {match}")
                if len(result['matches']) > 3:
                    print(f"      ... and {len(result['matches']) - 3} more")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_natural_language_processing():
    """Demonstrate how natural language would be processed."""
    print("\n🤖 Natural Language Processing Simulation")
    print("=" * 45)
    
    # Simulate what Gemini would extract from natural language
    natural_requests = [
        "Search for all PDF files from today",
        "Open the report.txt file I created yesterday", 
        "Find all documents modified last week",
        "Show me files from this morning",
        "Find recent Python files"
    ]
    
    # Simulated Gemini responses
    gemini_responses = [
        [{"operation": "search", "filename": "*.pdf", "timing": "today"}],
        [{"operation": "open", "filename": "report.txt", "timing": "yesterday"}],
        [{"operation": "search", "filename": "documents", "timing": "last week"}],
        [{"operation": "search", "filename": "*", "timing": "this morning"}],
        [{"operation": "search", "filename": "*.py", "timing": "recent"}]
    ]
    
    for i, (request, response) in enumerate(zip(natural_requests, gemini_responses), 1):
        print(f"\n💬 User: {request}")
        print(f"🤖 Gemini extracted: {json.dumps(response, indent=2)}")
        
        # Process each operation
        for operation_data in response:
            operation = operation_data["operation"]
            filename = operation_data["filename"]
            timing = operation_data.get("timing")
            
            print(f"   📂 Processing: {operation} '{filename}' with timing '{timing}'")
            
            try:
                result = execute_operation_with_timing(operation, filename, timing)
                print(f"   ✅ Result: {result.get('status')} - {result.get('message', '')}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

def main():
    """Main demonstration function."""
    print("🚀 Timing Integration Demonstration")
    print("=" * 40)
    print("This demo shows how the enhanced system handles timing-based file operations.")
    print()
    
    # Run demonstrations
    demo_timing_parsing()
    demo_operation_with_timing() 
    demo_natural_language_processing()
    
    print("\n" + "=" * 40)
    print("✅ Demonstration completed!")
    print("\nTo test with real Gemini AI integration, run:")
    print("python test_timing_integration.py")

if __name__ == "__main__":
    main() 