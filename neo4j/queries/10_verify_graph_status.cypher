// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 10_verify_graph_status.cypher
//
// PURPOSE:
// Check what has REALLY been created inside Neo4j.
//
// This is more important than VS Code yellow warnings.
// ============================================================


// Count Customer nodes
CALL {
    MATCH (c:Customer)
    RETURN count(c) AS customers
}


// Count Product nodes
CALL {
    MATCH (p:Product)
    RETURN count(p) AS products
}


// Count Session nodes
CALL {
    MATCH (s:Session)
    RETURN count(s) AS sessions
}


// Count Event nodes
CALL {
    MATCH (e:Event)
    RETURN count(e) AS events
}


// Count Order nodes
CALL {
    MATCH (o:Order)
    RETURN count(o) AS orders
}


// Count Customer -> Session connections
CALL {
    MATCH (:Customer)-[r:STARTED]->(:Session)
    RETURN count(r) AS started
}


// Count Session -> Event connections
CALL {
    MATCH (:Session)-[r:HAS_EVENT]->(:Event)
    RETURN count(r) AS has_event
}


// Count Event -> Event journey connections
CALL {
    MATCH (:Event)-[r:NEXT]->(:Event)
    RETURN count(r) AS next_links
}


// Count Event -> Product connections
CALL {
    MATCH (:Event)-[r:INTERACTED_WITH]->(:Product)
    RETURN count(r) AS product_interactions
}


// Count Purchase Event -> Order connections
CALL {
    MATCH (:Event)-[r:GENERATED]->(:Order)
    RETURN count(r) AS generated
}


// Count Customer -> Order connections
CALL {
    MATCH (:Customer)-[r:PLACED]->(:Order)
    RETURN count(r) AS placed
}


// Count Session -> Order connections
CALL {
    MATCH (:Session)-[r:CONVERTED_TO]->(:Order)
    RETURN count(r) AS converted_to
}


// Show everything in one row
RETURN
    customers,
    products,
    sessions,
    events,
    orders,
    started,
    has_event,
    next_links,
    product_interactions,
    generated,
    placed,
    converted_to;