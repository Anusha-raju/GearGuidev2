# Neo4j Schema Overview for Vehicle Repair Knowledge Graph

This document describes the schema used in the Neo4j database for vehicle repair manual ingestion. It covers:

- Node Labels and Properties
- Relationship Types and Directions
- Fulltext and Vector Index Names
- Cypher Commands for Schema Introspection

---

## Node Labels and Key Properties

| Label            | Key Properties         | Description                                        |
|------------------|------------------------|----------------------------------------------------|
| ProductGroup     | `name`                 | Top-level category (e.g., automobile)              |
| Manufacturer     | `name`                 | Brand or maker (e.g., Toyota Motor Corporation)    |
| Model            | `name`, `series`       | Vehicle model name and series                      |
| Component        | `name`                 | System/component (e.g., transmission)              |
| Problem          | `name`                 | Reported issue                                     |
| AdditionalInfo   | `name`                 | General descriptive information                    |
| Procedures       | `name`                 | Steps or instructions                              |
| BasicInfo        | `name`                 | Overview details (e.g., car info, introduction)    |
| SubComponent     | `name`                 | Parts within a component                           |
| SuspectArea      | `name`                 | Areas possibly related to a problem                |
| Symptom          | `name`                 | Observed behavior or state                         |
| TestProcedures   | `name`                 | Diagnostic steps                                   |

---

## Relationship Types

| Relationship            | Direction                | Description                                      |
|--------------------------|---------------------------|--------------------------------------------------|
| `HAS_MODEL`              | `(ProductGroup) → (Model)`| Groups models under a product group              |
| `MANUFACTURED_BY`        | `(Model) → (Manufacturer)`| Links model to manufacturer                      |
| `HAS_COMPONENT`          | `(Model) → (Component)`   | Models include components                        |
| `HAS_PROBLEM`            | `(Component) → (Problem)` | Component may have problem(s)                    |
| `HAS_ADDITIONALINFO`     | `(Component|Problem) → (AdditionalInfo)` |
| `HAS_PROCEDURES`         | `(Component|Problem) → (Procedures)`     |
| `HAS_BASICINFO`          | `(Component|Problem) → (BasicInfo)`      |
| `HAS_SUBCOMPONENT`       | `(Component|Problem) → (SubComponent)`   |
| `HAS_SUSPECTAREA`        | `(Problem) → (SuspectArea)`             |
| `HAS_SYMPTOM`            | `(Problem) → (Symptom)`                 |
| `HAS_TESTPROCEDURES`     | `(Problem) → (TestProcedures)`          |
| `HAS_SUBPROBLEM`         | `(Problem) → (Problem)` (nested problems)|

---

## Fulltext and Vector Index Names

These indexes speed up search and embedding operations.

### Fulltext Indexes

```cypher
CALL db.index.fulltext.createNodeIndex("search_Component", ["Component"], ["name"]);
CALL db.index.fulltext.createNodeIndex("search_Model", ["Model"], ["name", "series"]);
-- Repeat for each label/attribute as needed
```

### Vector Indexes

```cypher
CALL db.index.vector.createNodeIndex("vectorIndex_Component", "Component", "vector", 1536, "cosine");
CALL db.index.vector.createNodeIndex("vectorIndex_Model", "Model", "vector", 1536, "cosine");
-- Repeat for all node types with embeddings
```

---

## Cypher for Schema Introspection

### Show all node labels:
```cypher
CALL db.labels();
```

### Show all relationship types:
```cypher
CALL db.relationshipTypes();
```

### Show property keys:
```cypher
CALL db.propertyKeys();
```

### Show all indexes:
```cypher
SHOW INDEXES YIELD name, type, labelsOrTypes, properties;
```

###  Tip

Use `CALL db.schema.visualization()` in Neo4j Browser to visualize the full live schema graphically.