UNWIND [
  'ProductGroup', 'Manufacturer', 'Model', 'Component', 'Problem', 'AdditionalInfo',
  'Procedures', 'BasicInfo', 'SubComponent', 'SuspectArea', 'Symptom', 'TestProcedures'
] AS label
CALL {
  WITH label
  CALL apoc.cypher.run(
    'MATCH (n:' + label + ') RETURN "' + label + '" AS label, count(n) AS total,
     sum(CASE WHEN n.vector IS NOT NULL THEN 1 ELSE 0 END) AS with_vector,
     toFloat(sum(CASE WHEN n.vector IS NOT NULL THEN 1 ELSE 0 END)) / count(n) AS coverage',
    {}
  ) YIELD value
  RETURN value
}
RETURN value.label AS label, value.total AS total_nodes,
       value.with_vector AS vectorized_nodes,
       round(value.coverage * 100, 2) AS vector_coverage_percent
ORDER BY vector_coverage_percent ASC;