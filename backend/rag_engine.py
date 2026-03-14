"""
RAG Engine for SBN ChatAgent
Implements Retrieval-Augmented Generation using Ollama LLM
"""
import os
from typing import List, Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


class RAGEngine:
    """RAG Engine using Ollama and ChromaDB"""

    def __init__(self, persist_dir: str = "./data/chroma"):
        self.persist_dir = persist_dir
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=self.model_name,
            base_url=self.ollama_host
        )

        # Initialize vector store
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=persist_dir
        )

        # Initialize LLM
        self.llm = Ollama(
            model=self.model_name,
            base_url=self.ollama_host,
            temperature=0.7
        )

        # RAG prompt template
        self.prompt_template = """You are a helpful business assistant specializing in product information. Use the following context to answer questions about products.
If you cannot find the answer in the context, use your general knowledge but indicate that the information is not from the provided product catalog.

Context: {context}

Question: {question}

Answer: """

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

        # Initialize QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)

        # Add to vector store
        self.vector_store.add_documents(chunks)
        self.vector_store.persist()

    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            result = self.qa_chain.invoke({"query": question})

            # Extract source documents
            sources = []
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    sources.append(doc.page_content[:200] + "...")

            return {
                "answer": result.get("result", ""),
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": []
            }

    def add_product_data(self, products: List[Dict[str, Any]]) -> None:
        """Add product data to the RAG system"""
        documents = []

        for product in products:
            # Build comprehensive product description
            content_parts = []
            
            if product.get('ProdName'):
                content_parts.append(f"Product Name: {product['ProdName']}")
            if product.get('ProdNum'):
                content_parts.append(f"Product Number: {product['ProdNum']}")
            if product.get('ProdBrandName'):
                content_parts.append(f"Brand: {product['ProdBrandName']}")
            if product.get('ProdCatgName'):
                content_parts.append(f"Category: {product['ProdCatgName']}")
            if product.get('ProdSize'):
                content_parts.append(f"Size: {product['ProdSize']}")
            if product.get('Qty') is not None:
                content_parts.append(f"Quantity: {product['Qty']}")
            if product.get('SellingPrice'):
                content_parts.append(f"Selling Price: {product['SellingPrice']} {product.get('Currency', '')}")
            if product.get('ReferencePrice'):
                content_parts.append(f"Reference Price: {product['ReferencePrice']} {product.get('Currency', '')}")
            if product.get('ProductCost'):
                content_parts.append(f"Product Cost: {product['ProductCost']} {product.get('Currency', '')}")
            if product.get('ProdLangLongDesc'):
                content_parts.append(f"Description: {product['ProdLangLongDesc']}")
            
            content = " | ".join(content_parts) if content_parts else str(product)
            
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "product",
                    "source": "internal_api",
                    "product_id": product.get('ProdId'),
                    "product_name": product.get('ProdName', 'N/A')
                }
            ))

        if documents:
            self.add_documents(documents)

    def clear_vector_store(self) -> None:
        """Clear the vector store (for resetting data)"""
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name="products"
        )
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir
        )
