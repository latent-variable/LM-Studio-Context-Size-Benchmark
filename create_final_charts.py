#!/usr/bin/env python3
"""
Create comparison charts from context size benchmark results
"""

import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def load_all_model_results(results_dir=None):
    """Load results from all model CSV files"""
    results = {}
    resolved_dir = results_dir

    if resolved_dir is None:
        flat_files = glob.glob(os.path.join("results", "*_results.csv"))
        if flat_files:
            resolved_dir = "results"
            print(f"📁 Loading results from: {resolved_dir}")
        else:
            run_dirs = glob.glob(os.path.join("results", "run_*"))
            if run_dirs:
                resolved_dir = max(run_dirs)
                print(f"📁 Loading results from: {resolved_dir}")

    if resolved_dir is None:
        print("❌ No results files found!")
        return results, None

    csv_pattern = os.path.join(resolved_dir, "*_results.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        print(f"❌ No results files found in {resolved_dir}")
        return results, resolved_dir

    for csv_file in csv_files:
        print(f"📊 Loading {os.path.basename(csv_file)}")
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            continue

        if 'model_name' in df:
            names = df['model_name'].dropna()
            model_name = str(names.iloc[0]).strip() if not names.empty else None
        else:
            model_name = None

        if not model_name:
            # Fallback to filename-derived name
            base = os.path.basename(csv_file).replace('_results.csv', '')
            model_name = base.replace('_', '/')

        results[model_name] = df

    return results, resolved_dir

def create_comparison_charts(results, results_dir):
    """Create comparison charts showing performance vs context size"""
    
    if not results:
        print("❌ No results to plot")
        return
    
    # Set up the styling
    plt.style.use('default')
    
    # Colors for each model
    colors = {
        'qwen/qwen3-next-80b': '#d62728',     # Red
        'openai/gpt-oss-20b': '#ff7f0e',      # Orange  
        'openai/gpt-oss-120b': '#2ca02c',     # Green
        'unsloth/gpt-oss-120b': '#2ca02c',    # Green (alternative name)
        'unsloth/gpt-oss-20b': '#ff7f0e',     # Orange (alternative name)
    }
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('LM Studio Benchmark - M3 Max MacBook Pro 128GB', fontsize=16, fontweight='bold')
    
    # Chart 1: Generation vs Context Size
    ax1.set_title('Generation vs Context Size', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Context Size', fontsize=12)
    ax1.set_ylabel('TPS (Generation)', fontsize=12)
    
    max_gen_speed = 0
    max_context = 0
    
    for model_name, df in results.items():
        if len(df) == 0:
            continue
        df = df.sort_values('context_size')

        context_sizes = df['context_size'].values
        gen_speeds = df['tokens_per_second'].values
        
        # Get color for this model
        color = colors.get(model_name, '#1f77b4')  # Default blue
        
        # Clean model name for legend
        clean_name = model_name.replace('/', '-').replace('openai-', '').replace('unsloth-', '')
        
        ax1.plot(context_sizes, gen_speeds,
                color=color,
                linewidth=2,
                marker='o',
                markersize=4,
                label=clean_name)
        
        if len(gen_speeds) > 0:
            max_gen_speed = max(max_gen_speed, max(gen_speeds))
        if len(context_sizes) > 0:
            max_context = max(max_context, max(context_sizes))

    if max_context == 0:
        max_context = 1
    if max_gen_speed == 0:
        max_gen_speed = 1

    ax1.set_xlim(0, max_context * 1.05)
    ax1.set_ylim(0, max_gen_speed * 1.1)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # Format x-axis to show context sizes nicely
    if max_context >= 100000:
        ax1.set_xticks([0, 21026, 42052, 63079, 84105, 105131])
        ax1.set_xticklabels(['0', '21026', '42052', '63079', '84105', '105131'])
    else:
        step = max(1, max_context // 5)
        ticks = list(range(0, max_context + step, step))
        ax1.set_xticks(ticks)
        ax1.set_xticklabels([f'{t:,}' for t in ticks])
    
    # Chart 2: Prompt Processing vs Context Size  
    ax2.set_title('Prompt Processing vs Context Size', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Context Size', fontsize=12)
    ax2.set_ylabel('TPS (Prompt Processing)', fontsize=12)
    
    max_prompt_speed = 0
    
    for model_name, df in results.items():
        if len(df) == 0:
            continue
        df = df.sort_values('context_size')

        context_sizes = df['context_size'].values
        prompt_speeds = df['prompt_processing_speed'].values
        
        color = colors.get(model_name, '#1f77b4')
        clean_name = model_name.replace('/', '-').replace('openai-', '').replace('unsloth-', '')
        
        ax2.plot(context_sizes, prompt_speeds,
                color=color,
                linewidth=2,
                marker='o',
                markersize=4,
                label=clean_name)
        
        if len(prompt_speeds) > 0:
            max_prompt_speed = max(max_prompt_speed, max(prompt_speeds))

    if max_prompt_speed == 0:
        max_prompt_speed = 1

    ax2.set_xlim(0, max_context * 1.05)
    ax2.set_ylim(0, max_prompt_speed * 1.1)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    # Format x-axis same as first chart
    if max_context >= 100000:
        ax2.set_xticks([0, 21026, 42052, 63079, 84105, 105131])
        ax2.set_xticklabels(['0', '21026', '42052', '63079', '84105', '105131'])
    else:
        step = max(1, max_context // 5)
        ticks = list(range(0, max_context + step, step))
        ax2.set_xticks(ticks)
        ax2.set_xticklabels([f'{t:,}' for t in ticks])
    
    plt.tight_layout()

    chart_path = os.path.join(results_dir, 'benchmark_comparison_charts.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')

    if os.environ.get('BENCHMARK_SHOW_CHARTS') == '1':
        plt.show()
    else:
        plt.close(fig)
    
    print(f"📊 Benchmark results chart saved to: {chart_path}")
    
    # Print performance summary
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    for model_name, df in results.items():
        if len(df) == 0:
            continue
            
        print(f"\n{model_name}:")
        print("-" * len(model_name))
        
        # Performance at different context sizes
        key_contexts = [10000, 20000, 50000, 100000]
        for context in key_contexts:
            row = df[df['context_size'] == context]
            if not row.empty:
                gen_speed = row['tokens_per_second'].iloc[0]
                ttft = row['time_to_first_token'].iloc[0]
                prompt_speed = row['prompt_processing_speed'].iloc[0]
                print(f"  {context:>6,} tokens: {gen_speed:>5.1f} tok/s gen, {ttft:>6.2f}s TTFT, {prompt_speed:>6.1f} tok/s prompt")
        
        # Performance analysis
        if len(df) >= 2:
            first_gen = df['tokens_per_second'].iloc[0]
            last_gen = df['tokens_per_second'].iloc[-1]
            gen_drop = ((first_gen - last_gen) / first_gen) * 100
            
            first_ttft = df['time_to_first_token'].iloc[0]
            last_ttft = df['time_to_first_token'].iloc[-1]
            ttft_increase = ((last_ttft - first_ttft) / first_ttft) * 100
            
            print(f"  📊 Gen speed drop: {gen_drop:.1f}% ({first_gen:.1f} → {last_gen:.1f} tok/s)")
            print(f"  ⏱️  TTFT increase: {ttft_increase:.1f}% ({first_ttft:.2f}s → {last_ttft:.2f}s)")

def main():
    print("📊 Creating Context Size Benchmark Charts")
    print("=" * 50)
    
    # Load all results
    results, results_dir = load_all_model_results()
    
    if not results:
        print("❌ No benchmark results found!")
        print("Make sure to run the context size benchmark first:")
        print("  python smart_benchmark.py")
        return
    
    print(f"✅ Loaded results for {len(results)} models:")
    for model_name, df in results.items():
        print(f"  - {model_name}: {len(df)} data points")
    
    # Create comparison charts
    create_comparison_charts(results, results_dir)

if __name__ == "__main__":
    main()
