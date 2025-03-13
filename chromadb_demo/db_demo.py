from typing import List

import chromadb
import requests
from chromadb.errors import NotFoundError
from main_demo.tools.search_tool_vector import SiliconFlowEmbeddingFunction, OllamaEmbeddingFunction


# 使用内存数据库
# chroma_client = chromadb.Client()
# 使用持久化数据库-sqlite3

embedding_function = OllamaEmbeddingFunction()


client = chromadb.PersistentClient(path="../main_demo/tools/chroma_db")
collection = client.get_or_create_collection(name="yunwei_knowledge", embedding_function=embedding_function)  # 指定使用余弦距离

results = collection.query(
    query_texts=["车位"],
    n_results=5
)
print(results)

# # 格式化搜索结果
# formatted_results = []
# for i, (doc, metadata, distance) in enumerate(zip(
#         results['documents'][0],
#         results['metadatas'][0],
#         results['distances'][0]
# )):
#     chunk_info = f"(第 {metadata['chunk_index'] + 1}/{metadata['total_chunks']} 块)" \
#         if metadata.get('chunk_index') is not None else ""
#
#     formatted_results.append(
#         f"【{i + 1}】 | 【来源】：{metadata['title']} {chunk_info} | 【相关度】：{distance}\n"
#         f"{doc}\n"
#     )
#
# print("\n\n".join(formatted_results))


# 相关指令用法
# client.heartbeat()  # 返回纳秒心跳 用于确保客户端保持连接。
# client.reset()  # 清空并完全重置数据库 ⚠️ 破坏性的，不可逆转
# client.get_collection(name="test") # Get a collection object from an existing collection, by name. Will raise an exception if it's not found.
# client.get_or_create_collection(name="test") # Get a collection object from an existing collection, by name. If it doesn't exist, create it.
# client.delete_collection(name="my_collection") # Delete a collection and all associated embeddings, documents, and metadata. ⚠️ This is destructive and not reversible
# collection.peek() # returns a list of the first 10 items in the collection
# collection.count() # returns the number of items in the collection
# collection.modify(name="new_name") # Rename the collection
