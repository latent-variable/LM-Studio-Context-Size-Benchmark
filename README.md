# LM Studio Context Size Benchmark

A comprehensive benchmarking tool for measuring LM Studio model performance across different context sizes. Features accurate timing measurements, smart experiment management, and detailed logging.

## 🚀 Features

- **Accurate Timing**: Advanced timing system that excludes model loading time and provides reliable measurements
- **Smart Benchmarking**: Only runs missing experiments, reusing existing results for efficiency
- **Comprehensive Logging**: Detailed logs of every step with timestamps and performance metrics
- **Realistic Prompts**: Uses book content for realistic agentic coding simulation
- **Multiple Models**: Test multiple models simultaneously with configurable parameters
- **Performance Charts**: Automatic generation of performance comparison charts
- **Incremental Results**: Results saved incrementally with organized timestamped directories

## 📋 Requirements

- Python 3.8+
- LM Studio running locally
- PDF book file for realistic prompts

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/latent-variable/LM-Studio-Context-Size-Benchmark.git
   cd LM-Studio-Context-Size-Benchmark
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup LM Studio:**
   - Start LM Studio
   - Load your desired models
   - Ensure the API server is running (default: http://localhost:5002)

4. **Add a book file:**
   - Place a PDF book in the `books/` directory (e.g., `books/your_book.pdf`)
   - Update `config.yaml` to point to your book file

5. **Configure the benchmark:**
   - Copy and customize `config.yaml` for your setup
   - Set your models, context sizes, and system information

## 🎯 Usage

### Quick Start
```bash
python smart_benchmark.py
```

### Main Scripts

- **`smart_benchmark.py`** - Main benchmark runner with accurate timing and smart experiment management
- **`create_final_charts.py`** - Generate comparison charts from results
- **`list_results.py`** - List and analyze existing benchmark results
- **`setup.py`** - Setup and validation helper

### Configuration

Edit `config.yaml` to customize:

```yaml
# API Configuration
api:
  url: "http://localhost:5002"
  timeout: 600

# System Information
system:
  name: "M3 Max MacBook Pro 128GB RAM"
  notes: "4-bit quantization, 8-bit KV cache"

# Models to Test
models:
  - name: "qwen/qwen3-next-80b"
    enabled: true
    description: "Qwen 3 Next 80B"
  - name: "openai/gpt-oss-20b"
    enabled: true
    description: "GPT-OSS 20B"

# Test Parameters
test:
  context_sizes: [10000, 20000, 30000, 40000, 50000]
  max_tokens: 100
  temperature: 0.1
  delay_between_requests: 2
  delay_between_models: 5

# Content Settings
content:
  book_path: "books/your_book.pdf"

# Output Settings
output:
  results_dir: "results"
  create_charts: true
  save_summary: true
```

## 📊 Output Structure

```
results/
├── run_20250919_143022/          # Timestamped run directory
│   ├── benchmark.log             # Detailed execution logs
│   ├── qwen_qwen3_next_80b_results.csv
│   ├── openai_gpt_oss_20b_results.csv
│   ├── performance_charts.png    # Performance comparison charts
│   └── run_summary.txt          # Run summary and analysis
└── run_20250919_151045/         # Another run
    └── ...
```

## 🧠 How It Works

### Accurate Timing System

1. **Model Warmup**: Performs warmup requests to ensure the model is loaded
2. **Multiple Measurements**: Takes multiple measurements to detect inconsistencies
3. **Loading Detection**: Identifies and filters out measurements that include model loading time
4. **Smart Selection**: Selects the most consistent measurement representing actual performance

### Smart Benchmarking

1. **Existing Results Scan**: Scans all previous runs for existing data
2. **Missing Work Identification**: Determines which experiments are missing
3. **Selective Execution**: Only runs the missing experiments
4. **Result Combination**: Merges new and existing results for comprehensive analysis

### Realistic Prompts

- Uses actual book content chunked to specific token sizes
- Simulates agentic coding scenarios with analysis prompts
- Provides consistent, reproducible test conditions

## 📈 Metrics Measured

- **Time to First Token (TTFT)**: Prompt processing time
- **Generation Speed**: Tokens per second during generation
- **Prompt Processing Speed**: Tokens per second for prompt processing
- **Total Time**: Complete request duration
- **Token Counts**: Accurate prompt and completion token counts

## 🔧 Advanced Features

### Comprehensive Logging

Every operation is logged with:
- Timestamps and execution details
- API request/response information
- Timing measurements and variations
- Warning detection for loading delays
- Performance metrics and analysis

### Error Handling

- Automatic retry logic for failed requests
- Graceful handling of model loading delays
- Detailed error reporting and logging
- Partial result preservation

### Performance Analysis

- Automatic chart generation
- Performance degradation analysis
- Statistical consistency checking
- Comparative model analysis

## 📁 Files

- **`smart_benchmark.py`** - Main smart benchmark runner
- **`accurate_timing.py`** - Advanced timing measurement system
- **`logger.py`** - Comprehensive logging system
- **`benchmark.py`** - Core benchmarking logic
- **`book_loader.py`** - PDF book loading and chunking
- **`config_loader.py`** - Configuration management
- **`create_final_charts.py`** - Chart generation
- **`multi_model_benchmark.py`** - Legacy multi-model runner
- **`list_results.py`** - Results analysis utility
- **`setup.py`** - Setup and validation helper
- **`config.yaml`** - Main configuration file
- **`requirements.txt`** - Python dependencies
- **`books/`** - Directory for book content
- **`results/`** - Directory for benchmark results

## 🎨 Example Results

The benchmark generates detailed performance charts showing:
- Generation speed vs context size
- Time to first token vs context size  
- Prompt processing speed vs context size
- Comparative analysis across models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use and modify as needed.

## 🐛 Troubleshooting

### Common Issues

1. **Model Loading Delays**: The system automatically detects and handles model loading time
2. **API Timeouts**: Increase timeout values in `config.yaml`
3. **Memory Issues**: Reduce context sizes or test fewer models simultaneously
4. **Book Loading Errors**: Ensure your PDF is readable and in the `books/` directory

### Getting Help

- Check the detailed logs in `results/run_*/benchmark.log`
- Use `python list_results.py` to analyze existing results
- Run `python setup.py` to validate your configuration

## 🔬 Technical Details

### Timing Accuracy

The benchmark uses a hybrid approach:
1. Non-streaming request for accurate token counts
2. Streaming request for precise timing measurements
3. Multiple measurements with statistical analysis
4. Intelligent filtering of loading-related delays

### Smart Experiment Management

- Scans all previous results across all runs
- Identifies missing combinations of models and context sizes
- Preserves existing data while adding new measurements
- Enables incremental testing and model comparison

This ensures efficient use of compute resources and enables iterative experimentation without redundant work.