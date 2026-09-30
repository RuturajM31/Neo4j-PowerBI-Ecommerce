// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 04_load_sessions.cypher
//
// PURPOSE:
// 1. Create Session nodes
// 2. Connect each Customer to the Session they started
//
// Customer -> STARTED -> Session
// ============================================================


// ============================================================
// PART 1 - CREATE SESSION NODES
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/sessions.csv' AS row

MERGE (s:Session {
    session_id: toInteger(row.session_id)
})

SET
    s.start_time = datetime(row.start_time),
    s.device = row.device,
    s.source = row.source,
    s.country = row.country;


// ============================================================
// PART 2 - CONNECT CUSTOMER TO SESSION
// ============================================================

LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/sessions.csv' AS row

MATCH (c:Customer {
    customer_id: toInteger(row.customer_id)
})

MATCH (s:Session {
    session_id: toInteger(row.session_id)
})

MERGE (c)-[:STARTED]->(s);


// ============================================================
// PART 3 - CHECK THE RESULT
// ============================================================

MATCH (s:Session)
WITH count(s) AS session_count

MATCH (:Customer)-[r:STARTED]->(:Session)

RETURN
    session_count,
    count(r) AS started_relationships;