from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# import os 

# QURL=os.getenv("QCLIENT")

import os
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

COLLECTION_NAME = "materials"

embedding = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )

def upload_material(pdf_path: str):


    pdf_file = Path(pdf_path) 
    

    loader = PyPDFLoader(pdf_file)
    docs = loader.load()       #here loads the pdf file 

    #splits the texts with sizes and overlaping
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=250
    )

    chunks = splitter.split_documents(docs)

    for docs in chunks:
        docs.metadata["materials"]=(pdf_file).name

    print("length",len(chunks))

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding,
        client=client,
        collection_name=COLLECTION_NAME,
    )

    return {
        "status":True,
        "materialsShared": pdf_file.name
    }



















































