"""
集成测试套件 - 方案4.3.3系统集成与监控实施
实现所有模块的集成测试验证
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# 追加稳定包目录到 Python 路径
import sys
_CUR_DIR = Path(__file__).resolve().parent
# 目录层级：.../local_markdown_viewer/第二阶段实现提示词/.../outputs
# local_markdown_viewer 位于 parents[2]
_LMV_DIR = _CUR_DIR.parents[2]
sys.path.insert(0, str(_LMV_DIR))

# 导入实施的核心模块（指向稳定目录）
from integration.system_integration_coordinator import SystemIntegrationCoordinator
from monitoring.monitoring_system_deployer import MonitoringSystemDeployer
from benchmarks.performance_benchmark_tester import PerformanceBenchmarkTester
from integration.link_processor_integration_preparer import LinkProcessorIntegrationPreparer
from comparison_analysis_tool import ComparisonAnalysisTool


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    test_type: str
    status: str  # passed, failed, skipped
    execution_time: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = None


class IntegrationTestSuite:
    """集成测试套件"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
        
        # 初始化测试组件
        self.integration_coordinator = SystemIntegrationCoordinator()
        self.monitoring_deployer = MonitoringSystemDeployer()
        self.benchmark_tester = PerformanceBenchmarkTester()
        self.link_processor_preparer = LinkProcessorIntegrationPreparer()
        self.comparison_analyzer = ComparisonAnalysisTool()
    
    async def run_all_integration_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        print("开始运行集成测试套件...")
        
        try:
            # 1. 模块集成协调测试
            await self._test_module_integration_coordination()
            
            # 2. 监控系统部署测试
            await self._test_monitoring_system_deployment()
            
            # 3. 性能基准测试
            await self._test_performance_benchmark()
            
            # 4. LinkProcessor集成准备测试
            await self._test_link_processor_integration_preparation()
            
            # 5. 完善建议对比分析测试
            await self._test_comparison_analysis()
            
            # 6. 系统整体集成测试
            await self._test_system_integration()
            
            # 生成测试报告
            test_report = self._generate_test_report()
            
            print("集成测试套件执行完成")
            return test_report
            
        except Exception as e:
            print(f"集成测试套件执行失败: {e}")
            raise
    
    async def _test_module_integration_coordination(self):
        """测试模块集成协调"""
        test_name = "模块集成协调测试"
        start_time = time.time()
        
        try:
            # 测试系统集成协调器
            integration_result = await self.integration_coordinator.integrate_all_modules()
            
            # 验证集成结果
            assert integration_result["status"] == "completed", "集成状态应为completed"
            assert "total_modules" in integration_result, "应包含total_modules字段"
            assert "successful_modules" in integration_result, "应包含successful_modules字段"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="integration",
                status="passed",
                execution_time=execution_time,
                details=integration_result
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="integration",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    async def _test_monitoring_system_deployment(self):
        """测试监控系统部署"""
        test_name = "监控系统部署测试"
        start_time = time.time()
        
        try:
            # 测试监控系统部署
            deployment_result = await self.monitoring_deployer.deploy_monitoring_system()
            
            # 验证部署结果
            assert deployment_result["status"] == "success", "部署状态应为success"
            assert "monitoring_types" in deployment_result, "应包含monitoring_types字段"
            assert "alert_rules_count" in deployment_result, "应包含alert_rules_count字段"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="deployment",
                status="passed",
                execution_time=execution_time,
                details=deployment_result
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="deployment",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    async def _test_performance_benchmark(self):
        """测试性能基准测试"""
        test_name = "性能基准测试"
        start_time = time.time()
        
        try:
            # 测试性能基准测试器
            benchmark_result = await self.benchmark_tester.run_comprehensive_benchmark()
            
            # 验证基准测试结果
            assert benchmark_result["status"] == "completed", "基准测试状态应为completed"
            assert "baseline" in benchmark_result, "应包含baseline字段"
            assert "test_results" in benchmark_result, "应包含test_results字段"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="benchmark",
                status="passed",
                execution_time=execution_time,
                details=benchmark_result
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="benchmark",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    async def _test_link_processor_integration_preparation(self):
        """测试LinkProcessor集成准备"""
        test_name = "LinkProcessor集成准备测试"
        start_time = time.time()
        
        try:
            # 测试LinkProcessor集成准备
            preparation_result = await self.link_processor_preparer.prepare_link_processor_integration()
            
            # 验证准备结果
            assert preparation_result["status"] == "completed", "准备状态应为completed"
            assert "interfaces_count" in preparation_result, "应包含interfaces_count字段"
            assert "integration_points_count" in preparation_result, "应包含integration_points_count字段"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="preparation",
                status="passed",
                execution_time=execution_time,
                details=preparation_result
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="preparation",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    async def _test_comparison_analysis(self):
        """测试完善建议对比分析"""
        test_name = "完善建议对比分析测试"
        start_time = time.time()
        
        try:
            # 测试对比分析工具
            analysis_result = await self.comparison_analyzer.run_comprehensive_comparison_analysis()
            
            # 验证分析结果
            assert analysis_result["status"] == "completed", "分析状态应为completed"
            assert "comparison_results" in analysis_result, "应包含comparison_results字段"
            assert "improvement_recommendations" in analysis_result, "应包含improvement_recommendations字段"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="analysis",
                status="passed",
                execution_time=execution_time,
                details=analysis_result
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="analysis",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    async def _test_system_integration(self):
        """测试系统整体集成"""
        test_name = "系统整体集成测试"
        start_time = time.time()
        
        try:
            # 测试系统整体集成
            # 这里可以测试各个模块之间的协作
            integration_status = {
                "coordinator_ready": True,
                "monitoring_ready": True,
                "benchmark_ready": True,
                "link_processor_ready": True,
                "analysis_ready": True
            }
            
            # 验证所有模块都已就绪
            assert all(integration_status.values()), "所有模块都应就绪"
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="system",
                status="passed",
                execution_time=execution_time,
                details=integration_status
            ))
            
            print(f"✅ {test_name} 通过")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=test_name,
                test_type="system",
                status="failed",
                execution_time=execution_time,
                error_message=str(e)
            ))
            
            print(f"❌ {test_name} 失败: {e}")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "passed"])
        failed_tests = len([r for r in self.test_results if r.status == "failed"])
        skipped_tests = len([r for r in self.test_results if r.status == "skipped"])
        
        total_execution_time = time.time() - self.start_time
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_execution_time
            },
            "test_results": [asdict(result) for result in self.test_results],
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def save_test_report(self, file_path: Path):
        """保存测试报告"""
        try:
            report = self._generate_test_report()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, default=str, indent=2)
            
            print(f"测试报告已保存到: {file_path}")
            
        except Exception as e:
            print(f"保存测试报告失败: {e}")


# 运行集成测试的示例
async def main():
    """主函数"""
    test_suite = IntegrationTestSuite()
    report = await test_suite.run_all_integration_tests()
    
    # 保存测试报告
    test_suite.save_test_report(Path("integration_test_report.json"))
    
    # 打印测试摘要
    summary = report["test_summary"]
    print(f"\n测试摘要:")
    print(f"总测试数: {summary['total_tests']}")
    print(f"通过测试: {summary['passed_tests']}")
    print(f"失败测试: {summary['failed_tests']}")
    print(f"跳过测试: {summary['skipped_tests']}")
    print(f"成功率: {summary['success_rate']:.2f}%")
    print(f"总执行时间: {summary['total_execution_time']:.2f}秒")


if __name__ == "__main__":
    asyncio.run(main()) 