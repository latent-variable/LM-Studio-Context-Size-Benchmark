#!/usr/bin/env python3
"""
Accurate timing measurement that excludes model loading time
"""

import time
import requests
import json
from typing import Dict, List, Optional, Tuple
from logger import BenchmarkLogger

class AccurateTiming:
    def __init__(self, api_url: str, logger: BenchmarkLogger):
        self.api_url = api_url.rstrip('/')
        self.logger = logger
        
    def warmup_model(self, model_name: str, warmup_requests: int = 3) -> bool:
        """Warm up the model with small requests to ensure it's loaded"""
        self.logger.log_info(f"🔥 Warming up model: {model_name}")
        
        warmup_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "temperature": 0.1,
            "stream": False
        }
        
        warmup_times = []
        
        for i in range(warmup_requests):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.api_url}/v1/chat/completions",
                    json=warmup_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    warmup_time = end_time - start_time
                    warmup_times.append(warmup_time)
                    self.logger.log_debug(f"   Warmup {i+1}: {warmup_time:.3f}s")
                else:
                    self.logger.log_error(f"Warmup request {i+1} failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                self.logger.log_error(f"Warmup request {i+1} failed", e)
                return False
        
        if warmup_times:
            avg_warmup = sum(warmup_times) / len(warmup_times)
            min_warmup = min(warmup_times)
            max_warmup = max(warmup_times)
            
            self.logger.log_info(f"   Warmup complete: {avg_warmup:.3f}s avg, {min_warmup:.3f}s min, {max_warmup:.3f}s max")
            
            # Check if times are consistent (model is loaded)
            if max_warmup - min_warmup < 2.0:  # Less than 2s variation
                self.logger.log_info(f"   ✅ Model appears to be loaded (consistent timing)")
                return True
            else:
                self.logger.log_warning(f"   ⚠️  Large timing variation - model may still be loading")
                return False
        
        return False
    
    def measure_with_streaming(self, prompt: str, model_name: str, max_tokens: int = 100) -> Optional[Dict]:
        """Measure timing using streaming to get accurate TTFT"""
        self.logger.log_debug(f"📊 Starting streaming measurement for {len(prompt)} char prompt")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "stream": True
        }
        
        try:
            request_start = time.perf_counter()  # Use high precision timer
            
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=600,
                stream=True
            )
            
            if response.status_code != 200:
                self.logger.log_error(f"Streaming request failed: {response.status_code}")
                return None
            
            # Parse streaming response
            first_token_time = None
            last_token_time = None
            token_times = []
            content = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        
                        if data_str.strip() == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            
                            if 'choices' in data and len(data['choices']) > 0:
                                choice = data['choices'][0]
                                if 'delta' in choice and 'content' in choice['delta']:
                                    current_time = time.perf_counter()
                                    content_chunk = choice['delta']['content']
                                    
                                    if content_chunk:
                                        if first_token_time is None:
                                            first_token_time = current_time
                                            self.logger.log_debug(f"   First token at: {first_token_time - request_start:.3f}s")
                                        
                                        last_token_time = current_time
                                        token_times.append(current_time)
                                        content += content_chunk
                                        
                        except json.JSONDecodeError:
                            continue
            
            request_end = time.perf_counter()
            
            if first_token_time is None:
                self.logger.log_error("No tokens received in streaming response")
                return None
            
            # Calculate metrics
            total_time = request_end - request_start
            time_to_first_token = first_token_time - request_start
            generation_time = last_token_time - first_token_time if last_token_time and last_token_time > first_token_time else 0.001
            
            # Get token counts from a separate non-streaming request
            token_count_result = self._get_token_counts(prompt, model_name, max_tokens)
            if not token_count_result:
                self.logger.log_error("Could not get token counts")
                return None
            
            prompt_tokens = token_count_result['prompt_tokens']
            completion_tokens = len(content.split()) + content.count('.') + content.count(',')  # Rough estimate
            
            # Use actual completion tokens from non-streaming if available
            if 'completion_tokens' in token_count_result:
                completion_tokens = token_count_result['completion_tokens']
            
            tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0
            prompt_processing_speed = prompt_tokens / time_to_first_token if time_to_first_token > 0 else 0
            
            result = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'time_to_first_token': time_to_first_token,
                'generation_time': generation_time,
                'total_time': total_time,
                'tokens_per_second': tokens_per_second,
                'prompt_processing_speed': prompt_processing_speed,
                'content': content,
                'token_count': len(token_times)
            }
            
            self.logger.log_debug(f"   Streaming result: {completion_tokens} tokens in {generation_time:.3f}s = {tokens_per_second:.2f} tok/s")
            
            return result
                
        except Exception as e:
            self.logger.log_error("Streaming measurement failed", e)
            return None
    
    def _get_token_counts(self, prompt: str, model_name: str, max_tokens: int) -> Optional[Dict]:
        """Get accurate token counts from non-streaming request"""
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": min(10, max_tokens),  # Small number for quick response
            "temperature": 0.1,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                usage = result.get('usage', {})
                return {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
            else:
                self.logger.log_error(f"Token count request failed: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.log_error("Token count request failed", e)
            return None
    
    def measure_multiple_times(self, prompt: str, model_name: str, max_tokens: int = 100, 
                             measurements: int = 3) -> Optional[Dict]:
        """Take multiple measurements and return the most consistent one"""
        self.logger.log_info(f"📏 Taking {measurements} measurements for consistency")
        
        results = []
        
        for i in range(measurements):
            self.logger.log_debug(f"   Measurement {i+1}/{measurements}")
            result = self.measure_with_streaming(prompt, model_name, max_tokens)
            
            if result:
                results.append(result)
                self.logger.log_debug(f"      TTFT: {result['time_to_first_token']:.3f}s, "
                                    f"Gen: {result['tokens_per_second']:.2f} tok/s")
            else:
                self.logger.log_warning(f"   Measurement {i+1} failed")
            
            # Small delay between measurements
            if i < measurements - 1:
                time.sleep(1)
        
        if not results:
            self.logger.log_error("All measurements failed")
            return None
        
        # Analyze consistency
        ttfts = [r['time_to_first_token'] for r in results]
        gen_speeds = [r['tokens_per_second'] for r in results]
        
        ttft_avg = sum(ttfts) / len(ttfts)
        ttft_std = (sum((x - ttft_avg) ** 2 for x in ttfts) / len(ttfts)) ** 0.5
        
        gen_avg = sum(gen_speeds) / len(gen_speeds)
        gen_std = (sum((x - gen_avg) ** 2 for x in gen_speeds) / len(gen_speeds)) ** 0.5
        
        self.logger.log_info(f"   TTFT: {ttft_avg:.3f}s ± {ttft_std:.3f}s")
        self.logger.log_info(f"   Gen Speed: {gen_avg:.2f} ± {gen_std:.2f} tok/s")
        
        # Check for consistency
        if ttft_std > 1.0:  # More than 1s variation in TTFT
            self.logger.log_warning(f"   High TTFT variation ({ttft_std:.3f}s) - may include loading time")
        
        if gen_std > gen_avg * 0.2:  # More than 20% variation in generation speed
            self.logger.log_warning(f"   High generation speed variation ({gen_std:.2f} tok/s)")
        
        # Return the measurement closest to the median
        median_ttft = sorted(ttfts)[len(ttfts) // 2]
        best_result = min(results, key=lambda r: abs(r['time_to_first_token'] - median_ttft))
        
        self.logger.log_info(f"   Selected measurement with TTFT: {best_result['time_to_first_token']:.3f}s")
        
        return best_result
    
    def accurate_measurement(self, prompt: str, model_name: str, max_tokens: int = 100) -> Optional[Dict]:
        """Perform accurate measurement with warmup and multiple samples"""
        self.logger.log_info(f"🎯 Starting accurate measurement for {model_name}")
        
        # Step 1: Warm up the model
        if not self.warmup_model(model_name):
            self.logger.log_warning("Model warmup had issues, but continuing...")
        
        # Step 2: Take multiple measurements
        result = self.measure_multiple_times(prompt, model_name, max_tokens)
        
        if result:
            self.logger.log_info(f"✅ Accurate measurement complete:")
            self.logger.log_info(f"   TTFT: {result['time_to_first_token']:.3f}s")
            self.logger.log_info(f"   Generation: {result['tokens_per_second']:.2f} tok/s")
            self.logger.log_info(f"   Prompt processing: {result['prompt_processing_speed']:.2f} tok/s")
        
        return result
