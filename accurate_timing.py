#!/usr/bin/env python3
"""
Accurate timing measurement that excludes model loading time
"""

import time
import requests
import json
from typing import Dict, Optional

try:
    import tiktoken
except ImportError:  # Optional dependency for token counting
    tiktoken = None

from logger import BenchmarkLogger

class AccurateTiming:
    def __init__(self, api_url: str, logger: BenchmarkLogger, timeout: int = 60):
        self.api_url = api_url.rstrip('/')
        self.logger = logger
        self.timeout = timeout if timeout and timeout > 0 else 60
        self._encoding = self._load_encoder()
        
    def simple_warmup(self, model_name: str) -> bool:
        """Simple warmup with a basic yes/no question to ensure model is loaded"""
        self.logger.log_info(f"🔥 Warming up model: {model_name}")
        
        warmup_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Answer with just 'yes' or 'no': Is the sky blue?"}],
            "max_tokens": 5,
            "temperature": 0.1,
            "stream": False
        }
        
        try:
            self.logger.log_debug("   Sending warmup request...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=warmup_payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Give it time to load if needed
            )
            
            end_time = time.time()
            warmup_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                self.logger.log_info(f"   ✅ Model loaded and responded in {warmup_time:.3f}s")
                self.logger.log_debug(f"   Response: '{content}'")
                
                if warmup_time > 10.0:
                    self.logger.log_info(f"   📝 Model took {warmup_time:.1f}s to load - now ready for benchmarking")
                else:
                    self.logger.log_info(f"   📝 Model was already loaded - ready for benchmarking")
                
                return True
            else:
                self.logger.log_error(f"Warmup failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.log_error("Warmup request failed", e)
            return False
    
    def measure_with_streaming(self, prompt: str, model_name: str, max_tokens: int = 100) -> Optional[Dict]:
        """Measure timing using streaming to get accurate TTFT"""
        self.logger.log_debug(f"📊 Starting streaming measurement for {len(prompt)} char prompt")
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": True
        }

        if max_tokens and max_tokens > 0:
            payload["max_tokens"] = max_tokens
        
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

            prompt_tokens = token_count_result.get('prompt_tokens') or self._estimate_token_count(prompt)
            completion_tokens = self._estimate_token_count(content)

            reported_completion_tokens = token_count_result.get('completion_tokens')
            if reported_completion_tokens and reported_completion_tokens > completion_tokens:
                completion_tokens = reported_completion_tokens
            
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
        probe_tokens = max_tokens if max_tokens and max_tokens > 0 else 16
        probe_tokens = max(1, min(probe_tokens, 256))

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": False,
            "max_tokens": probe_tokens
        }

        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
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

        except requests.exceptions.Timeout:
            self.logger.log_warning("Token count request timed out; falling back to estimated tokens")
            return {
                'prompt_tokens': self._estimate_token_count(prompt),
                'completion_tokens': None,
                'total_tokens': None
            }
        except Exception as e:
            self.logger.log_error("Token count request failed", e)
            return None

    def _load_encoder(self):
        """Load default encoder for token estimation"""
        if tiktoken is None:
            return None

        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None

    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count using encoder fallback"""
        if not text:
            return 0

        if self._encoding is not None:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass

        # Simple fallback based on whitespace
        return max(1, len(text.split()))

    def single_measurement(self, prompt: str, model_name: str, max_tokens: int = 100) -> Optional[Dict]:
        """Take a single accurate measurement (model should already be warmed up)"""
        self.logger.log_info(f"📏 Taking single measurement")
        
        result = self.measure_with_streaming(prompt, model_name, max_tokens)
        
        if result:
            self.logger.log_info(f"   ✅ Measurement complete:")
            self.logger.log_info(f"      TTFT: {result['time_to_first_token']:.3f}s")
            self.logger.log_info(f"      Generation: {result['tokens_per_second']:.2f} tok/s")
            self.logger.log_info(f"      Prompt processing: {result['prompt_processing_speed']:.2f} tok/s")
        else:
            self.logger.log_error("Measurement failed")
        
        return result
    
    def accurate_measurement(self, prompt: str, model_name: str, max_tokens: int = 100, 
                           skip_warmup: bool = False) -> Optional[Dict]:
        """Perform accurate measurement with optional warmup and single measurement"""
        self.logger.log_info(f"🎯 Starting measurement for {model_name}")
        
        # Step 1: Warm up the model (only if not skipping)
        if not skip_warmup:
            if not self.simple_warmup(model_name):
                self.logger.log_warning("Model warmup failed, but continuing...")
        
        # Step 2: Take single measurement
        result = self.single_measurement(prompt, model_name, max_tokens)
        
        if result:
            self.logger.log_info(f"✅ Measurement complete:")
            self.logger.log_info(f"   TTFT: {result['time_to_first_token']:.3f}s")
            self.logger.log_info(f"   Generation: {result['tokens_per_second']:.2f} tok/s")
            self.logger.log_info(f"   Prompt processing: {result['prompt_processing_speed']:.2f} tok/s")
        
        return result
