#!/usr/bin/env python3
"""
Smart benchmark runner with accurate timing and comprehensive logging
Only runs missing experiments instead of redoing everything
"""

import os
import glob
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from config_loader import load_config, print_config_summary, validate_config
from book_loader import BookChunkLoader
from logger import BenchmarkLogger
from accurate_timing import AccurateTiming

@dataclass
class BenchmarkResult:
    """Store results from a single benchmark run"""
    model_name: str
    context_size: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    time_to_first_token: float
    generation_time: float
    total_time: float
    tokens_per_second: float
    prompt_processing_speed: float
    system_info: str
    timestamp: str

class SmartBenchmark:
    def __init__(self, config_path="config.yaml"):
        self.config = load_config(config_path)
        self.existing_results = {}
        self.missing_work = {}
        
        # Use single working results directory
        self.results_dir = self.config.results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Setup logging
        self.logger = BenchmarkLogger(self.results_dir)
        self.logger.log_config(self.config)
        
        # Setup accurate timing
        self.timing = AccurateTiming(self.config.api_url, self.logger)
        
        # Setup book loader
        self.book_loader = BookChunkLoader(self.config.book_path)
        
    def scan_existing_results(self) -> Dict[str, pd.DataFrame]:
        """Scan all existing result files and load data"""
        self.logger.log_info("🔍 Scanning existing results...")
        
        existing_results = {}
        
        # Look in the single results directory
        results_pattern = f"{self.results_dir}/*_results.csv"
        result_files = glob.glob(results_pattern)
        
        self.logger.log_info(f"   Found {len(result_files)} result files")
        
        # Group by model and combine data
        model_data = {}
        
        for file_path in result_files:
            try:
                df = pd.read_csv(file_path)
                if len(df) > 0:
                    # Extract model name from filename
                    filename = os.path.basename(file_path)
                    model_name = filename.replace('_results.csv', '')
                    
                    if model_name not in model_data:
                        model_data[model_name] = []
                    model_data[model_name].append(df)
                    
                    self.logger.log_debug(f"   Loaded {len(df)} results from {filename}")
                    
            except Exception as e:
                self.logger.log_warning(f"Could not load {file_path}: {e}")
        
        # Combine data for each model
        for model_name, dfs in model_data.items():
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                # Remove duplicates based on context_size
                combined_df = combined_df.drop_duplicates(subset=['context_size'], keep='last')
                existing_results[model_name] = combined_df
                
                contexts = sorted(combined_df['context_size'].unique())
                self.logger.log_info(f"   {model_name}: {len(contexts)} context sizes - {contexts}")
        
        self.logger.log_existing_results(existing_results)
        return existing_results
    
    def identify_missing_work(self, existing_results: Dict[str, pd.DataFrame]) -> Dict[str, List[int]]:
        """Identify which experiments are missing"""
        self.logger.log_info("🔍 Identifying missing work...")
        
        missing_work = {}
        
        # Get enabled models from config
        enabled_models = [model['name'] for model in self.config.models if model.get('enabled', True)]
        
        for model_name in enabled_models:
            existing_contexts = set()
            
            if model_name in existing_results:
                existing_contexts = set(existing_results[model_name]['context_size'].tolist())
            
            required_contexts = set(self.config.context_sizes)
            missing_contexts = sorted(required_contexts - existing_contexts)
            
            if missing_contexts:
                missing_work[model_name] = missing_contexts
        
        self.logger.log_missing_work(missing_work)
        return missing_work
    
    def run_missing_experiments(self, missing_work: Dict[str, List[int]]) -> Dict[str, List[BenchmarkResult]]:
        """Run only the missing experiments"""
        if not missing_work:
            self.logger.log_info("✅ No missing work - all experiments complete!")
            return {}
        
        new_results = {}
        
        for model_name, missing_contexts in missing_work.items():
            self.logger.log_model_start(model_name, missing_contexts)
            
            model_results = []
            first_measurement = True  # Track if this is the first measurement for this model
            
            for context_size in missing_contexts:
                self.logger.log_info(f"🧪 Testing {model_name} @ {context_size:,} tokens")
                
                # Generate realistic prompt
                prompt = self.book_loader.create_analysis_prompt(
                    self.book_loader.get_chunk_by_tokens(context_size)
                )
                
                self.logger.log_api_request(model_name, context_size, len(prompt.split()))
                
                # Use accurate timing measurement (warmup only on first measurement)
                result = self.timing.accurate_measurement(
                    prompt, 
                    model_name, 
                    max_tokens=self.config.max_tokens,
                    skip_warmup=not first_measurement
                )
                
                # After first measurement, skip warmup for subsequent ones
                if first_measurement:
                    first_measurement = False
                
                if result:
                    # Create benchmark result
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
                        system_info=self.config.system_name,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    model_results.append(benchmark_result)
                    self.logger.log_api_response(model_name, context_size, result)
                    
                    # Save incrementally
                    self.save_incremental_results(model_name, [benchmark_result])
                    
                else:
                    self.logger.log_error(f"Failed to get result for {model_name} @ {context_size:,} tokens")
                
                # Delay between requests
                if self.config.delay_between_requests > 0:
                    self.logger.log_debug(f"   Waiting {self.config.delay_between_requests}s...")
                    time.sleep(self.config.delay_between_requests)
            
            if model_results:
                new_results[model_name] = model_results
                self.logger.log_model_complete(model_name, len(model_results))
            
            # Delay between models
            if self.config.delay_between_models > 0 and model_name != list(missing_work.keys())[-1]:
                self.logger.log_info(f"⏳ Waiting {self.config.delay_between_models}s before next model...")
                time.sleep(self.config.delay_between_models)
        
        return new_results
    
    def save_incremental_results(self, model_name: str, results: List[BenchmarkResult]):
        """Save results incrementally to CSV"""
        csv_path = os.path.join(self.results_dir, f"{model_name.replace('/', '_')}_results.csv")
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'model_name': result.model_name,
                'context_size': result.context_size,
                'prompt_tokens': result.prompt_tokens,
                'completion_tokens': result.completion_tokens,
                'total_tokens': result.total_tokens,
                'time_to_first_token': result.time_to_first_token,
                'generation_time': result.generation_time,
                'total_time': result.total_time,
                'tokens_per_second': result.tokens_per_second,
                'prompt_processing_speed': result.prompt_processing_speed,
                'system_info': result.system_info,
                'timestamp': result.timestamp
            })
        
        new_df = pd.DataFrame(data)
        
        # Append to existing file or create new
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            # Remove duplicates based on context_size, keeping the latest
            combined_df = combined_df.drop_duplicates(subset=['context_size'], keep='last')
        else:
            combined_df = new_df
        
        combined_df.to_csv(csv_path, index=False)
        self.logger.log_debug(f"   Saved results to {csv_path}")
    
    def combine_results(self, existing_results: Dict[str, pd.DataFrame], 
                       new_results: Dict[str, List[BenchmarkResult]]) -> Dict[str, pd.DataFrame]:
        """Combine existing and new results"""
        self.logger.log_info("🔄 Combining existing and new results...")
        
        combined_results = existing_results.copy()
        
        for model_name, results in new_results.items():
            # Convert new results to DataFrame
            data = []
            for result in results:
                data.append({
                    'model_name': result.model_name,
                    'context_size': result.context_size,
                    'prompt_tokens': result.prompt_tokens,
                    'completion_tokens': result.completion_tokens,
                    'total_tokens': result.total_tokens,
                    'time_to_first_token': result.time_to_first_token,
                    'generation_time': result.generation_time,
                    'total_time': result.total_time,
                    'tokens_per_second': result.tokens_per_second,
                    'prompt_processing_speed': result.prompt_processing_speed,
                    'system_info': result.system_info,
                    'timestamp': result.timestamp
                })
            
            new_df = pd.DataFrame(data)
            
            if model_name in combined_results:
                # Combine with existing
                combined_df = pd.concat([combined_results[model_name], new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['context_size'], keep='last')
                combined_results[model_name] = combined_df
            else:
                combined_results[model_name] = new_df
            
            contexts = sorted(combined_results[model_name]['context_size'].unique())
            self.logger.log_info(f"   {model_name}: {len(contexts)} total contexts - {contexts}")
        
        return combined_results
    
    def create_combined_analysis(self, combined_results: Dict[str, pd.DataFrame]):
        """Create analysis and charts from combined results"""
        if not combined_results:
            self.logger.log_warning("No results to analyze")
            return
        
        self.logger.log_info("📊 Creating combined analysis...")
        
        # Import here to avoid circular imports
        from create_final_charts import create_comparison_charts
        
        try:
            create_comparison_charts(combined_results, self.results_dir)
            self.logger.log_info("✅ Charts created successfully")
        except Exception as e:
            self.logger.log_error("Failed to create charts", e)
        
        # Create summary
        summary_path = os.path.join(self.results_dir, "benchmark_summary.txt")
        with open(summary_path, 'w') as f:
            f.write("LM Studio Context Size Benchmark - Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {self.config.system_name}\n")
            f.write(f"API URL: {self.config.api_url}\n\n")
            
            f.write("Models Tested:\n")
            for model_name, df in combined_results.items():
                contexts = sorted(df['context_size'].unique())
                min_speed = df['tokens_per_second'].min()
                max_speed = df['tokens_per_second'].max()
                f.write(f"  {model_name}:\n")
                f.write(f"    Context sizes: {contexts}\n")
                f.write(f"    Speed range: {min_speed:.2f} - {max_speed:.2f} tok/s\n")
                f.write(f"    Data points: {len(df)}\n\n")
        
        self.logger.log_info(f"📄 Summary saved to {summary_path}")
    
    def run(self):
        """Run the complete smart benchmark process"""
        self.logger.log_info("🚀 Starting Smart Benchmark")
        
        # Step 1: Scan existing results
        existing_results = self.scan_existing_results()
        
        # Step 2: Identify missing work
        missing_work = self.identify_missing_work(existing_results)
        
        # Step 3: Run missing experiments
        new_results = self.run_missing_experiments(missing_work)
        
        # Step 4: Combine results
        combined_results = self.combine_results(existing_results, new_results)
        
        # Step 5: Create analysis
        if self.config.create_charts or self.config.save_summary:
            self.create_combined_analysis(combined_results)
        
        self.logger.log_info("✅ Smart Benchmark Complete!")
        
        return combined_results

def main():
    """Main function"""
    try:
        # Load and validate config
        config = load_config()
        print_config_summary(config)
        validate_config(config)
        
        # Run smart benchmark
        benchmark = SmartBenchmark()
        results = benchmark.run()
        
        print(f"\n🎉 Smart Benchmark Complete!")
        print(f"📁 Results saved to: {benchmark.results_dir}")
        print(f"📊 Models tested: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

if __name__ == "__main__":
    main()
