"""
第六阶段：性能优化策略测试

测试PerformanceOptimizationStrategy类的功能
"""

import unittest
import tempfile
import time
from pathlib import Path
import sys
sys.path.insert(0, '.')

from core.performance_optimization_strategy import (
    PerformanceOptimizationStrategy,
    OptimizationStrategy,
    OptimizationTarget,
    OptimizationLevel,
    OptimizationRule,
    OptimizationResult,
    PerformanceProfile
)


class TestPerformanceOptimizationStrategy(unittest.TestCase):
    """测试性能优化策略管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.optimizer = PerformanceOptimizationStrategy(
            config_dir=self.test_dir,
            enable_auto_optimization=False
        )
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'optimizer'):
            self.optimizer.shutdown()
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(len(self.optimizer.optimization_rules), 5)  # 5个默认规则
        self.assertEqual(len(self.optimizer.performance_profiles), 0)
        self.assertEqual(len(self.optimizer.optimization_results), 0)
    
    def test_add_optimization_rule(self):
        """测试添加优化规则"""
        success = self.optimizer.add_optimization_rule(
            name="test_rule",
            target=OptimizationTarget.FILE_READ,
            strategy=OptimizationStrategy.BALANCED,
            level=OptimizationLevel.MEDIUM,
            conditions={"test_condition": 100},
            actions=["test_action"],
            priority=1
        )
        
        self.assertTrue(success)
        self.assertIn("test_rule", self.optimizer.optimization_rules)
        
        rule = self.optimizer.optimization_rules["test_rule"]
        self.assertEqual(rule.name, "test_rule")
        self.assertEqual(rule.target, OptimizationTarget.FILE_READ)
        self.assertEqual(rule.strategy, OptimizationStrategy.BALANCED)
        self.assertEqual(rule.level, OptimizationLevel.MEDIUM)
    
    def test_remove_optimization_rule(self):
        """测试移除优化规则"""
        # 先添加规则
        self.optimizer.add_optimization_rule(
            name="test_rule",
            target=OptimizationTarget.CACHE,
            strategy=OptimizationStrategy.ADAPTIVE,
            level=OptimizationLevel.HIGH,
            conditions={"test_condition": 100},
            actions=["test_action"],
            priority=1
        )
        
        # 验证规则存在
        self.assertIn("test_rule", self.optimizer.optimization_rules)
        
        # 移除规则
        success = self.optimizer.remove_optimization_rule("test_rule")
        self.assertTrue(success)
        
        # 验证规则已移除
        self.assertNotIn("test_rule", self.optimizer.optimization_rules)
    
    def test_get_optimization_rules(self):
        """测试获取优化规则"""
        # 按目标过滤
        file_read_rules = self.optimizer.get_optimization_rules(
            target=OptimizationTarget.FILE_READ
        )
        self.assertGreater(len(file_read_rules), 0)
        for rule in file_read_rules:
            self.assertEqual(rule.target, OptimizationTarget.FILE_READ)
        
        # 按策略过滤
        balanced_rules = self.optimizer.get_optimization_rules(
            strategy=OptimizationStrategy.BALANCED
        )
        self.assertGreater(len(balanced_rules), 0)
        for rule in balanced_rules:
            self.assertEqual(rule.strategy, OptimizationStrategy.BALANCED)
        
        # 按级别过滤
        high_level_rules = self.optimizer.get_optimization_rules(
            level=OptimizationLevel.HIGH
        )
        self.assertGreater(len(high_level_rules), 0)
        for rule in high_level_rules:
            self.assertEqual(rule.level, OptimizationLevel.HIGH)
    
    def test_evaluate_optimization_conditions(self):
        """测试评估优化条件"""
        # 获取一个规则进行测试
        rules = self.optimizer.get_optimization_rules()
        if rules:
            rule = rules[0]
            # 测试条件评估（可能返回False，因为条件不满足）
            result = self.optimizer.evaluate_optimization_conditions(rule)
            self.assertIsInstance(result, bool)
    
    def test_execute_optimization_actions(self):
        """测试执行优化动作"""
        # 获取一个规则进行测试
        rules = self.optimizer.get_optimization_rules()
        if rules:
            rule = rules[0]
            result = self.optimizer.execute_optimization_actions(rule)
            
            self.assertIsInstance(result, OptimizationResult)
            self.assertEqual(result.rule_name, rule.name)
            self.assertEqual(result.target, rule.target)
            self.assertEqual(result.strategy, rule.strategy)
            self.assertEqual(result.level, rule.level)
            self.assertIsInstance(result.success, bool)
            self.assertIsInstance(result.performance_gain, float)
            self.assertIsInstance(result.resource_usage, dict)
            self.assertIsInstance(result.execution_time, float)
            self.assertIsInstance(result.timestamp, float)
            self.assertIsInstance(result.details, dict)
    
    def test_run_optimization_cycle(self):
        """测试运行优化周期"""
        results = self.optimizer.run_optimization_cycle()
        self.assertIsInstance(results, list)
        
        # 检查是否有结果
        if results:
            for result in results:
                self.assertIsInstance(result, OptimizationResult)
    
    def test_get_optimization_results(self):
        """测试获取优化结果"""
        # 先运行一个优化周期
        self.optimizer.run_optimization_cycle()
        
        # 获取所有结果
        all_results = self.optimizer.get_optimization_results()
        self.assertIsInstance(all_results, list)
        
        # 按目标过滤
        file_read_results = self.optimizer.get_optimization_results(
            target=OptimizationTarget.FILE_READ
        )
        self.assertIsInstance(file_read_results, list)
        
        # 只获取成功的结果
        success_results = self.optimizer.get_optimization_results(success_only=True)
        self.assertIsInstance(success_results, list)
    
    def test_get_optimization_statistics(self):
        """测试获取优化统计信息"""
        # 先运行一个优化周期
        self.optimizer.run_optimization_cycle()
        
        stats = self.optimizer.get_optimization_statistics()
        self.assertIsInstance(stats, dict)
        
        # 检查统计信息字段
        self.assertIn('total_results', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('average_performance_gain', stats)
        self.assertIn('target_distribution', stats)
        self.assertIn('strategy_distribution', stats)
        
        self.assertIsInstance(stats['total_results'], int)
        self.assertIsInstance(stats['success_rate'], float)
        self.assertIsInstance(stats['average_performance_gain'], float)
        self.assertIsInstance(stats['target_distribution'], dict)
        self.assertIsInstance(stats['strategy_distribution'], dict)
    
    def test_create_performance_profile(self):
        """测试创建性能配置"""
        success = self.optimizer.create_performance_profile(
            name="test_profile",
            description="测试性能配置",
            strategy=OptimizationStrategy.BALANCED,
            targets=[OptimizationTarget.FILE_READ, OptimizationTarget.CACHE],
            rule_names=["file_read_optimization", "cache_optimization"]
        )
        
        self.assertTrue(success)
        self.assertIn("test_profile", self.optimizer.performance_profiles)
        
        profile = self.optimizer.performance_profiles["test_profile"]
        self.assertEqual(profile.name, "test_profile")
        self.assertEqual(profile.description, "测试性能配置")
        self.assertEqual(profile.strategy, OptimizationStrategy.BALANCED)
        self.assertEqual(len(profile.targets), 2)
        self.assertEqual(len(profile.rules), 2)
    
    def test_get_performance_profile(self):
        """测试获取性能配置"""
        # 先创建配置
        self.optimizer.create_performance_profile(
            name="test_profile",
            description="测试性能配置",
            strategy=OptimizationStrategy.ADAPTIVE,
            targets=[OptimizationTarget.RENDER],
            rule_names=["render_optimization"]
        )
        
        # 获取配置
        profile = self.optimizer.get_performance_profile("test_profile")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "test_profile")
        
        # 获取不存在的配置
        nonexistent_profile = self.optimizer.get_performance_profile("nonexistent")
        self.assertIsNone(nonexistent_profile)
    
    def test_apply_performance_profile(self):
        """测试应用性能配置"""
        # 先创建配置
        self.optimizer.create_performance_profile(
            name="test_profile",
            description="测试性能配置",
            strategy=OptimizationStrategy.CONSERVATIVE,
            targets=[OptimizationTarget.MEMORY],
            rule_names=["memory_optimization"]
        )
        
        # 应用配置
        success = self.optimizer.apply_performance_profile("test_profile")
        self.assertTrue(success)
    
    def test_configuration_persistence(self):
        """测试配置持久化"""
        # 添加自定义规则
        self.optimizer.add_optimization_rule(
            name="custom_rule",
            target=OptimizationTarget.INTEGRATION,
            strategy=OptimizationStrategy.AGGRESSIVE,
            level=OptimizationLevel.MAXIMUM,
            conditions={"custom_condition": 200},
            actions=["custom_action"],
            priority=10
        )
        
        # 创建性能配置
        self.optimizer.create_performance_profile(
            name="custom_profile",
            description="自定义性能配置",
            strategy=OptimizationStrategy.AGGRESSIVE,
            targets=[OptimizationTarget.INTEGRATION],
            rule_names=["custom_rule"]
        )
        
        # 保存配置
        self.optimizer.save_configuration()
        
        # 创建新的实例加载配置
        new_optimizer = PerformanceOptimizationStrategy(
            config_dir=self.test_dir,
            enable_auto_optimization=False
        )
        
        # 加载配置
        new_optimizer.load_configuration()
        
        # 验证规则是否加载
        self.assertIn("custom_rule", new_optimizer.optimization_rules)
        
        # 验证性能配置是否加载
        self.assertIn("custom_profile", new_optimizer.performance_profiles)
        
        # 清理
        new_optimizer.shutdown()
    
    def test_shutdown(self):
        """测试关闭功能"""
        # 确保可以正常关闭
        self.optimizer.shutdown()
        # 这里主要测试没有异常抛出


def run_all_tests():
    """运行所有测试"""
    print("开始第六阶段性能优化策略测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceOptimizationStrategy))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    if result.wasSuccessful():
        print("🎉 第六阶段性能优化策略测试全部通过！")
    else:
        print("❌ 第六阶段性能优化策略测试有失败项")
        print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_all_tests()