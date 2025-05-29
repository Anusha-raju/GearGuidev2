import os
import re
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from neo4j import GraphDatabase

# --------------------------
# Map rawdata XML tags to graph node labels
# --------------------------
from constants import tag_to_label_map

# --------------------------
# Load credentials from .env file
# --------------------------
load_dotenv()
# uri = os.getenv("NEO4J_URI")
# username = os.getenv("NEO4J_USERNAME")
# password = os.getenv("NEO4J_PASSWORD")
uri = "bolt://localhost:7687"  # Use "neo4j://localhost:7687" if needed
username = "neo4j"
password = "Padma@8099"
driver = GraphDatabase.driver(uri, auth=(username, password))


# --------------------------
# Clean malformed XML safely
# --------------------------
def clean_xml(xml_content):
    try:
        xml_content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', xml_content)
        xml_content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_content)
        if xml_content.startswith("\ufeff"):
            xml_content = xml_content.lstrip("\ufeff")
        xml_content = re.sub(r'<(\d+–\d+)>', r'(\1)', xml_content)
        return f"<root>{xml_content}</root>"
    except Exception as e:
        print(f"❌ Error cleaning XML content: {e}")
        return xml_content


# --------------------------
# Recursively extract text from XML element
# --------------------------
def extract_full_text(element):
    texts = []
    if element.text and element.text.strip():
        texts.append(f"{element.tag}: {element.text.strip()}")
    for child in element:
        child_text = extract_full_text(child)
        if child_text:
            texts.append(child_text)
    return " | ".join(filter(None, texts))


# --------------------------
# Convert tag to its standardized node label
# --------------------------
def get_standardized_label(tag):
    for standard_label, synonyms in tag_to_label_map.items():
        if tag in synonyms:
            return standard_label
    return "AdditionalInfo"


# --------------------------
# Execute Cypher query with parameters
# --------------------------
def execute_query(query, parameters=None):
    try:
        with driver.session() as session:
            session.run(query, parameters or {})
    except Exception as e:
        print(f"❌ Cypher Error: {e}\nQuery: {query}\nParams: {parameters}")


# --------------------------
# Main function to parse and insert XML into Neo4j
# --------------------------
def parse_and_insert_data(xml_content: str, component_name: str):
    try:
        xml_content = clean_xml(xml_content)
        root = ET.fromstring(xml_content)

        # Static base nodes
        execute_query("MERGE (pg:ProductGroup {name: 'automobile'})")
        execute_query("MERGE (man:Manufacturer {name: 'toyota motor corporation'})")
        execute_query("MERGE (m:Model {name: 'yaris', series: 'ncp91, 93 series'})")

        execute_query("""
            MATCH (pg:ProductGroup {name: 'automobile'})
            MATCH (m:Model {name: 'yaris'})
            MERGE (pg)-[:HAS_MODEL]->(m)
        """)

        execute_query("""
            MATCH (m:Model {name: 'yaris'})
            MATCH (man:Manufacturer {name: 'toyota motor corporation'})
            MERGE (m)-[:MANUFACTURED_BY]->(man)
        """)

        execute_query("MERGE (c:Component {name: $name})", {"name": component_name.lower()})
        execute_query("""
            MATCH (m:Model {name: 'yaris'})
            MATCH (c:Component {name: $name})
            MERGE (m)-[:HAS_COMPONENT]->(c)
        """, {"name": component_name.lower()})

        # Detect problem block range
        problems = root.findall("problem")
        first_problem_index, last_problem_index = None, None
        for i, elem in enumerate(root):
            if elem.tag == "problem":
                first_problem_index = i if first_problem_index is None else first_problem_index
                last_problem_index = i

        # Ingest nodes before first problem
        if first_problem_index is not None:
            for i in range(first_problem_index):
                element = root[i]
                label = get_standardized_label(element.tag)
                text_value = extract_full_text(element)
                execute_query(f"MERGE (n:{label} {{name: $name}})", {"name": text_value})
                execute_query(f"""
                    MATCH (c:Component {{name: $component_name}})
                    MATCH (n:{label} {{name: $name}})
                    MERGE (c)-[:HAS_{label}]->(n)
                """, {"component_name": component_name.lower(), "name": text_value})

        # If too many problems → nest under parent
        if len(problems) > 3:
            parent_problem_name = f"{component_name.lower()}_problems"
            execute_query("MERGE (p:Problem {name: $name})", {"name": parent_problem_name})

        for problem_tag in problems:
            problem_name = problem_tag.text.strip().lower()
            execute_query("MERGE (p:Problem {name: $name})", {"name": problem_name})

            if len(problems) > 3:
                execute_query("""
                    MATCH (p1:Problem {name: $parent_name})
                    MATCH (p2:Problem {name: $problem_name})
                    MERGE (p1)-[:HAS_SUBPROBLEM]->(p2)
                """, {"parent_name": parent_problem_name, "problem_name": problem_name})

            # Process children of this problem
            current_index = list(root).index(problem_tag)
            for i in range(current_index + 1, len(root)):
                element = root[i]
                if element.tag == "problem":
                    break
                label = get_standardized_label(element.tag)
                text_value = extract_full_text(element)
                execute_query(f"""
                    MATCH (p:Problem {{name: $problem_name}})
                    OPTIONAL MATCH (p)-[:HAS_{label}]->(n:{label} {{name: $name}})
                    WITH p, n, $name AS name, "{label}" AS label
                    CALL apoc.do.when(
                        n IS NULL,
                        'CALL apoc.merge.node([label], {{name: name}}, {{}}) YIELD node
                         MERGE (p)-[:HAS_' + label + ']->(node)
                         RETURN node',
                        'SET n.name = n.name + " | " + name RETURN n',
                        {{p: p, name: name, label: label}}
                    ) YIELD value
                    RETURN value
                """, {"problem_name": problem_name, "name": text_value})

        # Ingest after last problem
        if last_problem_index is not None:
            for i in range(last_problem_index + 1, len(root)):
                element = root[i]
                label = get_standardized_label(element.tag)
                text_value = extract_full_text(element)
                execute_query(f"MERGE (n:{label} {{name: $name}})", {"name": text_value})
                execute_query(f"""
                    MATCH (c:Component {{name: $component_name}})
                    MATCH (n:{label} {{name: $name}})
                    MERGE (c)-[:HAS_{label}]->(n)
                """, {"component_name": component_name.lower(), "name": text_value})

        print(f"✅ Completed ingestion for component: {component_name}")

    except Exception as e:
        print(f"❌ Error ingesting component `{component_name}`: {e}")


# --------------------------
# Example batch runner
# --------------------------
if __name__ == "__main__":
    folder_path = r"C:\Users\dines\Downloads\Toyota Yaris 2005 Repair Manual extracted new\Toyota Yaris 2005 Repair Manual extracted"
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            with open(os.path.join(folder_path, file_name), "r", encoding="utf-8") as file:
                content = file.read()
                component_name = file_name.replace("_extracted.tsx", "").replace(".tsx", "").lower()
                parse_and_insert_data(content, component_name)
    driver.close()
