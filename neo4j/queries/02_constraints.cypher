// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 02_constraints.cypher
//
// PURPOSE:
// Stop Neo4j from creating duplicate nodes.
// Every important ID must be unique.
// ============================================================


// ------------------------------------------------------------
// CUSTOMER
// One customer_id = one Customer node
// ------------------------------------------------------------

CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
FOR (c:Customer)
REQUIRE c.customer_id IS UNIQUE;


// ------------------------------------------------------------
// PRODUCT
// One product_id = one Product node
// ------------------------------------------------------------

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product)
REQUIRE p.product_id IS UNIQUE;


// ------------------------------------------------------------
// SESSION
// One session_id = one Session node
// ------------------------------------------------------------

CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session)
REQUIRE s.session_id IS UNIQUE;


// ------------------------------------------------------------
// EVENT
// One event_id = one Event node
// ------------------------------------------------------------

CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (e:Event)
REQUIRE e.event_id IS UNIQUE;


// ------------------------------------------------------------
// ORDER
// One order_id = one Order node
// ------------------------------------------------------------

CREATE CONSTRAINT order_id_unique IF NOT EXISTS
FOR (o:Order)
REQUIRE o.order_id IS UNIQUE;


// ------------------------------------------------------------
// REVIEW
// One review_id = one Review node
// ------------------------------------------------------------

CREATE CONSTRAINT review_id_unique IF NOT EXISTS
FOR (r:Review)
REQUIRE r.review_id IS UNIQUE;


// ------------------------------------------------------------
// SHOW THE RULES WE CREATED
// ------------------------------------------------------------

SHOW CONSTRAINTS;