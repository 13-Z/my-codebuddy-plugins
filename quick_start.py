"""
快速开始 - 如何在对话中使用长期记忆服务
"""
import sys
sys.path.insert(0, '.')

from memory_service import get_memory_manager, get_memory_service

def quick_demo():
    """快速演示"""
    print("=" * 60)
    print("长期记忆服务快速开始")
    print("=" * 60)
    
    # 1. 获取记忆管理器
    print("\n1. 初始化记忆管理器...")
    manager = get_memory_manager()
    service = get_memory_service()
    
    # 2. 查看当前状态
    stats = service.get_stats()
    print(f"   记忆库状态: {stats['total_memories']} 条记忆")
    
    # 3. 手动存储一些重要信息
    print("\n2. 存储重要决策...")
    
    decisions = [
        "项目决定使用 React + TypeScript 作为前端技术栈",
        "后端选择 FastAPI + PostgreSQL 组合",
        "部署方案：使用 Docker 和 Kubernetes",
        "代码规范：使用 ESLint + Prettier 进行代码格式化",
        "测试策略：单元测试使用 Jest，E2E测试使用 Cypress"
    ]
    
    for i, decision in enumerate(decisions, 1):
        memory_id = manager.store_conversation_memory(
            decision,
            {"topic": f"技术决策_{i}", "importance": "high", "manual_store": True}
        )
        print(f"   [存储成功] {decision[:40]}...")
    
    # 4. 搜索相关记忆
    print("\n3. 搜索相关记忆...")
    
    queries = [
        "前端技术选型",
        "部署方案",
        "测试策略"
    ]
    
    for query in queries:
        print(f"\n   搜索: '{query}'")
        context = manager.get_relevant_context(query, max_memories=2)
        if context:
            print(f"   找到相关记忆:")
            print(f"   {context[:200]}...")
        else:
            print("   未找到相关记忆")
    
    # 5. 列出所有记忆
    print("\n4. 列出所有记忆...")
    all_memories = service.get_all_memories(limit=5)
    print(f"   最近 {len(all_memories)} 条记忆:")
    for i, mem in enumerate(all_memories, 1):
        text_preview = mem['text'][:60] + "..." if len(mem['text']) > 60 else mem['text']
        print(f"   {i}. {text_preview}")
    
    # 5.5 可选：手动清理低/普通重要性旧记忆（演示）
    print("\n5. 可选：手动清理旧记忆（低14天，普通60天，保留最新200条）...")
    cleanup_result = service.cleanup_memories(retention_days_low=14, retention_days_normal=60, min_keep=200)
    print(f"   清理结果: {cleanup_result}")

    # 5.6 可选：进入审查界面，手动勾选删除
    print("\n5.6 可选：运行 memory_review.py 进行手动审查 (30天以上非高重要记忆)")
    print("   命令: python memory_review.py")
    
    # 6. 模拟对话流程
    print("\n6. 模拟对话流程...")


    
    conversation = [
        "我们之前决定用什么前端框架？",
        "部署方案是什么？",
        "测试策略有哪些？"
    ]
    
    for user_message in conversation:
        print(f"\n   用户: {user_message}")
        
        # 检索相关记忆
        relevant_memories = manager.get_relevant_context(user_message)
        
        # 模拟AI响应（基于记忆）
        if relevant_memories:
            print(f"   助手: 根据我们的讨论，{relevant_memories[:100]}...")
        else:
            print(f"   助手: 我没有找到相关的历史记忆。")
    
    print("\n" + "=" * 60)
    print("快速演示完成！")
    print("=" * 60)
    
    # 最终统计
    final_stats = service.get_stats()
    print(f"\n最终统计:")
    print(f"  - 总记忆数: {final_stats['total_memories']}")
    print(f"  - 存储路径: {final_stats['persist_dir']}")
    print(f"\n记忆库文件位置: ./memory_db/")
    print("所有记忆已持久化保存，下次启动时仍然可用。")


def how_to_integrate():
    """如何集成到AI对话流程"""
    print("\n" + "=" * 60)
    print("如何集成到AI对话流程")
    print("=" * 60)
    
    print("""
基本集成模式：

1. 在对话开始时检索相关记忆
   ```python
   from memory_service import get_memory_manager
   
   manager = get_memory_manager()
   relevant_memories = manager.get_relevant_context(user_message)
   ```

2. 将记忆注入到AI提示词中
   ```python
   prompt = f'''
   相关历史记忆：
   {relevant_memories}
   
   当前用户问题：{user_message}
   
   请基于历史记忆回答。
   '''
   ```

3. 在对话中自动存储重要信息
   ```python
   # 自动检测并存储
   if manager.should_store(user_message):
       memory_id = manager.store_conversation_memory(user_message)
   
   # 存储AI响应中的重要信息
   if manager.should_store(ai_response):
       manager.store_conversation_memory(ai_response)
   ```

4. 手动管理记忆
   ```python
   # 手动存储特定信息
   manager.store_conversation_memory(
       "重要配置：API密钥必须存储在环境变量中",
       {"topic": "安全配置", "importance": "high"}
   )
   
   # 手动搜索
   memories = service.search_memories("数据库配置", n_results=5)
   ```

高级功能：
- 使用规则系统自动触发存储/检索
- 配置不同的嵌入模型优化性能
- 实现记忆重要性评分
- 添加记忆生命周期管理
    """)


if __name__ == "__main__":
    quick_demo()
    how_to_integrate()
    
    print("\n" + "=" * 60)
    print("下一步:")
    print("1. 查看 memory_service.py 了解完整API")
    print("2. 运行 memory_integration.py 查看完整示例")
    print("3. 查看 .codebuddy/rules/ 目录下的自动规则")
    print("4. 阅读 README.md 获取详细文档")
    print("=" * 60)