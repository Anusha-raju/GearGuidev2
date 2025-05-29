import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
import openai

# -------------------------
# Load secrets and configs
# -------------------------
load_dotenv()
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

from constants import schema_description, vector_index_names, default_prompt

# -------------------------
# Initialize Neo4j driver
# -------------------------
driver = GraphDatabase.driver(uri, auth=(username, password))


# -------------------------
# OpenAI embedding
# -------------------------
def get_openai_embedding(text):
    try:
        if not text:
            return None
        response = openai.embeddings.create(input=text, model=EMBEDDING_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None


# -------------------------
# Store embeddings into Neo4j
# -------------------------
def store_embeddings():
    try:
        with driver.session() as session:
            for node_type, attributes in schema_description.items():
                print(f"📌 Processing {node_type}...")

                query = f"""
                MATCH (n:{node_type})
                WHERE any(attr IN {attributes} WHERE n[attr] IS NOT NULL) AND n.vector IS NULL
                RETURN id(n) AS node_id, {', '.join([f"n.{attr} AS {attr}" for attr in attributes])}
                """

                result = session.run(query)
                for record in result:
                    node_id = record["node_id"]
                    text_to_embed = " ".join([str(record[attr]) for attr in attributes if record[attr]])
                    vector = get_openai_embedding(text_to_embed)
                    if vector:
                        session.run("""
                            MATCH (n) WHERE id(n) = $node_id
                            SET n.vector = $vector
                        """, node_id=node_id, vector=vector)
        print("✅ Embeddings stored successfully in Neo4j!")
    except Exception as e:
        print(f"❌ Error storing embeddings: {e}")


# -------------------------
# Run the embedding job
# -------------------------
if __name__ == "__main__":
    store_embeddings()
    driver.close()
