from crewai import LLM
import threading
import queue
import os
from typing import Any
from crewai import LLM
from crewai.utilities.events import LLMStreamChunkEvent, crewai_event_bus
from crewai.utilities.events.base_event_listener import BaseEventListener

# 用于通信的线程安全队列
token_queue = queue.Queue()


# Event Handler (Producer): 只负责将tokens入队列，不做处理
class MyLLMStreamListener(BaseEventListener):
    def __init__(self):
        super().__init__()

    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(LLMStreamChunkEvent)
        def on_llm_stream_chunk(source: Any, event: LLMStreamChunkEvent):
            # 不要在这里打印或屏蔽，只用快速入队即可！
            token = event.chunk
            token_queue.put(token)


llm_stream_listener = MyLLMStreamListener()


# 消费者线程处理到达的tokens
def token_consumer():
    while True:
        try:
            # 根据实际需要调整超时时间
            token = token_queue.get(timeout=5)
        except queue.Empty:
            print("\n----- 没有获取到新内容token，结束当次消费")
            break
        # 在此处理tokens内容：打印、保存、发送到 API 等
        print("\n----- 获取到新内容token -----")
        print(token)
        print("---------------------------------------")
        token_queue.task_done()


# 开启消费者线程
consumer_thread = threading.Thread(target=token_consumer, daemon=True)
consumer_thread.start()

stream_llm = LLM(
    # openrouter
    model="openrouter/google/gemini-2.0-flash-001",
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    stream=True
)

# 调用 LLM 生成流式输出
response = stream_llm.call("你认为AI前景如何？")

# 可选：等待消费者线程处理完所有项目后再关闭
token_queue.join()
print("\n----- 所有token输出完毕")

# 可选：确保出口干净整洁（如果主要出口立即出口）
consumer_thread.join(timeout=1)
