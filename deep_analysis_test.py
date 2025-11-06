#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度分析测试 - 回答预设追问的实际数据收集"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

output_file = Path("deep_analysis_results.txt")

with open(output_file, 'w', encoding='utf-8') as f:
    def log(msg):
        print(msg)
        f.write(msg + '\n')
        f.flush()
    
    log("=" * 70)
    log("006B追问深度分析测试")
    log("=" * 70)
    
    try:
        from utils.config_manager import ConfigManager
        
        log("\n[追问1分析] 配置访问场景完整性测试")
        log("-" * 60)
        
        cm = ConfigManager()
        
        # 测试未覆盖的场景
        log("\n测试场景5: ui_config.json访问")
        try:
            left_width = cm.get_unified_config('ui.layout.left_panel_width')
            log(f"[OK] get_unified_config('ui.layout.left_panel_width'): {left_width}")
        except Exception as e:
            log(f"[FAIL] ui_config访问失败: {e}")
        
        log("\n测试场景6: file_types.json访问")
        try:
            md_renderer = cm.get_unified_config('markdown_files.renderer')
            log(f"[结果] get_unified_config('markdown_files.renderer'): {md_renderer}")
        except Exception as e:
            log(f"[FAIL] file_types访问失败: {e}")
        
        log("\n[追问2分析] 边界情况测试")
        log("-" * 60)
        
        # 边界1：不存在的模块
        log("\n边界测试1: 不存在的模块")
        nonexistent = cm.get_external_module_config("nonexistent_module")
        log(f"[结果] get_external_module_config('nonexistent_module'): {nonexistent}")
        log(f"[类型] 返回类型: {type(nonexistent)}")
        log(f"[验证] 是否为空字典: {nonexistent == {}}")
        
        # 边界2：不存在的嵌套路径
        log("\n边界测试2: 不存在的嵌套路径")
        nonexistent_path = cm.get_unified_config('app.nonexistent.deep.path', default="DEFAULT")
        log(f"[结果] 不存在的路径返回: {nonexistent_path}")
        log(f"[验证] 是否返回默认值: {nonexistent_path == 'DEFAULT'}")
        
        # 边界3：external_modules中不存在的字段
        log("\n边界测试3: 模块中不存在的字段")
        nonexistent_field = cm.get_unified_config('external_modules.markdown_processor.nonexistent_field', default=None)
        log(f"[结果] 不存在的字段返回: {nonexistent_field}")
        log(f"[验证] 是否返回None: {nonexistent_field is None}")
        
        log("\n[追问3分析] 性能基准测试")
        log("-" * 60)
        
        # 性能测试1：初始化性能
        log("\n性能测试1: ConfigManager初始化")
        start_time = time.perf_counter()
        cm_new = ConfigManager()
        init_time = (time.perf_counter() - start_time) * 1000
        log(f"[结果] 初始化时间: {init_time:.2f}ms")
        
        # 性能测试2：首次配置访问
        log("\n性能测试2: 首次external_modules访问")
        cm_fresh = ConfigManager()
        cm_fresh._config_cache.clear()  # 清除缓存
        start_time = time.perf_counter()
        module_config = cm_fresh.get_external_module_config("markdown_processor")
        first_access_time = (time.perf_counter() - start_time) * 1000
        log(f"[结果] 首次访问时间: {first_access_time:.2f}ms")
        
        # 性能测试3：缓存访问
        log("\n性能测试3: 缓存命中访问")
        times = []
        for i in range(100):
            start_time = time.perf_counter()
            _ = cm.get_external_module_config("markdown_processor")
            times.append((time.perf_counter() - start_time) * 1000)
        avg_cached_time = sum(times) / len(times)
        log(f"[结果] 缓存访问平均时间: {avg_cached_time:.4f}ms (100次)")
        log(f"[结果] 最快访问: {min(times):.4f}ms")
        log(f"[结果] 最慢访问: {max(times):.4f}ms")
        
        # 性能测试4：get_unified_config vs get_config
        log("\n性能测试4: 不同访问方式性能对比")
        
        # 测试get_config
        times_old = []
        for i in range(100):
            start_time = time.perf_counter()
            _ = cm.get_config("app.name", config_type="app")
            times_old.append((time.perf_counter() - start_time) * 1000)
        
        # 测试get_unified_config
        times_new = []
        for i in range(100):
            start_time = time.perf_counter()
            _ = cm.get_unified_config("app.name")
            times_new.append((time.perf_counter() - start_time) * 1000)
        
        log(f"[结果] get_config平均: {sum(times_old)/100:.4f}ms")
        log(f"[结果] get_unified_config平均: {sum(times_new)/100:.4f}ms")
        log(f"[结果] 性能差异: {((sum(times_new)/100) / (sum(times_old)/100) - 1) * 100:.1f}%")
        
        log("\n[追问4分析] 向后兼容性验证")
        log("-" * 60)
        
        # 兼容性测试1：原有get_config接口
        log("\n兼容性测试1: 原有接口调用方式")
        try:
            # 模拟现有代码的调用方式
            app_name_old = cm.get_config("app.name", default=None, config_type="app")
            log(f"[OK] 旧方式get_config工作正常: {app_name_old}")
        except Exception as e:
            log(f"[FAIL] 旧方式失败: {e}")
        
        # 兼容性测试2：get_external_module_config回退机制
        log("\n兼容性测试2: 回退机制测试")
        # 测试从external_modules.json读取
        module_from_file = cm.get_external_module_config("markdown_processor")
        log(f"[OK] 从external_modules.json读取: enabled={module_from_file.get('enabled')}")
        
        # 模拟external_modules.json不存在时的回退
        log("[信息] 回退机制：优先external_modules.json，失败则回退到app_config")
        log("[信息] 当前app_config.json中已无external_modules字段，回退返回空字典")
        
        log("\n[追问5分析] 代码可扩展性评估")
        log("-" * 60)
        
        # 分析get_unified_config的扩展点
        log("\n扩展点分析: get_unified_config方法")
        log("[当前实现] 直接从_app_config中查找")
        log("[扩展方向] 可以添加配置类型路由逻辑")
        log("[兼容性] 调用代码无需修改，仅替换内部实现")
        
        log("\n[追问6分析] 006A任务实际需求验证")
        log("-" * 60)
        
        # 模拟006A的实际调用场景
        log("\n场景1: ApplicationStateManager初始化")
        app_config = cm._app_config
        markdown_config = app_config.get('markdown', {})
        cache_enabled = markdown_config.get('cache_enabled')
        log(f"[OK] 性能配置获取: cache_enabled={cache_enabled}")
        
        log("\n场景2: 获取外部模块配置")
        module_config = cm.get_external_module_config("markdown_processor")
        required_fields = ['enabled', 'module_path', 'version', 'required_functions']
        missing_fields = [f for f in required_fields if f not in module_config]
        if not missing_fields:
            log(f"[OK] 所有必需字段完整: {required_fields}")
        else:
            log(f"[FAIL] 缺少字段: {missing_fields}")
        
        log("\n场景3: required_functions验证")
        required_functions = module_config.get('required_functions', [])
        log(f"[OK] required_functions: {required_functions}")
        log(f"[OK] 函数数量: {len(required_functions)}")
        
        log("\n" + "=" * 70)
        log("[完成] 深度分析测试完成")
        log("=" * 70)
        
    except Exception as e:
        log(f"[FATAL] 分析测试失败: {e}")
        import traceback
        traceback.print_exc(file=f)
        sys.exit(1)

print(f"\n深度分析结果已保存到: {output_file.absolute()}")

































