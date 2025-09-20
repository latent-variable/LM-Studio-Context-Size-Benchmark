#!/usr/bin/env python3
"""
Configuration loader for the LM Studio benchmark
"""

import yaml
import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class BenchmarkConfig:
    """Configuration data class"""
    # API settings
    api_url: str
    api_timeout: int
    delay_between_requests: int
    delay_between_models: int
    
    # System info
    system_name: str
    system_notes: str
    
    # Models to test
    models: List[Dict[str, Any]]
    
    # Test settings
    context_sizes: List[int]
    max_tokens: int
    temperature: float
    
    # Content settings
    book_path: str
    prompt_types: List[str]
    
    # Output settings
    results_dir: str
    create_charts: bool
    save_summary: bool
    
    # Chart settings
    chart_dpi: int
    chart_figure_size: List[int]
    chart_colors: Dict[str, str]

def load_config(config_path: str = "config.yaml") -> BenchmarkConfig:
    """Load configuration from YAML file"""
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Extract context sizes (handle both list and range formats)
    if 'context_sizes' in config_data['test']:
        context_sizes = config_data['test']['context_sizes']
    elif 'context_range' in config_data['test']:
        range_config = config_data['test']['context_range']
        context_sizes = list(range(
            range_config['start'],
            range_config['end'] + 1,
            range_config['step']
        ))
    else:
        raise ValueError("Must specify either 'context_sizes' or 'context_range' in test configuration")
    
    # Filter enabled models
    enabled_models = [model for model in config_data['models'] if model.get('enabled', True)]
    
    return BenchmarkConfig(
        # API settings
        api_url=config_data['api']['url'],
        api_timeout=config_data['api']['timeout'],
        delay_between_requests=config_data['api']['delay_between_requests'],
        delay_between_models=config_data['api']['delay_between_models'],
        
        # System info
        system_name=config_data['system']['name'],
        system_notes=config_data['system']['notes'],
        
        # Models
        models=enabled_models,
        
        # Test settings
        context_sizes=context_sizes,
        max_tokens=config_data['test']['max_tokens'],
        temperature=config_data['test']['temperature'],
        
        # Content settings
        book_path=config_data['content']['book_path'],
        prompt_types=config_data['content']['prompt_types'],
        
        # Output settings
        results_dir=config_data['output']['results_dir'],
        create_charts=config_data['output']['create_charts'],
        save_summary=config_data['output']['save_summary'],
        
        # Chart settings
        chart_dpi=config_data['charts']['dpi'],
        chart_figure_size=config_data['charts']['figure_size'],
        chart_colors=config_data['charts']['colors']
    )

def print_config_summary(config: BenchmarkConfig):
    """Print a summary of the loaded configuration"""
    print("📋 Benchmark Configuration")
    print("=" * 50)
    print(f"🌐 API URL: {config.api_url}")
    print(f"💻 System: {config.system_name}")
    print(f"📚 Book: {config.book_path}")
    print(f"🎯 Models to test: {len(config.models)}")
    
    for i, model in enumerate(config.models, 1):
        status = "✅" if model.get('enabled', True) else "❌"
        print(f"  {i}. {status} {model['name']} - {model.get('description', 'No description')}")
    
    print(f"📊 Context sizes: {len(config.context_sizes)} steps")
    print(f"   Range: {min(config.context_sizes):,} - {max(config.context_sizes):,} tokens")
    print(f"   Steps: {config.context_sizes}")
    
    print(f"⚙️  Settings:")
    print(f"   Max tokens: {config.max_tokens}")
    print(f"   Temperature: {config.temperature}")
    print(f"   Timeout: {config.api_timeout}s")
    print()

def validate_config(config: BenchmarkConfig) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []
    
    # Check if book file exists
    if not os.path.exists(config.book_path):
        issues.append(f"Book file not found: {config.book_path}")
    
    # Check if we have models to test
    if not config.models:
        issues.append("No models enabled for testing")
    
    # Check context sizes
    if not config.context_sizes:
        issues.append("No context sizes specified")
    elif any(size <= 0 for size in config.context_sizes):
        issues.append("Context sizes must be positive")
    
    # Check API URL format
    if not config.api_url.startswith(('http://', 'https://')):
        issues.append("API URL must start with http:// or https://")
    
    return issues

def main():
    """Test configuration loading"""
    try:
        config = load_config()
        print_config_summary(config)
        
        # Validate configuration
        issues = validate_config(config)
        if issues:
            print("⚠️  Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration is valid!")
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")

if __name__ == "__main__":
    main()
