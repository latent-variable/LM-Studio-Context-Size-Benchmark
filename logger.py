#!/usr/bin/env python3
"""
Logging configuration for the benchmark
"""

import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_file=None):
    """Setup logging configuration"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for files
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

class BenchmarkLogger:
    """Specialized logger for benchmark operations"""
    
    def __init__(self, results_dir=None):
        self.logger = get_logger('benchmark')
        
        if results_dir:
            log_file = os.path.join(results_dir, 'benchmark.log')
            setup_logging(log_file=log_file)
        else:
            setup_logging()
    
    def log_config(self, config):
        """Log configuration details"""
        self.logger.info("=" * 60)
        self.logger.info("BENCHMARK CONFIGURATION")
        self.logger.info("=" * 60)
        self.logger.info(f"API URL: {config.api_url}")
        self.logger.info(f"System: {config.system_name}")
        self.logger.info(f"Notes: {config.system_notes}")
        self.logger.info(f"Book: {config.book_path}")
        self.logger.info(f"Context sizes: {config.context_sizes}")
        max_tokens_display = "Unlimited" if config.max_tokens <= 0 else config.max_tokens
        self.logger.info(f"Max tokens: {max_tokens_display}")
        self.logger.info(f"Temperature: {config.temperature}")
        self.logger.info(f"Timeout: {config.api_timeout}s")
        
        self.logger.info("Models to test:")
        for i, model in enumerate(config.models, 1):
            status = "ENABLED" if model.get('enabled', True) else "DISABLED"
            self.logger.info(f"  {i}. [{status}] {model['name']} - {model.get('description', 'No description')}")
    
    def log_existing_results(self, existing_results):
        """Log existing results found"""
        self.logger.info("=" * 60)
        self.logger.info("EXISTING RESULTS SCAN")
        self.logger.info("=" * 60)
        
        if not existing_results:
            self.logger.info("No existing results found")
            return
        
        for model_name, df in existing_results.items():
            contexts = sorted(df['context_size'].unique())
            self.logger.info(f"{model_name}:")
            self.logger.info(f"  Context sizes: {contexts}")
            self.logger.info(f"  Data points: {len(df)}")
            
            # Log some sample data
            for _, row in df.iterrows():
                self.logger.debug(f"    {row['context_size']:,} tokens: "
                                f"{row['tokens_per_second']:.2f} tok/s gen, "
                                f"{row['time_to_first_token']:.3f}s TTFT")
    
    def log_missing_work(self, missing_work):
        """Log missing work identified"""
        self.logger.info("=" * 60)
        self.logger.info("MISSING WORK ANALYSIS")
        self.logger.info("=" * 60)
        
        if not missing_work:
            self.logger.info("✅ All experiments complete - no missing work!")
            return
        
        total_experiments = sum(len(contexts) for contexts in missing_work.values())
        self.logger.info(f"Total missing experiments: {total_experiments}")
        
        for model_name, missing_contexts in missing_work.items():
            self.logger.info(f"{model_name}:")
            self.logger.info(f"  Missing contexts: {missing_contexts}")
            self.logger.info(f"  Experiments needed: {len(missing_contexts)}")
    
    def log_api_request(self, model_name, context_size, prompt_tokens):
        """Log API request details"""
        self.logger.info(f"🌐 API REQUEST: {model_name}")
        self.logger.info(f"   Context size: {context_size:,} tokens")
        self.logger.info(f"   Actual prompt tokens: {prompt_tokens:,}")
    
    def log_api_response(self, model_name, context_size, result):
        """Log API response details"""
        if result:
            self.logger.info(f"✅ API RESPONSE: {model_name} @ {context_size:,} tokens")
            self.logger.info(f"   Prompt tokens: {result.get('prompt_tokens', 'N/A')}")
            self.logger.info(f"   Completion tokens: {result.get('completion_tokens', 'N/A')}")
            self.logger.info(f"   Total time: {result.get('total_time', 'N/A'):.3f}s")
            self.logger.info(f"   Time to first token: {result.get('time_to_first_token', 'N/A'):.3f}s")
            self.logger.info(f"   Generation time: {result.get('generation_time', 'N/A'):.3f}s")
            self.logger.info(f"   Tokens per second: {result.get('tokens_per_second', 'N/A'):.2f}")
            self.logger.info(f"   Prompt processing speed: {result.get('prompt_processing_speed', 'N/A'):.2f}")
        else:
            self.logger.error(f"❌ API RESPONSE: {model_name} @ {context_size:,} tokens - FAILED")
    
    def log_model_start(self, model_name, missing_contexts):
        """Log start of model benchmark"""
        self.logger.info("=" * 80)
        self.logger.info(f"STARTING MODEL: {model_name}")
        self.logger.info(f"Missing contexts: {missing_contexts}")
        self.logger.info("=" * 80)
    
    def log_model_complete(self, model_name, results_count):
        """Log completion of model benchmark"""
        self.logger.info(f"✅ COMPLETED MODEL: {model_name}")
        self.logger.info(f"   New data points: {results_count}")
        self.logger.info("=" * 80)
    
    def log_error(self, message, exception=None):
        """Log error with optional exception"""
        self.logger.error(f"❌ ERROR: {message}")
        if exception:
            self.logger.error(f"   Exception: {str(exception)}")
            self.logger.debug("Exception details:", exc_info=True)
    
    def log_warning(self, message):
        """Log warning"""
        self.logger.warning(f"⚠️  WARNING: {message}")
    
    def log_info(self, message):
        """Log info"""
        self.logger.info(message)
    
    def log_debug(self, message):
        """Log debug"""
        self.logger.debug(message)
