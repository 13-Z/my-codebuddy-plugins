"""
长期记忆服务 - 基于 ChromaDB 和 Sentence Transformers
提供自动化存储、检索功能，可与对话流程集成。
"""
import os
import json
import uuid
from datetime import datetime, timedelta

from typing import List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings


def resolve_persist_dir(persist_dir: Optional[str] = None) -> str:
    """确定持久化目录，优先使用用户指定或D盘"""
    if persist_dir:
        return os.path.abspath(persist_dir)
    env_path = os.getenv("MEM_DB_PATH")
    if env_path:
        return os.path.abspath(env_path)
    # 优先尝试 D 盘 / E 盘 / WSL 映射
    drive_candidates = ["D:\\", "E:\\", "/mnt/d", "/mnt/e"]
    for drive in drive_candidates:
        if os.path.exists(drive):
            return os.path.abspath(os.path.join(drive, "codebuddy_memory_db"))
    return os.path.abspath("./memory_db")


class MemoryService:
    """长期记忆服务"""
    
    def __init__(self, persist_dir: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):

        """
        初始化记忆服务
        
        Args:
            persist_dir: 向量数据库存储目录
            model_name: 句子嵌入模型名称
        """
        resolved_dir = resolve_persist_dir(persist_dir)
        self.persist_dir = resolved_dir
        os.makedirs(resolved_dir, exist_ok=True)
        self._last_cleanup_ts: Optional[datetime] = None
        
        # 初始化嵌入模型
        print(f"正在加载嵌入模型: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=resolved_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        
        # 获取或创建记忆集合
        try:
            self.collection = self.client.get_collection("conversation_memory")
            print("已加载现有记忆集合")
        except:
            self.collection = self.client.create_collection(
                name="conversation_memory",
                metadata={"description": "对话长期记忆存储"}
            )
            print("已创建新的记忆集合")
    
    def store_memory(self, text: str, metadata: Optional[Dict] = None) -> str:
        """
        存储一段记忆
        
        Args:
            text: 记忆文本内容
            metadata: 附加元数据（如话题、时间、重要性等）
            
        Returns:
            记忆ID
        """
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"
        
        # 默认元数据
        default_metadata = {
            "timestamp": datetime.now().isoformat(),
            "source": "conversation",
            "importance": "medium",
            "module": "normal"
        }

        
        if metadata:
            default_metadata.update(metadata)
        
        # 添加到向量数据库
        self.collection.add(
            documents=[text],
            metadatas=[default_metadata],
            ids=[memory_id]
        )
        
        print(f"已存储记忆: {memory_id}")
        return memory_id
    
    def search_memories(self, query: str, n_results: int = 5, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            threshold: 相似度阈值（0-1），低于此值的结果将被过滤
            
        Returns:
            相关记忆列表，按相似度排序
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2  # 多取一些以便过滤
            )
            
            # 处理结果
            memories = []
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    # 由于ChromaDB不直接返回相似度分数，我们使用距离
                    # 这里简化处理：假设所有结果都相关
                    memory = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    memories.append(memory)
            
            # 按距离排序（越小越相似）
            memories.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
            
            # 返回前n_results个
            return memories[:n_results]
            
        except Exception as e:
            print(f"搜索记忆时出错: {e}")
            return []
    
    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有记忆（按时间倒序）"""
        try:
            # 获取所有记忆
            results = self.collection.get()
            
            memories = []
            for i in range(len(results['ids'])):
                memory = {
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                }
                memories.append(memory)
            
            # 按时间倒序排序
            memories.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
            return memories[:limit]
            
        except Exception as e:
            print(f"获取所有记忆时出错: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除指定记忆"""
        try:
            self.collection.delete(ids=[memory_id])
            print(f"已删除记忆: {memory_id}")
            return True
        except Exception as e:
            print(f"删除记忆时出错: {e}")
            return False
    
    def clear_all(self) -> bool:
        """清空所有记忆"""
        try:
            self.client.delete_collection("conversation_memory")
            self.collection = self.client.create_collection("conversation_memory")
            print("已清空所有记忆")
            return True
        except Exception as e:
            print(f"清空记忆时出错: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆库统计信息"""
        try:
            count = self.collection.count()
            drive, _ = os.path.splitdrive(self.persist_dir)
            return {
                "total_memories": count,
                "persist_dir": self.persist_dir,
                "storage_device": drive or "",
                "collection_name": "conversation_memory"
            }
        except:
            return {"total_memories": 0, "persist_dir": self.persist_dir}

    def cleanup_memories(self, retention_days_low: int = 14, retention_days_normal: int = 90, min_keep: int = 500) -> Dict[str, Any]:
        """清理旧的非重要记忆，释放空间"""
        try:
            results = self.collection.get()
            now = datetime.now()
            items = []
            for i in range(len(results["ids"])):
                meta = results["metadatas"][i] or {}
                ts_raw = meta.get("timestamp")
                try:
                    ts = datetime.fromisoformat(ts_raw) if ts_raw else None
                except Exception:
                    ts = None
                items.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": meta,
                    "timestamp": ts
                })

            # 按时间倒序，保留最新的 min_keep 条
            items.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)
            keep_latest = set([item["id"] for item in items[:min_keep]])

            to_delete = []
            for item in items[min_keep:]:
                meta = item["metadata"]
                importance = meta.get("importance", "medium")
                ts = item["timestamp"]
                if not ts:
                    continue
                age_days = (now - ts).days
                if importance in ["high", "重要", "critical"]:
                    continue  # 高重要性不清理
                if importance in ["low", "低"] and age_days > retention_days_low:
                    to_delete.append(item["id"])
                elif age_days > retention_days_normal:
                    to_delete.append(item["id"])

            if to_delete:
                self.collection.delete(ids=to_delete)

            return {
                "deleted": len(to_delete),
                "kept_latest": min_keep,
                "checked": len(items),
                "retention_days_low": retention_days_low,
                "retention_days_normal": retention_days_normal,
            }
        except Exception as e:
            print(f"清理记忆时出错: {e}")
            return {"deleted": 0, "error": str(e)}

    def auto_cleanup_if_needed(self, retention_days_low: int = 14, retention_days_normal: int = 90, min_keep: int = 500, min_interval_hours: int = 24) -> Dict[str, Any]:
        """按时间间隔自动清理，默认24小时运行一次"""
        now = datetime.now()
        if self._last_cleanup_ts and (now - self._last_cleanup_ts) < timedelta(hours=min_interval_hours):
            return {"skipped": True, "reason": "recent_cleanup"}
        result = self.cleanup_memories(retention_days_low, retention_days_normal, min_keep)
        self._last_cleanup_ts = now
        return result

    def list_cleanup_candidates(self, older_than_days: int = 30, importance_max: str = "medium", limit: int = 200) -> List[Dict[str, Any]]:
        """列出清理候选（默认：超过30天且非高重要）"""
        try:
            results = self.collection.get()
            now = datetime.now()
            items = []
            for i in range(len(results["ids"])):
                meta = results["metadatas"][i] or {}
                imp = meta.get("importance", "medium")
                if imp.lower() in ["high", "重要", "critical"]:
                    continue
                ts_raw = meta.get("timestamp")
                try:
                    ts = datetime.fromisoformat(ts_raw) if ts_raw else None
                except Exception:
                    ts = None
                if not ts:
                    continue
                age_days = (now - ts).days
                if age_days < older_than_days:
                    continue
                items.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": meta,
                    "timestamp": ts,
                    "age_days": age_days,
                })
            items.sort(key=lambda x: x["timestamp"] or datetime.min)
            return items[:limit]
        except Exception as e:
            print(f"列出清理候选时出错: {e}")
            return []


class ConversationMemoryManager:


    """对话记忆管理器 - 与AI对话流程集成"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.important_keywords = [
            "决定", "选择", "采用", "使用", "配置", "设置", "重要", "记住",
            "决策", "方案", "架构", "设计", "关键", "注意事项"
        ]
        self.high_keywords = [
            "安全", "密钥", "凭证", "生产", "上线", "合规", "隐私", "性能",
            "SLA", "故障", "严重", "高优先级", "必须", "关键路径"
        ]
        self.low_indicators = ["测试", "调试", "demo", "示例", "随便", "临时", "log", "日志"]
    
    def classify_importance(self, text: str, provided: Optional[str] = None) -> str:
        """根据文本内容判断重要性"""
        if provided:
            return provided
        text_lower = text.lower()
        # 关键/高优先级词命中则高
        for kw in self.high_keywords + self.important_keywords:
            if kw in text_lower:
                return "high"
        # 很短或明显是测试/日志则低
        if len(text.strip()) < 20:
            return "low"
        for kw in self.low_indicators:
            if kw in text_lower:
                return "low"
        return "medium"
    
    def should_store(self, text: str) -> bool:
        """判断是否应该存储这段文本"""
        importance = self.classify_importance(text)
        return importance in ["high", "medium"]
    
    def extract_topic(self, text: str) -> str:

        """从文本中提取话题"""
        # 简单实现：取前几个词作为话题
        words = text.split()[:5]
        return " ".join(words) + "..."
    
    def store_conversation_memory(self, text: str, conversation_context: Optional[Dict] = None) -> Optional[str]:
        """存储对话记忆"""
        if not self.should_store(text):
            return None
        
        provided_importance = conversation_context.get("importance") if conversation_context else None
        importance = self.classify_importance(text, provided_importance)
        module = "important" if importance == "high" else "normal"
        
        metadata = {
            "type": "conversation_memory",
            "topic": self.extract_topic(text),
            "importance": importance,
            "module": module,
            "auto_stored": True
        }
        
        if conversation_context:
            metadata.update(conversation_context)
        
        memory_id = self.memory_service.store_memory(text, metadata)
        # 默认每天触发一次自动清理（低/普通重要性且过期的记忆）
        self.memory_service.auto_cleanup_if_needed()
        return memory_id

    
    def get_relevant_context(self, current_query: str, max_memories: int = 3) -> str:
        """获取与当前查询相关的记忆上下文"""
        memories = self.memory_service.search_memories(current_query, n_results=max_memories)
        
        if not memories:
            return ""
        
        context_parts = ["**相关记忆（长期记忆）:**"]
        for i, mem in enumerate(memories, 1):
            text = mem['text']
            meta = mem['metadata']
            topic = meta.get('topic', '未知话题')
            time = meta.get('timestamp', '未知时间')
            importance = meta.get('importance', '未知')
            module = meta.get('module', 'normal')
            
            context_parts.append(f"{i}. [{topic} | {importance}/{module}] {text} (时间: {time})")
        
        return "\n".join(context_parts)



# 全局记忆服务实例
_memory_service_instance = None
_memory_manager_instance = None

def get_memory_service() -> MemoryService:
    """获取全局记忆服务实例（单例）"""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance

def get_memory_manager() -> ConversationMemoryManager:
    """获取全局记忆管理器实例（单例）"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_service = get_memory_service()
        _memory_manager_instance = ConversationMemoryManager(_memory_service)
    return _memory_manager_instance


# 测试函数
def test_memory_service():
    """测试记忆服务"""
    print("=== 测试记忆服务 ===")
    
    # 初始化
    service = MemoryService(persist_dir="./test_memory_db")
    
    # 存储测试记忆
    mem1_id = service.store_memory(
        "用户决定使用 React + TypeScript 构建前端项目，并采用 Vite 作为构建工具。",
        {"topic": "技术栈决策", "importance": "high"}
    )
    
    mem2_id = service.store_memory(
        "项目将使用 JWT 进行用户认证，并搭配 Redis 存储会话信息。",
        {"topic": "认证方案", "importance": "high"}
    )
    
    mem3_id = service.store_memory(
        "数据库选择 PostgreSQL，因为需要复杂查询和事务支持。",
        {"topic": "数据库选型", "importance": "high"}
    )
    
    # 搜索测试
    print("\n=== 搜索测试 ===")
    results = service.search_memories("前端框架选择", n_results=2)
    print(f"搜索到 {len(results)} 条相关记忆:")
    for i, mem in enumerate(results, 1):
        print(f"{i}. {mem['text']}")
    
    # 获取统计信息
    stats = service.get_stats()
    print(f"\n=== 统计信息 ===")
    print(f"总记忆数: {stats['total_memories']}")
    
    # 测试记忆管理器
    print("\n=== 测试记忆管理器 ===")
    manager = ConversationMemoryManager(service)
    
    test_text = "我们决定使用 Docker 容器化部署，并配置 Kubernetes 集群管理。"
    should_store = manager.should_store(test_text)
    print(f"是否应该存储: {should_store}")
    
    if should_store:
        mem_id = manager.store_conversation_memory(test_text, {"conversation_id": "test_001"})
        print(f"已存储记忆 ID: {mem_id}")
    
    # 获取相关上下文
    context = manager.get_relevant_context("部署方案", max_memories=2)
    print(f"\n相关上下文:\n{context}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_memory_service()