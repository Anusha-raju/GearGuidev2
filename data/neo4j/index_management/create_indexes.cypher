// === VECTOR INDEXES ===
CREATE VECTOR INDEX vectorIndex_ProductGroup FOR (n:ProductGroup) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Manufacturer FOR (n:Manufacturer) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Model FOR (n:Model) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Component FOR (n:Component) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Problem FOR (n:Problem) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_AdditionalInfo FOR (n:AdditionalInfo) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Procedures FOR (n:Procedures) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_BasicInfo FOR (n:BasicInfo) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_SubComponent FOR (n:SubComponent) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_SuspectArea FOR (n:SuspectArea) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_Symptom FOR (n:Symptom) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX vectorIndex_TestProcedures FOR (n:TestProcedures) ON (n.vector)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };


// === FULLTEXT INDEXES ===
CREATE FULLTEXT INDEX search_ProductGroup FOR (n:ProductGroup) ON EACH [n.name];
CREATE FULLTEXT INDEX search_Manufacturer FOR (n:Manufacturer) ON EACH [n.name];
CREATE FULLTEXT INDEX search_Model FOR (n:Model) ON EACH [n.name, n.series];
CREATE FULLTEXT INDEX search_Component FOR (n:Component) ON EACH [n.name];
CREATE FULLTEXT INDEX search_Problem FOR (n:Problem) ON EACH [n.name];
CREATE FULLTEXT INDEX search_AdditionalInfo FOR (n:AdditionalInfo) ON EACH [n.name];
CREATE FULLTEXT INDEX search_Procedures FOR (n:Procedures) ON EACH [n.name];
CREATE FULLTEXT INDEX search_BasicInfo FOR (n:BasicInfo) ON EACH [n.name];
CREATE FULLTEXT INDEX search_SubComponent FOR (n:SubComponent) ON EACH [n.name];
CREATE FULLTEXT INDEX search_SuspectArea FOR (n:SuspectArea) ON EACH [n.name];
CREATE FULLTEXT INDEX search_Symptom FOR (n:Symptom) ON EACH [n.name];
CREATE FULLTEXT INDEX search_TestProcedures FOR (n:TestProcedures) ON EACH [n.name];