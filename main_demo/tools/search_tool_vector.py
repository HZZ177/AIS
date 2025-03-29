from typing import Type, List, Optional, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import requests
import chromadb
from tqdm import tqdm
from main_demo.core.logger import logger
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions
import os # 确保导入 os 模块


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
                    logger.error(f"调用ollama embedding API失败，状态码: {response.status_code}")
                    embeddings.append([0.0] * 4096)
            except Exception as e:
                logger.error(f"embedding嵌入向量失败: {str(e)}")
                embeddings.append([0.0] * 4096)

        return embeddings


class SiliconFlowEmbeddingFunction:
    """自定义 siliconflow Embedding 函数"""

    def __init__(self, api_key="sk-vxyvdnryevgolxatlsqilklzpiyfadxpkkqpvsagrgvuzavi", model_name="Pro/BAAI/bge-m3"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://api.siliconflow.cn/v1/embeddings"
        self.dimension = 1024   # Pro/BAAI/bge-m3 的维度是 1024

    def __call__(self, input: List[str]) -> List[List[float]]:
        """生成文本嵌入向量
        Args:
            input: 需要生成嵌入向量的文本列表
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        logger.debug(f"--- SiliconFlowEmbeddingFunction __call__ 被调用 ---")
        logger.debug(f"输入文本数量: {len(input)}, 第一个文本片段(最多100字符): {input[0][:100] if input else 'N/A'}...")
        embeddings = []
        for idx, text in enumerate(input):
            logger.debug(f"正在处理第 {idx+1}/{len(input)} 个文本块的 embedding...")
            # 跳过空文本或仅包含空格的文本
            if not text or text.isspace():
                logger.warning(f"跳过空文本块的 embedding 生成")
                embeddings.append([0.0] * self.dimension)  # 使用零向量填充
                continue
            try:
                response = requests.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "input": text,
                        "encoding_format": "float"
                    }
                )
                response.raise_for_status()  # 改为检查 >=400 的错误状态码
                response_data = response.json()
                # 检查 'data' 列表是否存在且非空
                if 'data' in response_data and isinstance(response_data['data'], list) and len(
                        response_data['data']) > 0:
                    # 检查第一个元素是否有 'embedding' 并且它是一个列表
                    embedding_data = response_data['data'][0]
                    if 'embedding' in embedding_data and isinstance(embedding_data['embedding'], list) and len(
                            embedding_data['embedding']) == self.dimension:
                        embeddings.append(embedding_data['embedding'])
                        logger.debug(f"成功获取第 {idx+1} 个文本块的 embedding (维度: {len(embedding_data['embedding'])})")
                    else:
                        # 即使状态码 200，如果 embedding 数据无效或维度不匹配，也记录错误并使用零向量
                        logger.error(
                            f"API 成功响应但 embedding 数据无效或维度错误 ({len(embedding_data.get('embedding', []))} != {self.dimension})。Text: {text[:100]}... Response: {response_data}")
                        embeddings.append([0.0] * self.dimension)
                else:
                    # 即使状态码 200，如果 'data' 结构不符合预期，也记录错误
                    logger.error(
                        f"API 成功响应但 'data' 结构不符合预期。Text: {text[:100]}... Response: {response_data}")
                    embeddings.append([0.0] * self.dimension)
            except requests.exceptions.RequestException as e:
                # 处理所有 requests 相关的错误 (连接、超时、HTTP错误等)
                status_code = e.response.status_code if e.response is not None else "N/A"
                error_details = str(e)
                if e.response is not None:
                    try:
                        # 尝试获取响应体中的错误信息
                        error_details += f" | Response: {e.response.text}"
                    except Exception:
                        pass  # 忽略获取响应体时的错误
                logger.error(
                    f"调用 embedding API 失败 (状态码: {status_code})。Text: {text[:100]}... Error: {error_details}")
                embeddings.append([0.0] * self.dimension)
            except Exception as e:
                # 处理其他意外错误 (如 JSON 解析错误)
                logger.error(f"embedding 嵌入向量时发生意外错误: {str(e)}。Text: {text[:100]}...")
                embeddings.append([0.0] * self.dimension)
        logger.debug(f"--- SiliconFlowEmbeddingFunction __call__ 完成 --- 返回 {len(embeddings)} 个 embeddings.")
        return embeddings


class YunWeiSearchToolInput(BaseModel):
    """Input schema for SearchTool."""
    keyword: str = Field(..., description="需要查询的关键字")


class SearchTool(BaseTool):
    """
    1、从运维中心按关键字查询所有相关内容
    2、将内容分块后储存到向量数据库，跳过已存在的
    3、按照关键字从向量数据库中查询相关性最高的数个分块结果返回
    """
    name: str = "search_tool"
    description: str = """
    当需要查询运维中心知识库信息时使用该工具。
    """
    args_schema: Type[BaseModel] = YunWeiSearchToolInput

    # 使用 PrivateAttr 来存储私有属性
    _chroma_client: chromadb.PersistentClient = PrivateAttr(default=None)
    _collection: Any = PrivateAttr(default=None)
    # _embedding_function: SiliconFlowEmbeddingFunction = PrivateAttr(default=None)
    _embedding_function: SiliconFlowEmbeddingFunction = PrivateAttr(default=None)

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
            # 确认使用的db路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "chroma_db")
            logger.info(f"使用的 ChromaDB 绝对路径: {db_path}")

            # 初始化 ChromaDB 客户端
            self._chroma_client = chromadb.PersistentClient(
                path=db_path
            )
            logger.debug(f"ChromaDB 客户端初始化成功，dbid={id(self._chroma_client)}")

            # 初始化 embedding 函数
            # self._embedding_function = OllamaEmbeddingFunction(
            #     model_name="nomic-embed-text:latest"
            # )
            self._embedding_function = SiliconFlowEmbeddingFunction()
            logger.debug("Embedding 函数初始化成功")

            # 创建新集合
            self._collection = self._chroma_client.get_or_create_collection(
                name="yunwei_knowledge",
                embedding_function=self._embedding_function,
                metadata={"hnsw:space": "cosine"}  # 指定使用余弦距离
            )
            logger.info("集合初始化成功：yunwei_knowledge")

            if self._collection is None:
                raise Exception("集合初始化失败")

        except Exception as e:
            logger.info(f"ChromaDB 初始化失败: {str(e)}")
            raise

    @staticmethod
    def _split_text(text: str, chunk_size: int = 2048, overlap: int = 100) -> List[str]:
        """将长文本分成固定大小的块，可以指定重叠字数

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
            logger.info("没有文档需要存储")
            return

        # --- 使用 self._collection 来检查和添加 ---
        if self._collection is None:
            logger.warning("尝试存储时发现 ChromaDB 集合 (self._collection) 未初始化，尝试重新获取...")
            try:
                self._collection = self._chroma_client.get_collection(
                    name="yunwei_knowledge",
                    embedding_function=self._embedding_function
                )
                logger.info("重新获取 Collection 成功")
            except Exception as e:
                 logger.error(f"重新获取 Collection 失败: {e}", exc_info=True)
                 return # 获取失败则无法继续存储

        # 首先计算总块数
        total_chunks = 0
        valid_docs = []
        valid_docs_ids = []
        for doc in documents:
            if "接口" not in doc.get("text", "") and doc.get("md"):
                chunks = self._split_text(doc.get("md", ""))
                total_chunks += len(chunks)
                valid_docs.append((doc, chunks))
                valid_docs_ids.append(doc.get("docId"))

        logger.warning(valid_docs)
        logger.info(f"去掉接口文档，总计 {len(valid_docs)} 个文档，{total_chunks} 个文本块")
        total_stored = 0

        # 使用进度条显示总进度
        with tqdm(total=total_chunks, desc="存储文档块") as pbar:
            for doc_index, (doc, chunks) in enumerate(valid_docs):
                title = doc.get("text", "")

                for chunk_index, chunk in enumerate(chunks):
                    try:
                        # 直接存储每个块
                        doc_id = f"doc_{valid_docs_ids[doc_index]}_chunk_{chunk_index + 1}"
                        # 仍然使用 self._collection 来执行 get 和 add
                        existing = self._collection.get(ids=[doc_id]).get("ids") != []
                        if existing:
                            logger.info(f"向量存储跳过已存在的文档块 {doc_id}")
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
                        logger.error(f"\n存储块时出错 (文档 {doc_index}, 块 {chunk_index}): {str(e)}")

                    pbar.update(1)

        logger.info(f"\n成功存储 {total_stored} 个文本块到向量数据库")

    def _search_from_chromadb(self, keyword: str, n_results: int = 5) -> str:
        """从 ChromaDB 搜索相关文档"""
        try:
            logger.info(f"开始从chromadb查询关键词：{keyword}")

            # --- 修改：强制重新获取 Collection 对象， crewai中直接使用self.collection会导致查不到任何东西，原因未知 ---
            if self._chroma_client:
                try:
                    # 尝试重新获取集合对象，而不是直接使用 self._collection
                    current_collection = self._chroma_client.get_collection(
                        name="yunwei_knowledge",
                        embedding_function=self._embedding_function # 确保传递 embedding function
                    )
                    collection_count = current_collection.count()
                    logger.info(f"查询前检查：重新获取集合 '{current_collection.name}' 成功，包含 {collection_count} 个文档")
                except Exception as e:
                    logger.error(f"查询前检查：重新获取集合时出错: {e}", exc_info=True)
                    return "错误：向量数据库集合获取失败"
            else:
                logger.error("查询前检查：ChromaDB 客户端 self._chroma_client 未初始化！")
                return "错误：向量数据库客户端未初始化"

            if current_collection is None:
                 logger.error("查询前检查：未能成功获取 Collection 对象")
                 return "错误：无法执行查询，Collection 对象无效"
            # --- 修改结束 ---


            logger.info(f"""
            即将执行的搜索语句：
            results = current_collection.query(
                query_texts={[keyword]},
                n_results={n_results}
            )
            """)
            # 使用重新获取的 collection 对象进行查询
            results = current_collection.query(
                query_texts=[keyword],
                n_results=n_results
            )
            logger.info(f"ChromaDB 查询原始返回: {results}")

            # 检查 documents 是否为空列表或列表的第一个元素为空列表 (使用 results 变量)
            if not results or not results.get('documents') or not results['documents'][0]:
                logger.warning(f"查询关键词 '{keyword}' 未在 ChromaDB 中找到任何匹配文档。")
                return "未找到相关信息"

            # 格式化搜索结果 (使用 results 变量)
            formatted_results = []
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
            )):
                chunk_info = f"(第 {metadata['chunk_index'] + 1}/{metadata['total_chunks']} 块)-({doc_id})" \
                    if metadata.get('chunk_index') is not None else ""

                formatted_results.append(
                    f"【{i + 1}】 | 【来源】：{metadata['title']} {chunk_info} | 【相关度】：{distance}\n"
                    f"{doc}\n"
                )

            logger.info(f"成功格式化 {len(formatted_results)} 条搜索结果。")
            return "\n\n".join(formatted_results)

        except Exception as e:
            logger.error(f"向量搜索执行过程中出错: {str(e)}", exc_info=True)
            return f"向量搜索出错: {str(e)}"

    def _run(self, keyword: str) -> str:
        """
        1、从运维中心按关键字搜索相关背景资料
        2、将搜索结果分块，存储到ChromaDB，如果已存在id则跳过
        3、从 ChromaDB 搜索相关文档
        :param keyword:
        :return:
        """
        logger.info(f"--- SearchTool._run 被调用 ---")
        logger.info(f"接收到的 keyword 类型: {type(keyword)}, 值: {repr(keyword)}")

        try:
            # 参数处理
            if isinstance(keyword, dict) and 'keyword' in keyword:
                 actual_keyword = keyword.get('keyword')
                 logger.info(f"从字典中提取 keyword: {actual_keyword}")
            elif isinstance(keyword, str):
                 actual_keyword = keyword
                 logger.info(f"接收到的 keyword 是字符串: {actual_keyword}")
            else:
                 logger.error(f"接收到非预期的 keyword 类型: {type(keyword)}。尝试将其转为字符串。")
                 actual_keyword = str(keyword)

            if not actual_keyword or not actual_keyword.strip():
                logger.error("提取或转换后的 keyword 为空或无效，无法执行搜索。")
                return "错误：未能获取有效的搜索关键字。"

            logger.info(f"工具实际使用的关键词：'{actual_keyword}'")

            logger.info(f"开始从 运维中心API 获取数据，关键词: '{actual_keyword}'")
            api_data = self._fetch_api_data(actual_keyword)
            logger.info(f"从API获取到 {len(api_data)} 条数据")

            logger.info(f"开始存储数据到 ChromaDB")
            self._store_in_chromadb(api_data)   # 内部会检查 self._collection
            logger.info(f"数据存储完成")

            logger.info(f"开始从 ChromaDB 搜索，关键词: '{actual_keyword}'")
            results = self._search_from_chromadb(actual_keyword)    # 内部会重新获取 collection
            logger.info(f"ChromaDB 搜索完成，_search_from_chromadb 返回结果长度: {len(results)}")

            return results

        except Exception as e:
            logger.error(f"工具错误详情: {str(e)}", exc_info=True)
            return f"工具执行出错: {str(e)}"


if __name__ == "__main__":
    tool = SearchTool()

    # 测试搜索
    test_keywords = "车位状态"
    result = tool.run(keyword=test_keywords)
    print(result)
