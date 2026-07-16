#This is retriveing phase:

from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()
import os 

client = OpenAI()

QURL=os.getenv("QCLIENT")

COLLECTION_NAME="materials"

# Embedding model
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)



def query_service(user_query: str):

    q_client=QdrantClient(QURL)

    #q_client.delete_collection(collection_name="materials")

    #checking if the name exists in collections 
    collection=[q.name for q in q_client.get_collections().collections]

    if COLLECTION_NAME not in collection:
        return {
            "status":False,
            "materials":[],
            "summary":"No uploads yet.Kindly upload pdf..."

        }



    # Connect to existing Qdrant collection
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embedding_model,
        url=QURL,
        collection_name=COLLECTION_NAME
    )

        # Retrieve top similar chunks
    retrieved_docs = vector_store.similarity_search_with_score(
            query=user_query,
            k=10
        )

    if not retrieved_docs:
            return {
                "status":False,
                "materials": [],
                "summary": "No relevant information found."
            }

    context = ""
    materials = set()

    for doc,score in retrieved_docs:
            
            print("scores",score)
            print("metadata",doc.metadata)
            print("content",doc.page_content)

            material = doc.metadata.get("materials", "Unknown PDF")
            page = doc.metadata.get("page", "Unknown")

            materials.add(material)

            context += f"""
    Material: {material}
    Page: {page}

Content:
{doc.page_content}

-------------------------------------
"""

    SYSTEM_PROMPT = f"""
You are a document assistant.

Use the retrieved document content to answer the user's question.

IMPORTANT:
- If the user asks for a summary, short form, overview, or key points, summarize the retrieved content.
- If the user asks a specific question, answer it using the retrieved content.
- If the answer is genuinely not present in the retrieved content, say:
  "I could not find that information in the uploaded material."

Retrieved document content:

{context}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "status":True,
        "form":{
        "materialsShared": list(materials),
         },
        "summary":answer
    }








