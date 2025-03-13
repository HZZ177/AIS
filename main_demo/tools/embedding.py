from typing import List
import requests
from main_demo.core.logger import logger


class BasicEmbeddingFunction:
    """基础Embedding类"""

    def __init__(self, model_name):
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
