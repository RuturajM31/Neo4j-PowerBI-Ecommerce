// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 14_finish_core_graph.cypher
//
// WHAT ARE WE DOING?
//
// 1. Connect Orders to Products actually bought
//
//      Order -> CONTAINS -> Product
//
// 2. Create Reviews
//
//      Order -> HAS_REVIEW -> Review -> ABOUT -> Product
//
// After this, the main graph structure is complete.
// ============================================================


// ============================================================
// 1. ORDER -> PRODUCT
// ============================================================

CALL {

    LOAD CSV WITH HEADERS
    FROM 'file:///bi_ecommerce/order_items.csv' AS row

    // Find the Order
    MATCH (o:Order {
        order_id: toInteger(row.order_id)
    })

    // Find the Product
    MATCH (p:Product {
        product_id: toInteger(row.product_id)
    })

    // Connect Order to Product
    MERGE (o)-[r:CONTAINS]->(p)

    // Save information about what was bought
    SET
        r.quantity = toInteger(row.quantity),
        r.unit_price_usd = toFloat(row.unit_price_usd),
        r.line_total_usd = toFloat(row.line_total_usd)

    RETURN count(*) AS order_product_rows
}


// ============================================================
// 2. CREATE REVIEWS
// ============================================================

CALL {

    LOAD CSV WITH HEADERS
    FROM 'file:///bi_ecommerce/reviews.csv' AS row

    // Find the Order
    MATCH (o:Order {
        order_id: toInteger(row.order_id)
    })

    // Find the Product
    MATCH (p:Product {
        product_id: toInteger(row.product_id)
    })

    // Create the Review
    MERGE (r:Review {
        review_id: toInteger(row.review_id)
    })

    // Add Review information
    SET
        r.rating = toInteger(row.rating),
        r.review_text = row.review_text,
        r.review_time = datetime(row.review_time)

    // Order -> Review
    MERGE (o)-[:HAS_REVIEW]->(r)

    // Review -> Product
    MERGE (r)-[:ABOUT]->(p)

    RETURN count(*) AS review_rows
}


// ============================================================
// 3. CHECK THE RESULT
// ============================================================

CALL {
    MATCH (:Order)-[r:CONTAINS]->(:Product)
    RETURN count(r) AS contains_relationships
}

CALL {
    MATCH (r:Review)
    RETURN count(r) AS review_count
}

CALL {
    MATCH (:Order)-[r:HAS_REVIEW]->(:Review)
    RETURN count(r) AS has_review_relationships
}

CALL {
    MATCH (:Review)-[r:ABOUT]->(:Product)
    RETURN count(r) AS about_relationships
}

RETURN
    contains_relationships,
    review_count,
    has_review_relationships,
    about_relationships;