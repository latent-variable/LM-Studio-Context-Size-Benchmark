# LM Studio Context Size Benchmark

A comprehensive benchmarking tool for measuring generation speed and prompt processing performance across different context sizes using the LM Studio API. Uses realistic book content to create meaningful prompts that test model performance degradation.

## Features

- **Context Size Testing**: Tests models with increasing context sizes from 10k to 100k tokens
- **Realistic Prompts**: Uses Harry Potter book content for meaningful, varied prompts
- **Accurate Timing**: Separates prompt processing time from generation time
- **Performance Metrics**: Measures generation speed, time to first token, and prompt processing speed
- **Visualization**: Creates comprehensive charts showing performance vs context size
- **Incremental Saving**: Saves results after each test to prevent data loss
- **Multi-Model Support**: Benchmarks multiple models sequentially

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Add a book file for realistic prompts:
   - Place a PDF book in the `books/` directory (e.g., `books/mybook.pdf`)
   - Update `config.yaml` to point to your book file
   - See `books/README.md` for detailed instructions

3. Make sure LM Studio is running and accessible at your API endpoint

## Usage

### Run Full Benchmark
```bash
python multi_model_benchmark.py
```

### Create Charts from Results
```bash
python create_final_charts.py
# Automatically finds and uses the latest results directory
```

### Test Book Loader
```bash
python book_loader.py
```

## Configuration

The benchmark is configured via `config.yaml`. You can customize:

- **Models to test**: Enable/disable specific models and add descriptions
- **Context sizes**: Specify exact sizes or use a range (start/end/step)
- **API settings**: URL, timeouts, delays between requests
- **System info**: Name and notes for your hardware setup
- **Content settings**: Book path and prompt types
- **Output settings**: Results directory, chart generation

### Test Configuration
```bash
python config_loader.py  # Validate and view current configuration
```

Default models tested:
- `qwen/qwen3-next-80b` - Qwen 3 Next 80B
- `openai/gpt-oss-20b` - GPT-OSS 20B  
- `openai/gpt-oss-120b` - GPT-OSS 120B

Default context sizes: 10k, 20k, 30k, 40k, 50k, 60k, 70k, 80k, 90k, 100k tokens

## Output

Each benchmark run creates a timestamped directory in `results/run_YYYYMMDD_HHMMSS/` containing:

1. **Results CSV files**: `{model}_results.csv` - Complete results for each model (updated after each test)
2. **Performance charts**: `benchmark_comparison_charts.png` - Visual comparison
3. **Run summary**: `run_summary.txt` - Overview of the entire benchmark run

## How It Works

1. **Book Content Loading**: Extracts text from Harry Potter PDF and creates realistic prompts
2. **Streaming API Calls**: Uses streaming to accurately measure time to first token vs generation time  
3. **Incremental Testing**: Tests context sizes from 10k to 100k tokens in 10k increments
4. **Performance Analysis**: Identifies performance cliffs and degradation patterns
5. **Visualization**: Creates charts showing generation speed and prompt processing vs context size

## Metrics Measured

- **Generation Speed**: Tokens per second during text generation
- **Time to First Token (TTFT)**: Time taken to process prompt and start generating
- **Prompt Processing Speed**: Tokens per second for prompt processing
- **Performance Degradation**: How metrics change with increasing context size
- **Performance Cliffs**: Sudden drops in performance at specific context sizes

## Requirements

- Python 3.8+
- LM Studio running with API enabled
- Models loaded in 4-bit quantization (recommended)
- KV-Cache at 8-bit (recommended)

## Files

- `config.yaml` - Configuration file for all benchmark settings
- `multi_model_benchmark.py` - Main benchmark script
- `config_loader.py` - Configuration loading and validation
- `book_loader.py` - PDF text extraction and prompt generation
- `benchmark.py` - Core benchmarking functionality  
- `create_final_charts.py` - Generates comparison charts
- `list_results.py` - View and manage benchmark results
- `books/` - Directory for book content (add your own PDF/text files)

## Troubleshooting

- Ensure LM Studio API is accessible at the specified URL
- Check that models are loaded and available
- Increase timeout values for slower models
- Reduce max context size if running into memory issues