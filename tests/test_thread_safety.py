#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程安全测试用例 v1.0.0
LAD-IMPL-006A: 架构修正方案实施
测试所有组件的线程安全性

作者: LAD Team
创建时间: 2025-10-11
"""

import sys
import unittest
import threading
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_manager import ConfigManager
from core.application_state_manager import ApplicationStateManager
from core.snapshot_manager import SnapshotManager
from core.unified_cache_manager import UnifiedCacheManager
from core.performance_metrics import PerformanceMetrics


class TestThreadSafety(unittest.TestCase):
    """
    线程安全测试用例
    测试ApplicationStateManager、SnapshotManager和UnifiedCacheManager的并发安全性
    """
    
    def setUp(self):
        """测试前准备"""
        self.config_manager = ConfigManager()
        self.state_manager = ApplicationStateManager(self.config_manager)
        self.snapshot_manager = SnapshotManager(self.config_manager)
        self.cache_manager = UnifiedCacheManager()
        self.performance_metrics = PerformanceMetrics(self.config_manager)
        
        # 设置依赖关系
        self.state_manager.set_snapshot_manager(self.snapshot_manager)
        self.state_manager.set_performance_metrics(self.performance_metrics)
        self.snapshot_manager.set_cache_manager(self.cache_manager)
        
        # 测试结果收集
        self.test_results = []
        self.test_errors = []
    
    def test_concurrent_module_updates(self):
        """测试1：并发模块状态更新"""
        print("\n=== 测试1：并发模块状态更新 ===")
        
        def update_module_status(thread_id: int) -> Dict[str, Any]:
            """模拟并发更新操作"""
            results = {'thread_id': thread_id, 'updates': [], 'errors': []}
            
            for i in range(10):
                try:
                    status_data = {
                        'function_mapping_status': f'status_{thread_id}_{i}',
                        'thread_id': thread_id,
                        'iteration': i,
                        'timestamp': time.time(),
                        'required_functions': [f'func_{thread_id}_{i}'],
                        'available_functions': [f'func_{thread_id}_{i}']
                    }
                    
                    success = self.state_manager.update_module_status(
                        f'test_module_{thread_id}', 
                        status_data
                    )
                    
                    results['updates'].append({
                        'iteration': i,
                        'success': success,
                        'timestamp': time.time()
                    })
                    
                    if not success:
                        results['errors'].append(
                            f"Update failed in thread {thread_id}, iteration {i}"
                        )
                    
                    time.sleep(0.001)  # 模拟处理时间
                    
                except Exception as e:
                    results['errors'].append(
                        f"Exception in thread {thread_id}, iteration {i}: {e}"
                    )
            
            return results
        
        # 启动5个线程并发更新
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_module_status, i) for i in range(5)]
            results = concurrent.futures.wait(futures, timeout=30)
            
            # 收集结果
            for future in results.done:
                try:
                    result = future.result()
                    self.test_results.append(result)
                    self.test_errors.extend(result['errors'])
                except Exception as e:
                    self.test_errors.append(f"Future result error: {e}")
        
        # 验证结果
        print(f"完成的更新操作: {sum(len(r['updates']) for r in self.test_results)}")
        print(f"错误数量: {len(self.test_errors)}")
        
        self.assertEqual(
            len(self.test_errors), 0, 
            f"并发更新测试出现错误: {self.test_errors[:3]}"
        )
        
        # 验证最终状态一致性
        for i in range(5):
            final_status = self.state_manager.get_module_status(f'test_module_{i}')
            self.assertIsNotNone(final_status, f"模块 test_module_{i} 状态为空")
            self.assertIn('_lock_info', final_status, "缺少锁信息")
        
        print("✅ 测试1通过：并发更新正常，状态一致")
    
    def test_snapshot_consistency(self):
        """测试2：快照一致性"""
        print("\n=== 测试2：快照一致性 ===")
        
        def concurrent_snapshot_operations(module_name: str) -> Dict[str, Any]:
            """并发快照操作"""
            results = {'module_name': module_name, 'operations': [], 'errors': []}
            
            for i in range(5):
                try:
                    # 保存快照
                    data = {
                        'iteration': i,
                        'module': module_name,
                        'function_mapping_status': f'status_{i}',
                        'timestamp': time.time()
                    }
                    
                    save_success = self.snapshot_manager.save_module_snapshot(
                        module_name, data
                    )
                    
                    # 立即读取快照
                    snapshot = self.snapshot_manager.get_module_snapshot(module_name)
                    
                    results['operations'].append({
                        'iteration': i,
                        'save_success': save_success,
                        'snapshot_valid': snapshot.get('module') == module_name,
                        'snapshot_iteration': snapshot.get('iteration', -1)
                    })
                    
                    if not save_success:
                        results['errors'].append(
                            f"Save failed for {module_name}, iteration {i}"
                        )
                    
                    if snapshot.get('module') != module_name:
                        results['errors'].append(
                            f"Snapshot inconsistent for {module_name}, iteration {i}"
                        )
                    
                    time.sleep(0.001)  # 模拟处理时间
                    
                except Exception as e:
                    results['errors'].append(
                        f"Exception in {module_name}, iteration {i}: {e}"
                    )
            
            return results
        
        # 多线程并发操作不同模块
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(concurrent_snapshot_operations, f'module_{i}') 
                for i in range(3)
            ]
            results = concurrent.futures.wait(futures, timeout=30)
            
            # 收集结果
            for future in results.done:
                try:
                    result = future.result()
                    self.test_results.append(result)
                    self.test_errors.extend(result['errors'])
                except Exception as e:
                    self.test_errors.append(f"Future result error: {e}")
        
        # 验证结果
        print(f"完成的快照操作: {sum(len(r['operations']) for r in self.test_results)}")
        print(f"错误数量: {len(self.test_errors)}")
        
        self.assertEqual(
            len(self.test_errors), 0, 
            f"快照一致性测试出现错误: {self.test_errors[:3]}"
        )
        
        print("✅ 测试2通过：快照一致性正常")
    
    def test_cache_atomic_operations(self):
        """测试3：缓存原子操作"""
        print("\n=== 测试3：缓存原子操作 ===")
        
        def concurrent_atomic_operations(operation_id: int) -> Dict[str, Any]:
            """并发原子操作"""
            results = {'operation_id': operation_id, 'operations': [], 'errors': []}
            
            for i in range(10):
                try:
                    key = f"atomic_test_{operation_id}"
                    
                    # 原子递增操作
                    new_value = self.cache_manager.atomic_increment(key, 1)
                    
                    # 比较并交换操作
                    cas_key = f"{key}_cas"
                    cas_success = self.cache_manager.compare_and_swap(
                        cas_key, i-1, i
                    )
                    
                    # 原子字典更新
                    dict_key = f"{key}_dict"
                    self.cache_manager.atomic_set(dict_key, {})
                    dict_success = self.cache_manager.atomic_update_dict(
                        dict_key, {f'field_{i}': f'value_{i}'}
                    )
                    
                    results['operations'].append({
                        'iteration': i,
                        'increment_value': new_value,
                        'cas_success': cas_success,
                        'dict_success': dict_success
                    })
                    
                    time.sleep(0.001)  # 模拟处理时间
                    
                except Exception as e:
                    results['errors'].append(
                        f"Exception in operation {operation_id}, iteration {i}: {e}"
                    )
            
            return results
        
        # 多线程并发原子操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(concurrent_atomic_operations, i) 
                for i in range(4)
            ]
            results = concurrent.futures.wait(futures, timeout=30)
            
            # 收集结果
            for future in results.done:
                try:
                    result = future.result()
                    self.test_results.append(result)
                    self.test_errors.extend(result['errors'])
                except Exception as e:
                    self.test_errors.append(f"Future result error: {e}")
        
        # 验证结果
        print(f"完成的原子操作: {sum(len(r['operations']) for r in self.test_results)}")
        print(f"错误数量: {len(self.test_errors)}")
        
        self.assertEqual(
            len(self.test_errors), 0, 
            f"原子操作测试出现错误: {self.test_errors[:3]}"
        )
        
        # 验证原子递增的一致性
        for i in range(4):
            final_value = self.cache_manager.get(f"atomic_test_{i}", 0)
            self.assertEqual(
                final_value, 10, 
                f"原子递增结果不正确: expected 10, got {final_value}"
            )
        
        print("✅ 测试3通过：原子操作正常，数值一致")
    
    def test_deadlock_detection(self):
        """测试4：死锁检测"""
        print("\n=== 测试4：死锁检测 ===")
        
        deadlock_detected = threading.Event()
        
        def operation_a():
            """操作A：先锁模块1，再锁模块2"""
            try:
                self.state_manager.update_module_status(
                    'module_1', 
                    {'status': 'a_updating_1'}
                )
                time.sleep(0.1)
                self.state_manager.update_module_status(
                    'module_2', 
                    {'status': 'a_updating_2'}
                )
            except Exception as e:
                self.test_errors.append(f"Operation A error: {e}")
        
        def operation_b():
            """操作B：先锁模块2，再锁模块1"""
            try:
                self.state_manager.update_module_status(
                    'module_2', 
                    {'status': 'b_updating_2'}
                )
                time.sleep(0.1)
                self.state_manager.update_module_status(
                    'module_1', 
                    {'status': 'b_updating_1'}
                )
            except Exception as e:
                self.test_errors.append(f"Operation B error: {e}")
        
        def deadlock_monitor():
            """死锁监控"""
            time.sleep(5)  # 等待5秒
            if not deadlock_detected.is_set():
                deadlock_detected.set()
                self.test_errors.append(
                    "Potential deadlock detected - operations did not complete within 5 seconds"
                )
        
        # 启动操作和监控
        thread_a = threading.Thread(target=operation_a)
        thread_b = threading.Thread(target=operation_b)
        monitor_thread = threading.Thread(target=deadlock_monitor)
        
        thread_a.start()
        thread_b.start()
        monitor_thread.start()
        
        # 等待完成
        thread_a.join(timeout=6)
        thread_b.join(timeout=6)
        
        if thread_a.is_alive() or thread_b.is_alive():
            self.test_errors.append("Threads did not complete - possible deadlock")
        
        deadlock_detected.set()  # 停止监控
        monitor_thread.join(timeout=1)
        
        # 验证无死锁
        print(f"错误数量: {len(self.test_errors)}")
        self.assertEqual(
            len(self.test_errors), 0, 
            f"死锁检测测试失败: {self.test_errors}"
        )
        
        print("✅ 测试4通过：无死锁，锁机制正常")
    
    def test_performance_impact(self):
        """测试5：性能影响"""
        print("\n=== 测试5：性能影响 ===")
        
        # 单线程基准测试
        start_time = time.time()
        for i in range(100):
            self.state_manager.update_module_status(
                'perf_test', 
                {'iteration': i}
            )
            self.state_manager.get_module_status('perf_test')
        single_thread_time = time.time() - start_time
        
        # 多线程性能测试
        def concurrent_operations(thread_id: int):
            for i in range(20):
                self.state_manager.update_module_status(
                    f'perf_test_{thread_id}', 
                    {'iteration': i}
                )
                self.state_manager.get_module_status(f'perf_test_{thread_id}')
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(concurrent_operations, i) 
                for i in range(5)
            ]
            concurrent.futures.wait(futures)
        multi_thread_time = time.time() - start_time
        
        # 计算开销
        # 多线程总操作数 = 5 * 20 = 100，与单线程相同
        overhead_ratio = multi_thread_time / single_thread_time
        
        print(f"单线程时间: {single_thread_time:.3f}s")
        print(f"多线程时间: {multi_thread_time:.3f}s")
        print(f"开销比率: {overhead_ratio:.2f}x")
        
        # 验证性能开销在可接受范围内（不超过3倍）
        self.assertLess(
            overhead_ratio, 3.0, 
            f"线程安全开销过大: {overhead_ratio:.2f}x"
        )
        
        print(f"✅ 测试5通过：性能开销 {overhead_ratio:.2f}x (可接受)")


def run_thread_safety_tests():
    """运行线程安全测试套件"""
    print("\n" + "="*60)
    print("LAD-IMPL-006A 线程安全测试套件")
    print("="*60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestThreadSafety)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有线程安全测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查日志")
        return 1


if __name__ == '__main__':
    exit_code = run_thread_safety_tests()
    sys.exit(exit_code)

