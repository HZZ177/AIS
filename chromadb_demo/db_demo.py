import chromadb
from chromadb.errors import NotFoundError


# 使用内存数据库
# chroma_client = chromadb.Client()
# 使用持久化数据库-sqlite3
client = chromadb.PersistentClient(path="./db")
collection = client.get_or_create_collection(name="my_collection")

collection.add(
    documents=["这是一份关于食物的文件", "这是一份关于米其林排行的文件"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    ids=["id3", "id4"]
)

results = collection.query(
    query_texts=["最好吃的食物是什么"],
    n_results=4
)

print(results)


# 相关指令用法
# client.heartbeat()  # 返回纳秒心跳 用于确保客户端保持连接。
# client.reset()  # 清空并完全重置数据库 ⚠️ 破坏性的，不可逆转
# client.get_collection(name="test") # Get a collection object from an existing collection, by name. Will raise an exception if it's not found.
# client.get_or_create_collection(name="test") # Get a collection object from an existing collection, by name. If it doesn't exist, create it.
# client.delete_collection(name="my_collection") # Delete a collection and all associated embeddings, documents, and metadata. ⚠️ This is destructive and not reversible
# collection.peek() # returns a list of the first 10 items in the collection
# collection.count() # returns the number of items in the collection
# collection.modify(name="new_name") # Rename the collection
