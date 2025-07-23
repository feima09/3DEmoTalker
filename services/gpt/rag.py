from .openai import OpenAI
from .qwen import Qwen
from utils import Config, get_logger, Template
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
import json
import copy
import time
import yaml

home_dir = os.getcwd()
logging = get_logger()

config = Config.get("GPT", {})
per_config = config.get("pre_config", "")
if per_config is not None:
    with open(f"{home_dir}/configs/gpt/{per_config}", 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
config = config.get("RAG", {})

embedding_config = config.get("embedding", {})
embedding = OpenAIEmbeddings(
    base_url=embedding_config.get("api_endpoint", "https://api.openai.com/v1/embeddings"),
    api_key=embedding_config.get("api_key", ""),
    model=embedding_config.get("model", "text-embedding-ada-002"),
)

top_k = config.get("top_k", 3)


def load_docs_from_json() -> List[Document]:
    start_time = time.time()
    logging.info("Loading documents from JSON files...")
    
    documents = []
    
    rag_dir = os.path.join(home_dir, "configs", "rag", "data")
    
    for filename in os.listdir(rag_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(rag_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                for i, item in enumerate(data):
                    if "input" in item and "output" in item:
                        doc = Document(
                            page_content=item["input"],
                            metadata={
                                "source_doc_id": f"{filename}_{i}",
                                "original_question": item["input"],
                                "original_answer": item["output"]
                            }
                        )
                        documents.append(doc)
                    else:
                        logging.error(f"Skipping item {i} in {filename} due to missing 'input' or 'output' fields")
            
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON from {file_path}: {str(e)}")
            except FileNotFoundError as e:
                logging.error(f"File not found: {file_path}: {str(e)}")
            except Exception as e:
                logging.error(f"Error processing {file_path}: {str(e)}")
    
    end_time = time.time()
    logging.info(f"Loaded {len(documents)} documents in {end_time - start_time:.2f} seconds.")
    
    return documents


def create_retriever(documents: List[Document]):
    start_time = time.time()
    logging.info("Creating retriever...")
    
    if not documents:
        raise ValueError("No documents found to create retriever.")
    logging.info(f"Creating retriever with {len(documents)} documents.")
    
    try:
        vectorstore = FAISS.from_documents(
            documents,
            embedding
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    except Exception as e:
        logging.error(f"Error creating retriever: {str(e)}")
        raise e
    
    end_time = time.time()
    logging.info(f"Retriever created in {end_time - start_time:.2f} seconds.")
    
    return retriever


retriever = create_retriever(load_docs_from_json())


def format_retrieved_docs(docs: List[Document]) -> str:
    formatted_docs = []
    if not docs:
        return "未检索到相关信息。"
    for i, doc in enumerate(docs):
        original_question = doc.metadata.get('original_question', '未知问题')
        logging.info(f"Original question: {original_question}")
        original_answer = doc.metadata.get('original_answer', '未知答案')
        logging.info(f"Original answer: {original_answer}")
        formatted_docs.append(f"相关问答 {i+1}:\n原始问题: {original_question}\n原始答案: {original_answer}")
    return "\n\n".join(formatted_docs)


def invoke_rag(query: str) -> str:
    start_time = time.time()
    logging.info("Invoking RAG...")
    
    retrieval_docs = retriever.invoke(query)
    
    formatted_docs = format_retrieved_docs(retrieval_docs)
    
    template = copy.deepcopy(Template)
    
    formatted_docs = template.format(
        context=formatted_docs,
        question=query
    )
    
    end_time = time.time()
    logging.info(f"RAG invoked in {end_time - start_time:.2f} seconds.")
    
    return formatted_docs


class RAG(OpenAI):
    def set_body(self, message: str) -> dict:
        message = invoke_rag(message)
        return super().set_body(message)
    

class RAG_Qwen(Qwen):
    def set_body(self, message: str) -> dict:
        message = invoke_rag(message)
        return super().set_body(message)
    
