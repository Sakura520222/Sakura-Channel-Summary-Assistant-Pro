#!/usr/bin/env python3
"""测试配置加载功能"""

import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    API_ID, API_HASH, BOT_TOKEN, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
    LOG_LEVEL, ADMIN_LIST, BLACKLIST_ENABLED, BLACKLIST_THRESHOLD_COUNT,
    BLACKLIST_THRESHOLD_HOURS, validate_config
)

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("配置加载测试")
    print("=" * 60)
    
    # 测试环境变量加载
    print("\n1. 环境变量配置:")
    print(f"   API_ID: {'***' + API_ID[-4:] if API_ID and len(API_ID) > 4 else '未设置'}")
    print(f"   API_HASH: {'***' if API_HASH else '未设置'}")
    print(f"   BOT_TOKEN: {'***' + BOT_TOKEN[-4:] if BOT_TOKEN and len(BOT_TOKEN) > 4 else '未设置'}")
    print(f"   LLM_API_KEY: {'***' + LLM_API_KEY[-4:] if LLM_API_KEY and len(LLM_API_KEY) > 4 else '未设置'}")
    print(f"   LLM_BASE_URL: {LLM_BASE_URL}")
    print(f"   LLM_MODEL: {LLM_MODEL}")
    
    # 测试日志配置
    print("\n2. 日志配置:")
    print(f"   LOG_LEVEL: {LOG_LEVEL}")
    print(f"   LOG_DIR: {os.getenv('LOG_DIR', 'log')}")
    print(f"   LOG_RETENTION_DAYS: {os.getenv('LOG_RETENTION_DAYS', '30')}")
    
    # 测试管理员配置
    print("\n3. 管理员配置:")
    print(f"   ADMIN_LIST: {ADMIN_LIST}")
    
    # 测试黑名单配置
    print("\n4. 黑名单配置:")
    print(f"   BLACKLIST_ENABLED: {BLACKLIST_ENABLED}")
    print(f"   BLACKLIST_THRESHOLD_COUNT: {BLACKLIST_THRESHOLD_COUNT}")
    print(f"   BLACKLIST_THRESHOLD_HOURS: {BLACKLIST_THRESHOLD_HOURS}")
    
    # 执行配置验证
    print("\n5. 配置验证:")
    is_valid, errors, warnings = validate_config()
    
    print(f"   验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    if errors:
        print(f"\n   错误 ({len(errors)}):")
        for error in errors:
            print(f"     ❌ {error}")
    
    if warnings:
        print(f"\n   警告 ({len(warnings)}):")
        for warning in warnings:
            print(f"     ⚠️  {warning}")
    
    print("\n" + "=" * 60)
    
    if is_valid:
        print("✅ 所有配置项加载成功！")
        return 0
    else:
        print("❌ 配置验证失败，请检查上述错误")
        return 1

if __name__ == "__main__":
    exit_code = test_config_loading()
    sys.exit(exit_code)
