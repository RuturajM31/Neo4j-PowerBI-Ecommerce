// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 11_connect_orders_products.cypher
//
// WHAT ARE WE DOING?
//
// Connect every Order to the Products that were actually bought.
//
// Example:
//
// Order #500
//     |
//   CONTAINS
//     |
//     v
//   Product
//
// The CONTAINS relationship also stores:
//
// quantity
// unit_price_usd
// line_total_usd
//
// ============================================================


// Read the cleaned order_items.csv file
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/order_items.csv' AS row


// ------------------------------------------------------------
// FIND THE ORDER
// ------------------------------------------------------------

// Find the Order using order_id
MATCH (o:Order {
    order_id: toInteger(row.order_id)
})


// ------------------------------------------------------------
// FIND THE PRODUCT
// ------------------------------------------------------------

// Find the Product using product_id
MATCH (p:Product {
    product_id: toInteger(row.product_id)
})


// ------------------------------------------------------------
// CREATE ORDER -> PRODUCT CONNECTION
// ------------------------------------------------------------

// Create:
//
// Order -> CONTAINS -> Product
//
// MERGE prevents duplicate Order-Product connections
MERGE (o)-[r:CONTAINS]->(p)


// ------------------------------------------------------------
// SAVE PURCHASE DETAILS ON THE ARROW
// ------------------------------------------------------------

// Example:
//
// Order
//   |
// CONTAINS
// quantity = 2
// price = $25
// total = $50
//   |
//   v
// Product

SET
    r.quantity = toInteger(row.quantity),
    r.unit_price_usd = toFloat(row.unit_price_usd),
    r.line_total_usd = toFloat(row.line_total_usd)


// ------------------------------------------------------------
// COUNT HOW MANY CSV ROWS WE PROCESSED
// ------------------------------------------------------------

WITH count(*) AS rows_processed


// ------------------------------------------------------------
// CHECK HOW MANY ORDER -> PRODUCT CONNECTIONS EXIST
// ------------------------------------------------------------

MATCH (:Order)-[r:CONTAINS]->(:Product)

RETURN
    rows_processed,
    count(r) AS contains_relationships;