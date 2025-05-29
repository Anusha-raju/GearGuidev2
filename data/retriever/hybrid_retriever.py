import openai
import os
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))
openai.api_key = os.getenv("OPENAI_API_KEY")
embedding_model = os.getenv("EMBEDDING_MODEL")
top_k = int(os.getenv("top_k"))
threshold = float(os.getenv("threshold"))
model = os.getenv("model")
alpha = float(os.getenv("alpha"))


# Escape Lucene special characters
def escape_lucene_query(query):
    lucene_special_chars = r'+-!(){}[]^"~*?:\\/'
    return ''.join(['\\' + c if c in lucene_special_chars else c for c in query])


def execute_query(query, parameters=None):
    """Executes a Cypher query on Neo4j with error handling."""
    try:
        with driver.session() as session:
            session.run(query, parameters or {})
    except Exception as e:
        print(f"Error executing query: {query}\nError: {e}")


# Stores previous interactions
vChatHistory = []


def get_latest_bot_content(chat_history):
    """Get the latest assistant message from the chat history."""
    return next((msg["content"] for msg in reversed(chat_history) if msg["role"] == "assistant"), "")


def get_openai_response(prompt):
    """Generate a response from OpenAI GPT-4o based on the given prompt."""
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as ex:
        print(f"Exception in getting OpenAI response: {ex}")
        return ""


def get_openai_embedding(text):
    """Generate an embedding vector for a given text using OpenAI embeddings API."""
    try:
        response = openai.embeddings.create(input=text, model=embedding_model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def rephrase(user_query, chat_history):
    """Rephrase user query based on the conversation history to improve clarity and entity resolution."""
    prompt = f"""
    Based on the provided conversation history, the following user query needs to be modified to capture all key details and named entities if they are referenced using pronouns or third person references. 
    The primary goal is to ensure the query is clear, concise, and contains all necessary named entities for accurate and precise similarity search. 
    If the query already contains all required details, return it as-is. Do not return any explanations or duplicate previously asked questions. If modification is needed, ensure the query remains true to the original intent and meaning.

    Chat History: {chat_history}
    Query to modify: {user_query}

    Warning: Do not explain anything
    """
    return get_openai_response(prompt)


def get_related_nodes(node_name, node_type):
    """Find related nodes based on whether the node is a Problem or a child node."""
    try:
        with driver.session() as session:
            if node_type == "Problem":
                query = """
                MATCH (p:Problem {name: $node_name})-[:HAS_PROCEDURES|:HAS_SUBCOMPONENT|:HAS_TESTPROCEDURES
                     |:HAS_SUBPROBLEM|:HAS_ADDITIONALINFO|:HAS_SYMPTOM
                     |:HAS_SUSPECTAREA|:HAS_BASICINFO]->(child)
                RETURN labels(child) AS child_type, child.name AS child_name
                """
                result = session.run(query, node_name=node_name)
                return [{"node_type": record["child_type"][0], "name": record["child_name"]} for record in result]
            else:
                query = """
                MATCH (problem:Problem)-[:HAS_PROCEDURES|:HAS_SUBCOMPONENT|:HAS_TESTPROCEDURES
                     |:HAS_SUBPROBLEM|:HAS_ADDITIONALINFO|:HAS_SYMPTOM
                     |:HAS_SUSPECTAREA|:HAS_BASICINFO]->(child {name: $node_name})
                WITH problem
                MATCH (problem)-[:HAS_PROCEDURES|:HAS_SUBCOMPONENT|:HAS_TESTPROCEDURES
                     |:HAS_SUBPROBLEM|:HAS_ADDITIONALINFO|:HAS_SYMPTOM
                     |:HAS_SUSPECTAREA|:HAS_BASICINFO]->(related_child)
                RETURN labels(problem) AS problem_type, problem.name AS problem_name, 
                       labels(related_child) AS child_type, related_child.name AS child_name
                """
                result = session.run(query, node_name=node_name)
                related_nodes = []
                for record in result:
                    related_nodes.append({"node_type": record["child_type"][0], "name": record["child_name"]})
                return related_nodes
    except Exception as e:
        print(f"Error retrieving related nodes: {e}")
        return []


# def process_top_nodes(results):
#     """Process the top retrieved nodes and find their related nodes."""
#     content = []
#     for node in results:
#         related_nodes = get_related_nodes(node["name"], node["node_type"][0])
#         for rel in related_nodes:
#             content.append(f"{rel['node_type']}: {rel['name']}")
#     return content

def process_top_nodes(results):
    """Process the top retrieved nodes and find their related nodes in parallel."""
    content = []

    def fetch_related(node):
        related = get_related_nodes(node["name"], node["node_type"][0])
        return [f"{rel['node_type']}: {rel['name']}" for rel in related]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_related, node) for node in results]

        for future in as_completed(futures):
            try:
                content.extend(future.result())
            except Exception as e:
                print(f"Error processing node relationships: {e}")

    return content


def vector_search(driver, node_label, query_vector):
    """Retrieve top-k similar nodes from Neo4j vector index."""
    if query_vector is None:
        return []
    try:
        query_vector = np.array(query_vector, dtype=np.float32).tolist()
        index_name = f'vectorIndex_{node_label}'
        cypher_query = """
        CALL db.index.vector.queryNodes(
            $index_name,
            $top_k,
            $query_vector
        ) YIELD node, score
        WHERE score >= $threshold
        RETURN labels(node) AS node_type, node.name AS name, score
        """
        with driver.session() as session:
            results = session.run(
                cypher_query,
                index_name=index_name,
                query_vector=query_vector,
                top_k=top_k,
                threshold=threshold
            )
            return [{"name": r["name"], "node_type": r["node_type"], "score": round(alpha * r["score"], 4)} for r in
                    results]
    except Exception as e:
        print(f"Vector search error: {e}")
        return []


# Fulltext search
def fulltext_search(driver, node_label, query_text):
    index_name = f'search_{node_label}'
    cypher = f"""
    CALL db.index.fulltext.queryNodes('{index_name}', $query_text)
    YIELD node, score
    RETURN labels(node)[0] AS node_type, node.name AS name, score LIMIT {top_k}
    """
    with driver.session() as session:
        results = session.run(cypher, {
            "query_text": escape_lucene_query(query_text)
        })
        return [{"name": r["name"], "node_type": r["node_type"], "score": round((1 - alpha) * r["score"], 4)} for r in
                results]


# Hybrid retrieval using ThreadPoolExecutor
def hybrid_search(driver, query_text, query_vector, node_label):
    with ThreadPoolExecutor() as executor:
        future_vector = executor.submit(vector_search, driver, node_label, query_vector)
        future_fulltext = executor.submit(fulltext_search, driver, node_label, query_text)

        vector_result = future_vector.result()
        fulltext_result = future_fulltext.result()

    # Normalize vector scores (already in 0-1 range), so multiply directly
    for r in vector_result:
        r["confidence_score"] = round(alpha * r["score"], 4)

    # Normalize fulltext scores (scale relative to max)
    if fulltext_result:
        max_text_score = max(r["score"] for r in fulltext_result)
        for r in fulltext_result:
            normalized_score = r["score"] / max_text_score if max_text_score else 0
            r["confidence_score"] = round((1 - alpha) * normalized_score, 4)

    # Merge and deduplicate by node.name
    merged = vector_result + fulltext_result
    seen, final = set(), []
    for r in sorted(merged, key=lambda x: x["confidence_score"], reverse=True):
        if r["name"] not in seen:
            seen.add(r["name"])
            final.append(r)
    return final[:top_k]


def retrieve_data(user_query):
    """
    Run hybrid (vector + fulltext) search across all labels in parallel.
    Returns top-k globally ranked, deduplicated results.
    """
    query_vector = get_openai_embedding(user_query)
    if query_vector is None:
        return []

    all_results = []

    # Run hybrid_search in parallel for all labels
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(hybrid_search, driver, user_query, query_vector, label): label
            for label in ['SuspectArea', 'Symptom']
        }

        for future in as_completed(futures):
            try:
                all_results.extend(future.result())
            except Exception as e:
                print(f"Search failed for label {futures[future]}: {e}")

    # Deduplicate and sort by hybrid confidence score
    seen, final_results = set(), []
    for result in sorted(all_results, key=lambda x: x.get("confidence_score", 0), reverse=True):
        node_name = result.get("name")
        if node_name and node_name not in seen:
            seen.add(node_name)
            final_results.append(result)

    return final_results[:top_k]


# def retrieve_data(user_query):
#     """Retrieve top relevant nodes from Neo4j using vector similarity (Problem + Symptom)."""
#     query_vector = get_openai_embedding(user_query)
#     if query_vector is None:
#         return []
#
#     # Define which labels to search and in which priority
#     label_priority = ["Symptom", "Problem"]
#     final_results = []
#
#     for label in label_priority:
#         # matches = vector_search(query_vector, label)
#         matches = hybrid_search(driver, user_query, query_vector, label, top_k=top_k, threshold=threshold)
#
#         # Deduplicate based on name
#         seen = set()
#         unique = []
#         for match in sorted(matches, key=lambda x: x["score"], reverse=True):
#             if match["name"] not in seen:
#                 seen.add(match["name"])
#                 unique.append(match)
#         if len(unique) > 3:
#             final_results.extend(unique[:3])
#         else:
#             final_results.extend(unique)
#
#     return final_results


def final_call(user_query, content):
    """Generate the final LLM response using the retrieved context and rephrased query."""
    prompt = f"""
Act as an Automobile Service Agent and answer the user's query based on structured Data.

### Context Information
You have access to a knowledge graph containing details about:
- Problems (e.g., engine overheating, AC not cooling)
- Symptoms, Procedures, Test Procedures, Suspect Areas
- Additional Information, including technical specs and numerical data
Don't miss out the numerical values if relevant to the User Query

### Guidelines:

- Always reference relevant numerical values (e.g., temperature thresholds, pressure ranges, voltage) if applicable.
- Use technical terms only where appropriate—ensure the explanation is clear to a service technician or vehicle owner.
- If the query matches multiple problems or procedures, return a structured response highlighting each possibility.
- Prefer bullet points or short paragraphs for clarity when listing steps, procedures, or areas of concern.
- Use the following content to generate a helpful response to answer the User Query in a structured manner:

Content:
{content}

User Query:
{user_query}

Strict Constraints:
- Only use the provided context.
- Do NOT generate an answer if no relevant information is found.
- Don't give long responses. Ensure responses are clear, concise, and helpful.
"""
    return get_openai_response(prompt)


def rag_advisor(user_query):
    """Main entry point: handles chat history, rephrasing, retrieval, and LLM generation."""
    global vChatHistory
    vChatHistory.append({"role": "user", "content": user_query})

    retrieved_results = retrieve_data(user_query)
    content = process_top_nodes(retrieved_results)

    if vChatHistory:
        user_query = rephrase(user_query, get_latest_bot_content(vChatHistory))

    response = final_call(user_query, content)
    vChatHistory.append({"role": "assistant", "content": f"user_query:{user_query},response:{response}"})
    return response


if __name__ == "__main__":
    query = "Why is my AC not working in Yaris?"
    response = rag_advisor(query)
    print("\n💬 Final Response:\n", response)
