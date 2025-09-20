#!/usr/bin/env python3
"""
LM Studio Context Size Benchmark
Measures generation speed and prompt processing performance across different context sizes
"""

import json
import time
import csv
import os
from datetime import datetime
from benchmark import LMStudioBenchmark, BenchmarkResult
from book_loader import BookChunkLoader
from config_loader import load_config, print_config_summary, validate_config
from dataclasses import asdict

class ContextSizeBenchmark:
    def __init__(self, config_path="config.yaml"):
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.benchmark = LMStudioBenchmark(self.config.api_url)
        self.book_loader = BookChunkLoader(self.config.book_path)
        
        # Create timestamped results directory
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = f"{self.config.results_dir}/run_{self.run_timestamp}"
        os.makedirs(self.results_dir, exist_ok=True)
        
        print(f"📁 Results will be saved to: {self.results_dir}")
        
    def generate_realistic_prompt(self, target_tokens: int) -> str:
        """Generate a realistic prompt using book content"""
        # Get book chunk of the target size
        book_chunk = self.book_loader.get_chunk_by_tokens(target_tokens)
        
        # Create analysis prompt
        prompt = self.book_loader.create_analysis_prompt(book_chunk)
        
        return prompt
    
    def run_model_benchmark(self, model_info: dict, save_prefix: str = None):
        """Run benchmark for a single model with incremental saving"""
        model_name = model_info['name']
        if not save_prefix:
            save_prefix = model_name.replace('/', '_').replace('-', '_')
        
        print(f"\n🚀 Starting benchmark for {model_name}")
        print(f"Description: {model_info.get('description', 'No description')}")
        print(f"Context sizes: {self.config.context_sizes}")
        print("=" * 80)
        
        results = []
        
        for context_size in self.config.context_sizes:
            print(f"\n📊 Testing {model_name} with {context_size:,} tokens...")
            
            try:
                # Generate realistic prompt
                prompt = self.generate_realistic_prompt(context_size)
                
                # Make request
                result = self.benchmark.make_completion_request(
                    prompt, model_name, max_tokens=self.config.max_tokens
                )
                
                if result:
                    benchmark_result = BenchmarkResult(
                        model_name=model_name,
                        context_size=context_size,
                        prompt_tokens=result['prompt_tokens'],
                        completion_tokens=result['completion_tokens'],
                        total_tokens=result['total_tokens'],
                        time_to_first_token=result['time_to_first_token'],
                        generation_time=result['generation_time'],
                        total_time=result['total_time'],
                        tokens_per_second=result['tokens_per_second'],
                        prompt_processing_speed=result['prompt_processing_speed'],
                        system_info=f"{self.config.system_name} ({self.config.system_notes})",
                        timestamp=datetime.now().isoformat()
                    )
                    
                    results.append(benchmark_result)
                    
                    print(f"  ✅ Prompt tokens: {result['prompt_tokens']:,}")
                    print(f"  ⏱️  TTFT: {result['time_to_first_token']:.3f}s")
                    print(f"  🚀 Gen speed: {result['tokens_per_second']:.2f} tok/s")
                    print(f"  📈 Prompt speed: {result['prompt_processing_speed']:.2f} tok/s")
                    
                    # Save updated results to single CSV file
                    results_file = os.path.join(self.results_dir, f"{save_prefix}_results.csv")
                    self.save_incremental_results(results, results_file)
                    
                else:
                    print(f"  ❌ Failed to get result for {context_size:,} tokens")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error at {context_size:,} tokens: {e}")
                # Save what we have so far
                if results:
                    results_file = os.path.join(self.results_dir, f"{save_prefix}_results.csv")
                    self.save_incremental_results(results, results_file)
                    print(f"  💾 Partial results saved to: {results_file}")
                break
            
            # Small delay between requests
            time.sleep(self.config.delay_between_requests)
        
        # Results are already saved incrementally
        if results:
            results_file = os.path.join(self.results_dir, f"{save_prefix}_results.csv")
            print(f"\n✅ {model_name} benchmark completed with {len(results)} data points")
            print(f"💾 Results saved to: {results_file}")
            return results
        else:
            print(f"\n❌ No results collected for {model_name}")
            return []
    
    def save_incremental_results(self, results, filename):
        """Save results to CSV file"""
        with open(filename, 'w', newline='') as csvfile:
            if results:
                fieldnames = list(asdict(results[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for result in results:
                    writer.writerow(asdict(result))
    
    def create_run_summary(self, all_results):
        """Create a summary of the entire benchmark run"""
        summary_file = os.path.join(self.results_dir, "run_summary.txt")
        
        with open(summary_file, 'w') as f:
            f.write(f"LM Studio Context Size Benchmark Run\n")
            f.write(f"{'='*50}\n")
            f.write(f"Timestamp: {self.run_timestamp}\n")
            f.write(f"System: {self.config.system_name}\n")
            f.write(f"Notes: {self.config.system_notes}\n")
            f.write(f"Models tested: {len(all_results)}\n")
            f.write(f"API URL: {self.config.api_url}\n")
            f.write(f"Context sizes: {self.config.context_sizes}\n\n")
            
            for model_name, results in all_results.items():
                f.write(f"Model: {model_name}\n")
                f.write(f"{'-'*30}\n")
                f.write(f"Data points collected: {len(results)}\n")
                
                if results:
                    first = results[0]
                    last = results[-1]
                    
                    f.write(f"Context range: {first.context_size:,} - {last.context_size:,} tokens\n")
                    f.write(f"Generation speed: {first.tokens_per_second:.1f} → {last.tokens_per_second:.1f} tok/s\n")
                    f.write(f"TTFT: {first.time_to_first_token:.2f}s → {last.time_to_first_token:.2f}s\n")
                    
                    # Calculate performance drop
                    gen_drop = ((first.tokens_per_second - last.tokens_per_second) / first.tokens_per_second) * 100
                    ttft_increase = ((last.time_to_first_token - first.time_to_first_token) / first.time_to_first_token) * 100
                    
                    f.write(f"Performance degradation: {gen_drop:.1f}% speed drop, {ttft_increase:.1f}% TTFT increase\n")
                
                f.write(f"\n")
            
            f.write(f"Files generated:\n")
            f.write(f"- CSV results files for each model\n")
            f.write(f"- Performance charts (if generated)\n")
            f.write(f"- This summary file\n")
        
        print(f"📋 Run summary saved to: {summary_file}")
    
    def run_all_models_benchmark(self):
        """Run benchmark on all configured models"""
        available_models = self.benchmark.get_available_models()
        print(f"Available models: {available_models}")
        
        all_results = {}
        
        for model_info in self.config.models:
            model_name = model_info['name']
            
            if model_name in available_models:
                print(f"\n{'='*80}")
                print(f"BENCHMARKING: {model_name}")
                print(f"DESCRIPTION: {model_info.get('description', 'No description')}")
                print(f"{'='*80}")
                
                results = self.run_model_benchmark(model_info)
                
                if results:
                    all_results[model_name] = results
                    print(f"✅ Completed {model_name}: {len(results)} data points")
                else:
                    print(f"❌ Failed {model_name}: No data collected")
                
                # Wait between models
                print(f"\n⏳ Waiting {self.config.delay_between_models} seconds before next model...")
                time.sleep(self.config.delay_between_models)
                
            else:
                print(f"⚠️  Model {model_name} not available, skipping...")
        
        # Create run summary
        if all_results and self.config.save_summary:
            self.create_run_summary(all_results)
        
        return all_results

def main():
    try:
        # Load and validate configuration
        config = load_config()
        print_config_summary(config)
        
        issues = validate_config(config)
        if issues:
            print("❌ Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")
            return
        
        print("✅ Configuration is valid!")
        print("\n" + "=" * 50)
        
        # Run benchmark
        benchmark = ContextSizeBenchmark()
        results = benchmark.run_all_models_benchmark()
        
        print(f"\n🎉 Benchmark completed!")
        print(f"Models tested: {len(results)}")
        
        for model, model_results in results.items():
            print(f"  {model}: {len(model_results)} data points")
        
        print(f"\n💾 Results saved to: {benchmark.results_dir}")
        if config.create_charts:
            print(f"📊 Run 'python create_final_charts.py' to generate comparison charts!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    main()
