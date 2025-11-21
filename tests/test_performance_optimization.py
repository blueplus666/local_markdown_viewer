#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三阶段性能优化测试 v1.0.0
测试高性能文件读取器、渲染性能优化器、内存优化管理器和性能基准测试器

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import os
import sys
import time
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入性能优化组件
from core.high_performance_file_reader import (
    HighPerformanceFileReader, ReadStrategy, FileType, FileInfo, ReadMetrics
)
from core.render_performance_optimizer import (
    RenderPerformanceOptimizer, RenderStrategy, RenderMode, RenderMetrics, RenderChunk
)
from core.memory_optimization_manager import (
    MemoryOptimizationManager, MemoryStrategy, MemoryThreshold, MemoryInfo, MemoryMetrics
)
from core.performance_benchmark import (
    PerformanceBenchmark, BenchmarkType, BenchmarkResultEnum, BenchmarkResult, BenchmarkMetrics
)


class TestHighPerformanceFileReader(unittest.TestCase):
    """测试高性能文件读取器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.md"
        
        # 创建测试文件
        test_content = "# 测试文件\n\n这是一个用于测试的Markdown文件。\n" * 100
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        self.file_reader = HighPerformanceFileReader()
    
    def tearDown(self):
        """测试后清理"""
        self.file_reader.shutdown()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_file_reader_initialization(self):
        """测试文件读取器初始化"""
        self.assertIsNotNone(self.file_reader)
        self.assertIsNotNone(self.file_reader.cache_manager)
        self.assertIsNotNone(self.file_reader.error_handler)
    
    def test_read_file_sync(self):
        """测试同步文件读取"""
        result = self.file_reader.read_file(str(self.test_file), ReadStrategy.SYNC)
        
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('metrics', result)
        self.assertIn('file_info', result)
        
        # 验证文件信息
        file_info = result['file_info']
        self.assertEqual(file_info['file_type'], 'markdown')
        self.assertGreater(file_info['size'], 0)
    
    def test_read_file_mapped(self):
        """测试内存映射文件读取"""
        result = self.file_reader.read_file(str(self.test_file), ReadStrategy.MAPPED)
        
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('metrics', result)
    
    def test_read_file_streaming(self):
        """测试流式文件读取"""
        result = self.file_reader.read_file(str(self.test_file), ReadStrategy.STREAMING)
        
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        self.assertIn('metrics', result)
    
    def test_file_info_cache(self):
        """测试文件信息缓存"""
        # 第一次读取
        info1 = self.file_reader.get_file_info(str(self.test_file))
        self.assertIsNotNone(info1)
        
        # 第二次读取应该从缓存获取
        info2 = self.file_reader.get_file_info(str(self.test_file))
        self.assertEqual(info1.path, info2.path)
    
    def test_read_stats(self):
        """测试读取统计信息"""
        # 执行几次读取
        for _ in range(3):
            self.file_reader.read_file(str(self.test_file))
        
        stats = self.file_reader.get_read_stats()
        self.assertGreater(stats['total_reads'], 0)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('strategy_usage', stats)


class TestRenderPerformanceOptimizer(unittest.TestCase):
    """测试渲染性能优化器"""
    
    def setUp(self):
        """测试前准备"""
        self.renderer = RenderPerformanceOptimizer()
        self.test_content = "# 测试内容\n\n这是一个测试Markdown内容。\n" * 50
    
    def tearDown(self):
        """测试后清理"""
        self.renderer.shutdown()
    
    def test_renderer_initialization(self):
        """测试渲染器初始化"""
        self.assertIsNotNone(self.renderer)
        self.assertIsNotNone(self.renderer.cache_manager)
        self.assertIsNotNone(self.renderer.error_handler)
    
    def test_render_content_single_thread(self):
        """测试单线程渲染"""
        result = self.renderer.render_content(
            self.test_content, 
            RenderStrategy.SINGLE_THREAD, 
            RenderMode.FULL
        )
        
        self.assertTrue(result['success'])
        self.assertIn('html', result)
        self.assertIn('metrics', result)
        self.assertIn('content_hash', result)
    
    def test_render_content_multi_thread(self):
        """测试多线程渲染"""
        result = self.renderer.render_content(
            self.test_content, 
            RenderStrategy.MULTI_THREAD, 
            RenderMode.FULL
        )
        
        self.assertTrue(result['success'])
        self.assertIn('html', result)
        self.assertIn('metrics', result)
    
    def test_render_content_incremental(self):
        """测试增量渲染"""
        result = self.renderer.render_content(
            self.test_content, 
            RenderStrategy.INCREMENTAL, 
            RenderMode.FULL
        )
        
        self.assertTrue(result['success'])
        self.assertIn('html', result)
        self.assertIn('metrics', result)
    
    def test_render_content_lazy(self):
        """测试懒加载渲染"""
        result = self.renderer.render_content(
            self.test_content, 
            RenderStrategy.LAZY, 
            RenderMode.SKELETON
        )
        
        self.assertTrue(result['success'])
        self.assertIn('html', result)
        self.assertIn('metrics', result)
    
    def test_render_file(self):
        """测试文件渲染"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(self.test_content)
            temp_file = f.name
        
        try:
            result = self.renderer.render_file(temp_file)
            self.assertTrue(result['success'])
            self.assertIn('html', result)
        finally:
            os.unlink(temp_file)
    
    def test_render_stats(self):
        """测试渲染统计信息"""
        # 执行几次渲染
        for _ in range(3):
            self.renderer.render_content(self.test_content)
        
        stats = self.renderer.get_render_stats()
        self.assertGreater(stats['total_renders'], 0)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('strategy_usage', stats)


class TestMemoryOptimizationManager(unittest.TestCase):
    """测试内存优化管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.memory_manager = MemoryOptimizationManager()
    
    def tearDown(self):
        """测试后清理"""
        self.memory_manager.shutdown()
    
    def test_memory_manager_initialization(self):
        """测试内存管理器初始化"""
        self.assertIsNotNone(self.memory_manager)
        self.assertIsNotNone(self.memory_manager.cache_manager)
        self.assertIsNotNone(self.memory_manager.error_handler)
    
    def test_get_memory_info(self):
        """测试获取内存信息"""
        memory_info = self.memory_manager.get_memory_info()
        
        self.assertIsNotNone(memory_info)
        self.assertGreater(memory_info.total_memory_mb, 0)
        self.assertGreaterEqual(memory_info.memory_percent, 0)
        self.assertLessEqual(memory_info.memory_percent, 1)
    
    def test_memory_strategy_management(self):
        """测试内存策略管理"""
        # 测试设置策略
        self.memory_manager.set_memory_strategy(MemoryStrategy.AGGRESSIVE)
        self.assertEqual(self.memory_manager.strategy, MemoryStrategy.AGGRESSIVE)
        
        self.memory_manager.set_memory_strategy(MemoryStrategy.CONSERVATIVE)
        self.assertEqual(self.memory_manager.strategy, MemoryStrategy.CONSERVATIVE)
    
    def test_memory_threshold_management(self):
        """测试内存阈值管理"""
        # 测试设置阈值
        self.memory_manager.set_memory_threshold(MemoryThreshold.HIGH, 0.8)
        self.assertEqual(self.memory_manager.memory_thresholds[MemoryThreshold.HIGH], 0.8)
    
    def test_manual_memory_optimization(self):
        """测试手动内存优化"""
        result = self.memory_manager.optimize_memory()
        self.assertIsNotNone(result)
    
    def test_memory_stats(self):
        """测试内存统计信息"""
        stats = self.memory_manager.get_memory_stats()
        
        self.assertIn('strategy', stats)
        self.assertIn('monitoring_interval', stats)
        self.assertIn('gc_collections', stats)
        self.assertIn('memory_thresholds', stats)


class TestPerformanceBenchmark(unittest.TestCase):
    """测试性能基准测试器"""
    
    def setUp(self):
        """测试前准备"""
        self.benchmark = PerformanceBenchmark()
    
    def tearDown(self):
        """测试后清理"""
        self.benchmark.shutdown()
    
    def test_benchmark_initialization(self):
        """测试基准测试器初始化"""
        self.assertIsNotNone(self.benchmark)
        self.assertIsNotNone(self.benchmark.file_reader)
        self.assertIsNotNone(self.benchmark.render_optimizer)
        self.assertIsNotNone(self.benchmark.memory_manager)
    
    def test_create_test_files(self):
        """测试创建测试文件"""
        test_dir = Path(tempfile.mkdtemp())
        try:
            test_files = self.benchmark.create_test_files(test_dir)
            self.assertEqual(len(test_files), 3)  # small, medium, large
            
            for test_file in test_files:
                self.assertTrue(test_file.exists())
                self.assertGreater(test_file.stat().st_size, 0)
        finally:
            import shutil
            shutil.rmtree(test_dir)
    
    def test_file_read_benchmark(self):
        """测试文件读取基准测试"""
        # 创建测试文件
        test_dir = Path(tempfile.mkdtemp())
        try:
            test_files = self.benchmark.create_test_files(test_dir)
            
            # 运行文件读取基准测试
            results = self.benchmark.benchmark_file_read(test_files)
            
            self.assertGreater(len(results), 0)
            
            for result in results:
                self.assertIsNotNone(result.metrics)
                self.assertIsNotNone(result.baseline_comparison)
                self.assertIsNotNone(result.recommendations)
        finally:
            import shutil
            shutil.rmtree(test_dir)
    
    def test_render_benchmark(self):
        """测试渲染基准测试"""
        # 创建测试文件
        test_dir = Path(tempfile.mkdtemp())
        try:
            test_files = self.benchmark.create_test_files(test_dir)
            
            # 运行渲染基准测试
            results = self.benchmark.benchmark_render(test_files)
            
            self.assertGreater(len(results), 0)
            
            for result in results:
                self.assertIsNotNone(result.metrics)
                self.assertIsNotNone(result.baseline_comparison)
                self.assertIsNotNone(result.recommendations)
        finally:
            import shutil
            shutil.rmtree(test_dir)
    
    def test_memory_benchmark(self):
        """测试内存基准测试"""
        results = self.benchmark.benchmark_memory()
        
        self.assertGreater(len(results), 0)
        
        for result in results:
            self.assertIsNotNone(result.metrics)
            self.assertIsNotNone(result.baseline_comparison)
            self.assertIsNotNone(result.recommendations)
    
    def test_integration_benchmark(self):
        """测试集成基准测试"""
        results = self.benchmark.benchmark_integration()
        
        self.assertGreater(len(results), 0)
        
        for result in results:
            self.assertIsNotNone(result.metrics)
            self.assertIsNotNone(result.baseline_comparison)
            self.assertIsNotNone(result.recommendations)
    
    def test_generate_report(self):
        """测试生成性能报告"""
        # 运行一些基准测试
        test_dir = Path(tempfile.mkdtemp())
        try:
            test_files = self.benchmark.create_test_files(test_dir)
            
            results = {
                BenchmarkType.FILE_READ.value: self.benchmark.benchmark_file_read(test_files),
                BenchmarkType.RENDER.value: self.benchmark.benchmark_render(test_files),
                BenchmarkType.MEMORY.value: self.benchmark.benchmark_memory(),
                BenchmarkType.INTEGRATION.value: self.benchmark.benchmark_integration()
            }
            
            # 生成报告
            report = self.benchmark.generate_report(results)
            
            self.assertIsInstance(report, str)
            self.assertIn("性能基准测试报告", report)
            self.assertIn("测试总结", report)
        finally:
            import shutil
            shutil.rmtree(test_dir)


class TestPerformanceOptimizationIntegration(unittest.TestCase):
    """测试性能优化集成"""
    
    def setUp(self):
        """测试前准备"""
        _t_all = time.perf_counter()
        _t0 = time.perf_counter(); self.file_reader = HighPerformanceFileReader(); print(f"[BASE] setup.file_reader: {time.perf_counter() - _t0:.3f}s")
        _t1 = time.perf_counter(); self.renderer = RenderPerformanceOptimizer(); print(f"[BASE] setup.renderer: {time.perf_counter() - _t1:.3f}s")
        _t2 = time.perf_counter(); self.memory_manager = MemoryOptimizationManager(); print(f"[BASE] setup.memory_manager: {time.perf_counter() - _t2:.3f}s")
        _t3 = time.perf_counter(); self.benchmark = PerformanceBenchmark(); print(f"[BASE] setup.benchmark: {time.perf_counter() - _t3:.3f}s")
        
        # 创建测试文件
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "integration_test.md"
        
        test_content = "# 集成测试\n\n这是一个用于集成测试的Markdown文件。\n" * 200
        _t4 = time.perf_counter()
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"[BASE] setup.file_io: {time.perf_counter() - _t4:.3f}s")
        print(f"[BASE] setup.total: {time.perf_counter() - _t_all:.3f}s")
    
    def tearDown(self):
        """测试后清理"""
        _t_all = time.perf_counter()
        _t0 = time.perf_counter(); self.file_reader.shutdown(); print(f"[BASE] teardown.file_reader.shutdown: {time.perf_counter() - _t0:.3f}s")
        _t1 = time.perf_counter(); self.renderer.shutdown(); print(f"[BASE] teardown.renderer.shutdown: {time.perf_counter() - _t1:.3f}s")
        _t2 = time.perf_counter(); self.memory_manager.shutdown(); print(f"[BASE] teardown.memory_manager.shutdown: {time.perf_counter() - _t2:.3f}s")
        _t3 = time.perf_counter(); self.benchmark.shutdown(); print(f"[BASE] teardown.benchmark.shutdown: {time.perf_counter() - _t3:.3f}s")
        
        import shutil
        _t4 = time.perf_counter(); shutil.rmtree(self.temp_dir); print(f"[BASE] teardown.cleanup: {time.perf_counter() - _t4:.3f}s")
        print(f"[BASE] teardown.total: {time.perf_counter() - _t_all:.3f}s")
    
    def test_end_to_end_performance_workflow(self):
        """测试端到端性能工作流"""
        _t_all = time.perf_counter()
        _t0 = time.perf_counter()
        read_result = self.file_reader.read_file(str(self.test_file), ReadStrategy.MAPPED)
        print(f"[PROF] e2e.read: {time.perf_counter() - _t0:.3f}s")
        self.assertTrue(read_result['success'])
        
        _t1 = time.perf_counter()
        render_result = self.renderer.render_content(
            read_result['content'], 
            RenderStrategy.MULTI_THREAD, 
            RenderMode.FULL
        )
        print(f"[PROF] e2e.render: {time.perf_counter() - _t1:.3f}s")
        self.assertTrue(render_result['success'])
        
        _t2 = time.perf_counter()
        memory_info = self.memory_manager.optimize_memory()
        print(f"[PROF] e2e.optimize_memory: {time.perf_counter() - _t2:.3f}s")
        self.assertIsNotNone(memory_info)
        
        _t3 = time.perf_counter()
        benchmark_results = self.benchmark.benchmark_file_read([self.test_file])
        print(f"[PROF] e2e.benchmark_file_read: {time.perf_counter() - _t3:.3f}s")
        self.assertGreater(len(benchmark_results), 0)
        print(f"[PROF] e2e.total: {time.perf_counter() - _t_all:.3f}s")
        
        # 验证整个流程的性能指标
        read_metrics = read_result['metrics']
        render_metrics = render_result['metrics']
        
        self.assertGreater(read_metrics['throughput_mbps'], 0)
        self.assertGreater(render_metrics['render_speed_chars_per_ms'], 0)
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        _t_all = time.perf_counter()
        _t_loop = time.perf_counter()
        for _ in range(5):
            self.file_reader.read_file(str(self.test_file))
            self.renderer.render_content("# 测试内容\n", RenderStrategy.SINGLE_THREAD)
        print(f"[PROF] mon.loop: {time.perf_counter() - _t_loop:.3f}s")
        
        _t0 = time.perf_counter(); read_stats = self.file_reader.get_read_stats(); print(f"[PROF] mon.get_read_stats: {time.perf_counter() - _t0:.3f}s")
        _t1 = time.perf_counter(); render_stats = self.renderer.get_render_stats(); print(f"[PROF] mon.get_render_stats: {time.perf_counter() - _t1:.3f}s")
        _t2 = time.perf_counter(); memory_stats = self.memory_manager.get_memory_stats(); print(f"[PROF] mon.get_memory_stats: {time.perf_counter() - _t2:.3f}s")
        print(f"[PROF] mon.total: {time.perf_counter() - _t_all:.3f}s")
        
        # 验证统计信息
        self.assertGreater(read_stats['total_reads'], 0)
        self.assertGreater(render_stats['total_renders'], 0)
        self.assertIn('strategy', memory_stats)


def run_performance_tests():
    """运行性能测试"""
    print("🚀 开始运行第三阶段性能优化测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestHighPerformanceFileReader,
        TestRenderPerformanceOptimizer,
        TestMemoryOptimizationManager,
        TestPerformanceBenchmark,
        TestPerformanceOptimizationIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print(f"\n📊 测试结果总结:")
    print(f"- 运行测试: {result.testsRun}")
    print(f"- 失败: {len(result.failures)}")
    print(f"- 错误: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！第三阶段性能优化实施成功！")
    else:
        print("\n⚠️ 部分测试失败，请检查实现代码。")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1) 