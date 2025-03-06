from crewai_tools.tools.pdf_search_tool.pdf_search_tool import PDFSearchTool

# pdf文档读取工具，通过文档内容向量化并读取
tool_pdf = PDFSearchTool(
    pdf=r"/knowledge_demo/test.pdf",
    config=dict(
        embedder=dict(
            provider="ollama",
            config=dict(
                model="nomic-embed-text",
                base_url="http://127.0.0.1:11434",
            )
        )
    )
)