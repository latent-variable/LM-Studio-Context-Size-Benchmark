#!/usr/bin/env python3
"""
LM Studio Benchmark Tool
Measures generation speed vs context size for different models.
Simulates agentic coding scenarios by building up prompts incrementally.
"""

import requests
import json
import time
import csv
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import os

@dataclass
class BenchmarkResult:
    """Store results from a single benchmark run"""
    model_name: str
    context_size: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    time_to_first_token: float  # Prompt processing time
    generation_time: float      # Time spent generating tokens
    total_time: float          # Total request time
    tokens_per_second: float   # Generation speed (completion_tokens / generation_time)
    prompt_processing_speed: float  # prompt_tokens / time_to_first_token
    system_info: str
    timestamp: str

class LMStudioBenchmark:
    def __init__(self, api_url: str = "http://localhost:5002"):
        self.api_url = api_url.rstrip('/')
        self.results: List[BenchmarkResult] = []
        
    def get_available_models(self) -> List[str]:
        """Get list of available models from LM Studio"""
        try:
            response = requests.get(f"{self.api_url}/v1/models")
            if response.status_code == 200:
                models = response.json()
                return [model['id'] for model in models['data']]
            else:
                print(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def generate_coding_prompt(self, target_tokens: int) -> str:
        """Generate a coding prompt of approximately target_tokens length"""
        base_system = """You are an expert software engineer working on a complex web application. You need to analyze the following codebase and implement new features while maintaining code quality and following best practices."""
        
        # Base code content that simulates a real codebase
        code_template = """
// React Component - UserDashboard.tsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { User, Project, Task, Analytics } from '../types';
import { api } from '../services/api';

interface UserDashboardProps {
  userId: string;
  permissions: string[];
  theme: 'light' | 'dark';
}

export const UserDashboard: React.FC<UserDashboardProps> = ({
  userId,
  permissions,
  theme
}) => {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const queryClient = useQueryClient();

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => api.users.getById(userId),
    staleTime: 5 * 60 * 1000,
  });

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects', userId],
    queryFn: () => api.projects.getByUserId(userId),
    enabled: !!userId,
  });

  const { data: analytics } = useQuery({
    queryKey: ['analytics', userId, selectedProject?.id],
    queryFn: () => api.analytics.getUserAnalytics(userId, selectedProject?.id),
    enabled: !!selectedProject,
    refetchInterval: 30000,
  });

  const updateProjectMutation = useMutation({
    mutationFn: api.projects.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project updated successfully');
    },
    onError: (error) => {
      toast.error('Failed to update project');
      console.error('Project update error:', error);
    },
  });

  const filteredTasks = useMemo(() => {
    if (!selectedProject?.tasks) return [];
    return selectedProject.tasks.filter(task => 
      filterStatus === 'all' || task.status === filterStatus
    );
  }, [selectedProject?.tasks, filterStatus]);

  const handleProjectSelect = useCallback((project: Project) => {
    setSelectedProject(project);
    setFilterStatus('all');
  }, []);

  const handleTaskStatusUpdate = useCallback(async (taskId: string, status: string) => {
    try {
      await api.tasks.updateStatus(taskId, status);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    } catch (error) {
      toast.error('Failed to update task status');
    }
  }, [queryClient]);

  if (userLoading || projectsLoading) {
    return <div className="loading-spinner">Loading dashboard...</div>;
  }

  return (
    <div className={`dashboard ${theme}`}>
      <header className="dashboard-header">
        <h1>Welcome back, {user?.name}</h1>
        <div className="user-stats">
          <span>Active Projects: {projects?.length || 0}</span>
          <span>Completed Tasks: {analytics?.completedTasks || 0}</span>
        </div>
      </header>
      
      <div className="dashboard-content">
        <aside className="sidebar">
          <h2>Projects</h2>
          <ul className="project-list">
            {projects?.map(project => (
              <li 
                key={project.id}
                className={selectedProject?.id === project.id ? 'active' : ''}
                onClick={() => handleProjectSelect(project)}
              >
                <span className="project-name">{project.name}</span>
                <span className="task-count">{project.tasks?.length || 0} tasks</span>
              </li>
            ))}
          </ul>
        </aside>
        
        <main className="main-content">
          {selectedProject ? (
            <>
              <div className="project-header">
                <h2>{selectedProject.name}</h2>
                <div className="filters">
                  <select 
                    value={filterStatus} 
                    onChange={(e) => setFilterStatus(e.target.value)}
                  >
                    <option value="all">All Tasks</option>
                    <option value="pending">Pending</option>
                    <option value="in-progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>
              
              <div className="tasks-grid">
                {filteredTasks.map(task => (
                  <div key={task.id} className="task-card">
                    <h3>{task.title}</h3>
                    <p>{task.description}</p>
                    <div className="task-meta">
                      <span className={`status ${task.status}`}>{task.status}</span>
                      <span className="priority">{task.priority}</span>
                    </div>
                    <div className="task-actions">
                      <button 
                        onClick={() => handleTaskStatusUpdate(task.id, 'in-progress')}
                        disabled={task.status === 'completed'}
                      >
                        Start
                      </button>
                      <button 
                        onClick={() => handleTaskStatusUpdate(task.id, 'completed')}
                        disabled={task.status === 'completed'}
                      >
                        Complete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <h2>Select a project to get started</h2>
              <p>Choose a project from the sidebar to view and manage tasks.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
"""
        
        # Calculate how many times to repeat the code template
        current_length = len(base_system + code_template)
        if current_length >= target_tokens * 4:  # Rough token estimation
            return base_system + code_template[:target_tokens * 4]
        
        repeats_needed = (target_tokens * 4) // len(code_template)
        repeated_code = code_template * repeats_needed
        
        # Add some variation to make it more realistic
        variations = [
            "\n// Backend API - userController.js\n",
            "\n// Database Schema - migrations/\n", 
            "\n// Utils - helpers/\n",
            "\n// Tests - __tests__/\n",
            "\n// Configuration - config/\n"
        ]
        
        final_prompt = base_system + repeated_code
        for i, variation in enumerate(variations):
            if len(final_prompt) < target_tokens * 4:
                final_prompt += variation + repeated_code
        
        return final_prompt[:target_tokens * 4]  # Rough truncation
    
    def make_completion_request(self, prompt: str, model: str, max_tokens: int = 100) -> Optional[Dict]:
        """Make a streaming completion request to LM Studio API with accurate timing"""
        messages = [{"role": "user", "content": prompt}]
        
        # First, get token counts with a non-streaming request
        token_payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1,  # Minimal tokens to get prompt token count
            "temperature": 0.1,
            "stream": False
        }
        
        try:
            # Quick request to get prompt token count
            token_response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=token_payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            prompt_tokens = 0
            if token_response.status_code == 200:
                token_result = token_response.json()
                usage = token_result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
            
            # Now make the actual streaming request for timing
            stream_payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "stream": True
            }
            
            request_start = time.time()
            
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=stream_payload,
                headers={"Content-Type": "application/json"},
                timeout=600,
                stream=True
            )
            
            if response.status_code != 200:
                print(f"  Streaming request failed: {response.status_code}")
                return self._make_non_streaming_request(prompt, model, max_tokens)
            
            # Parse streaming response for timing
            first_token_time = None
            last_token_time = None
            completion_tokens = 0
            content = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str.strip() == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            
                            # Track token timing
                            if 'choices' in data and len(data['choices']) > 0:
                                choice = data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    current_time = time.time()
                                    content_chunk = choice['delta']['content']
                                    
                                    if content_chunk:  # Only count non-empty content
                                        # First token marks end of prompt processing
                                        if first_token_time is None:
                                            first_token_time = current_time
                                        
                                        # Update last token time
                                        last_token_time = current_time
                                        content += content_chunk
                                        
                                        # Rough token count (will be more accurate than 0)
                                        completion_tokens = len(content.split()) + content.count(',') + content.count('.')
                                    
                        except json.JSONDecodeError:
                            continue
            
            request_end = time.time()
            
            # If we didn't get timing from streaming, fall back to non-streaming
            if first_token_time is None:
                print("  No tokens generated, falling back to non-streaming...")
                return self._make_non_streaming_request(prompt, model, max_tokens)
            
            # Calculate timing metrics
            total_time = request_end - request_start
            time_to_first_token = first_token_time - request_start
            generation_time = last_token_time - first_token_time if last_token_time and last_token_time > first_token_time else 0.01
            
            # Ensure we have reasonable token counts
            if completion_tokens == 0:
                completion_tokens = max(1, len(content.split()))
            
            # Calculate speeds
            tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
            prompt_processing_speed = prompt_tokens / time_to_first_token if time_to_first_token > 0 else 0
            
            return {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'time_to_first_token': time_to_first_token,
                'generation_time': generation_time,
                'total_time': total_time,
                'tokens_per_second': tokens_per_second,
                'prompt_processing_speed': prompt_processing_speed,
                'content': content
            }
                
        except Exception as e:
            print(f"Error making completion request: {e}")
            return None
    
    def _make_non_streaming_request(self, prompt: str, model: str, max_tokens: int = 100) -> Optional[Dict]:
        """Fallback non-streaming request with less accurate timing"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                total_time = end_time - start_time
                
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                
                # Rough estimates for non-streaming
                time_to_first_token = total_time * 0.2  # Estimate 20% for prompt processing
                generation_time = total_time * 0.8
                
                tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
                prompt_processing_speed = prompt_tokens / time_to_first_token if time_to_first_token > 0 else 0
                
                return {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'time_to_first_token': time_to_first_token,
                    'generation_time': generation_time,
                    'total_time': total_time,
                    'tokens_per_second': tokens_per_second,
                    'prompt_processing_speed': prompt_processing_speed,
                    'content': result.get('choices', [{}])[0].get('message', {}).get('content', '')
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error in fallback request: {e}")
            return None
    
    def run_benchmark(self, model: str, max_context_size: int = 100000, step_size: int = 10000) -> List[BenchmarkResult]:
        """Run benchmark for a single model"""
        print(f"\nRunning benchmark for model: {model}")
        print(f"Max context size: {max_context_size}, Step size: {step_size}")
        
        model_results = []
        
        for context_size in range(step_size, max_context_size + 1, step_size):
            print(f"Testing context size: {context_size} tokens...")
            
            # Generate prompt of target size
            prompt = self.generate_coding_prompt(context_size)
            
            # Make completion request
            result = self.make_completion_request(prompt, model)
            
            if result:
                benchmark_result = BenchmarkResult(
                    model_name=model,
                    context_size=context_size,
                    prompt_tokens=result['prompt_tokens'],
                    completion_tokens=result['completion_tokens'],
                    total_tokens=result['total_tokens'],
                    time_to_first_token=result['time_to_first_token'],
                    generation_time=result['generation_time'],
                    total_time=result['total_time'],
                    tokens_per_second=result['tokens_per_second'],
                    prompt_processing_speed=result['prompt_processing_speed'],
                    system_info="M3 Max MacBook Pro 128GB RAM",
                    timestamp=datetime.now().isoformat()
                )
                
                model_results.append(benchmark_result)
                self.results.append(benchmark_result)
                
                print(f"  Actual prompt tokens: {result['prompt_tokens']}")
                print(f"  Time to first token: {result['time_to_first_token']:.3f}s")
                print(f"  Generation speed: {result['tokens_per_second']:.2f} tokens/sec")
                print(f"  Prompt processing speed: {result['prompt_processing_speed']:.2f} tokens/sec")
                print(f"  Total time: {result['total_time']:.3f}s")
            else:
                print(f"  Failed to get result for context size {context_size}")
                break
            
            # Small delay to avoid overwhelming the API
            time.sleep(1)
        
        return model_results
    
    def save_results_csv(self, filename: str = None):
        """Save benchmark results to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            if self.results:
                fieldnames = list(asdict(self.results[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for result in self.results:
                    writer.writerow(asdict(result))
        
        print(f"Results saved to: {filename}")
    
    def create_visualizations(self, output_dir: str = "charts"):
        """Create visualization charts similar to the original benchmark"""
        if not self.results:
            print("No results to visualize")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Group results by model
        models = {}
        for result in self.results:
            if result.model_name not in models:
                models[result.model_name] = []
            models[result.model_name].append(result)
        
        # Generation Speed vs Context Size
        plt.figure(figsize=(12, 8))
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, (model_name, results) in enumerate(models.items()):
            context_sizes = [r.context_size for r in results]
            tokens_per_sec = [r.tokens_per_second for r in results]
            
            plt.plot(context_sizes, tokens_per_sec, 
                    label=model_name, 
                    color=colors[i % len(colors)],
                    linewidth=2, 
                    marker='o', 
                    markersize=4)
        
        plt.xlabel('Context Size (tokens)')
        plt.ylabel('TPS (Generation)')
        plt.title('Generation vs Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/generation_vs_context.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Prompt Processing Speed vs Context Size
        plt.figure(figsize=(12, 8))
        
        for i, (model_name, results) in enumerate(models.items()):
            context_sizes = [r.context_size for r in results]
            prompt_tps = [r.prompt_processing_speed for r in results]
            
            plt.plot(context_sizes, prompt_tps, 
                    label=model_name, 
                    color=colors[i % len(colors)],
                    linewidth=2, 
                    marker='o', 
                    markersize=4)
        
        plt.xlabel('Context Size (tokens)')
        plt.ylabel('TPS (Prompt Processing)')
        plt.title('Prompt Processing vs Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/prompt_processing_vs_context.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Time to First Token vs Context Size
        plt.figure(figsize=(12, 8))
        
        for i, (model_name, results) in enumerate(models.items()):
            context_sizes = [r.context_size for r in results]
            ttft = [r.time_to_first_token for r in results]
            
            plt.plot(context_sizes, ttft, 
                    label=model_name, 
                    color=colors[i % len(colors)],
                    linewidth=2, 
                    marker='o', 
                    markersize=4)
        
        plt.xlabel('Context Size (tokens)')
        plt.ylabel('Time to First Token (seconds)')
        plt.title('Time to First Token vs Context Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/time_to_first_token_vs_context.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Charts saved to {output_dir}/ directory")

def main():
    parser = argparse.ArgumentParser(description='LM Studio Benchmark Tool')
    parser.add_argument('--api-url', default='http://localhost:5002', 
                       help='LM Studio API URL')
    parser.add_argument('--models', nargs='+', 
                       help='Specific models to benchmark (default: all available)')
    parser.add_argument('--max-context', type=int, default=100000,
                       help='Maximum context size to test')
    parser.add_argument('--step-size', type=int, default=10000,
                       help='Step size for context increments')
    parser.add_argument('--output-dir', default='results',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize benchmark
    benchmark = LMStudioBenchmark(args.api_url)
    
    # Get available models
    available_models = benchmark.get_available_models()
    if not available_models:
        print("No models available. Make sure LM Studio is running and accessible.")
        return
    
    print(f"Available models: {available_models}")
    
    # Determine which models to benchmark
    models_to_test = args.models if args.models else available_models
    
    # Run benchmarks
    for model in models_to_test:
        if model in available_models:
            benchmark.run_benchmark(model, args.max_context, args.step_size)
        else:
            print(f"Model '{model}' not available, skipping...")
    
    if benchmark.results:
        # Save results
        csv_path = os.path.join(args.output_dir, f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        benchmark.save_results_csv(csv_path)
        
        # Create visualizations
        charts_dir = os.path.join(args.output_dir, "charts")
        benchmark.create_visualizations(charts_dir)
        
        print(f"\nBenchmark completed! Results saved to {args.output_dir}/")
    else:
        print("No results collected.")

if __name__ == "__main__":
    main()
