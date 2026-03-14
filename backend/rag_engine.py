"""
RAG Engine for SBN ChatAgent
Implements Retrieval-Augmented Generation using Ollama LLM
"""
import os
import logging
from typing import List, Optional, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG Engine using Ollama and ChromaDB"""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.model_name = settings.ollama_model
        self.ollama_host = settings.ollama_host

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

        # Initialize LLM with optimized settings
        self.llm = Ollama(
            model=self.model_name,
            base_url=self.ollama_host,
            temperature=0.3,  # Lower temperature for more factual responses
            num_ctx=4096,  # Increased context window for better RAG
            top_p=0.9  # Nucleus sampling for better coherence
        )

        # RAG prompt template with enhanced instructions
        self.prompt_template = """You are a professional AI product assistant for SBN. Your role is to help users find and understand product information.

IMPORTANT INSTRUCTIONS:
1. Use ONLY the provided context to answer questions about products
2. If the answer is not in the context, say "I don't have that information in the product catalog" and offer general guidance
3. Be specific and cite product names, numbers, and prices when available
4. If asked about categories, list all relevant products from that category
5. For price comparisons, provide clear comparisons with specific values
6. Keep responses concise but informative (2-4 sentences unless more detail is requested)
7. If the user asks about availability, refer to the Quantity (Qty) field
8. Always be helpful and professional in tone

Previous Conversation (if any):
{context}

Question: {question}

Answer:"""

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

    def query(self, question: str, context_history: str = "") -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User's question
            context_history: Optional conversation history to include in context
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Build context with RAG retrieval and conversation history
            retrieved_docs = self.vector_store.similarity_search(question, k=5)
            rag_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Combine RAG context with conversation history
            full_context = rag_context
            if context_history:
                full_context = f"Previous Conversation:\n{context_history}\n\nProduct Context:\n{rag_context}"

            # Build prompt with full context
            prompt = self.prompt_template.format(context=full_context, question=question)
            
            # Generate response
            response = self.llm.invoke(prompt)

            # Extract source documents
            sources = []
            for doc in retrieved_docs:
                sources.append(doc.page_content[:200] + "...")

            return {
                "answer": response,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Query error: {e}")
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
