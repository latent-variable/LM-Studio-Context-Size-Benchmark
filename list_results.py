#!/usr/bin/env python3
"""
List and analyze benchmark results
"""

import os
import glob
import pandas as pd
from datetime import datetime

def list_results():
    """List benchmark results"""
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        print("📁 No benchmark results found.")
        print("Run 'python smart_benchmark.py' to create your first benchmark.")
        return
    
    # Look for result files
    csv_files = glob.glob(f"{results_dir}/*_results.csv")
    
    if not csv_files:
        print("📁 No benchmark results found.")
        print("Run 'python smart_benchmark.py' to create your first benchmark.")
        return
    
    print("📊 Benchmark Results:")
    print("=" * 50)
    
    total_experiments = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                model_name = df['model_name'].iloc[0]
                contexts = sorted(df['context_size'].unique())
                min_speed = df['tokens_per_second'].min()
                max_speed = df['tokens_per_second'].max()
                
                print(f"🤖 {model_name}")
                print(f"   Context sizes: {contexts}")
                print(f"   Speed range: {min_speed:.2f} - {max_speed:.2f} tok/s")
                print(f"   Data points: {len(df)}")
                print()
                
                total_experiments += len(df)
        except Exception as e:
            print(f"❌ Error reading {csv_file}: {e}")
    
    print(f"📈 Total experiments: {total_experiments}")
    
    # Check for charts and summary
    chart_file = os.path.join(results_dir, "benchmark_comparison_charts.png")
    summary_file = os.path.join(results_dir, "benchmark_summary.txt")
    
    if os.path.exists(chart_file):
        print(f"📊 Charts available: {chart_file}")
    
    if os.path.exists(summary_file):
        print(f"📄 Summary available: {summary_file}")

def show_details(identifier=None):
    """Show detailed results"""
    results_dir = "results"
    
    if not identifier:
        list_results()
        return
    
    # Load and display detailed results
    csv_files = glob.glob(f"{results_dir}/*_results.csv")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                model_name = df['model_name'].iloc[0]
                print(f"\n📊 Detailed Results for {model_name}:")
                print("=" * 60)
                
                for _, row in df.iterrows():
                    print(f"Context: {row['context_size']:,} tokens")
                    print(f"  TTFT: {row['time_to_first_token']:.3f}s")
                    print(f"  Generation: {row['tokens_per_second']:.2f} tok/s")
                    print(f"  Prompt processing: {row['prompt_processing_speed']:.2f} tok/s")
                    print(f"  Total time: {row['total_time']:.3f}s")
                    print()
        except Exception as e:
            print(f"❌ Error reading {csv_file}: {e}")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        show_details(sys.argv[1])
    else:
        list_results()
        print("\n💡 Usage:")
        print("  python list_results.py           - List all results")
        print("  python list_results.py details   - Show detailed results")

if __name__ == "__main__":
    main()