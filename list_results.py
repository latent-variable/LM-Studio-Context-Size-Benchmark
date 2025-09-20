#!/usr/bin/env python3
"""
List and manage benchmark results directories
"""

import os
import glob
from datetime import datetime

def list_results():
    """List all benchmark result directories"""
    results_dirs = glob.glob("results/run_*")
    
    if not results_dirs:
        print("📁 No benchmark results found.")
        print("Run 'python multi_model_benchmark.py' to create your first benchmark.")
        return
    
    # Sort by timestamp (newest first)
    results_dirs.sort(reverse=True)
    
    print("📊 Benchmark Results Directories:")
    print("=" * 50)
    
    for i, results_dir in enumerate(results_dirs):
        # Extract timestamp from directory name
        timestamp_str = results_dir.split('_', 2)[-1]  # Get everything after "run_"
        
        try:
            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_time = timestamp_str
        
        # Check what files are in the directory
        csv_files = glob.glob(os.path.join(results_dir, "*.csv"))
        chart_files = glob.glob(os.path.join(results_dir, "*.png"))
        summary_files = glob.glob(os.path.join(results_dir, "run_summary.txt"))
        
        # Count models (results CSV files)
        results_files = [f for f in csv_files if f.endswith('_results.csv')]
        model_count = len(results_files)
        
        status = "✅ Complete" if summary_files else "⚠️ Incomplete"
        
        print(f"{i+1:2d}. {os.path.basename(results_dir)}")
        print(f"    📅 Time: {formatted_time}")
        print(f"    📊 Models: {model_count}")
        print(f"    📄 Files: {len(csv_files)} CSV, {len(chart_files)} charts")
        print(f"    🎯 Status: {status}")
        print()
    
    return results_dirs

def show_run_details(run_dir):
    """Show detailed information about a specific run"""
    if not os.path.exists(run_dir):
        print(f"❌ Directory {run_dir} not found")
        return
    
    print(f"📁 Details for: {run_dir}")
    print("=" * 50)
    
    # Check for summary file
    summary_file = os.path.join(run_dir, "run_summary.txt")
    if os.path.exists(summary_file):
        print("📋 Run Summary:")
        with open(summary_file, 'r') as f:
            print(f.read())
    else:
        # Manual analysis
        csv_files = glob.glob(os.path.join(run_dir, "*.csv"))
        results_files = [f for f in csv_files if f.endswith('_results.csv')]
        
        print(f"📊 Files found: {len(csv_files)} total CSV files")
        print(f"🎯 Models completed: {len(results_files)}")
        
        for results_file in results_files:
            model_name = os.path.basename(results_file).replace('_results.csv', '').replace('_', '/')
            print(f"  - {model_name}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        # Show details for specific run
        run_arg = sys.argv[1]
        
        # If it's a number, use it as index
        if run_arg.isdigit():
            results_dirs = list_results()
            if results_dirs:
                idx = int(run_arg) - 1
                if 0 <= idx < len(results_dirs):
                    print()
                    show_run_details(results_dirs[idx])
                else:
                    print(f"❌ Invalid index {run_arg}. Use 1-{len(results_dirs)}")
        else:
            # Treat as directory name
            if not run_arg.startswith("results/"):
                run_arg = f"results/{run_arg}"
            show_run_details(run_arg)
    else:
        # List all results
        list_results()
        print("💡 Usage:")
        print("  python list_results.py           - List all results")
        print("  python list_results.py 1         - Show details for run #1")
        print("  python list_results.py run_...   - Show details for specific run")

if __name__ == "__main__":
    main()
