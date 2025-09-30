import time
import statistics
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from document_processor import DocumentProcessor
    from rag_handler import RAGHandler
    from voice_service import VoiceService
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Some benchmarks may not run properly")

class PerformanceBenchmark:
    def __init__(self):
        self.results = {}
        self.test_files = []

    def create_test_files(self):
        """Create test files of various sizes"""
        test_files = {}

        # Small document (< 1KB)
        small_content = "This is a small test document for performance testing. " * 10
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(small_content)
            test_files['small'] = f.name

        # Medium document (~ 10KB)
        medium_content = "This is a medium-sized test document for performance testing. " * 200
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(medium_content)
            test_files['medium'] = f.name

        # Large document (~ 100KB)
        large_content = "This is a large test document for performance testing. " * 2000
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            test_files['large'] = f.name

        self.test_files = list(test_files.values())
        return test_files

    def cleanup_test_files(self):
        """Clean up created test files"""
        for file_path in self.test_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")

    async def benchmark_document_processing(self):
        """Benchmark document processing pipeline"""
        print("🔄 Benchmarking document processing...")

        try:
            processor = DocumentProcessor()
            test_files = self.create_test_files()
            results = {}

            for size_name, file_path in test_files.items():
                if not os.path.exists(file_path):
                    continue

                print(f"  Testing {size_name} document...")
                times = []

                # Run multiple iterations for average
                for i in range(3):
                    start_time = time.time()
                    try:
                        docs = processor.load_document(file_path)
                        chunks = processor.split_documents(docs)
                        end_time = time.time()
                        processing_time = end_time - start_time
                        times.append(processing_time)
                        print(f"    Iteration {i+1}: {processing_time:.3f}s, {len(chunks)} chunks")
                    except Exception as e:
                        print(f"    Error in iteration {i+1}: {e}")
                        continue

                if times:
                    results[size_name] = {
                        "avg_time": statistics.mean(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                        "file_size": os.path.getsize(file_path),
                        "iterations": len(times)
                    }

            self.results['document_processing'] = results
            return results

        except Exception as e:
            print(f"Error in document processing benchmark: {e}")
            return {}

    async def benchmark_query_performance(self):
        """Benchmark query response times"""
        print("🔍 Benchmarking query performance...")

        try:
            rag_handler = RAGHandler()

            test_queries = [
                "What is the main topic?",
                "Summarize the key points",
                "What are the conclusions?",
                "Can you provide more details about the methodology?",
                "What are the limitations mentioned?",
                "How does this relate to current research?",
                "What are the practical applications?",
                "What future work is suggested?"
            ]

            times = []
            successful_queries = 0

            for i, query in enumerate(test_queries):
                print(f"  Query {i+1}/{len(test_queries)}: '{query[:30]}...'")
                start_time = time.time()
                try:
                    result = rag_handler.ask_question(query)
                    end_time = time.time()
                    query_time = end_time - start_time
                    times.append(query_time)
                    successful_queries += 1
                    print(f"    Response time: {query_time:.3f}s")
                except Exception as e:
                    print(f"    Error: {e}")
                    continue

            if times:
                results = {
                    "total_queries": len(test_queries),
                    "successful_queries": successful_queries,
                    "success_rate": successful_queries / len(test_queries) * 100,
                    "avg_time": statistics.mean(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                    "queries_per_second": 1 / statistics.mean(times) if times else 0
                }

                print(f"  Average query time: {results['avg_time']:.3f}s")
                print(f"  Success rate: {results['success_rate']:.1f}%")
                print(f"  Queries per second: {results['queries_per_second']:.2f}")

                self.results['query_performance'] = results
                return results
            else:
                print("  No successful queries to benchmark")
                return {}

        except Exception as e:
            print(f"Error in query performance benchmark: {e}")
            return {}

    async def benchmark_concurrent_queries(self):
        """Test concurrent query handling"""
        print("⚡ Benchmarking concurrent query performance...")

        try:
            rag_handler = RAGHandler()

            async def single_query(query_id):
                start_time = time.time()
                try:
                    result = rag_handler.ask_question(f"Test query number {query_id}")
                    end_time = time.time()
                    return {
                        "query_id": query_id,
                        "time": end_time - start_time,
                        "success": True
                    }
                except Exception as e:
                    end_time = time.time()
                    return {
                        "query_id": query_id,
                        "time": end_time - start_time,
                        "success": False,
                        "error": str(e)
                    }

            concurrency_levels = [1, 2, 5, 10]
            results = {}

            for level in concurrency_levels:
                print(f"  Testing concurrency level: {level}")
                tasks = [single_query(i) for i in range(level)]

                start_time = time.time()
                query_results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time

                successful = [r for r in query_results if r['success']]
                if successful:
                    times = [r['time'] for r in successful]
                    results[level] = {
                        "total_queries": level,
                        "successful_queries": len(successful),
                        "success_rate": len(successful) / level * 100,
                        "total_time": total_time,
                        "avg_query_time": statistics.mean(times),
                        "max_query_time": max(times),
                        "throughput": len(successful) / total_time
                    }
                    print(f"    Success rate: {results[level]['success_rate']:.1f}%")
                    print(f"    Avg time: {results[level]['avg_query_time']:.3f}s")
                    print(f"    Throughput: {results[level]['throughput']:.2f} queries/s")

            self.results['concurrent_queries'] = results
            return results

        except Exception as e:
            print(f"Error in concurrent query benchmark: {e}")
            return {}

    async def benchmark_voice_processing(self):
        """Benchmark voice processing if available"""
        print("🎤 Benchmarking voice processing...")

        try:
            voice_service = VoiceService()

            # Test getting available voices
            start_time = time.time()
            voices = voice_service.get_available_voices()
            voices_time = time.time() - start_time

            # Test TTS if possible
            tts_times = []
            test_texts = [
                "Hello world",
                "This is a test of text-to-speech functionality",
                "The quick brown fox jumps over the lazy dog"
            ]

            for text in test_texts:
                try:
                    start_time = time.time()
                    result = voice_service.synthesize_speech(text, "alloy")
                    tts_time = time.time() - start_time
                    tts_times.append(tts_time)

                    # Cleanup generated audio file
                    if result.get("status") == "success" and "audio_file" in result:
                        if os.path.exists(result["audio_file"]):
                            os.unlink(result["audio_file"])

                except Exception as e:
                    print(f"    TTS error for '{text}': {e}")
                    continue

            results = {
                "voices_available": len(voices),
                "voices_lookup_time": voices_time,
                "tts_tests": len(test_texts),
                "tts_successful": len(tts_times)
            }

            if tts_times:
                results.update({
                    "avg_tts_time": statistics.mean(tts_times),
                    "min_tts_time": min(tts_times),
                    "max_tts_time": max(tts_times)
                })

            print(f"  Available voices: {results['voices_available']}")
            print(f"  TTS success rate: {results['tts_successful']}/{results['tts_tests']}")

            self.results['voice_processing'] = results
            return results

        except Exception as e:
            print(f"Error in voice processing benchmark: {e}")
            return {}

    def generate_report(self):
        """Generate a comprehensive performance report"""
        print("\n" + "="*60)
        print("🚀 PERFORMANCE BENCHMARK REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if 'document_processing' in self.results:
            print("📄 Document Processing Performance:")
            for size, data in self.results['document_processing'].items():
                print(f"  {size.capitalize()} files:")
                print(f"    Average time: {data['avg_time']:.3f}s")
                print(f"    File size: {data['file_size']:,} bytes")
                print(f"    Processing rate: {data['file_size']/data['avg_time']/1024:.1f} KB/s")

        if 'query_performance' in self.results:
            print("\n🔍 Query Performance:")
            data = self.results['query_performance']
            print(f"  Success rate: {data['success_rate']:.1f}%")
            print(f"  Average response time: {data['avg_time']:.3f}s")
            print(f"  Queries per second: {data['queries_per_second']:.2f}")

        if 'concurrent_queries' in self.results:
            print("\n⚡ Concurrent Query Performance:")
            for level, data in self.results['concurrent_queries'].items():
                print(f"  Concurrency {level}:")
                print(f"    Success rate: {data['success_rate']:.1f}%")
                print(f"    Throughput: {data['throughput']:.2f} queries/s")

        if 'voice_processing' in self.results:
            print("\n🎤 Voice Processing Performance:")
            data = self.results['voice_processing']
            print(f"  Available voices: {data['voices_available']}")
            print(f"  TTS success rate: {data['tts_successful']}/{data['tts_tests']}")
            if 'avg_tts_time' in data:
                print(f"  Average TTS time: {data['avg_tts_time']:.3f}s")

        print("\n" + "="*60)

    def save_results(self, filename=None):
        """Save benchmark results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"benchmark_results_{timestamp}.json"

        results_with_metadata = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_version": "1.0",
            "results": self.results
        }

        try:
            with open(filename, 'w') as f:
                json.dump(results_with_metadata, f, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

async def main():
    """Run all benchmarks"""
    print("🏃 Starting Performance Benchmarks...")
    print("="*60)

    benchmark = PerformanceBenchmark()

    try:
        # Run all benchmarks
        await benchmark.benchmark_document_processing()
        await benchmark.benchmark_query_performance()
        await benchmark.benchmark_concurrent_queries()
        await benchmark.benchmark_voice_processing()

        # Generate and save report
        benchmark.generate_report()
        benchmark.save_results()

    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
    finally:
        # Cleanup
        benchmark.cleanup_test_files()
        print("\n✅ Benchmark completed")

if __name__ == "__main__":
    asyncio.run(main())