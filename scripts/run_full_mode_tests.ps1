param(
  [string]$Python = "python",
  [switch]$Quiet,
  [switch]$Enable013
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Push-Location $root
try {
  # Disable fast mode flags for full coverage
  Remove-Item Env:LAD_TEST_MODE -ErrorAction SilentlyContinue
  Remove-Item Env:LAD_QA_FAST -ErrorAction SilentlyContinue
  Remove-Item Env:LAD_FAST_EXIT -ErrorAction SilentlyContinue

  # Ensure UTF-8 console for Windows
  $env:PYTHONUTF8 = "1"
  $env:PYTHONIOENCODING = "utf-8"
  # Qt offscreen & logging noise suppression for CI/local consistency
  $env:QT_QPA_PLATFORM = "offscreen"
  $env:QT_LOGGING_RULES = "*.debug=false;qt.qpa.*=false;qt.text.*=false;qt.fonts.*=false"
  if ($Enable013) { $env:LAD_RUN_013_TESTS = "1" }

  # Tests that should run in full mode to cover threads/IO/long waits
  $tests = @(
    "tests\test_thread_safety.py",
    "tests\test_performance_optimization.py::TestRenderPerformanceOptimizer::test_render_content_multi_thread",
    "tests\test_performance_optimization.py::TestRenderPerformanceOptimizer::test_render_content_incremental",
    "tests\test_performance_optimization.py::TestPerformanceOptimizationIntegration::test_end_to_end_performance_workflow",
    "tests\test_performance_optimization.py::TestPerformanceBenchmark::test_integration_benchmark",
    "tests\test_observability_enhancement.py::TestObservabilityIntegration::test_end_to_end_observability_workflow",
    "tests\test_observability_enhancement.py::TestPerformanceMetricsManager::test_metrics_collection",
    "tests\test_observability_enhancement.py::TestPerformanceMetricsManager::test_metrics_export",
    "tests\test_qa_all.py::test_run_integration_suite",
    "tests\test_qa_all.py::test_run_validation_suite"
  )

  $args = @("-m","pytest")
  if ($Quiet) { $args += "-q" } else { $args += "-vv"; $args += "-s"; $args += "-ra" }
  $args += $tests

  Write-Host "Running FULL-MODE tests (fast mode OFF) at $root" -ForegroundColor Cyan
  & $Python @args
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
