"""
Optimized Voice Service with Performance Enhancements
Integrates caching, connection pooling, and performance optimizations for TTS/STT
"""

import asyncio
import hashlib
import time
import io
import tempfile
import os
from typing import Dict, List, Optional, Any, BinaryIO, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime, timedelta
import numpy as np

from loguru import logger
from .cache_manager import (
    cache_manager, get_cached_tts, set_cached_tts, 
    get_cached_stt, set_cached_stt
)
from .connection_pool import connection_manager
from .voice_service import (
    VoiceService, TTSCacheEntry, STTConfig, StreamingAudioChunk,
    TranscriptionResult, AudioFormat, SUPPORTED_AUDIO_FORMATS
)
from .config import settings

@dataclass
class OptimizedVoiceConfig:
    """Configuration for optimized voice service"""
    # Caching settings
    enable_tts_cache: bool = True
    enable_stt_cache: bool = True
    tts_cache_ttl: int = 86400  # 24 hours
    stt_cache_ttl: int = 3600   # 1 hour
    
    # Performance settings
    max_concurrent_tts: int = 5
    max_concurrent_stt: int = 3
    tts_batch_size: int = 10
    stt_batch_size: int = 5
    
    # Audio processing settings
    enable_audio_optimization: bool = True
    audio_quality_threshold: float = 0.3
    max_audio_length: int = 600  # 10 minutes
    
    # Connection settings
    openai_timeout: int = 30
    openai_max_retries: int = 3
    openai_retry_delay: float = 1.0

class OptimizedVoiceService(VoiceService):
    """Optimized voice service with performance enhancements"""
    
    def __init__(self, config: Optional[OptimizedVoiceConfig] = None):
        # Initialize parent class first
        super().__init__()
        
        self.config = config or OptimizedVoiceConfig()
        
        # Thread pools for concurrent processing
        self._tts_executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tts)
        self._stt_executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_stt)
        
        # Performance tracking
        self._stats = {
            'tts_requests': 0,
            'tts_cache_hits': 0,
            'tts_avg_time': 0.0,
            'stt_requests': 0,
            'stt_cache_hits': 0,
            'stt_avg_time': 0.0,
            'audio_optimizations': 0
        }
        
        # HTTP client for API calls
        self._http_client = None
        
        logger.info("Optimized voice service initialized")
    
    async def initialize(self):
        """Initialize optimized components"""
        try:
            # Initialize HTTP client from connection pool
            self._http_client = connection_manager.get_http_pool()
            
            logger.info("Optimized voice service components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimized voice service: {e}")
            raise
    
    async def synthesize_speech_optimized(
        self,
        text: str,
        voice: Optional[str] = None,
        output_file_path: Optional[str] = None,
        use_cache: bool = True,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """Optimized text-to-speech synthesis with caching and performance improvements"""
        start_time = time.time()
        
        try:
            self._stats['tts_requests'] += 1
            
            # Input validation
            if not text or not text.strip():
                return {
                    'audio_file': '',
                    'output_file': '',
                    'status': 'error',
                    'error': 'Text is required for speech synthesis',
                    'error_type': 'invalid_input'
                }
            
            text = text.strip()
            
            # Check text length
            max_text_length = getattr(settings, "TTS_MAX_TEXT_LENGTH", 4096)
            if len(text) > max_text_length:
                return {
                    'audio_file': '',
                    'output_file': '',
                    'status': 'error',
                    'error': f'Text too long ({len(text)} chars). Maximum allowed: {max_text_length}',
                    'error_type': 'text_too_long'
                }
            
            # Resolve voice parameter
            resolved_voice = voice or getattr(settings, "TTS_VOICE", "alloy")
            
            # Generate cache key
            text_hash = hashlib.md5(f"{text}:{resolved_voice}:{output_format}".encode()).hexdigest()
            
            # Check cache first
            if use_cache and self.config.enable_tts_cache:
                cached_audio = await get_cached_tts(text_hash)
                if cached_audio:
                    self._stats['tts_cache_hits'] += 1
                    
                    # Write cached audio to file
                    target_path = output_file_path or self._ensure_output_path(None)
                    try:
                        with open(target_path, 'wb') as f:
                            f.write(cached_audio)
                        
                        response_time = (time.time() - start_time) * 1000
                        return {
                            'audio_file': target_path,
                            'output_file': target_path,
                            'voice': resolved_voice,
                            'text_length': len(text),
                            'status': 'success',
                            'cached': True,
                            'response_time_ms': response_time
                        }
                    except Exception as e:
                        logger.warning(f"Failed to write cached audio: {e}")
            
            # Generate speech
            audio_data = await self._generate_tts_audio(text, resolved_voice, output_format)
            
            if not audio_data:
                return {
                    'audio_file': '',
                    'output_file': '',
                    'status': 'error',
                    'error': 'Speech synthesis failed',
                    'error_type': 'synthesis_failed'
                }
            
            # Write to file
            target_path = output_file_path or self._ensure_output_path(None)
            with open(target_path, 'wb') as f:
                f.write(audio_data)
            
            # Cache result
            if use_cache and self.config.enable_tts_cache:
                await set_cached_tts(text_hash, audio_data, ttl=self.config.tts_cache_ttl)
            
            # Update stats
            response_time = (time.time() - start_time) * 1000
            self._stats['tts_avg_time'] = (
                (self._stats['tts_avg_time'] * (self._stats['tts_requests'] - 1) + response_time) /
                self._stats['tts_requests']
            )
            
            return {
                'audio_file': target_path,
                'output_file': target_path,
                'voice': resolved_voice,
                'text_length': len(text),
                'status': 'success',
                'cached': False,
                'response_time_ms': response_time
            }
            
        except Exception as e:
            logger.error(f"Optimized TTS failed: {e}")
            return {
                'audio_file': '',
                'output_file': '',
                'status': 'error',
                'error': str(e),
                'error_type': 'synthesis_failed',
                'response_time_ms': (time.time() - start_time) * 1000
            }
    
    async def _generate_tts_audio(self, text: str, voice: str, output_format: str) -> Optional[bytes]:
        """Generate TTS audio using optimized HTTP client"""
        if not self.client or self.test_mode:
            return await self._generate_fake_tts_audio(text)
        
        try:
            # Prepare request data
            data = {
                'model': settings.TTS_MODEL,
                'voice': voice,
                'input': text,
                'response_format': output_format,
                'speed': getattr(settings, "TTS_SPEED", 1.0)
            }
            
            # Make API request using connection pool
            response = await self._http_client.post(
                'https://api.openai.com/v1/audio/speech',
                headers={
                    'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=data
            )
            
            if response['status_code'] == 200:
                return response['data']
            else:
                logger.error(f"TTS API error: {response}")
                return None
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    async def _generate_fake_tts_audio(self, text: str) -> bytes:
        """Generate fake TTS audio for test mode"""
        # Create a simple audio file with text content
        fake_audio = b"FAKE_AUDIO_DATA:" + text.encode('utf-8')
        return fake_audio
    
    async def transcribe_audio_optimized(
        self,
        audio_file_path: Optional[str],
        language: Optional[str] = None,
        enhance_audio: bool = True
    ) -> Dict[str, Any]:
        """Optimized audio transcription with caching and performance improvements"""
        start_time = time.time()
        
        try:
            self._stats['stt_requests'] += 1
            
            # Input validation
            if not audio_file_path:
                return {
                    'text': '',
                    'status': 'error',
                    'error': 'Audio file path is required',
                    'error_type': 'invalid_input'
                }
            
            if not os.path.exists(audio_file_path):
                return {
                    'text': '',
                    'status': 'error',
                    'error': 'Audio file not found',
                    'error_type': 'file_not_found'
                }
            
            # Generate cache key
            file_stat = os.stat(audio_file_path)
            cache_data = f"{audio_file_path}:{file_stat.st_size}:{file_stat.st_mtime}:{language}"
            audio_hash = hashlib.md5(cache_data.encode()).hexdigest()
            
            # Check cache first
            if self.config.enable_stt_cache:
                cached_result = await get_cached_stt(audio_hash)
                if cached_result:
                    self._stats['stt_cache_hits'] += 1
                    cached_result['cached'] = True
                    cached_result['response_time_ms'] = (time.time() - start_time) * 1000
                    return cached_result
            
            # Enhance audio if enabled
            processed_path = audio_file_path
            if enhance_audio and self.config.enable_audio_optimization:
                enhancement_result = await self._enhance_audio_for_stt(audio_file_path)
                if enhancement_result['status'] == 'success':
                    processed_path = enhancement_result['enhanced_file']
                    self._stats['audio_optimizations'] += 1
            
            # Transcribe audio
            transcription_result = await self._transcribe_audio_file(processed_path, language)
            
            # Cache result
            if self.config.enable_stt_cache and transcription_result.get('status') == 'success':
                await set_cached_stt(audio_hash, transcription_result, ttl=self.config.stt_cache_ttl)
            
            # Update stats
            response_time = (time.time() - start_time) * 1000
            self._stats['stt_avg_time'] = (
                (self._stats['stt_avg_time'] * (self._stats['stt_requests'] - 1) + response_time) /
                self._stats['stt_requests']
            )
            
            transcription_result['response_time_ms'] = response_time
            transcription_result['cached'] = False
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Optimized STT failed: {e}")
            return {
                'text': '',
                'status': 'error',
                'error': str(e),
                'error_type': 'transcription_failed',
                'response_time_ms': (time.time() - start_time) * 1000
            }
    
    async def _transcribe_audio_file(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using optimized approach"""
        if not self.client or self.test_mode:
            return await self._transcribe_audio_test_mode(audio_file_path, language)
        
        try:
            # Read audio file
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Prepare request
            files = {
                'file': (os.path.basename(audio_file_path), audio_data, 'audio/wav')
            }
            data = {
                'model': settings.WHISPER_MODEL,
                'language': language,
                'response_format': 'verbose_json',
                'temperature': self.stt_config.transcription_temperature
            }
            
            # Make API request using connection pool
            response = await self._http_client.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers={
                    'Authorization': f'Bearer {settings.OPENAI_API_KEY}'
                },
                files=files,
                data=data
            )
            
            if response['status_code'] == 200:
                transcription_data = response['data']
                
                return {
                    'text': transcription_data.get('text', ''),
                    'language': transcription_data.get('language', language or 'unknown'),
                    'duration': transcription_data.get('duration', 0),
                    'confidence': transcription_data.get('confidence', 1.0),
                    'segments': transcription_data.get('segments', []),
                    'status': 'success'
                }
            else:
                logger.error(f"STT API error: {response}")
                return {
                    'text': '',
                    'status': 'error',
                    'error': f"API error: {response.get('error', 'Unknown error')}",
                    'error_type': 'api_error'
                }
                
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                'text': '',
                'status': 'error',
                'error': str(e),
                'error_type': 'transcription_failed'
            }
    
    async def _transcribe_audio_test_mode(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Test mode transcription"""
        file_size = os.path.getsize(audio_file_path)
        duration_estimate = file_size / (128000 / 8)  # Rough estimate
        
        return {
            'text': f"[Test mode transcription of {os.path.basename(audio_file_path)}]",
            'language': language or 'unknown',
            'duration': duration_estimate,
            'confidence': 0.0,
            'segments': [],
            'status': 'success'
        }
    
    async def _enhance_audio_for_stt(self, audio_file_path: str) -> Dict[str, Any]:
        """Enhance audio quality for better transcription"""
        try:
            # This would implement audio enhancement using librosa, noisereduce, etc.
            # For now, return the original file path
            
            # In a real implementation, you would:
            # 1. Load audio with librosa
            # 2. Apply noise reduction
            # 3. Normalize audio
            # 4. Save enhanced audio
            # 5. Return enhanced file path
            
            return {
                'status': 'success',
                'original_file': audio_file_path,
                'enhanced_file': audio_file_path,
                'enhancements_applied': ['placeholder']
            }
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'enhanced_file': audio_file_path
            }
    
    async def batch_synthesize_speech(
        self,
        texts: List[str],
        voice: Optional[str] = None,
        output_format: str = "mp3"
    ) -> List[Dict[str, Any]]:
        """Batch TTS synthesis with concurrent processing"""
        if not texts:
            return []
        
        # Limit batch size
        batch_texts = texts[:self.config.tts_batch_size]
        
        # Create tasks for concurrent processing
        tasks = []
        for text in batch_texts:
            task = self.synthesize_speech_optimized(
                text=text,
                voice=voice,
                output_format=output_format
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'audio_file': '',
                    'output_file': '',
                    'status': 'error',
                    'error': str(result),
                    'error_type': 'batch_error',
                    'text': batch_texts[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def batch_transcribe_audio(
        self,
        audio_files: List[str],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Batch audio transcription with concurrent processing"""
        if not audio_files:
            return []
        
        # Limit batch size
        batch_files = audio_files[:self.config.stt_batch_size]
        
        # Create tasks for concurrent processing
        tasks = []
        for audio_file in batch_files:
            task = self.transcribe_audio_optimized(
                audio_file_path=audio_file,
                language=language
            )
            tasks.append(task)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'text': '',
                    'status': 'error',
                    'error': str(result),
                    'error_type': 'batch_error',
                    'audio_file': batch_files[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get voice service performance statistics"""
        tts_cache_hit_rate = (self._stats['tts_cache_hits'] / 
                             max(1, self._stats['tts_requests']))
        stt_cache_hit_rate = (self._stats['stt_cache_hits'] / 
                             max(1, self._stats['stt_requests']))
        
        return {
            'tts': {
                'total_requests': self._stats['tts_requests'],
                'cache_hits': self._stats['tts_cache_hits'],
                'cache_hit_rate': tts_cache_hit_rate,
                'avg_response_time_ms': self._stats['tts_avg_time'],
                'max_concurrent': self.config.max_concurrent_tts
            },
            'stt': {
                'total_requests': self._stats['stt_requests'],
                'cache_hits': self._stats['stt_cache_hits'],
                'cache_hit_rate': stt_cache_hit_rate,
                'avg_response_time_ms': self._stats['stt_avg_time'],
                'max_concurrent': self.config.max_concurrent_stt
            },
            'audio_optimizations': self._stats['audio_optimizations'],
            'config': {
                'tts_cache_enabled': self.config.enable_tts_cache,
                'stt_cache_enabled': self.config.enable_stt_cache,
                'audio_optimization_enabled': self.config.enable_audio_optimization
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on voice service"""
        health = {
            'status': 'healthy',
            'components': {},
            'performance': {}
        }
        
        try:
            # Test TTS
            tts_result = await self.synthesize_speech_optimized("Health check test")
            health['components']['tts'] = {
                'status': 'healthy' if tts_result['status'] == 'success' else 'unhealthy',
                'response_time_ms': tts_result.get('response_time_ms', 0)
            }
            
            # Test STT
            # Create a temporary test audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(b"fake audio data")
                temp_path = temp_file.name
            
            try:
                stt_result = await self.transcribe_audio_optimized(temp_path)
                health['components']['stt'] = {
                    'status': 'healthy' if stt_result['status'] == 'success' else 'unhealthy',
                    'response_time_ms': stt_result.get('response_time_ms', 0)
                }
            finally:
                os.unlink(temp_path)
            
            # Performance metrics
            health['performance'] = self.get_performance_stats()
            
            # Check overall health
            component_statuses = [comp['status'] for comp in health['components'].values()]
            if any(status == 'unhealthy' for status in component_statuses):
                health['status'] = 'degraded'
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def clear_cache(self):
        """Clear voice service caches"""
        try:
            await cache_manager.clear_namespace('tts')
            await cache_manager.clear_namespace('stt')
            logger.info("Voice service caches cleared")
        except Exception as e:
            logger.error(f"Failed to clear voice caches: {e}")
    
    async def shutdown(self):
        """Shutdown optimized voice service"""
        try:
            # Shutdown thread pools
            self._tts_executor.shutdown(wait=True)
            self._stt_executor.shutdown(wait=True)
            
            logger.info("Optimized voice service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during voice service shutdown: {e}")

# Global optimized voice service instance
optimized_voice_service = OptimizedVoiceService()