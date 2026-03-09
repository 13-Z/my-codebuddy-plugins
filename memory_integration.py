"""
记忆服务集成示例
展示如何将长期记忆服务集成到AI对话流程中
"""
import sys
import json
from typing import Dict, Any

# 添加当前目录到路径，以便导入memory_service
sys.path.insert(0, '.')

try:
    from memory_service import get_memory_manager, get_memory_service
except ImportError as e:
    print(f"导入memory_service失败: {e}")
    print("请确保已安装 chromadb 和 sentence-transformers")
    print("运行: pip install chromadb sentence-transformers")
    sys.exit(1)


class ConversationIntegration:
    """对话集成类 - 模拟AI对话流程中的记忆集成"""
    
    def __init__(self):
        self.memory_manager = get_memory_manager()
        self.memory_service = get_memory_service()
        self.conversation_history = []
        self.current_topic = ""
    
    def process_user_message(self, user_message: str, conversation_id: str = "default") -> Dict[str, Any]:
        """
        处理用户消息，集成长期记忆
        
        Args:
            user_message: 用户消息
            conversation_id: 对话ID
            
        Returns:
            包含增强上下文和处理结果
        """
        print(f"\n{'='*60}")
        print(f"用户消息: {user_message}")
        print(f"{'='*60}")
        
        # 1. 自动存储重要信息（如果适用）
        stored_memory_id = self.memory_manager.store_conversation_memory(
            user_message,
            {"conversation_id": conversation_id, "user_message": True}
        )
        
        if stored_memory_id:
            print(f"[记忆存储] 已自动存储重要信息，记忆ID: {stored_memory_id}")
        
        # 2. 检索相关记忆
        relevant_memories = self.memory_manager.get_relevant_context(user_message)
        
        # 3. 构建增强的上下文
        enhanced_context = self._build_enhanced_context(user_message, relevant_memories)
        
        # 4. 模拟AI处理（这里只是演示）
        ai_response = self._simulate_ai_response(user_message, relevant_memories)
        
        # 5. 存储AI响应中的重要信息（可选）
        if self._contains_important_info(ai_response):
            self.memory_manager.store_conversation_memory(
                ai_response,
                {"conversation_id": conversation_id, "source": "ai_response", "user_message": False}
            )
        
        # 6. 更新对话历史
        self.conversation_history.append({
            "user": user_message,
            "ai": ai_response,
            "relevant_memories": relevant_memories,
            "timestamp": self._get_timestamp()
        })
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "relevant_memories": relevant_memories,
            "enhanced_context": enhanced_context,
            "stored_memory_id": stored_memory_id,
            "conversation_id": conversation_id
        }
    
    def _build_enhanced_context(self, user_message: str, relevant_memories: str) -> str:
        """构建增强的上下文"""
        context_parts = []
        
        # 添加系统提示
        context_parts.append("你是一个有帮助的AI助手，可以访问长期记忆库。")
        
        # 添加相关记忆（如果有）
        if relevant_memories and relevant_memories.strip():
            context_parts.append("\n" + relevant_memories)
        
        # 添加当前用户消息
        context_parts.append(f"\n当前用户消息: {user_message}")
        
        return "\n".join(context_parts)
    
    def _simulate_ai_response(self, user_message: str, relevant_memories: str) -> str:
        """模拟AI响应（实际使用时替换为真实的AI调用）"""
        
        # 根据相关记忆调整响应
        if relevant_memories and "技术栈" in relevant_memories:
            return "基于我们之前的讨论，你选择了React+TypeScript技术栈。我可以帮你继续完善前端架构。"
        elif relevant_memories and "数据库" in relevant_memories:
            return "根据记忆，你之前选择了PostgreSQL数据库。需要我帮你设计数据库表结构吗？"
        elif "决定" in user_message or "选择" in user_message:
            return "这是一个重要的决策。我会记住这个选择，以便后续参考。"
        elif "之前" in user_message or "记得" in user_message:
            if relevant_memories:
                return f"是的，我记得。相关记忆：{relevant_memories[:100]}..."
            else:
                return "我没有找到相关的历史记忆。请提供更多细节。"
        else:
            return f"我已收到你的消息: '{user_message}'。我会根据上下文提供帮助。"
    
    def _contains_important_info(self, text: str) -> bool:
        """检查文本是否包含重要信息"""
        important_keywords = ["重要", "注意", "决定", "选择", "配置", "设置", "建议", "推荐"]
        return any(keyword in text for keyword in important_keywords)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "total_messages": len(self.conversation_history),
            "current_topic": self.current_topic,
            "memory_stats": self.memory_service.get_stats()
        }
    
    def search_memories_directly(self, query: str, n_results: int = 5):
        """直接搜索记忆（用于调试或特定查询）"""
        print(f"\n[直接搜索] 查询: '{query}'")
        memories = self.memory_service.search_memories(query, n_results=n_results)
        
        if not memories:
            print("未找到相关记忆")
            return
        
        print(f"找到 {len(memories)} 条相关记忆:")
        for i, mem in enumerate(memories, 1):
            print(f"{i}. ID: {mem['id']}")
            print(f"   文本: {mem['text'][:100]}...")
            print(f"   话题: {mem['metadata'].get('topic', 'N/A')}")
            print(f"   时间: {mem['metadata'].get('timestamp', 'N/A')}")
            print()
    
    def list_all_memories(self, limit: int = 10):
        """列出所有记忆"""
        print(f"\n[所有记忆] 显示最近 {limit} 条:")
        memories = self.memory_service.get_all_memories(limit=limit)
        
        if not memories:
            print("记忆库为空")
            return
        
        for i, mem in enumerate(memories, 1):
            print(f"{i}. ID: {mem['id']}")
            print(f"   文本: {mem['text'][:80]}...")
            print(f"   时间: {mem['metadata'].get('timestamp', 'N/A')}")
            print()


def run_demo():
    """运行演示"""
    print("=" * 60)
    print("长期记忆服务集成演示")
    print("=" * 60)
    
    # 初始化集成
    integration = ConversationIntegration()
    
    # 演示对话
    demo_conversations = [
        "我们决定使用 React + TypeScript 构建前端项目，并采用 Vite 作为构建工具。",
        "数据库选择 PostgreSQL，因为需要复杂查询和事务支持。",
        "关于前端框架，我们应该选择哪个？",
        "数据库配置有什么注意事项？",
        "我之前决定用什么技术栈来着？",
        "我们将使用 Docker 容器化部署，配置 Kubernetes 集群。"
    ]
    
    for i, message in enumerate(demo_conversations, 1):
        print(f"\n{'#'*60}")
        print(f"对话轮次 {i}")
        print(f"{'#'*60}")
        
        result = integration.process_user_message(message, f"demo_conversation_{i}")
        
        print(f"\nAI响应: {result['ai_response']}")
        
        if result['relevant_memories']:
            print(f"\n相关记忆:\n{result['relevant_memories']}")
    
    # 显示记忆库状态
    print(f"\n{'='*60}")
    print("记忆库状态")
    print("=" * 60)
    
    stats = integration.memory_service.get_stats()
    print(f"总记忆数: {stats['total_memories']}")
    print(f"存储路径: {stats['persist_dir']}")
    
    # 列出所有记忆
    integration.list_all_memories(limit=5)
    
    # 演示直接搜索
    integration.search_memories_directly("前端框架", n_results=3)
    integration.search_memories_directly("部署", n_results=2)
    
    print("\n演示完成！")


if __name__ == "__main__":
    run_demo()