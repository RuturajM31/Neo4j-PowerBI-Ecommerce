# ============================================================
# PROJECT: Neo4j + Power BI E-commerce Intelligence
# FILE: 01_prepare_data.py
#
# WHAT THIS SCRIPT DOES:
#
# 1. Reads the original CSV files from archive
# 2. Keeps the original files untouched
# 3. Puts customer events in the correct order
# 4. Creates the "next event" for every event
# 5. Connects purchase events to the correct orders
# 6. Connects orders back to the correct sessions
# 7. Cleans repeated order-product rows
# 8. Saves clean files into data_clean
#
# ============================================================


# Import Path so Python can work with our project folders
from pathlib import Path

# Import pandas so we can work with CSV data
import pandas as pd


# ============================================================
# STEP 1 - PROJECT FOLDERS
# ============================================================

# Find the main project folder.
#
# Our script is here:
# Neo4j_PowerBI_Ecommerce\scripts\01_prepare_data.py
#
# parents[1] moves back to:
# Neo4j_PowerBI_Ecommerce
ROOT = Path(__file__).resolve().parents[1]


# Original Kaggle files are stored here
RAW = ROOT / "archive"


# Clean files will be saved here
CLEAN = ROOT / "data_clean"


# Create the data_clean folder if it does not exist
CLEAN.mkdir(exist_ok=True)


# ============================================================
# STEP 2 - LOAD ALL 7 ORIGINAL CSV FILES
# ============================================================

# Customer information
customers = pd.read_csv(
    RAW / "customers.csv"
)


# Product information
products = pd.read_csv(
    RAW / "products.csv"
)


# Customer website sessions
sessions = pd.read_csv(
    RAW / "sessions.csv"
)


# Website actions:
# page_view, add_to_cart, checkout, purchase
events = pd.read_csv(
    RAW / "events.csv"
)


# Completed customer orders
orders = pd.read_csv(
    RAW / "orders.csv"
)


# Products inside each order
order_items = pd.read_csv(
    RAW / "order_items.csv"
)


# Customer reviews
reviews = pd.read_csv(
    RAW / "reviews.csv"
)


# ============================================================
# STEP 3 - CLEAN EVENT NUMBER COLUMNS
# ============================================================

# Some events do not have a product.
#
# Because of empty values, pandas may read product_id like:
#
# 93.0
#
# We want:
#
# 93
#
# Int64 allows normal numbers AND empty values.
events["product_id"] = (
    events["product_id"]
    .astype("Int64")
)


# Quantity is sometimes empty
events["qty"] = (
    events["qty"]
    .astype("Int64")
)


# Cart size is sometimes empty
events["cart_size"] = (
    events["cart_size"]
    .astype("Int64")
)


# ============================================================
# STEP 4 - TURN TIME TEXT INTO REAL DATETIME VALUES
# ============================================================

# We need real dates so Python can put events
# in the correct time order.
events["timestamp"] = pd.to_datetime(
    events["timestamp"]
)


# We also need real order times so we can match
# Purchase events to Orders.
orders["order_time"] = pd.to_datetime(
    orders["order_time"]
)


# ============================================================
# STEP 5 - PUT EVENTS IN THE CORRECT JOURNEY ORDER
# ============================================================

# Example:
#
# Page View
#      ↓
# Add To Cart
#      ↓
# Checkout
#      ↓
# Purchase
#
# We sort:
#
# 1. by session
# 2. by time
# 3. by event_id
#
# event_id is used if two events happen at the same second.

events = (
    events
    .sort_values(
        [
            "session_id",
            "timestamp",
            "event_id"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# STEP 6 - CREATE NEXT EVENT
# ============================================================

# We want Neo4j to understand:
#
# Event 1 → Event 2
# Event 2 → Event 3
# Event 3 → Event 4
#
# Example:
#
# Page View → Add To Cart → Checkout → Purchase
#
# shift(-1) looks at the NEXT event inside the same session.

events["next_event_id"] = (
    events
    .groupby("session_id")["event_id"]
    .shift(-1)
    .astype("Int64")
)


# ============================================================
# STEP 7 - FIND ALL PURCHASE EVENTS
# ============================================================

# Keep only rows where event_type = purchase.
#
# We need:
#
# event_id
# session_id
# timestamp

purchase_events = events.loc[
    events["event_type"] == "purchase",
    [
        "event_id",
        "session_id",
        "timestamp"
    ]
].copy()


# ============================================================
# STEP 8 - FIND WHICH CUSTOMER MADE EACH PURCHASE
# ============================================================

# events.csv has session_id.
#
# sessions.csv tells us:
#
# session_id → customer_id
#
# So we add customer_id to each purchase event.

purchase_events = purchase_events.merge(

    sessions[
        [
            "session_id",
            "customer_id"
        ]
    ],

    on="session_id",

    how="left",

    validate="many_to_one"
)


# ============================================================
# STEP 9 - CONNECT PURCHASE EVENT TO THE CORRECT ORDER
# ============================================================

# We match using:
#
# customer_id
# +
# exact purchase time
#
# Example:
#
# Customer 100
# Purchase time = 10:30
#
# matches
#
# Customer 100
# Order time = 10:30
#
# We checked the actual dataset:
# all 33,580 purchases match exactly one order.

purchase_map = purchase_events.merge(

    orders[
        [
            "order_id",
            "customer_id",
            "order_time"
        ]
    ],

    left_on=[
        "customer_id",
        "timestamp"
    ],

    right_on=[
        "customer_id",
        "order_time"
    ],

    how="left",

    validate="one_to_one"
)


# ============================================================
# STEP 10 - CHECK THE PURCHASE → ORDER CONNECTION
# ============================================================

# If even one purchase does not find an order,
# stop the script.
if purchase_map["order_id"].isna().any():

    raise ValueError(
        "ERROR: Some purchase events could not find an order."
    )


# Every order should appear exactly once.
if purchase_map["order_id"].nunique() != len(orders):

    raise ValueError(
        "ERROR: Purchase events do not match all orders."
    )


# ============================================================
# STEP 11 - ADD ORDER_ID TO EVENTS
# ============================================================

# Create a small mapping:
#
# event_id → order_id
#
# Only Purchase events will have an order_id.

event_order_map = purchase_map[
    [
        "event_id",
        "order_id"
    ]
]


# Add order_id into the full events table.
events = events.merge(

    event_order_map,

    on="event_id",

    how="left",

    validate="one_to_one"
)


# Keep order_id as a clean integer column
# while still allowing empty rows.
events["order_id"] = (
    events["order_id"]
    .astype("Int64")
)


# ============================================================
# STEP 12 - CONNECT ORDERS BACK TO SESSIONS
# ============================================================

# We also want:
#
# Session → Order
#
# Example:
#
# Session 50
#     ↓
# Purchase Event
#     ↓
# Order 900
#
# So we add session_id into orders.csv.

order_session_map = purchase_map[
    [
        "order_id",
        "session_id"
    ]
]


# Add session_id to the Orders table.
orders = orders.merge(

    order_session_map,

    on="order_id",

    how="left",

    validate="one_to_one"
)


# Make session_id a clean integer column
orders["session_id"] = (
    orders["session_id"]
    .astype("Int64")
)


# Check that every order found a session.
if orders["session_id"].isna().any():

    raise ValueError(
        "ERROR: Some orders could not find a session."
    )


# ============================================================
# STEP 13 - CLEAN REPEATED ORDER-PRODUCT ROWS
# ============================================================

# Some orders contain the same product more than once.
#
# Example:
#
# Order 10 + Product 5 + Quantity 1
# Order 10 + Product 5 + Quantity 2
#
# We combine them into:
#
# Order 10 + Product 5 + Quantity 3
#
# This gives Neo4j one clean:
#
# Order → Product
#
# relationship.

order_items_clean = (

    order_items

    .groupby(
        [
            "order_id",
            "product_id",
            "unit_price_usd"
        ],
        as_index=False
    )

    .agg(

        # Add the quantities together
        quantity=(
            "quantity",
            "sum"
        ),

        # Add the money values together
        line_total_usd=(
            "line_total_usd",
            "sum"
        )
    )
)


# Money should have only two decimal places.
order_items_clean["line_total_usd"] = (
    order_items_clean["line_total_usd"]
    .round(2)
)


# ============================================================
# STEP 14 - SAVE CLEAN FILES
# ============================================================

# Save Customers
customers.to_csv(
    CLEAN / "customers.csv",
    index=False
)


# Save Products
products.to_csv(
    CLEAN / "products.csv",
    index=False
)


# Save Sessions
sessions.to_csv(
    CLEAN / "sessions.csv",
    index=False
)


# Save Events.
#
# date_format writes timestamps directly while saving.
# This is faster than manually changing 760,958 dates to text.
events.to_csv(
    CLEAN / "events.csv",
    index=False,
    date_format="%Y-%m-%dT%H:%M:%S"
)


# Save Orders
orders.to_csv(
    CLEAN / "orders.csv",
    index=False,
    date_format="%Y-%m-%dT%H:%M:%S"
)


# Save cleaned Order Items
order_items_clean.to_csv(
    CLEAN / "order_items.csv",
    index=False
)


# Save Reviews
reviews.to_csv(
    CLEAN / "reviews.csv",
    index=False
)


# ============================================================
# STEP 15 - COUNT THE JOURNEY LINKS WE CREATED
# ============================================================

# Count Event → NEXT → Event links
next_links = (
    events["next_event_id"]
    .notna()
    .sum()
)


# Count Purchase → Order links
purchase_links = (
    events["order_id"]
    .notna()
    .sum()
)


# Count Session → Order links
order_session_links = (
    orders["session_id"]
    .notna()
    .sum()
)


# ============================================================
# STEP 16 - SHOW RESULTS
# ============================================================

print()

print(
    "FULL JOURNEY DATA PREPARATION COMPLETE"
)

print(
    "=" * 55
)


# Show the number of rows in each clean table
print(
    f"Customers:                 {len(customers):,}"
)

print(
    f"Products:                  {len(products):,}"
)

print(
    f"Sessions:                  {len(sessions):,}"
)

print(
    f"Events:                    {len(events):,}"
)

print(
    f"Orders:                    {len(orders):,}"
)

print(
    f"Order Items:               {len(order_items_clean):,}"
)

print(
    f"Reviews:                   {len(reviews):,}"
)


# ============================================================
# CUSTOMER JOURNEY RESULTS
# ============================================================

print()

print(
    "CUSTOMER JOURNEY"
)

print(
    "-" * 55
)


# Number of Event → Event connections
print(
    f"NEXT links created:        {next_links:,}"
)


# Number of Purchase → Order connections
print(
    f"Purchases linked to Order: {purchase_links:,}"
)


# Number of Orders connected to Sessions
print(
    f"Orders linked to Session:  {order_session_links:,}"
)


# ============================================================
# ORDER ITEM CLEANING RESULTS
# ============================================================

print()

print(
    "ORDER ITEM CLEANING"
)

print(
    "-" * 55
)


# Original number of order item rows
print(
    f"Original rows:             {len(order_items):,}"
)


# Clean number of rows
print(
    f"Clean rows:                {len(order_items_clean):,}"
)


# How many repeated rows were combined
print(
    f"Rows combined:             "
    f"{len(order_items) - len(order_items_clean):,}"
)


# ============================================================
# OUTPUT FOLDER
# ============================================================

print()

print(
    "Clean files saved in:"
)

print(
    CLEAN
)


print()

print(
    "DATA IS READY FOR NEO4J."
)