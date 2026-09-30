from pathlib import Path
from getpass import getpass
from textwrap import shorten, wrap
import re

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap

from neo4j import GraphDatabase


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUERY_DIR = PROJECT_ROOT / "neo4j" / "queries"
EXPORT_DIR = PROJECT_ROOT / "exports"
CHART_DIR = EXPORT_DIR / "charts"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# NEO4J CONNECTION
# ============================================================

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_DATABASE = "neo4j"


# ============================================================
# QUERY / OUTPUT FILES
# ============================================================

QUERY_FILES = {
    16: "16_funnel_analysis.cypher",
    17: "17_abandonment_analysis.cypher",
    18: "18_conversion_journey_length.cypher",
    19: "19_conversion_time.cypher",
    20: "20_common_journey_paths.cypher",
    21: "21_viewed_not_purchased.cypher",
    22: "22_product_copurchase.cypher",
    23: "23_product_affinity.cypher",
    24: "24_cross_sell_opportunities.cypher",
    25: "25_category_copurchase.cypher",
    26: "26_customer_value_segments.cypher",
    27: "27_device_source_conversion.cypher",
    28: "28_executive_summary.cypher",
}

CSV_FILES = {
    16: "funnel_analysis.csv",
    17: "abandonment_analysis.csv",
    18: "conversion_journey_length.csv",
    19: "conversion_time.csv",
    20: "common_journey_paths.csv",
    21: "viewed_not_purchased.csv",
    22: "product_copurchase.csv",
    23: "product_affinity.csv",
    24: "cross_sell_opportunities.csv",
    25: "category_copurchase.csv",
    26: "customer_value_segments.csv",
    27: "device_source_conversion.csv",
    28: "executive_summary.csv",
}

CHART_FILES = {
    16: "16_customer_funnel.png",
    17: "17_funnel_abandonment.png",
    18: "18_conversion_journey_length.png",
    19: "19_conversion_time.png",
    20: "20_common_journey_paths.png",
    21: "21_viewed_not_purchased.png",
    22: "22_product_copurchase_network.png",
    23: "23_product_affinity.png",
    24: "24_cross_sell_opportunities.png",
    25: "25_category_copurchase_heatmap.png",
    26: "26_customer_value_segments.png",
    27: "27_device_source_conversion.png",
    28: "28_executive_kpis.png",
}

EXPECTED_COLUMNS = {
    16: {
        "total_sessions", "page_view_sessions", "add_to_cart_sessions",
        "checkout_sessions", "purchase_sessions", "view_to_cart_pct",
        "cart_to_checkout_pct", "checkout_to_purchase_pct",
        "overall_conversion_pct",
    },
    17: {
        "stage_order", "journey_outcome", "sessions",
        "percentage_of_sessions",
    },
    18: {
        "converted_sessions", "avg_events_to_purchase",
        "median_events_to_purchase", "min_events_to_purchase",
        "max_events_to_purchase", "avg_next_steps_to_purchase",
    },
    19: {
        "converted_sessions", "avg_conversion_minutes",
        "median_conversion_minutes", "fastest_conversion_minutes",
        "slowest_conversion_minutes",
    },
    20: {
        "journey_path", "sessions", "percentage_of_converted_sessions",
    },
    21: {
        "product_id", "product_name", "category", "viewed_sessions",
        "purchased_after_view_sessions", "viewed_not_purchased_sessions",
        "view_to_purchase_pct", "view_without_purchase_pct",
    },
    22: {
        "product_1_id", "product_1_name", "product_1_category",
        "product_2_id", "product_2_name", "product_2_category",
        "copurchase_orders",
    },
    23: {
        "product_1_id", "product_1_name", "product_1_category",
        "product_2_id", "product_2_name", "product_2_category",
        "copurchase_orders", "product_1_orders", "product_2_orders",
        "support_pct", "confidence_1_to_2_pct",
        "confidence_2_to_1_pct", "lift",
    },
    24: {
        "purchased_product_id", "purchased_product_name",
        "purchased_product_category", "cross_sell_product_id",
        "cross_sell_product_name", "cross_sell_product_category",
        "opportunity_sessions",
    },
    25: {
        "category_1", "category_2", "orders_together",
        "percentage_of_all_orders", "relationship_type",
    },
    26: {
        "segment_order", "customer_segment", "customers", "orders",
        "revenue_usd", "avg_orders_per_customer",
        "avg_revenue_per_customer_usd",
    },
    27: {
        "device", "source", "sessions", "converted_sessions",
        "conversion_rate_pct", "revenue_usd", "avg_order_value_usd",
    },
    28: {
        "total_customers", "total_sessions", "total_orders",
        "total_revenue_usd", "avg_order_value_usd", "conversion_rate_pct",
        "purchasing_customers", "purchasing_customer_pct", "repeat_buyers",
        "repeat_buyer_pct_of_buyers", "total_reviews",
    },
}


# ============================================================
# PROFESSIONAL BI THEME
# ============================================================

NAVY = "#17324D"
BLUE = "#2F6B9A"
TEAL = "#2A9D8F"
SKY = "#74A9CF"
SLATE = "#66788A"
AMBER = "#D9A441"
RED = "#C95A5A"
LIGHT = "#E9EEF3"
MID = "#B8C4CE"
DARK = "#243746"
WHITE = "#FFFFFF"
SOFT_BG = "#F7F9FB"

CATEGORY_PALETTE = [
    "#17324D", "#2F6B9A", "#2A9D8F", "#74A9CF",
    "#66788A", "#D9A441", "#7A6FA8", "#5A8F7B",
]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.titlesize": 20,
    "axes.labelsize": 10.5,
    "axes.edgecolor": MID,
    "axes.labelcolor": DARK,
    "xtick.color": DARK,
    "ytick.color": DARK,
    "text.color": DARK,
    "figure.facecolor": WHITE,
    "axes.facecolor": WHITE,
    "savefig.facecolor": WHITE,
})


# ============================================================
# VALIDATION + IO HELPERS
# ============================================================

def validate_query_files():
    missing = [
        str(QUERY_DIR / filename)
        for filename in QUERY_FILES.values()
        if not (QUERY_DIR / filename).exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing Cypher query file(s):\n" +
            "\n".join(f" - {path}" for path in missing)
        )


def clean_query(query_text):
    return re.sub(r";\s*$", "", query_text.strip())


def run_cypher(session, query_file):
    query_path = QUERY_DIR / query_file
    query_text = clean_query(query_path.read_text(encoding="utf-8"))
    result = session.run(query_text)
    rows = [record.data() for record in result]

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError(
            f"Query returned no rows: {query_file}"
        )

    return df


def validate_result(query_number, df):
    expected = EXPECTED_COLUMNS[query_number]

    missing = expected.difference(
        df.columns
    )

    if missing:
        raise ValueError(
            f"Query {query_number} is missing required column(s): " +
            ", ".join(sorted(missing))
        )

    required = list(expected)

    if df[required].isnull().any().any():

        null_columns = (
            df[required]
            .columns[df[required].isnull().any()]
            .tolist()
        )

        raise ValueError(
            f"Query {query_number} returned null values in required column(s): " +
            ", ".join(null_columns)
        )


def validate_cross_query_integrity(results):

    q16 = results[16].iloc[0]
    q17 = results[17]
    q26 = results[26]
    q28 = results[28].iloc[0]

    checks = [
        (
            int(q16["total_sessions"]),
            int(q28["total_sessions"]),
            "Q16 total sessions vs Q28 total sessions",
        ),
        (
            int(q16["purchase_sessions"]),
            int(q28["total_orders"]),
            "Q16 purchase sessions vs Q28 total orders",
        ),
        (
            int(q17["sessions"].sum()),
            int(q28["total_sessions"]),
            "Q17 outcome sessions vs Q28 total sessions",
        ),
        (
            int(q26["customers"].sum()),
            int(q28["total_customers"]),
            "Q26 customer segments vs Q28 total customers",
        ),
        (
            int(q26["orders"].sum()),
            int(q28["total_orders"]),
            "Q26 segment orders vs Q28 total orders",
        ),
    ]

    failures = [
        label
        for left, right, label in checks
        if left != right
    ]

    revenue_segments = float(
        q26["revenue_usd"].sum()
    )

    revenue_total = float(
        q28["total_revenue_usd"]
    )

    if abs(
        revenue_segments - revenue_total
    ) > 0.05:
        failures.append(
            "Q26 segment revenue vs Q28 total revenue"
        )

    if failures:
        raise ValueError(
            "Cross-query integrity check failed:\n - " +
            "\n - ".join(failures)
        )

    print(
        "\nCross-query integrity checks passed."
    )


def validate_outputs():

    problems = []

    for filename in CSV_FILES.values():

        path = EXPORT_DIR / filename

        if (
            not path.exists()
            or path.stat().st_size == 0
        ):
            problems.append(
                str(path)
            )

    for filename in CHART_FILES.values():

        path = CHART_DIR / filename

        if (
            not path.exists()
            or path.stat().st_size == 0
        ):
            problems.append(
                str(path)
            )

    if problems:
        raise RuntimeError(
            "Expected output file(s) missing or empty:\n - " +
            "\n - ".join(problems)
        )

    print(
        f"\nOutput validation passed: "
        f"{len(CSV_FILES)} CSV files and "
        f"{len(CHART_FILES)} chart files created."
    )


# ============================================================
# FORMAT / DISPLAY HELPERS
# ============================================================

def format_number(value):
    return f"{int(round(float(value))):,}"


def format_currency(value):
    return f"${float(value):,.2f}"


def format_percent(value):
    return f"{float(value):.2f}%"


def compact_currency(value):

    value = float(value)

    if abs(value) >= 1_000_000:
        return (
            f"${value / 1_000_000:.1f}M"
        )

    if abs(value) >= 1_000:
        return (
            f"${value / 1_000:.0f}K"
        )

    return f"${value:,.0f}"


def minutes_business(value):

    value = float(value)

    hours = int(
        value // 60
    )

    minutes = int(
        round(value % 60)
    )

    if hours > 0:
        return (
            f"{value:.0f} min  "
            f"({hours}h {minutes:02d}m)"
        )

    return f"{value:.0f} min"


def shorten_text(
    value,
    width=34
):

    return shorten(
        str(value),
        width=width,
        placeholder="…"
    )


EVENT_LABELS = {
    "page_view": "Page View",
    "add_to_cart": "Add to Cart",
    "checkout": "Checkout",
    "purchase": "Purchase",
}


def business_path(
    value,
    width=58
):

    parts = [
        part.strip()
        for part in str(value).split("->")
    ]

    readable = " → ".join(
        EVENT_LABELS.get(
            part,
            part.replace(
                "_",
                " "
            ).title()
        )
        for part in parts
    )

    return "\n".join(
        wrap(
            readable,
            width=width
        )
    )


def style_axis(
    ax,
    grid_axis="x"
):

    ax.spines[
        "top"
    ].set_visible(
        False
    )

    ax.spines[
        "right"
    ].set_visible(
        False
    )

    ax.spines[
        "left"
    ].set_color(
        MID
    )

    ax.spines[
        "bottom"
    ].set_color(
        MID
    )

    ax.grid(
        axis=grid_axis,
        color=LIGHT,
        linewidth=0.8
    )

    ax.set_axisbelow(
        True
    )


def add_title(
    ax,
    title,
    subtitle
):

    ax.set_title(
        title,
        loc="left",
        fontweight="bold",
        color=NAVY,
        pad=26
    )

    ax.text(
        0,
        1.02,
        subtitle,
        transform=ax.transAxes,
        fontsize=10.5,
        color=SLATE,
        va="bottom",
    )


def add_footer(fig):

    fig.text(
        0.01,
        0.012,
        "Source: Neo4j graph analytics | Synthetic e-commerce dataset",
        ha="left",
        va="bottom",
        fontsize=7.5,
        color=SLATE,
    )

    fig.text(
        0.99,
        0.012,
        "Ruturaj Mokashi",
        ha="right",
        va="bottom",
        fontsize=7.5,
        color=SLATE,
    )


def save_chart(
    fig,
    filename
):

    add_footer(fig)

    output_path = (
        CHART_DIR
        / filename
    )

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.18
    )

    plt.close(fig)

    print(
        f"   Chart: {filename}"
    )


def draw_insight_box(
    fig,
    x,
    y,
    width,
    height,
    title,
    body,
    accent=TEAL
):

    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        transform=fig.transFigure,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        facecolor=SOFT_BG,
        edgecolor=LIGHT,
        linewidth=1.0,
    )

    fig.patches.append(box)

    fig.add_artist(
        plt.Line2D(
            [
                x + 0.012,
                x + 0.012
            ],
            [
                y + 0.02,
                y + height - 0.02
            ],
            transform=fig.transFigure,
            color=accent,
            linewidth=4,
            solid_capstyle="round",
        )
    )

    fig.text(
        x + 0.03,
        y + height - 0.045,
        title,
        fontsize=9.5,
        color=SLATE
    )

    fig.text(
        x + 0.03,
        y + 0.04,
        body,
        fontsize=12.5,
        fontweight="bold",
        color=NAVY
    )


# ============================================================
# QUERY 16 — CONVERSION FUNNEL
# ============================================================

def chart_16_funnel(df):

    row = df.iloc[0]

    stages = [
        "Page View",
        "Add to Cart",
        "Checkout",
        "Purchase"
    ]

    values = [
        float(
            row[
                "page_view_sessions"
            ]
        ),
        float(
            row[
                "add_to_cart_sessions"
            ]
        ),
        float(
            row[
                "checkout_sessions"
            ]
        ),
        float(
            row[
                "purchase_sessions"
            ]
        ),
    ]

    stage_rates = [
        100.0,
        float(
            row[
                "view_to_cart_pct"
            ]
        ),
        float(
            row[
                "cart_to_checkout_pct"
            ]
        ),
        float(
            row[
                "checkout_to_purchase_pct"
            ]
        ),
    ]

    drop_rates = [
        None,
        100 - float(
            row[
                "view_to_cart_pct"
            ]
        ),
        100 - float(
            row[
                "cart_to_checkout_pct"
            ]
        ),
        100 - float(
            row[
                "checkout_to_purchase_pct"
            ]
        ),
    ]

    fig, ax = plt.subplots(
        figsize=(14, 7.5)
    )

    bars = ax.barh(
        stages,
        values,
        color=[
            NAVY,
            BLUE,
            SKY,
            TEAL
        ],
        height=0.62
    )

    ax.invert_yaxis()

    add_title(
        ax,
        "Customer Conversion Funnel",
        (
            f"Overall session conversion: "
            f"{float(row['overall_conversion_pct']):.2f}% | "
            f"The largest proportional loss occurs between "
            f"Add to Cart and Checkout."
        )
    )

    max_value = max(
        values
    )

    for i, (
        bar,
        value,
        rate
    ) in enumerate(
        zip(
            bars,
            values,
            stage_rates
        )
    ):

        label = (
            f"{value:,.0f}"
        )

        if i > 0:

            label += (
                f"  |  "
                f"{rate:.2f}% "
                f"from prior stage"
            )

        ax.text(
            bar.get_width()
            + max_value * 0.012,
            bar.get_y()
            + bar.get_height() / 2,
            label,
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=DARK,
        )

        if i > 0:

            ax.text(
                max_value * 0.51,
                bar.get_y() - 0.15,
                (
                    f"Drop-off: "
                    f"{drop_rates[i]:.2f}%"
                ),
                fontsize=9,
                color=SLATE,
            )

    ax.set_xlabel(
        "Sessions"
    )

    ax.set_xlim(
        0,
        max_value * 1.25
    )

    ax.xaxis.set_major_formatter(
        FuncFormatter(
            lambda x, pos:
            (
                f"{x / 1000:.0f}K"
                if x >= 1000
                else f"{x:.0f}"
            )
        )
    )

    style_axis(
        ax,
        "x"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "16_customer_funnel.png"
    )


# ============================================================
# QUERY 17 — ABANDONMENT OUTCOMES
# ============================================================

def chart_17_abandonment(df):

    data = (
        df
        .sort_values(
            "stage_order"
        )
        .copy()
    )

    colors = [
        SLATE,
        AMBER,
        RED,
        TEAL
    ]

    fig, ax = plt.subplots(
        figsize=(14, 7.5)
    )

    bars = ax.barh(
        data[
            "journey_outcome"
        ],
        data[
            "sessions"
        ].astype(float),
        color=colors,
        height=0.62,
    )

    ax.invert_yaxis()

    add_title(
        ax,
        "Where Customers Leave the Journey",
        (
            "Each session is assigned to one final outcome; "
            "the categories are mutually exclusive."
        )
    )

    max_value = float(
        data[
            "sessions"
        ].max()
    )

    for bar, row in zip(
        bars,
        data.itertuples()
    ):

        ax.text(
            bar.get_width()
            + max_value * 0.015,
            bar.get_y()
            + bar.get_height() / 2,
            (
                f"{int(row.sessions):,}"
                f"  |  "
                f"{float(row.percentage_of_sessions):.2f}%"
            ),
            va="center",
            fontsize=10.5,
            fontweight="bold",
        )

    ax.set_xlabel(
        "Sessions"
    )

    ax.set_xlim(
        0,
        max_value * 1.28
    )

    style_axis(
        ax,
        "x"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "17_funnel_abandonment.png"
    )


# ============================================================
# QUERY 18 — JOURNEY LENGTH
# ============================================================

def chart_18_journey_length(df):

    row = df.iloc[0]

    minimum = float(
        row[
            "min_events_to_purchase"
        ]
    )

    maximum = float(
        row[
            "max_events_to_purchase"
        ]
    )

    average = float(
        row[
            "avg_events_to_purchase"
        ]
    )

    median = float(
        row[
            "median_events_to_purchase"
        ]
    )

    sessions = int(
        row[
            "converted_sessions"
        ]
    )

    next_steps = float(
        row[
            "avg_next_steps_to_purchase"
        ]
    )

    fig = plt.figure(
        figsize=(16, 9)
    )

    ax = fig.add_axes(
        [
            0.08,
            0.24,
            0.84,
            0.48
        ]
    )

    fig.text(
        0.06,
        0.92,
        "Conversion Journey Length",
        fontsize=24,
        fontweight="bold",
        color=NAVY
    )

    fig.text(
        0.06,
        0.875,
        (
            "Successful purchases typically require "
            "about nine customer events."
        ),
        fontsize=11,
        color=SLATE,
    )

    ax.hlines(
        1,
        minimum,
        maximum,
        color=LIGHT,
        linewidth=18,
        zorder=1
    )

    ax.hlines(
        1,
        minimum,
        maximum,
        color=BLUE,
        linewidth=3,
        zorder=2
    )

    ax.scatter(
        [
            minimum,
            maximum
        ],
        [
            1,
            1
        ],
        s=180,
        color=[
            SLATE,
            SLATE
        ],
        zorder=3
    )

    ax.scatter(
        [average],
        [1],
        s=300,
        color=TEAL,
        edgecolor=WHITE,
        linewidth=2,
        zorder=4
    )

    ax.scatter(
        [median],
        [1],
        s=220,
        marker="D",
        color=NAVY,
        edgecolor=WHITE,
        linewidth=1.5,
        zorder=5
    )

    ax.text(
        minimum,
        1.12,
        (
            f"Minimum\n"
            f"{minimum:.0f} events"
        ),
        ha="center",
        va="bottom",
        fontsize=10,
        color=SLATE
    )

    ax.text(
        maximum,
        1.12,
        (
            f"Maximum\n"
            f"{maximum:.0f} events"
        ),
        ha="center",
        va="bottom",
        fontsize=10,
        color=SLATE
    )

    ax.text(
        average,
        0.82,
        (
            f"Average\n"
            f"{average:.2f}"
        ),
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=TEAL
    )

    ax.text(
        median,
        1.16,
        (
            f"Median\n"
            f"{median:.1f}"
        ),
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color=NAVY
    )

    ax.set_xlim(
        max(
            0,
            minimum - 1
        ),
        maximum + 1
    )

    ax.set_ylim(
        0.55,
        1.45
    )

    ax.set_yticks(
        []
    )

    ax.set_xlabel(
        "Events from first interaction to purchase",
        labelpad=6
    )

    ax.spines[
        [
            "top",
            "right",
            "left"
        ]
    ].set_visible(
        False
    )

    ax.spines[
        "bottom"
    ].set_color(
        MID
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.8
    )

    ax.set_axisbelow(
        True
    )

    draw_insight_box(
        fig,
        0.08,
        0.045,
        0.25,
        0.115,
        "Converted sessions",
        f"{sessions:,}",
        NAVY
    )

    draw_insight_box(
        fig,
        0.375,
        0.045,
        0.25,
        0.115,
        "Typical journey",
        f"~{median:.0f} events",
        TEAL
    )

    draw_insight_box(
        fig,
        0.67,
        0.045,
        0.25,
        0.115,
        "Average transitions",
        f"{next_steps:.2f} NEXT steps",
        BLUE
    )

    save_chart(
        fig,
        "18_conversion_journey_length.png"
    )


# ============================================================
# QUERY 19 — TIME TO PURCHASE
# ============================================================

def chart_19_conversion_time(df):

    row = df.iloc[0]

    fastest = float(
        row[
            "fastest_conversion_minutes"
        ]
    )

    slowest = float(
        row[
            "slowest_conversion_minutes"
        ]
    )

    average = float(
        row[
            "avg_conversion_minutes"
        ]
    )

    median = float(
        row[
            "median_conversion_minutes"
        ]
    )

    sessions = int(
        row[
            "converted_sessions"
        ]
    )

    fig = plt.figure(
        figsize=(16, 9)
    )

    ax = fig.add_axes(
        [
            0.08,
            0.24,
            0.84,
            0.48
        ]
    )

    fig.text(
        0.06,
        0.92,
        "Time to Purchase",
        fontsize=24,
        fontweight="bold",
        color=NAVY
    )

    fig.text(
        0.06,
        0.875,
        (
            f"The typical converted session completes "
            f"in about {median / 60:.1f} hours; "
            f"average and median are closely aligned."
        ),
        fontsize=11,
        color=SLATE,
    )

    ax.hlines(
        1,
        fastest,
        slowest,
        color=LIGHT,
        linewidth=18,
        zorder=1
    )

    ax.hlines(
        1,
        fastest,
        slowest,
        color=BLUE,
        linewidth=3,
        zorder=2
    )

    ax.scatter(
        [
            fastest,
            slowest
        ],
        [
            1,
            1
        ],
        s=180,
        color=[
            SLATE,
            SLATE
        ],
        zorder=3
    )

    ax.scatter(
        [average],
        [1],
        s=300,
        color=TEAL,
        edgecolor=WHITE,
        linewidth=2,
        zorder=4
    )

    ax.scatter(
        [median],
        [1],
        s=220,
        marker="D",
        color=NAVY,
        edgecolor=WHITE,
        linewidth=1.5,
        zorder=5
    )

    ax.text(
        fastest,
        1.12,
        (
            f"Fastest\n"
            f"{fastest:.0f} min"
        ),
        ha="center",
        va="bottom",
        fontsize=10,
        color=SLATE
    )

    ax.text(
        slowest,
        1.12,
        (
            f"Slowest\n"
            f"{minutes_business(slowest)}"
        ),
        ha="center",
        va="bottom",
        fontsize=10,
        color=SLATE
    )

    ax.text(
        average,
        0.82,
        (
            f"Average\n"
            f"{minutes_business(average)}"
        ),
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=TEAL
    )

    ax.text(
        median,
        1.16,
        (
            f"Median\n"
            f"{minutes_business(median)}"
        ),
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
        color=NAVY
    )

    ax.set_xlim(
        max(
            0,
            fastest - 10
        ),
        slowest + 15
    )

    ax.set_ylim(
        0.55,
        1.45
    )

    ax.set_yticks(
        []
    )

    ax.set_xlabel(
        "Minutes from session start to purchase",
        labelpad=6
    )

    ax.spines[
        [
            "top",
            "right",
            "left"
        ]
    ].set_visible(
        False
    )

    ax.spines[
        "bottom"
    ].set_color(
        MID
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.8
    )

    ax.set_axisbelow(
        True
    )

    draw_insight_box(
        fig,
        0.08,
        0.045,
        0.25,
        0.115,
        "Converted sessions",
        f"{sessions:,}",
        NAVY
    )

    draw_insight_box(
        fig,
        0.375,
        0.045,
        0.25,
        0.115,
        "Average time",
        minutes_business(
            average
        ),
        TEAL
    )

    draw_insight_box(
        fig,
        0.67,
        0.045,
        0.25,
        0.115,
        "Observed range",
        (
            f"{fastest:.0f}–"
            f"{slowest:.0f} min"
        ),
        BLUE
    )

    save_chart(
        fig,
        "19_conversion_time.png"
    )


# ============================================================
# QUERY 20 — COMMON JOURNEY PATHS
# ============================================================

def chart_20_journey_paths(df):

    data = (
        df
        .head(10)
        .copy()
    )

    coverage = float(
        data[
            "percentage_of_converted_sessions"
        ].sum()
    )

    data[
        "label"
    ] = (
        data[
            "journey_path"
        ]
        .apply(
            lambda x:
            business_path(
                x,
                56
            )
        )
    )

    data = data.sort_values(
        "sessions"
    )

    fig, ax = plt.subplots(
        figsize=(16, 10)
    )

    colors = [
        BLUE
    ] * len(data)

    if colors:
        colors[
            -1
        ] = TEAL

    bars = ax.barh(
        data[
            "label"
        ],
        data[
            "sessions"
        ].astype(float),
        color=colors,
        height=0.66
    )

    add_title(
        ax,
        "Most Common Purchase Journeys",
        (
            f"The top 10 journey patterns account for "
            f"{coverage:.2f}% of converted sessions, "
            f"showing substantial path diversity."
        )
    )

    max_value = float(
        data[
            "sessions"
        ].max()
    )

    for bar, row in zip(
        bars,
        data.itertuples()
    ):

        ax.text(
            bar.get_width()
            + max_value * 0.015,
            bar.get_y()
            + bar.get_height() / 2,
            (
                f"{int(row.sessions):,}"
                f" | "
                f"{float(row.percentage_of_converted_sessions):.2f}%"
            ),
            va="center",
            fontsize=9.5,
        )

    ax.set_xlabel(
        "Converted Sessions"
    )

    ax.set_xlim(
        0,
        max_value * 1.30
    )

    style_axis(
        ax,
        "x"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "20_common_journey_paths.png"
    )


# ============================================================
# QUERY 21 — VIEWED BUT NOT PURCHASED
# ============================================================

def chart_21_viewed_not_purchased(df):

    data = (
        df
        .head(15)
        .copy()
        .sort_values(
            "viewed_not_purchased_sessions"
        )
    )

    data[
        "label"
    ] = (
        data.apply(
            lambda row:
            (
                f"{shorten_text(row['product_name'], 34)}"
                f"\n"
                f"{row['category']}"
            ),
            axis=1,
        )
    )

    fig, ax = plt.subplots(
        figsize=(16, 10)
    )

    ax.barh(
        data[
            "label"
        ],
        data[
            "purchased_after_view_sessions"
        ].astype(float),
        color=TEAL,
        label="Purchased after view",
    )

    ax.barh(
        data[
            "label"
        ],
        data[
            "viewed_not_purchased_sessions"
        ].astype(float),
        left=data[
            "purchased_after_view_sessions"
        ].astype(float),
        color=LIGHT,
        edgecolor=MID,
        label="Viewed but not purchased",
    )

    add_title(
        ax,
        (
            "High-Interest Products With Weak "
            "Purchase Follow-Through"
        ),
        (
            "Products are ranked by the number of viewing "
            "sessions that did not convert to purchase."
        )
    )

    max_value = float(
        data[
            "viewed_sessions"
        ].max()
    )

    for y_pos, row in enumerate(
        data.itertuples()
    ):

        ax.text(
            float(
                row.viewed_sessions
            )
            + max_value * 0.012,
            y_pos,
            (
                f"{float(row.view_to_purchase_pct):.1f}% "
                f"converted"
            ),
            va="center",
            fontsize=9.2,
            color=DARK,
        )

    ax.set_xlabel(
        "Viewing Sessions"
    )

    ax.set_xlim(
        0,
        max_value * 1.22
    )

    ax.legend(
        frameon=False,
        loc="lower right"
    )

    style_axis(
        ax,
        "x"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "21_viewed_not_purchased.png"
    )


# ============================================================
# QUERY 22 — PRODUCT CO-PURCHASE RELATIONSHIP MAP
# ============================================================

def chart_22_product_network(df):

    # A force-directed network becomes unreadable because
    # this SKU network is sparse.
    #
    # Instead, show the strongest graph edges as a clean
    # relationship map.

    data = (
        df
        .head(12)
        .copy()
        .sort_values(
            [
                "copurchase_orders",
                "product_1_name"
            ],
            ascending=[
                False,
                True
            ]
        )
    )

    categories = sorted(
        set(
            data[
                "product_1_category"
            ]
        ).union(
            set(
                data[
                    "product_2_category"
                ]
            )
        )
    )

    category_colors = {
        category:
        CATEGORY_PALETTE[
            i
            % len(
                CATEGORY_PALETTE
            )
        ]
        for i, category
        in enumerate(
            categories
        )
    }

    fig, ax = plt.subplots(
        figsize=(16, 10)
    )

    y = np.arange(
        len(data)
    )

    x_left = 0.14
    x_right = 0.86

    max_orders = float(
        data[
            "copurchase_orders"
        ].max()
    )

    for idx, row in enumerate(
        data.itertuples()
    ):

        weight = float(
            row.copurchase_orders
        )

        width = (
            1.5
            + 4.0
            * (
                weight
                / max_orders
            )
        )

        same_category = (
            row.product_1_category
            == row.product_2_category
        )

        line_color = (
            TEAL
            if same_category
            else SKY
        )

        ax.plot(
            [
                x_left,
                x_right
            ],
            [
                idx,
                idx
            ],
            color=line_color,
            linewidth=width,
            alpha=0.65,
            zorder=1
        )

        ax.scatter(
            [x_left],
            [idx],
            s=260,
            color=category_colors[
                row.product_1_category
            ],
            edgecolor=WHITE,
            linewidth=1.5,
            zorder=3
        )

        ax.scatter(
            [x_right],
            [idx],
            s=260,
            color=category_colors[
                row.product_2_category
            ],
            edgecolor=WHITE,
            linewidth=1.5,
            zorder=3
        )

        ax.text(
            x_left - 0.03,
            idx,
            (
                f"{shorten_text(row.product_1_name, 30)}"
                f"\n"
                f"{row.product_1_category}"
            ),
            ha="right",
            va="center",
            fontsize=9.2,
            color=DARK,
        )

        ax.text(
            x_right + 0.03,
            idx,
            (
                f"{shorten_text(row.product_2_name, 30)}"
                f"\n"
                f"{row.product_2_category}"
            ),
            ha="left",
            va="center",
            fontsize=9.2,
            color=DARK,
        )

        ax.text(
            0.50,
            idx,
            (
                f"{int(weight)} "
                f"shared orders"
            ),
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color=NAVY,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor=WHITE,
                edgecolor=LIGHT,
            ),
        )

    ax.set_xlim(
        0,
        1
    )

    ax.set_ylim(
        -0.8,
        len(data) - 0.2
    )

    ax.set_xticks(
        []
    )

    ax.set_yticks(
        []
    )

    ax.invert_yaxis()

    for spine in ax.spines.values():
        spine.set_visible(
            False
        )

    ax.set_title(
        "Top Product Co-Purchase Relationships",
        loc="left",
        fontweight="bold",
        color=NAVY,
        pad=24
    )

    ax.text(
        0,
        1.015,
        (
            "The SKU-level graph is sparse, so the strongest "
            "Neo4j relationships are shown as readable edge "
            "pairs rather than a force-directed hairball."
        ),
        transform=ax.transAxes,
        fontsize=10.2,
        color=SLATE,
    )

    ax.text(
        0.14,
        1.0,
        "Product A",
        transform=ax.transAxes,
        ha="center",
        fontsize=9.5,
        color=SLATE
    )

    ax.text(
        0.86,
        1.0,
        "Product B",
        transform=ax.transAxes,
        ha="center",
        fontsize=9.5,
        color=SLATE
    )

    legend_y = 0.015
    legend_x = 0.10

    for i, category in enumerate(
        categories
    ):

        x = (
            legend_x
            + i * 0.12
        )

        fig.text(
            x,
            legend_y + 0.025,
            "●",
            color=category_colors[
                category
            ],
            fontsize=13,
            ha="center"
        )

        fig.text(
            x + 0.012,
            legend_y + 0.026,
            category,
            color=SLATE,
            fontsize=8.0,
            ha="left"
        )

    fig.tight_layout(
        rect=[
            0,
            0.06,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "22_product_copurchase_network.png"
    )


# ============================================================
# QUERY 23 — PRODUCT AFFINITY WITH EVIDENCE CONTEXT
# ============================================================

def chart_23_product_affinity(df):

    data = (
        df
        .head(20)
        .copy()
    )

    data[
        "base_orders"
    ] = (
        data[
            [
                "product_1_orders",
                "product_2_orders"
            ]
        ]
        .min(
            axis=1
        )
        .astype(float)
    )

    data[
        "same_category"
    ] = (
        data[
            "product_1_category"
        ]
        == data[
            "product_2_category"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(15, 9)
    )

    same = data[
        data[
            "same_category"
        ]
    ]

    cross = data[
        ~data[
            "same_category"
        ]
    ]

    ax.scatter(
        same[
            "base_orders"
        ],
        same[
            "lift"
        ],
        s=(
            80
            + same[
                "copurchase_orders"
            ].astype(float) * 35
        ),
        color=TEAL,
        alpha=0.82,
        edgecolor=WHITE,
        linewidth=0.8,
        label="Same category",
    )

    ax.scatter(
        cross[
            "base_orders"
        ],
        cross[
            "lift"
        ],
        s=(
            80
            + cross[
                "copurchase_orders"
            ].astype(float) * 35
        ),
        color=BLUE,
        alpha=0.82,
        edgecolor=WHITE,
        linewidth=0.8,
        label="Cross category",
    )

    label_rows = pd.concat(
        [
            data.nlargest(
                4,
                "lift"
            ),
            data.nlargest(
                3,
                "base_orders"
            ),
        ]
    ).drop_duplicates(
        subset=[
            "product_1_id",
            "product_2_id"
        ]
    )

    for row in label_rows.itertuples():

        label = (
            f"{shorten_text(row.product_1_name, 18)}"
            f"\n× "
            f"{shorten_text(row.product_2_name, 18)}"
        )

        ax.annotate(
            label,
            (
                float(
                    row.base_orders
                ),
                float(
                    row.lift
                )
            ),
            xytext=(
                7,
                7
            ),
            textcoords="offset points",
            fontsize=8.2,
            color=DARK,
        )

    add_title(
        ax,
        "Product Affinity: Lift vs. Evidence Base",
        (
            "Higher lift indicates stronger-than-random "
            "co-purchase; moving right indicates a larger "
            "underlying purchase base. Shared-order counts "
            "remain small, so treat SKU recommendations "
            "as directional."
        )
    )

    ax.set_xlabel(
        "Smaller product purchase base (orders)"
    )

    ax.set_ylabel(
        "Lift vs. random expectation"
    )

    ax.legend(
        frameon=False,
        loc="upper right"
    )

    style_axis(
        ax,
        "both"
    )

    shared_counts = sorted(
        data[
            "copurchase_orders"
        ]
        .astype(int)
        .unique()
        .tolist()
    )

    shared_text = ", ".join(
        map(
            str,
            shared_counts
        )
    )

    fig.text(
        0.09,
        0.075,
        (
            f"Evidence note: top affinity pairs are supported "
            f"by only {shared_text} shared-order count(s) in "
            f"this output. High lift does not equal high volume."
        ),
        fontsize=9.4,
        color=RED,
    )

    fig.tight_layout(
        rect=[
            0,
            0.09,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "23_product_affinity.png"
    )


# ============================================================
# QUERY 24 — CROSS-SELL RELATIONSHIP SHORTLIST
# ============================================================

def chart_24_cross_sell(df):

    data = (
        df
        .head(12)
        .copy()
        .sort_values(
            [
                "opportunity_sessions",
                "purchased_product_name"
            ],
            ascending=[
                False,
                True
            ]
        )
    )

    categories = sorted(
        set(
            data[
                "purchased_product_category"
            ]
        ).union(
            set(
                data[
                    "cross_sell_product_category"
                ]
            )
        )
    )

    category_colors = {
        category:
        CATEGORY_PALETTE[
            i
            % len(
                CATEGORY_PALETTE
            )
        ]
        for i, category
        in enumerate(
            categories
        )
    }

    fig, ax = plt.subplots(
        figsize=(16, 10)
    )

    x_left = 0.16
    x_right = 0.84

    for idx, row in enumerate(
        data.itertuples()
    ):

        sessions = int(
            row.opportunity_sessions
        )

        line_width = (
            1.5
            + sessions * 0.55
        )

        ax.plot(
            [
                x_left,
                x_right
            ],
            [
                idx,
                idx
            ],
            color=LIGHT,
            linewidth=line_width,
            zorder=1
        )

        ax.scatter(
            [x_left],
            [idx],
            s=220,
            color=category_colors[
                row.purchased_product_category
            ],
            edgecolor=WHITE,
            linewidth=1.3,
            zorder=3
        )

        ax.scatter(
            [x_right],
            [idx],
            s=220,
            color=category_colors[
                row.cross_sell_product_category
            ],
            edgecolor=WHITE,
            linewidth=1.3,
            zorder=3
        )

        ax.text(
            x_left - 0.03,
            idx,
            (
                f"{shorten_text(row.purchased_product_name, 31)}"
                f"\n"
                f"{row.purchased_product_category}"
            ),
            ha="right",
            va="center",
            fontsize=9.1,
        )

        ax.text(
            x_right + 0.03,
            idx,
            (
                f"{shorten_text(row.cross_sell_product_name, 31)}"
                f"\n"
                f"{row.cross_sell_product_category}"
            ),
            ha="left",
            va="center",
            fontsize=9.1,
        )

        ax.text(
            0.50,
            idx,
            (
                f"{sessions} "
                f"opportunity sessions"
            ),
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color=NAVY,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor=WHITE,
                edgecolor=LIGHT
            ),
        )

    ax.set_xlim(
        0,
        1
    )

    ax.set_ylim(
        -0.8,
        len(data) - 0.2
    )

    ax.set_xticks(
        []
    )

    ax.set_yticks(
        []
    )

    ax.invert_yaxis()

    for spine in ax.spines.values():
        spine.set_visible(
            False
        )

    ax.set_title(
        "Cross-Sell Opportunity Shortlist",
        loc="left",
        fontweight="bold",
        color=NAVY,
        pad=24
    )

    ax.text(
        0,
        1.015,
        (
            "The left product was purchased; the right product "
            "was viewed in the same session but omitted from "
            "the final order. Counts are small, so use these "
            "as test candidates rather than definitive "
            "recommendations."
        ),
        transform=ax.transAxes,
        fontsize=10.2,
        color=SLATE,
    )

    ax.text(
        0.16,
        1.0,
        "Purchased product",
        transform=ax.transAxes,
        ha="center",
        fontsize=9.5,
        color=SLATE
    )

    ax.text(
        0.84,
        1.0,
        "Viewed but not purchased",
        transform=ax.transAxes,
        ha="center",
        fontsize=9.5,
        color=SLATE
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "24_cross_sell_opportunities.png"
    )


# ============================================================
# QUERY 25 — CATEGORY CO-PURCHASE HEATMAP
# ============================================================

def chart_25_category_heatmap(df):

    categories = sorted(
        set(
            df[
                "category_1"
            ]
        ).union(
            set(
                df[
                    "category_2"
                ]
            )
        )
    )

    matrix = pd.DataFrame(
        0.0,
        index=categories,
        columns=categories
    )

    for row in df.itertuples():

        value = float(
            row.orders_together
        )

        matrix.loc[
            row.category_1,
            row.category_2
        ] = value

        matrix.loc[
            row.category_2,
            row.category_1
        ] = value

    cmap = LinearSegmentedColormap.from_list(
        "bi_blue",
        [
            WHITE,
            SKY,
            BLUE,
            NAVY
        ]
    )

    fig, ax = plt.subplots(
        figsize=(13, 10)
    )

    image = ax.imshow(
        matrix.values,
        aspect="auto",
        cmap=cmap
    )

    ax.set_xticks(
        np.arange(
            len(categories)
        )
    )

    ax.set_yticks(
        np.arange(
            len(categories)
        )
    )

    ax.set_xticklabels(
        categories,
        rotation=35,
        ha="right"
    )

    ax.set_yticklabels(
        categories
    )

    max_value = (
        matrix
        .to_numpy()
        .max()
    )

    for i in range(
        len(categories)
    ):

        for j in range(
            len(categories)
        ):

            value = matrix.iloc[
                i,
                j
            ]

            if value > 0:

                text_color = (
                    WHITE
                    if value
                    > max_value * 0.55
                    else DARK
                )

                ax.text(
                    j,
                    i,
                    f"{value:,.0f}",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color=text_color,
                    fontweight=(
                        "bold"
                        if value
                        > max_value * 0.55
                        else "normal"
                    ),
                )

    cbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.046,
        pad=0.04
    )

    cbar.set_label(
        "Orders Together"
    )

    ax.set_title(
        "Category Co-Purchase Matrix",
        loc="left",
        fontweight="bold",
        color=NAVY,
        pad=24
    )

    ax.text(
        0,
        1.015,
        (
            "Higher values indicate category combinations "
            "appearing together in more orders. Diagonal cells "
            "represent same-category baskets."
        ),
        transform=ax.transAxes,
        fontsize=10.2,
        color=SLATE,
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "25_category_copurchase_heatmap.png"
    )


# ============================================================
# QUERY 26 — CUSTOMER VALUE SEGMENTS
# ============================================================

def chart_26_customer_segments(df):

    data = df.copy()

    fig, ax = plt.subplots(
        figsize=(14, 7.5)
    )

    bars = ax.barh(
        data[
            "customer_segment"
        ],
        data[
            "revenue_usd"
        ].astype(float),
        color=[
            LIGHT,
            BLUE,
            TEAL
        ],
        edgecolor=[
            MID,
            BLUE,
            TEAL
        ],
        height=0.62,
    )

    ax.invert_yaxis()

    total_revenue = float(
        data[
            "revenue_usd"
        ].sum()
    )

    repeat_row = data[
        data[
            "customer_segment"
        ]
        == "Repeat Buyer"
    ].iloc[0]

    repeat_share = (
        float(
            repeat_row[
                "revenue_usd"
            ]
        )
        / total_revenue
        * 100
        if total_revenue
        else 0
    )

    add_title(
        ax,
        "Revenue Contribution by Customer Segment",
        (
            f"Repeat buyers generate "
            f"{repeat_share:.1f}% of total revenue, "
            f"making retention the dominant "
            f"commercial driver."
        )
    )

    max_value = float(
        data[
            "revenue_usd"
        ].max()
    )

    for bar, row in zip(
        bars,
        data.itertuples()
    ):

        revenue = float(
            row.revenue_usd
        )

        share = (
            revenue
            / total_revenue
            * 100
            if total_revenue
            else 0
        )

        ax.text(
            bar.get_width()
            + max_value * 0.015,
            bar.get_y()
            + bar.get_height() / 2,
            (
                f"{format_currency(revenue)}"
                f" | "
                f"{share:.1f}% revenue"
                f" | "
                f"{int(row.customers):,} customers"
            ),
            va="center",
            fontsize=9.5,
            fontweight="bold",
        )

    ax.set_xlabel(
        "Revenue (USD)"
    )

    ax.set_xlim(
        0,
        max_value * 1.38
    )

    ax.xaxis.set_major_formatter(
        FuncFormatter(
            lambda x, pos:
            (
                f"${x / 1_000_000:.1f}M"
                if x >= 1_000_000
                else f"${x / 1000:.0f}K"
            )
        )
    )

    style_axis(
        ax,
        "x"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "26_customer_value_segments.png"
    )


# ============================================================
# QUERY 27 — DEVICE × SOURCE CONVERSION HEATMAP
# ============================================================

def chart_27_device_source(df):

    conversion = df.pivot(
        index="device",
        columns="source",
        values="conversion_rate_pct"
    )

    sessions = df.pivot(
        index="device",
        columns="source",
        values="sessions"
    )

    cmap = LinearSegmentedColormap.from_list(
        "bi_teal",
        [
            WHITE,
            SKY,
            TEAL,
            NAVY
        ]
    )

    fig, ax = plt.subplots(
        figsize=(14, 8)
    )

    image = ax.imshow(
        conversion.values,
        aspect="auto",
        cmap=cmap
    )

    ax.set_xticks(
        np.arange(
            len(
                conversion.columns
            )
        )
    )

    ax.set_xticklabels(
        [
            str(x).title()
            for x
            in conversion.columns
        ]
    )

    ax.set_yticks(
        np.arange(
            len(
                conversion.index
            )
        )
    )

    ax.set_yticklabels(
        [
            str(x).title()
            for x
            in conversion.index
        ]
    )

    finite_values = conversion.to_numpy(
        dtype=float
    )

    threshold = (
        np.nanmin(
            finite_values
        )
        + np.nanmax(
            finite_values
        )
    ) / 2

    for i in range(
        len(
            conversion.index
        )
    ):

        for j in range(
            len(
                conversion.columns
            )
        ):

            rate = conversion.iloc[
                i,
                j
            ]

            sess = sessions.iloc[
                i,
                j
            ]

            if pd.notna(
                rate
            ):

                text_color = (
                    WHITE
                    if float(
                        rate
                    ) >= threshold
                    else DARK
                )

                ax.text(
                    j,
                    i,
                    (
                        f"{float(rate):.2f}%"
                        f"\n"
                        f"{int(sess):,} sessions"
                    ),
                    ha="center",
                    va="center",
                    fontsize=9.2,
                    color=text_color,
                    fontweight="bold",
                )

    cbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.046,
        pad=0.04
    )

    cbar.set_label(
        "Conversion Rate (%)"
    )

    best = (
        df
        .sort_values(
            [
                "conversion_rate_pct",
                "sessions"
            ],
            ascending=[
                False,
                False
            ]
        )
        .iloc[0]
    )

    add_title(
        ax,
        (
            "Conversion Rate by Device "
            "and Traffic Source"
        ),
        (
            f"Rates are relatively tight across segments; "
            f"the highest observed rate is "
            f"{float(best['conversion_rate_pct']):.2f}% "
            f"for {str(best['device']).title()} + "
            f"{str(best['source']).title()}, "
            f"based on {int(best['sessions']):,} sessions."
        )
    )

    ax.set_xlabel(
        "Traffic Source"
    )

    ax.set_ylabel(
        "Device"
    )

    fig.tight_layout(
        rect=[
            0,
            0.04,
            1,
            0.96
        ]
    )

    save_chart(
        fig,
        "27_device_source_conversion.png"
    )


# ============================================================
# QUERY 28 — EXECUTIVE KPI DASHBOARD
# ============================================================

def chart_28_executive(df):

    row = df.iloc[0]

    fig = plt.figure(
        figsize=(16, 9)
    )

    ax = fig.add_axes(
        [
            0,
            0,
            1,
            1
        ]
    )

    ax.axis(
        "off"
    )

    fig.text(
        0.055,
        0.92,
        "Executive Commerce Performance",
        fontsize=24,
        fontweight="bold",
        color=NAVY
    )

    fig.text(
        0.055,
        0.875,
        (
            "Scale, commercial performance and customer "
            "retention in one executive view."
        ),
        fontsize=11,
        color=SLATE
    )

    groups = [
        (
            "Scale",
            [
                (
                    "Customers",
                    format_number(
                        row[
                            "total_customers"
                        ]
                    )
                ),
                (
                    "Sessions",
                    format_number(
                        row[
                            "total_sessions"
                        ]
                    )
                ),
                (
                    "Orders",
                    format_number(
                        row[
                            "total_orders"
                        ]
                    )
                ),
            ],
            NAVY,
        ),
        (
            "Commercial",
            [
                (
                    "Revenue",
                    format_currency(
                        row[
                            "total_revenue_usd"
                        ]
                    )
                ),
                (
                    "Average Order Value",
                    format_currency(
                        row[
                            "avg_order_value_usd"
                        ]
                    )
                ),
                (
                    "Session Conversion",
                    format_percent(
                        row[
                            "conversion_rate_pct"
                        ]
                    )
                ),
            ],
            BLUE,
        ),
        (
            "Customer Loyalty",
            [
                (
                    "Purchasing Customers",
                    (
                        f"{format_number(row['purchasing_customers'])}"
                        f" | "
                        f"{format_percent(row['purchasing_customer_pct'])}"
                    )
                ),
                (
                    "Repeat Buyers",
                    (
                        f"{format_number(row['repeat_buyers'])}"
                        f" | "
                        f"{format_percent(row['repeat_buyer_pct_of_buyers'])}"
                    )
                ),
                (
                    "Reviews",
                    format_number(
                        row[
                            "total_reviews"
                        ]
                    )
                ),
            ],
            TEAL,
        ),
    ]

    left = 0.055
    group_width = 0.89
    group_height = 0.19
    card_gap = 0.02

    card_width = (
        group_width
        - 2 * card_gap
    ) / 3

    start_y = 0.64
    group_gap = 0.045

    for g_idx, (
        group_name,
        metrics,
        accent
    ) in enumerate(
        groups
    ):

        y = (
            start_y
            - g_idx
            * (
                group_height
                + group_gap
            )
        )

        fig.text(
            left,
            y
            + group_height
            + 0.016,
            group_name.upper(),
            fontsize=9.5,
            fontweight="bold",
            color=accent
        )

        for c_idx, (
            label,
            value
        ) in enumerate(
            metrics
        ):

            x = (
                left
                + c_idx
                * (
                    card_width
                    + card_gap
                )
            )

            box = FancyBboxPatch(
                (
                    x,
                    y
                ),
                card_width,
                group_height,
                transform=fig.transFigure,
                boxstyle=(
                    "round,pad=0.012,"
                    "rounding_size=0.012"
                ),
                facecolor=WHITE,
                edgecolor=LIGHT,
                linewidth=1.2,
            )

            fig.patches.append(
                box
            )

            fig.add_artist(
                plt.Line2D(
                    [
                        x + 0.012,
                        x
                        + card_width
                        - 0.012
                    ],
                    [
                        y
                        + group_height
                        - 0.012,
                        y
                        + group_height
                        - 0.012
                    ],
                    transform=fig.transFigure,
                    color=accent,
                    linewidth=3.2,
                    solid_capstyle="round",
                )
            )

            fig.text(
                x + 0.022,
                y + 0.118,
                label,
                fontsize=9.5,
                color=SLATE
            )

            fig.text(
                x + 0.022,
                y + 0.052,
                value,
                fontsize=19,
                fontweight="bold",
                color=NAVY
            )

    repeat_pct = float(
        row[
            "repeat_buyer_pct_of_buyers"
        ]
    )

    conversion = float(
        row[
            "conversion_rate_pct"
        ]
    )

    insight = (
        f"Retention is the strongest structural signal: "
        f"{repeat_pct:.2f}% of purchasing customers are repeat "
        f"buyers, while session conversion is "
        f"{conversion:.2f}%."
    )

    draw_insight_box(
        fig,
        0.055,
        0.055,
        0.89,
        0.105,
        "Executive takeaway",
        insight,
        TEAL
    )

    save_chart(
        fig,
        "28_executive_kpis.png"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    validate_query_files()

    print(
        "\nNeo4j BI Export + Visualization"
    )

    print(
        "=" * 60
    )

    password = getpass(
        "Neo4j password: "
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USER,
            password
        ),
    )

    try:

        driver.verify_connectivity()

        print(
            "\nConnected to Neo4j successfully."
        )

        print(
            "\nRunning analytical queries...\n"
        )

        results = {}

        with driver.session(
            database=NEO4J_DATABASE
        ) as session:

            for number, filename in (
                QUERY_FILES.items()
            ):

                print(
                    f"Query {number}: "
                    f"{filename}"
                )

                df = run_cypher(
                    session,
                    filename
                )

                validate_result(
                    number,
                    df
                )

                results[
                    number
                ] = df

                csv_path = (
                    EXPORT_DIR
                    / CSV_FILES[
                        number
                    ]
                )

                df.to_csv(
                    csv_path,
                    index=False,
                    encoding="utf-8-sig"
                )

                print(
                    f"   CSV: "
                    f"{CSV_FILES[number]} "
                    f"({len(df):,} rows)"
                )

        validate_cross_query_integrity(
            results
        )

        print(
            "\nCreating BI visualizations...\n"
        )

        chart_16_funnel(
            results[16]
        )

        chart_17_abandonment(
            results[17]
        )

        chart_18_journey_length(
            results[18]
        )

        chart_19_conversion_time(
            results[19]
        )

        chart_20_journey_paths(
            results[20]
        )

        chart_21_viewed_not_purchased(
            results[21]
        )

        chart_22_product_network(
            results[22]
        )

        chart_23_product_affinity(
            results[23]
        )

        chart_24_cross_sell(
            results[24]
        )

        chart_25_category_heatmap(
            results[25]
        )

        chart_26_customer_segments(
            results[26]
        )

        chart_27_device_source(
            results[27]
        )

        chart_28_executive(
            results[28]
        )

        validate_outputs()

        print(
            "\n"
            + "=" * 60
        )

        print(
            "NEO4J BI EXPORT + VISUALIZATION COMPLETE"
        )

        print(
            "=" * 60
        )

        print(
            f"\nCSV exports:\n"
            f"{EXPORT_DIR}"
        )

        print(
            f"\nCharts:\n"
            f"{CHART_DIR}"
        )

    finally:

        driver.close()


if __name__ == "__main__":

    main()