// ============================================================
// TEST: Can Neo4j read our customer CSV?
// ============================================================

// Read customers.csv from Neo4j's import folder
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/customers.csv' AS row

// Show only 3 customers
RETURN
    row.customer_id AS customer_id,
    row.name AS customer_name,
    row.country AS country

LIMIT 3;