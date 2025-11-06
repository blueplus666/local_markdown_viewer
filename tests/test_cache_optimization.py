#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存优化测试脚本 v1.0.0
测试统一缓存管理器和失效管理器的功能

作者: LAD Team
创建时间: 2025-08-16
最后更新: 2025-08-16
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.unified_cache_manager import UnifiedCacheManager, CacheStrategy
from core.cache_invalidation_manager import CacheInvalidationManager, InvalidationTrigger
from core.markdown_renderer import HybridMarkdownRenderer
from core.dynamic_module_importer import DynamicModuleImporter


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cache_optimization_test.log', encoding='utf-8')
        ]
    )


def test_unified_cache_manager():
    """测试统一缓存管理器"""
    print("\n" + "="*50)
    print("测试统一缓存管理器")
    print("="*50)
    
    # 创建缓存管理器
    cache_manager = UnifiedCacheManager(
        max_size=100,
        default_ttl=60,  # 1分钟过期
        strategy=CacheStrategy.LRU,
        cache_dir=project_root / "cache" / "test"
    )
    
    # 测试基本功能
    print("1. 测试基本缓存功能...")
    
    # 设置缓存
    cache_manager.set("test_key_1", "test_value_1", ttl=30)
    cache_manager.set("test_key_2", {"data": "test_value_2"}, ttl=60)
    
    # 获取缓存
    value1 = cache_manager.get("test_key_1")
    value2 = cache_manager.get("test_key_2")
    
    print(f"   缓存值1: {value1}")
    print(f"   缓存值2: {value2}")
    
    # 测试缓存命中
    print("2. 测试缓存命中...")
    start_time = time.time()
    cached_value = cache_manager.get("test_key_1")
    end_time = time.time()
    print(f"   缓存命中耗时: {(end_time - start_time) * 1000:.2f}ms")
    
    # 测试统计信息
    print("3. 测试统计信息...")
    stats = cache_manager.get_stats()
    print(f"   总条目数: {stats.total_entries}")
    print(f"   命中率: {stats.hit_rate:.2%}")
    print(f"   命中次数: {stats.hit_count}")
    print(f"   未命中次数: {stats.miss_count}")
    print(f"   驱逐次数: {stats.eviction_count}")
    print(f"   内存使用: {stats.memory_usage:.2f}MB")
    
    # 测试策略切换
    print("4. 测试策略切换...")
    cache_manager.set_strategy(CacheStrategy.LFU)
    print(f"   当前策略: {cache_manager.strategy.value}")
    
    # 测试过期清理
    print("5. 测试过期清理...")
    cache_manager.set("expire_test", "will_expire", ttl=1)  # 1秒过期
    time.sleep(2)
    expired_value = cache_manager.get("expire_test")
    print(f"   过期后获取: {expired_value}")
    
    # 清理
    cache_manager.shutdown()
    print("✅ 统一缓存管理器测试完成")


def test_cache_invalidation_manager():
    """测试缓存失效管理器"""
    print("\n" + "="*50)
    print("测试缓存失效管理器")
    print("="*50)
    
    # 创建缓存管理器
    cache_manager = UnifiedCacheManager(max_size=50)
    
    # 创建失效管理器
    invalidation_manager = CacheInvalidationManager(
        cache_manager,
        invalidation_dir=project_root / "cache" / "invalidation_test"
    )
    
    # 设置测试缓存
    print("1. 设置测试缓存...")
    cache_manager.set("file_test_1", "content_1")
    cache_manager.set("file_test_2", "content_2")
    cache_manager.set("config_test_1", "config_1")
    cache_manager.set("module_import_test", "module_1")
    
    print(f"   初始缓存条目数: {len(cache_manager.get_keys())}")
    
    # 测试模式失效
    print("2. 测试模式失效...")
    invalidated_count = invalidation_manager.invalidate_by_pattern(
        "file_*", 
        InvalidationTrigger.MANUAL_REQUEST,
        "测试模式失效"
    )
    print(f"   模式失效数量: {invalidated_count}")
    
    # 测试规则失效
    print("3. 测试规则失效...")
    invalidated_count = invalidation_manager.invalidate_by_rule(
        "config_changed",
        InvalidationTrigger.CONFIG_CHANGED
    )
    print(f"   规则失效数量: {invalidated_count}")
    
    # 测试文件监控
    print("4. 测试文件监控...")
    test_file = project_root / "test_file.txt"
    test_file.write_text("test content", encoding='utf-8')
    
    invalidation_manager.watch_file(str(test_file))
    print(f"   监控文件数: {len(invalidation_manager.file_watchers)}")
    
    # 测试统计信息
    print("5. 测试统计信息...")
    stats = invalidation_manager.get_invalidation_stats()
    print(f"   总失效次数: {stats['total_invalidations']}")
    print(f"   触发器统计: {stats['trigger_stats']}")
    print(f"   活跃规则数: {stats['active_rules']}")
    print(f"   监控文件数: {stats['watched_files']}")
    
    # 测试历史记录
    print("6. 测试历史记录...")
    history = invalidation_manager.get_invalidation_history(5)
    print(f"   最近失效事件数: {len(history)}")
    
    # 清理
    test_file.unlink(missing_ok=True)
    invalidation_manager.shutdown()
    cache_manager.shutdown()
    print("✅ 缓存失效管理器测试完成")


def test_markdown_renderer_cache():
    """测试Markdown渲染器缓存"""
    print("\n" + "="*50)
    print("测试Markdown渲染器缓存")
    print("="*50)
    
    # 创建渲染器
    renderer = HybridMarkdownRenderer()
    
    # 测试内容渲染缓存
    print("1. 测试内容渲染缓存...")
    
    test_content = """
# 测试标题

这是一个测试文档。

## 子标题

- 列表项1
- 列表项2

```python
print("Hello World")
```
"""
    
    # 第一次渲染
    start_time = time.time()
    result1 = renderer.render(test_content)
    first_render_time = time.time() - start_time
    
    print(f"   第一次渲染耗时: {first_render_time * 1000:.2f}ms")
    print(f"   渲染成功: {result1['success']}")
    print(f"   是否缓存: {result1.get('cached', False)}")
    
    # 第二次渲染（应该命中缓存）
    start_time = time.time()
    result2 = renderer.render(test_content)
    second_render_time = time.time() - start_time
    
    print(f"   第二次渲染耗时: {second_render_time * 1000:.2f}ms")
    print(f"   渲染成功: {result2['success']}")
    print(f"   是否缓存: {result2.get('cached', False)}")
    print(f"   缓存命中: {result2.get('cache_hit', False)}")
    
    # 计算性能提升
    if first_render_time > 0:
        improvement = (first_render_time - second_render_time) / first_render_time * 100
        print(f"   性能提升: {improvement:.1f}%")
    
    # 测试缓存信息
    print("2. 测试缓存信息...")
    cache_info = renderer.get_cache_info()
    print(f"   缓存条目数: {cache_info['total']}")
    print(f"   命中率: {cache_info['hit_rate']:.2%}")
    print(f"   内存使用: {cache_info['memory_usage_mb']:.2f}MB")
    print(f"   监控文件数: {cache_info['watched_files']}")
    
    # 测试失效统计
    invalidation_stats = cache_info['invalidation_stats']
    print(f"   失效统计: {invalidation_stats['total_invalidations']} 次")
    
    print("✅ Markdown渲染器缓存测试完成")


def test_dynamic_module_importer_cache():
    """测试动态模块导入器缓存"""
    print("\n" + "="*50)
    print("测试动态模块导入器缓存")
    print("="*50)
    
    # 创建导入器
    importer = DynamicModuleImporter()
    
    # 测试模块导入缓存
    print("1. 测试模块导入缓存...")
    
    # 第一次导入（应该失败，因为没有实际模块）
    start_time = time.time()
    result1 = importer.import_module("test_module")
    first_import_time = time.time() - start_time
    
    print(f"   第一次导入耗时: {first_import_time * 1000:.2f}ms")
    print(f"   导入成功: {result1['success']}")
    print(f"   是否缓存: {result1.get('cached', False)}")
    
    # 第二次导入（应该命中缓存）
    start_time = time.time()
    result2 = importer.import_module("test_module")
    second_import_time = time.time() - start_time
    
    print(f"   第二次导入耗时: {second_import_time * 1000:.2f}ms")
    print(f"   导入成功: {result2['success']}")
    print(f"   是否缓存: {result2.get('cached', False)}")
    print(f"   缓存命中: {result2.get('cache_hit', False)}")
    
    # 测试导入状态
    print("2. 测试导入状态...")
    status = importer.get_import_status()
    print(f"   总导入次数: {status['total_imports']}")
    print(f"   成功导入次数: {status['successful_imports']}")
    print(f"   失败导入次数: {status['failed_imports']}")
    print(f"   缓存命中次数: {status['cache_hits']}")
    
    # 测试统一缓存统计
    unified_stats = status['unified_cache_stats']
    print(f"   统一缓存条目数: {unified_stats['total_entries']}")
    print(f"   统一缓存命中率: {unified_stats['hit_rate']:.2%}")
    print(f"   统一缓存内存使用: {unified_stats['memory_usage_mb']:.2f}MB")
    
    print("✅ 动态模块导入器缓存测试完成")


def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "="*50)
    print("测试缓存性能")
    print("="*50)
    
    # 创建缓存管理器
    cache_manager = UnifiedCacheManager(max_size=1000)
    
    # 性能测试数据
    test_data = {
        f"key_{i}": f"value_{i}" * 100  # 较大的值
        for i in range(100)
    }
    
    print("1. 测试写入性能...")
    start_time = time.time()
    for key, value in test_data.items():
        cache_manager.set(key, value)
    write_time = time.time() - start_time
    
    print(f"   写入100个条目耗时: {write_time * 1000:.2f}ms")
    print(f"   平均写入时间: {write_time / 100 * 1000:.2f}ms/条目")
    
    print("2. 测试读取性能...")
    start_time = time.time()
    for key in test_data.keys():
        cache_manager.get(key)
    read_time = time.time() - start_time
    
    print(f"   读取100个条目耗时: {read_time * 1000:.2f}ms")
    print(f"   平均读取时间: {read_time / 100 * 1000:.2f}ms/条目")
    
    print("3. 测试缓存命中性能...")
    start_time = time.time()
    for key in test_data.keys():
        cache_manager.get(key)  # 第二次读取，应该命中缓存
    hit_time = time.time() - start_time
    
    print(f"   缓存命中100次耗时: {hit_time * 1000:.2f}ms")
    print(f"   平均命中时间: {hit_time / 100 * 1000:.2f}ms/条目")
    
    # 性能提升计算
    if read_time > 0:
        hit_improvement = (read_time - hit_time) / read_time * 100
        print(f"   缓存命中性能提升: {hit_improvement:.1f}%")
    
    # 最终统计
    final_stats = cache_manager.get_stats()
    print(f"   最终命中率: {final_stats.hit_rate:.2%}")
    print(f"   最终内存使用: {final_stats.memory_usage:.2f}MB")
    
    cache_manager.shutdown()
    print("✅ 缓存性能测试完成")


def main():
    """主测试函数"""
    print("🚀 开始缓存优化测试")
    print("="*60)
    
    # 设置日志
    setup_logging()
    
    try:
        # 运行各项测试
        test_unified_cache_manager()
        test_cache_invalidation_manager()
        test_markdown_renderer_cache()
        test_dynamic_module_importer_cache()
        test_cache_performance()
        
        print("\n" + "="*60)
        print("🎉 所有缓存优化测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        logging.error(f"测试错误: {e}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 