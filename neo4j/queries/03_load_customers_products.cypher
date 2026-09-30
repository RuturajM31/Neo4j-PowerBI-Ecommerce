// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 03_load_customers_products.cypher
//
// WHAT ARE WE DOING?
//
// We are creating our first real Neo4j nodes.
//
// customers.csv  -> Customer circles
// products.csv   -> Product circles
//
// ============================================================


// ============================================================
// 1. CREATE CUSTOMER NODES
// ============================================================

// Read customers.csv
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/customers.csv' AS row

// Find the customer by customer_id.
// If it does not exist, Neo4j creates it.
MERGE (c:Customer {
    customer_id: toInteger(row.customer_id)
})

// Add customer information inside the node.
SET
    c.name = row.name,
    c.email = row.email,
    c.country = row.country,
    c.age = toInteger(row.age),
    c.signup_date = date(row.signup_date),
    c.marketing_opt_in = toBoolean(row.marketing_opt_in);


// ============================================================
// 2. CREATE PRODUCT NODES
// ============================================================

// Read products.csv
LOAD CSV WITH HEADERS
FROM 'file:///bi_ecommerce/products.csv' AS row

// Create one Product node for each unique product_id.
MERGE (p:Product {
    product_id: toInteger(row.product_id)
})

// Add product information.
SET
    p.name = row.name,
    p.category = row.category,
    p.price_usd = toFloat(row.price_usd),
    p.cost_usd = toFloat(row.cost_usd),
    p.margin_usd = toFloat(row.margin_usd);


// ============================================================
// 3. CHECK HOW MANY NODES WERE CREATED
// ============================================================

MATCH (c:Customer)
WITH count(c) AS customers

MATCH (p:Product)

RETURN
    customers,
    count(p) AS products;