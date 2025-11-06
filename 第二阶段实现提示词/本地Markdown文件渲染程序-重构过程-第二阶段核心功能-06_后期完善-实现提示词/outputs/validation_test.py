"""
实际运行验证脚本 - 方案4.3.3系统集成与监控实施
验证所有模块的实际运行情况
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加当前目录与项目内稳定包目录到 Python 路径
_CUR_DIR = Path(__file__).resolve().parent
# 目录层级：.../local_markdown_viewer/第二阶段实现提示词/.../outputs
# local_markdown_viewer 位于 parents[2]
_LMV_DIR = _CUR_DIR.parents[2]
sys.path.insert(0, str(_LMV_DIR))

# 导入所有实施模块（指向稳定目录）
from integration.system_integration_coordinator import SystemIntegrationCoordinator
from monitoring.monitoring_system_deployer import MonitoringSystemDeployer
from benchmarks.performance_benchmark_tester import PerformanceBenchmarkTester
from integration.link_processor_integration_preparer import LinkProcessorIntegrationPreparer
from comparison_analysis_tool import ComparisonAnalysisTool
from integration_test_suite import IntegrationTestSuite


class ValidationTestRunner:
    """验证测试运行器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    async def run_all_validation_tests(self):
        """运行所有验证测试"""
        print("=" * 60)
        print("方案4.3.3系统集成与监控实施 - 实际运行验证")
        print("=" * 60)
        
        try:
            # 1. 验证系统集成协调器
            await self._test_system_integration_coordinator()
            
            # 2. 验证监控系统部署器
            await self._test_monitoring_system_deployer()
            
            # 3. 验证性能基准测试器
            await self._test_performance_benchmark_tester()
            
            # 4. 验证LinkProcessor集成准备器
            await self._test_link_processor_integration_preparer()
            
            # 5. 验证对比分析工具
            await self._test_comparison_analysis_tool()
            
            # 6. 验证集成测试套件
            await self._test_integration_test_suite()
            
            # 7. 生成验证报告
            await self._generate_validation_report()
            
        except Exception as e:
            print(f"❌ 验证测试失败: {e}")
            raise
    
    async def _test_system_integration_coordinator(self):
        """验证系统集成协调器"""
        print("\n🔧 验证系统集成协调器...")
        
        try:
            coordinator = SystemIntegrationCoordinator()
            
            # 测试基本功能
            result = await coordinator.integrate_all_modules()
            
            # 验证结果
            assert result["status"] == "completed", "集成状态应为completed"
            assert "total_modules" in result, "应包含total_modules字段"
            assert "successful_modules" in result, "应包含successful_modules字段"
            
            self.test_results["system_integration_coordinator"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ 系统集成协调器验证通过")
            
        except Exception as e:
            self.test_results["system_integration_coordinator"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ 系统集成协调器验证失败: {e}")
    
    async def _test_monitoring_system_deployer(self):
        """验证监控系统部署器"""
        print("\n📊 验证监控系统部署器...")
        
        try:
            deployer = MonitoringSystemDeployer()
            
            # 测试部署功能
            result = await deployer.deploy_monitoring_system()
            
            # 验证结果
            assert result["status"] == "success", "部署状态应为success"
            assert "monitoring_types" in result, "应包含monitoring_types字段"
            assert "alert_rules_count" in result, "应包含alert_rules_count字段"
            
            self.test_results["monitoring_system_deployer"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ 监控系统部署器验证通过")
            
        except Exception as e:
            self.test_results["monitoring_system_deployer"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ 监控系统部署器验证失败: {e}")
    
    async def _test_performance_benchmark_tester(self):
        """验证性能基准测试器"""
        print("\n⚡ 验证性能基准测试器...")
        
        try:
            tester = PerformanceBenchmarkTester()
            
            # 测试基准测试功能
            result = await tester.run_comprehensive_benchmark()
            
            # 验证结果
            assert result["status"] == "completed", "基准测试状态应为completed"
            assert "baseline" in result, "应包含baseline字段"
            assert "test_results" in result, "应包含test_results字段"
            
            self.test_results["performance_benchmark_tester"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ 性能基准测试器验证通过")
            
        except Exception as e:
            self.test_results["performance_benchmark_tester"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ 性能基准测试器验证失败: {e}")
    
    async def _test_link_processor_integration_preparer(self):
        """验证LinkProcessor集成准备器"""
        print("\n🔗 验证LinkProcessor集成准备器...")
        
        try:
            preparer = LinkProcessorIntegrationPreparer()
            
            # 测试集成准备功能
            result = await preparer.prepare_link_processor_integration()
            
            # 验证结果
            assert result["status"] == "completed", "准备状态应为completed"
            assert "interfaces_count" in result, "应包含interfaces_count字段"
            assert "integration_points_count" in result, "应包含integration_points_count字段"
            
            self.test_results["link_processor_integration_preparer"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ LinkProcessor集成准备器验证通过")
            
        except Exception as e:
            self.test_results["link_processor_integration_preparer"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ LinkProcessor集成准备器验证失败: {e}")
    
    async def _test_comparison_analysis_tool(self):
        """验证对比分析工具"""
        print("\n📈 验证对比分析工具...")
        
        try:
            analyzer = ComparisonAnalysisTool()
            
            # 测试对比分析功能
            result = await analyzer.run_comprehensive_comparison_analysis()
            
            # 验证结果
            assert result["status"] == "completed", "分析状态应为completed"
            assert "comparison_results" in result, "应包含comparison_results字段"
            assert "improvement_recommendations" in result, "应包含improvement_recommendations字段"
            
            self.test_results["comparison_analysis_tool"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ 对比分析工具验证通过")
            
        except Exception as e:
            self.test_results["comparison_analysis_tool"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ 对比分析工具验证失败: {e}")
    
    async def _test_integration_test_suite(self):
        """验证集成测试套件"""
        print("\n🧪 验证集成测试套件...")
        
        try:
            test_suite = IntegrationTestSuite()
            
            # 测试集成测试功能
            result = await test_suite.run_all_integration_tests()
            
            # 验证结果
            assert "test_summary" in result, "应包含test_summary字段"
            assert "test_results" in result, "应包含test_results字段"
            
            self.test_results["integration_test_suite"] = {
                "status": "passed",
                "result": result
            }
            
            print("✅ 集成测试套件验证通过")
            
        except Exception as e:
            self.test_results["integration_test_suite"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ 集成测试套件验证失败: {e}")
    
    async def _generate_validation_report(self):
        """生成验证报告"""
        print("\n" + "=" * 60)
        print("验证报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results.values() if r["status"] == "failed"])
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {(passed_tests / total_tests * 100):.2f}%")
        
        print(f"\n总执行时间: {time.time() - self.start_time:.2f}秒")
        
        # 详细结果
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"{status_icon} {test_name}: {result['status']}")
            if result["status"] == "failed":
                print(f"   错误: {result['error']}")
        
        # 保存报告
        report_file = Path("validation_report.json")
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, default=str, indent=2)
        
        print(f"\n验证报告已保存到: {report_file}")


async def main():
    """主函数"""
    runner = ValidationTestRunner()
    await runner.run_all_validation_tests()


if __name__ == "__main__":
    asyncio.run(main())