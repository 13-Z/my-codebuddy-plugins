# 长期记忆服务

基于 ChromaDB 和 Sentence Transformers 的长期记忆系统，可突破单次对话的上下文限制。

### English Overview
- Long-term memory manager: store/search/review/cleanup conversation memories.
- Importance tiers & modules: high/medium/low → important/normal, shown in search results.
- Configurable storage path: `MEM_DB_PATH` preferred (e.g., `D:/codebuddy_memory_db`), fallback `./memory_db`.
- Monthly review checklist: pick 7/15/30 days, select items to delete.
- Auto/manual cleanup: stale low/medium memories cleaned with safety floor (keep latest 500).
- Demos: `memory_integration.py`, quick start `quick_start.py`.

### English Quick Start
1) Install deps: `pip install -r requirements.txt`
2) Run demo: `python memory_integration.py`
3) Monthly review UI: `python memory_review.py` (choose 7/15/30 days and select to delete)
4) Optional storage path: set `MEM_DB_PATH` (prefer a larger drive) or pass `persist_dir` to `MemoryService`.

## 功能特性


- **自动存储**：检测对话中的重要决策、技术选型、用户偏好并自动存储
- **语义检索**：基于向量相似度检索相关记忆，支持语义理解
- **对话集成**：无缝集成到AI对话流程，提供上下文感知
- **持久化存储**：记忆永久保存，支持跨会话访问
- **规则驱动**：通过规则定义存储和检索策略

## 快速开始

### 1. 安装依赖
```bash
pip install chromadb sentence-transformers
```

### 2. 运行测试
```bash
python memory_service.py
```

### 3. 运行集成演示
```bash
python memory_integration.py
```

### 4. 在项目中使用
```python
from memory_service import get_memory_manager

# 获取记忆管理器
manager = get_memory_manager()

# 存储重要信息
memory_id = manager.store_conversation_memory(
    "用户决定使用React+TypeScript技术栈",
    {"conversation_id": "conv_001", "importance": "high"}
)

# 检索相关记忆
context = manager.get_relevant_context("前端框架选择")
print(context)
```

## 项目结构

```
.
├── memory_service.py          # 核心记忆服务
├── memory_integration.py      # 对话集成示例
├── requirements.txt           # 依赖列表
└── .codebuddy/rules/          # 自动存储和检索规则
    ├── auto_store_important_decisions.mdc
    └── retrieve_relevant_memories.mdc
```

## 规则系统

系统包含两个预定义规则：

### 1. 自动存储重要决策
- 检测技术决策、项目配置、用户偏好等
- 自动提取话题和重要性等级
- 排除无关内容（问候语、简单确认等）

### 2. 检索相关记忆
- 对话开始时自动检索相关历史
- 话题变更时更新上下文
- 支持语义相似度搜索

## 配置选项

### 记忆服务配置
```python
from memory_service import MemoryService

# 优先从环境变量读取存储路径（建议指向大盘，如 D:\codebuddy_memory_db）
# 环境变量：MEM_DB_PATH
service = MemoryService(
    persist_dir=None,              # 传 None 则使用 MEM_DB_PATH，否则默认 D盘 -> ./memory_db
    model_name="all-mpnet-base-v2"     # 嵌入模型
)
```

- 默认存储目录优先：`MEM_DB_PATH` > `D:\codebuddy_memory_db` > `./memory_db`
- 统计信息会显示 `storage_device` 便于确认盘符

### 重要/普通记忆模块与自动清理
- 自动标注：`importance = high/medium/low`，并映射 `module = important/normal`
- 自动清理：低/普通重要性且过期的记忆会在存储时按日触发清理（默认低14天、普通90天，保底保留最新500条）
- 手动清理：`MemoryService.cleanup_memories(retention_days_low=14, retention_days_normal=90, min_keep=500)`
- 强制立即清理：`MemoryService.auto_cleanup_if_needed(min_interval_hours=0)`
- **按月审查界面**：`python memory_review.py`（列出30天以上非高重要记忆，手动勾选保留/删除，可输入 all/范围/序号）


### 嵌入模型选择
- `all-MiniLM-L6-v2`（默认）：平衡速度与精度，384维
- `all-mpnet-base-v2`：更高精度，768维
- `paraphrase-MiniLM-L3-v2`：更快，384维


## API参考

### MemoryService 类
- `store_memory(text, metadata)` - 存储记忆
- `search_memories(query, n_results)` - 搜索记忆
- `get_all_memories(limit)` - 获取所有记忆
- `delete_memory(memory_id)` - 删除记忆
- `get_stats()` - 获取统计信息

### ConversationMemoryManager 类
- `should_store(text)` - 判断是否应存储
- `store_conversation_memory(text, context)` - 存储对话记忆
- `get_relevant_context(query)` - 获取相关上下文

## 与AI对话流程集成

### 基本集成模式
1. **接收用户消息**
2. **自动存储重要内容**
3. **检索相关记忆**
4. **构建增强上下文**
5. **调用AI模型**
6. **存储AI响应中的重要信息**

### 示例流程
```python
# 1. 初始化
manager = get_memory_manager()

# 2. 处理用户消息
user_message = "我们决定使用Docker部署"
relevant_memories = manager.get_relevant_context(user_message)

# 3. 构建提示词
prompt = f"""
相关历史记忆：
{relevant_memories}

当前问题：{user_message}
请基于历史记忆回答。
"""

# 4. 调用AI并存储结果
ai_response = call_ai_model(prompt)
if manager.should_store(ai_response):
    manager.store_conversation_memory(ai_response)
```

## 性能考虑

- **首次加载**：需要下载预训练模型（约数百MB）
- **检索速度**：毫秒级响应（依赖硬件）
- **存储空间**：每百万记忆约需1-2GB磁盘空间
- **内存使用**：嵌入模型常驻内存，约200-500MB

## 扩展建议

### 1. 添加Web API
```python
# 使用FastAPI创建REST API
from fastapi import FastAPI
app = FastAPI()

@app.post("/store")
def store_memory_api(text: str):
    manager = get_memory_manager()
    memory_id = manager.store_conversation_memory(text)
    return {"memory_id": memory_id}
```

### 2. 添加管理界面
- 记忆浏览和搜索界面
- 手动编辑和删除功能
- 记忆库统计分析

### 3. 高级功能
- 记忆重要性自动评分
- 记忆生命周期管理（自动归档、清理）
- 多用户隔离支持
- 记忆关联图构建

## 故障排除

### 常见问题
1. **导入错误**：确保已安装所有依赖
2. **模型下载失败**：检查网络连接，或手动下载模型
3. **存储权限问题**：确保对存储目录有写权限
4. **内存不足**：使用更小的嵌入模型或增加系统内存

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 许可证

MIT License