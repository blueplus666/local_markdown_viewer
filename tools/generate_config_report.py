#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证报告生成工具
LAD-IMPL-009: 基础功能验证 - 配置冲突检测部分
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_validator import ConfigValidator
from utils.config_manager import ConfigManager


def generate_config_validation_report(output_dir: str = None):
    """生成配置验证报告
    
    Args:
        output_dir: 输出目录，默认为项目根目录下的 reports/
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "reports"
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 初始化验证器
    config_manager = ConfigManager()
    validator = ConfigValidator(config_manager)
    
    # 执行验证
    module_validation = validator.validate_external_modules_config()
    conflict_detection = validator.detect_config_conflicts()
    config_summary = validator.get_config_summary()
    
    # 组装报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "module_validation": module_validation,
        "conflict_detection": conflict_detection,
        "config_summary": config_summary
    }
    
    # 保存JSON报告
    json_report_path = output_path / "config_validation_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 生成Markdown摘要
    md_report_path = output_path / "config_validation_report.md"
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write("# LAD-IMPL-009 配置验证报告\n\n")
        f.write(f"**生成时间**: {report['generated_at']}\n\n")
        
        # 模块验证结果
        f.write("## 模块配置验证\n")
        if report['module_validation']['valid']:
            f.write(f"✅ 验证通过，共验证 {report['module_validation']['module_count']} 个模块\n")
        else:
            f.write(f"❌ 验证失败: {report['module_validation']['error']}\n")
        f.write("\n")
        
        # 冲突检测结果
        f.write("## 配置冲突检测\n")
        if not report['conflict_detection']['conflicts_found']:
            f.write("✅ 未发现配置冲突\n")
        else:
            f.write(f"⚠️ 发现 {report['conflict_detection']['conflict_count']} 个配置冲突:\n")
            for conflict in report['conflict_detection']['conflicts']:
                f.write(f"- [{conflict.get('severity', 'info').upper()}] {conflict['message']}\n")
        f.write("\n")
        
        # 配置摘要
        f.write("## 配置文件摘要\n")
        for filename, info in report['config_summary']['config_files'].items():
            if info['exists']:
                f.write(f"- `{filename}`: 存在，大小 {info.get('size', 0)} 字节\n")
            else:
                f.write(f"- `{filename}`: 不存在\n")
        f.write("\n")
    
    print(f"配置验证报告已生成:")
    print(f"  JSON: {json_report_path}")
    print(f"  Markdown: {md_report_path}")
    
    return report


def main():
    """主函数"""
    try:
        generate_config_validation_report()
    except Exception as e:
        print(f"生成配置验证报告时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
