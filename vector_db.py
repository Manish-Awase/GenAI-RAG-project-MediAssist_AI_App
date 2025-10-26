import chromadb
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import os
import time
from pubmed import PubMedRetriever

VECTOR_PATH = Path.cwd() / "resources/vectordb"
if not VECTOR_PATH.exists():
    os.makedirs(VECTOR_PATH, exist_ok=True)

load_dotenv()
GROQ_MODEL = os.getenv("GROQ_MODEL")
client_p = chromadb.PersistentClient(path=VECTOR_PATH)
llm_faq = Groq()





from sentence_transformers import SentenceTransformer

class LocalEmbeddingFunction:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        # Prefix for E5 models
        input = [f"query: {text}" for text in input]
        return self.model.encode(input, normalize_embeddings=True)







class to_create_collection:

    @staticmethod
    def get_database_for_Healthcare_from_pubmed(diseases):
        database = {}

        for disease in diseases:
            pmid_list = PubMedRetriever.search_pubmed_articles(search_term=disease,max_results=300)

            data = PubMedRetriever.fetch_pubmed_abstracts(pmid_list=pmid_list)
            database[disease] = data

        return database

    @staticmethod
    def get_database_injestion_into_vector_store(database):
        # create collection

        # Initialize with E5 model
        embedding_function = LocalEmbeddingFunction("intfloat/e5-base-v2")
        client_p.create_collection(name="Diseases_for_Healthcare",embedding_function=embedding_function)

        # data entries to vector db for diseases ["obesity", "Type 2 Diabetes", "metabolic disorders"]
        for disease in database:
           
            documents = [data['title'] for data in database[disease] if data['title'] is not None]
         
            metadatas = [{"abstract":
                              data["abstract"].get("Label") or data["abstract"].get("SUMMARY", "")}
                         for data in database[disease]
                         if data['title'] is not None
                         ]

            ids = [data["pmid"] for data in database[disease] if data['title'] is not None]

            collection = client_p.get_collection("Diseases_for_Healthcare")
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids

            )


def data_ingestion(diseases):
    disease_list= ["obesity", "Type 2 Diabetes", "metabolic disorders"]

    diseases=disease_list
    print("articles must be only from the ' disease_list'")
    if "Diseases_for_Healthcare" in [c.name for c in client_p.list_collections()]:
        print("Collection Diseases_for_Healthcare already exists")

    else:
        print("Ingesting Healthcare data into Chromadb...")

        # data collection using pubmed

        database=to_create_collection.get_database_for_Healthcare_from_pubmed(diseases)
        to_create_collection.get_database_injestion_into_vector_store(database)

        print(f"Healthcare Data successfully ingested into Chroma collection: Diseases_for_Healthcare")


def get_relevant_qa(query):

    query_text = f"query: {query}"

    collection = client_p.get_collection("Diseases_for_Healthcare")
    result = collection.query(query_texts=[query_text], n_results=3)
    return ''.join([r["abstract"] for r in result['metadatas'][0]])



def generate_answer(query, context):
    prompt = f'''
            You are ai assistant that is expert in providing quick, evidence based summaries.
             The system will:
            - Provide concise ,summarized, evidence-based answers.
            - Highlight key findings and limitations.
            - Only If context include information about intermittent fasting then  Highlight key findings and limitations based on intermittent fasting. 
            - Given the following context and question, generate answer based on this context only.    
            - Compared across fasting protocols 
          
            If the answer is not relate to the context, kindly state "I don't know". Don't try to make up an answer.
            After "I DON'T KNOW" ,starting new line you can give concise reason as REASON: reason
            CONTEXT: {context}

            QUESTION: {query}

            '''
    answer = llm_faq.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model=GROQ_MODEL,
        max_tokens=None)
    return answer.choices[0].message.content


def faq_chain(article_list,query):
    data_ingestion(article_list)
    time.sleep(1)
    context = get_relevant_qa(query)
    time.sleep(1)
    answer = generate_answer(query, context)
    return answer
def query_to_answer(query):
    context = get_relevant_qa(query)
    time.sleep(1)
    answer = generate_answer(query, context)
    return answer

if __name__ == '__main__':
    diseases = ["obesity", "Type 2 Diabetes", "metabolic disorders"]
    # data_ingestion(diseases)
    # query=''
    # answer =query_to_answer(query)

    # context = get_relevant_qa(query)
    # answer = generate_answer(query, context)
    # print("Answer:", answer)
    query='Theoretical discussion and research progress on treatment of glucocorticoid- induced osteoporosis with traditional Chinese medicine.'
    # context=get_relevant_qa(query)
    # print(context)
    query='Is alternate-day fasting effective for metabolic syndrome?'
    query='Compare outcomes of 5:2 vs. 16:8 fasting protocols'
    print(faq_chain(diseases,query))


