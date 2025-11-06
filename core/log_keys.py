# -*- coding: utf-8 -*-
"""
日志键名规范定义
LAD-IMPL-009: 基础功能验证 - 日志结构化统一
"""

# 标准日志键名规范
LOG_KEYS = {
    'renderer_branch': '渲染器分支类型',
    'module': '模块名称',
    'used_fallback': '是否使用fallback',
    'function_mapping_status': '函数映射状态',
    'missing_functions': '缺失函数列表',
    'non_callable_functions': '不可调用函数列表',
    'fallback_reason': 'fallback原因',
    'path': '模块路径',
    'error_code': '错误代码',
    'message': '错误消息',
    'correlation_id': '关联ID',
    'operation': '操作类型',
    'component': '组件名称',
    'function_validation': '函数验证状态',
    'validation_details': '验证详情',
    'elapsed_ms': '耗时(毫秒)',
    'import_method': '导入方法',
    'cached': '是否从缓存加载',
    'timestamp': '时间戳'
}
