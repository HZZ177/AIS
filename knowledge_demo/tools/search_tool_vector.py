import re
from typing import Type, List, Optional, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import requests
import json
import chromadb
import numpy as np
from tqdm import tqdm


class OllamaEmbeddingFunction:
    """自定义 Ollama Embedding 函数"""

    def __init__(self, model_name: str = "nomic-embed-text:latest"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/embeddings"

    def __call__(self, input: List[str]) -> List[List[float]]:
        """生成文本嵌入向量

        Args:
            input: 需要生成嵌入向量的文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        embeddings = []

        for text in input:
            try:
                response = requests.post(
                    self.url,
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                if response.status_code == 200:
                    embedding = response.json().get('embedding', [])
                    embeddings.append(embedding)
                else:
                    print(f"Error getting embedding: {response.status_code}")
                    embeddings.append([0.0] * 4096)
            except Exception as e:
                print(f"Error in embedding generation: {str(e)}")
                embeddings.append([0.0] * 4096)

        return embeddings


class YunWeiSearchToolInput(BaseModel):
    """Input schema for SearchTool."""
    keyword: str = Field(..., description="需要查询的关键字")


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = """
    当需要查询运维中心知识库信息时使用该工具。
    """
    args_schema: Type[BaseModel] = YunWeiSearchToolInput

    # 使用 PrivateAttr 来存储私有属性
    _chroma_client: chromadb.PersistentClient = PrivateAttr(default=None)
    _collection: Any = PrivateAttr(default=None)
    _embedding_function: OllamaEmbeddingFunction = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_chromadb()

    def _fetch_api_data(self, keyword: str) -> List[dict]:
        """从 API 获取数据"""
        url = "https://yunwei-help.keytop.cn/helpApi/HelpDoc/getDataByKeyword"
        payload = {
            "keyword": keyword,
            "pageIndex": 1,
            "pageSize": 20,
            "projectId": 27
        }
        headers = {
            'token': '5iw61f16wtjh2p46ue38h19tloo5pftw9fupsd7omeyd6b9uj1jyv4pr0ts86hvdozt8apcrbhbahb9giw74o0kt14c0mxzzxfp40wmfqdiaahsxdvaqzvofmmplm2aesjtgk1pt67zpx7bb',
            'userid': '6c2c601eaf9c4babbb0f8b1a6601260c',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("data", {}).get("list", [])
        return []

    def _initialize_chromadb(self):
        """初始化 ChromaDB 客户端和集合"""
        try:
            import shutil
            import os

            # 删除现有的数据库
            db_path = "./chroma_db"

            # 初始化 ChromaDB 客户端
            self._chroma_client = chromadb.PersistentClient(
                path=db_path
            )
            print(f"ChromaDB 客户端初始化成功，dbid={id(self._chroma_client)}")

            # 初始化 embedding 函数
            self._embedding_function = OllamaEmbeddingFunction(
                model_name="nomic-embed-text:latest"
            )
            print("Embedding 函数初始化成功")

            # 创建新集合
            self._collection = self._chroma_client.get_or_create_collection(
                name="yunwei_knowledge",
                embedding_function=self._embedding_function,
                metadata={"hnsw:space": "cosine"}  # 指定使用余弦距离
            )
            print("集合初始化成功：yunwei_knowledge")

            if self._collection is None:
                raise Exception("集合初始化失败")

        except Exception as e:
            print(f"ChromaDB 初始化失败: {str(e)}")
            raise

    def _split_text(self, text: str, chunk_size: int = 2048, overlap: int = 100) -> List[str]:
        """将长文本分成固定大小的块

        Args:
            text: 要分割的文本
            chunk_size: 每个块的最大字符数
            overlap: 块之间的重叠字符数

        Returns:
            List[str]: 文本块列表
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            # 计算当前块的结束位置
            end = start + chunk_size

            # 如果不是最后一块，添加重叠部分
            if end < text_len:
                chunks.append(text[start:end])
                # 下一块的起始位置 = 当前块的结束位置 - 重叠长度
                start = end - overlap
            else:
                # 最后一块，直接添加剩余文本
                chunks.append(text[start:])
                break

        return chunks

    def _store_in_chromadb(self, documents: List[dict]) -> None:
        """将文档存储到 ChromaDB，逐块存储"""
        if not documents:
            print("没有文档需要存储")
            return

        if self._collection is None:
            print("ChromaDB 集合未初始化")
            return

        # 首先计算总块数
        total_chunks = 0
        valid_docs = []
        for doc in documents:
            if "接口" not in doc.get("text", "") and doc.get("md"):
                chunks = self._split_text(doc.get("md", ""))
                total_chunks += len(chunks)
                valid_docs.append((doc, chunks))

        print(f"去掉接口文档，总计 {len(valid_docs)} 个文档，{total_chunks} 个文本块")
        total_stored = 0

        # 使用进度条显示总进度
        with tqdm(total=total_chunks, desc="存储文档块") as pbar:
            for doc_index, (doc, chunks) in enumerate(valid_docs):
                title = doc.get("text", "")

                for chunk_index, chunk in enumerate(chunks):
                    try:
                        # 直接存储每个块
                        doc_id = f"doc_{doc_index}_chunk_{chunk_index}"
                        existing = self._collection.get(doc_id) is not None
                        if existing:
                            print(f"跳过已存在的文档块 {doc_id}")
                            pbar.update(1)
                            continue
                        metadata = {
                            "title": title,
                            "source": "yunwei_api",
                            "chunk_index": chunk_index,
                            "total_chunks": len(chunks)
                        }

                        self._collection.add(
                            documents=[chunk],
                            ids=[doc_id],
                            metadatas=[metadata]
                        )

                        total_stored += 1
                        pbar.set_postfix({
                            "已存储": total_stored,
                            "当前文档": f"{title[:20]}..."
                        })

                    except Exception as e:
                        print(f"\n存储块时出错 (文档 {doc_index}, 块 {chunk_index}): {str(e)}")

                    pbar.update(1)

        print(f"\n成功存储 {total_stored} 个文本块到向量数据库")

    def _search_from_chromadb(self, keyword: str, n_results: int = 5) -> str:
        """从 ChromaDB 搜索相关文档"""
        try:
            print(f"查询，dbid={id(self._chroma_client)}")
            results = self._collection.query(
                query_texts=[keyword],
                n_results=n_results
            )

            if not results['documents'][0]:
                return "未找到相关信息"

            # 格式化搜索结果
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
            )):
                chunk_info = f"(第 {metadata['chunk_index'] + 1}/{metadata['total_chunks']} 块)" \
                    if metadata.get('chunk_index') is not None else ""

                formatted_results.append(
                    f"【{i + 1}】 | 【来源】：{metadata['title']} {chunk_info} | 【相关度】：{distance}\n"
                    f"{doc}\n"
                )

            return "\n\n".join(formatted_results)

            # return results
        except Exception as e:
            return f"搜索出错: {str(e)}"

    def _run(self, keyword: str) -> str:
        try:
            if isinstance(keyword, dict):
                keyword = keyword.get('keyword')

            print(f"接收的关键词：{keyword}")

            # 确保 ChromaDB 已初始化
            if self._collection is None:
                print("ChromaDB 集合未初始化，尝试重新初始化...")
                self._initialize_chromadb()

            # 1. 从 API 获取数据
            api_data = self._fetch_api_data(keyword)
            print(f"从 API 获取到 {len(api_data)} 条数据")

            # 2. 存储到 ChromaDB
            self._store_in_chromadb(api_data)

            # 3. 从 ChromaDB 搜索
            results = self._search_from_chromadb(keyword)

            return results

        except Exception as e:
            print(f"错误详情: {str(e)}")
            return f"工具执行出错: {str(e)}"


if __name__ == "__main__":
    tool = SearchTool()

    # 测试搜索
    test_keywords = ["入车后，车位状态不变化",]
    for keyword in test_keywords:
        print(f"\n测试关键词: {keyword}")
        print("=" * 50)
        result = tool.run(keyword=keyword)
        print(result)
