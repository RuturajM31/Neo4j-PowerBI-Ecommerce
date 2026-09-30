// ============================================================
// PROJECT: Neo4j + Power BI E-commerce
// FILE: 20_common_journey_paths.cypher
//
// BUSINESS QUESTION:
//
// What are the most common complete customer journeys
// that end in a Purchase?
//
// Example:
//
// page_view -> add_to_cart -> checkout -> purchase
//
// We will return the TOP 10 most common paths.
// ============================================================


// ------------------------------------------------------------
// 1. FIND EVERY CONVERTED SESSION
// ------------------------------------------------------------

MATCH (s:Session)-[:CONVERTED_TO]->(o:Order)


// Find the Purchase Event that generated the Order
MATCH (s)-[:HAS_EVENT]->(purchase:Event)-[:GENERATED]->(o)

WHERE purchase.event_type = 'purchase'


// ------------------------------------------------------------
// 2. FIND THE FIRST EVENT IN THE SESSION
// ------------------------------------------------------------

MATCH (s)-[:HAS_EVENT]->(first:Event)

WHERE NOT EXISTS {

    MATCH (s)-[:HAS_EVENT]->(:Event)-[:NEXT]->(first)

}


// ------------------------------------------------------------
// 3. FOLLOW THE REAL EVENT JOURNEY
// ------------------------------------------------------------

MATCH journey =
    (first)-[:NEXT*0..]->(purchase)


// ------------------------------------------------------------
// 4. TURN THE EVENT NODES INTO EVENT TYPES
// ------------------------------------------------------------

WITH
    s,
    [event IN nodes(journey) | event.event_type] AS event_types


// ------------------------------------------------------------
// 5. TURN THE LIST INTO A READABLE PATH
//
// Example:
//
// ["page_view", "add_to_cart", "purchase"]
//
// becomes:
//
// page_view -> add_to_cart -> purchase
// ------------------------------------------------------------

WITH
    s,

    reduce(
        path = '',
        event_type IN event_types |

        path +

        CASE
            WHEN path = ''
            THEN ''
            ELSE ' -> '
        END +

        event_type

    ) AS journey_path


// ------------------------------------------------------------
// 6. COUNT HOW MANY SESSIONS USED EACH PATH
// ------------------------------------------------------------

WITH
    journey_path,
    count(DISTINCT s) AS sessions


// ------------------------------------------------------------
// 7. CALCULATE TOTAL CONVERTED SESSIONS
// ------------------------------------------------------------

WITH
    collect({
        journey_path: journey_path,
        sessions: sessions
    }) AS journey_results,

    sum(sessions) AS total_converted_sessions


// ------------------------------------------------------------
// 8. TURN RESULTS BACK INTO ROWS
// ------------------------------------------------------------

UNWIND journey_results AS result


// ------------------------------------------------------------
// 9. RETURN TOP 10 JOURNEY PATHS
// ------------------------------------------------------------

RETURN
    result.journey_path AS journey_path,

    result.sessions AS sessions,

    round(
        100.0 * result.sessions /
        total_converted_sessions,
        2
    ) AS percentage_of_converted_sessions

ORDER BY sessions DESC

LIMIT 10;