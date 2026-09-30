from html import escape
from pathlib import Path
from textwrap import dedent
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import streamlit as st

# ============================================================
# APP CONFIG + PATHS
# ============================================================
st.set_page_config(
    page_title="Customer Journey & Product Network Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT / "exports"
CHARTS = EXPORTS / "charts"

CSV = {
    16: EXPORTS / "funnel_analysis.csv",
    17: EXPORTS / "abandonment_analysis.csv",
    18: EXPORTS / "conversion_journey_length.csv",
    19: EXPORTS / "conversion_time.csv",
    20: EXPORTS / "common_journey_paths.csv",
    21: EXPORTS / "viewed_not_purchased.csv",
    22: EXPORTS / "product_copurchase.csv",
    23: EXPORTS / "product_affinity.csv",
    24: EXPORTS / "cross_sell_opportunities.csv",
    25: EXPORTS / "category_copurchase.csv",
    26: EXPORTS / "customer_value_segments.csv",
    27: EXPORTS / "device_source_conversion.csv",
    28: EXPORTS / "executive_summary.csv",
}

PNG = {
    16: CHARTS / "16_customer_funnel.png",
    17: CHARTS / "17_funnel_abandonment.png",
    18: CHARTS / "18_conversion_journey_length.png",
    19: CHARTS / "19_conversion_time.png",
    20: CHARTS / "20_common_journey_paths.png",
    21: CHARTS / "21_viewed_not_purchased.png",
    22: CHARTS / "22_product_copurchase_network.png",
    23: CHARTS / "23_product_affinity.png",
    24: CHARTS / "24_cross_sell_opportunities.png",
    25: CHARTS / "25_category_copurchase_heatmap.png",
    26: CHARTS / "26_customer_value_segments.png",
    27: CHARTS / "27_device_source_conversion.png",
    28: CHARTS / "28_executive_kpis.png",
}

EXEC_COLS = {
    "total_customers", "total_sessions", "total_orders", "total_revenue_usd",
    "avg_order_value_usd", "conversion_rate_pct", "purchasing_customers",
    "purchasing_customer_pct", "repeat_buyers", "repeat_buyer_pct_of_buyers",
    "total_reviews",
}

FUNNEL_COLS = {
    "total_sessions", "page_view_sessions", "add_to_cart_sessions",
    "checkout_sessions", "purchase_sessions", "view_to_cart_pct",
    "cart_to_checkout_pct", "checkout_to_purchase_pct", "overall_conversion_pct",
}

SEGMENT_COLS = {
    "segment_order", "customer_segment", "customers", "orders", "revenue_usd",
    "avg_orders_per_customer", "avg_revenue_per_customer_usd",
}

CHANNEL_COLS = {
    "device", "source", "sessions", "converted_sessions", "conversion_rate_pct",
    "revenue_usd", "avg_order_value_usd",
}

# ============================================================
# HELPERS
# ============================================================
def render_html(content: str) -> None:
    clean = dedent(content).strip()

    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(
            re.sub(r"\n\s*", " ", clean),
            unsafe_allow_html=True,
        )


@st.cache_data(show_spinner=False)
def _read_csv(path_string: str, mtime_ns: int) -> pd.DataFrame:
    _ = mtime_ns

    return pd.read_csv(
        path_string,
        encoding="utf-8-sig",
    )


def read_required(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(
            f"Required export missing or empty: {path}"
        )

    df = _read_csv(
        str(path),
        path.stat().st_mtime_ns,
    )

    if df.empty:
        raise ValueError(
            f"{path.name} contains no data rows."
        )

    return df


def require_columns(
    df: pd.DataFrame,
    required: set[str],
    filename: str,
) -> None:

    missing = required.difference(
        df.columns
    )

    if missing:
        raise ValueError(
            f"{filename} missing column(s): "
            + ", ".join(
                sorted(missing)
            )
        )

    selected = df[
        list(required)
    ]

    if selected.isnull().any().any():
        bad = (
            selected
            .columns[
                selected
                .isnull()
                .any()
            ]
            .tolist()
        )

        raise ValueError(
            f"{filename} contains nulls in: "
            + ", ".join(bad)
        )


def to_numeric(
    df: pd.DataFrame,
    columns: set[str],
    filename: str,
) -> pd.DataFrame:

    out = df.copy()

    for column in columns:

        out[column] = pd.to_numeric(
            out[column],
            errors="coerce",
        )

        if out[column].isnull().any():
            raise ValueError(
                f"{filename} contains invalid numeric "
                f"data in '{column}'."
            )

    return out


def normalize(name: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(name).lower(),
    ).strip("_")


def find_col(
    df: pd.DataFrame,
    *candidates: str,
) -> str | None:

    lookup = {
        normalize(col): col
        for col in df.columns
    }

    for candidate in candidates:
        if normalize(candidate) in lookup:
            return lookup[
                normalize(candidate)
            ]

    return None


def fmt_num(value) -> str:
    return f"{int(round(float(value))):,}"


def fmt_money(value) -> str:
    return f"${float(value):,.2f}"


def fmt_pct(value) -> str:
    return f"{float(value):.2f}%"

# ============================================================
# LOAD + VALIDATE Q16–Q28
# ============================================================
try:

    missing_assets = []

    for q in range(
        16,
        29,
    ):

        if (
            not CSV[q].exists()
            or CSV[q].stat().st_size == 0
        ):
            missing_assets.append(
                f"Q{q} CSV ({CSV[q].name})"
            )

        if (
            not PNG[q].exists()
            or PNG[q].stat().st_size == 0
        ):
            missing_assets.append(
                f"Q{q} chart ({PNG[q].name})"
            )

    if missing_assets:
        raise FileNotFoundError(
            "Missing/empty asset(s): "
            + "; ".join(missing_assets)
        )

    DATA = {
        q: read_required(
            CSV[q]
        )
        for q in range(
            16,
            29,
        )
    }

    require_columns(
        DATA[28],
        EXEC_COLS,
        CSV[28].name,
    )

    require_columns(
        DATA[16],
        FUNNEL_COLS,
        CSV[16].name,
    )

    require_columns(
        DATA[26],
        SEGMENT_COLS,
        CSV[26].name,
    )

    require_columns(
        DATA[27],
        CHANNEL_COLS,
        CSV[27].name,
    )

    if len(
        DATA[28]
    ) != 1:
        raise ValueError(
            "Q28 must contain exactly one executive summary row."
        )

    if len(
        DATA[16]
    ) != 1:
        raise ValueError(
            "Q16 must contain exactly one funnel summary row."
        )

    DATA[28] = to_numeric(
        DATA[28],
        EXEC_COLS,
        CSV[28].name,
    )

    DATA[16] = to_numeric(
        DATA[16],
        FUNNEL_COLS,
        CSV[16].name,
    )

    DATA[26] = to_numeric(
        DATA[26],
        {
            "segment_order",
            "customers",
            "orders",
            "revenue_usd",
            "avg_orders_per_customer",
            "avg_revenue_per_customer_usd",
        },
        CSV[26].name,
    )

    DATA[27] = to_numeric(
        DATA[27],
        {
            "sessions",
            "converted_sessions",
            "conversion_rate_pct",
            "revenue_usd",
            "avg_order_value_usd",
        },
        CSV[27].name,
    )

    for (
        df,
        fields,
        filename,
    ) in [
        (
            DATA[28],
            {
                "conversion_rate_pct",
                "purchasing_customer_pct",
                "repeat_buyer_pct_of_buyers",
            },
            CSV[28].name,
        ),
        (
            DATA[16],
            {
                "view_to_cart_pct",
                "cart_to_checkout_pct",
                "checkout_to_purchase_pct",
                "overall_conversion_pct",
            },
            CSV[16].name,
        ),
        (
            DATA[27],
            {
                "conversion_rate_pct",
            },
            CSV[27].name,
        ),
    ]:

        for field in fields:

            if not df[
                field
            ].between(
                0,
                100,
                inclusive="both",
            ).all():

                raise ValueError(
                    f"{filename} contains an invalid percentage "
                    f"in '{field}'."
                )

    DATA[26][
        "customer_segment"
    ] = (
        DATA[26][
            "customer_segment"
        ]
        .astype(str)
        .str.strip()
    )

    DATA[27][
        "device"
    ] = (
        DATA[27][
            "device"
        ]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    DATA[27][
        "source"
    ] = (
        DATA[27][
            "source"
        ]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    executive = DATA[28].iloc[0]
    funnel = DATA[16].iloc[0]
    segments = DATA[26]
    channels = DATA[27]

except Exception as error:

    st.error(
        "The analytics application could not initialize."
    )

    st.code(
        str(error)
    )

    st.stop()

# ============================================================
# CROSS-QUERY RECONCILIATION
# ============================================================
failures = []

checks = [
    (
        int(
            funnel[
                "total_sessions"
            ]
        ),
        int(
            executive[
                "total_sessions"
            ]
        ),
        "Q16 sessions vs Q28 sessions",
    ),
    (
        int(
            funnel[
                "purchase_sessions"
            ]
        ),
        int(
            executive[
                "total_orders"
            ]
        ),
        "Q16 purchases vs Q28 orders",
    ),
    (
        int(
            segments[
                "customers"
            ].sum()
        ),
        int(
            executive[
                "total_customers"
            ]
        ),
        "Q26 customers vs Q28 customers",
    ),
    (
        int(
            segments[
                "orders"
            ].sum()
        ),
        int(
            executive[
                "total_orders"
            ]
        ),
        "Q26 orders vs Q28 orders",
    ),
    (
        int(
            channels[
                "sessions"
            ].sum()
        ),
        int(
            executive[
                "total_sessions"
            ]
        ),
        "Q27 sessions vs Q28 sessions",
    ),
]

failures.extend(
    label
    for left, right, label in checks
    if left != right
)

if abs(
    float(
        segments[
            "revenue_usd"
        ].sum()
    )
    - float(
        executive[
            "total_revenue_usd"
        ]
    )
) > 0.05:

    failures.append(
        "Q26 revenue vs Q28 revenue"
    )

buyers = segments[
    segments[
        "customer_segment"
    ]
    .str.casefold()
    .isin(
        {
            "one-time buyer",
            "repeat buyer",
        }
    )
]

if int(
    buyers[
        "customers"
    ].sum()
) != int(
    executive[
        "purchasing_customers"
    ]
):

    failures.append(
        "Q26 buyers vs Q28 purchasing customers"
    )

repeat_rows = segments[
    segments[
        "customer_segment"
    ]
    .str.casefold()
    .eq(
        "repeat buyer"
    )
]

if len(
    repeat_rows
) != 1:

    failures.append(
        "Q26 must contain exactly one Repeat Buyer row"
    )

elif int(
    repeat_rows
    .iloc[0][
        "customers"
    ]
) != int(
    executive[
        "repeat_buyers"
    ]
):

    failures.append(
        "Q26 repeat buyers vs Q28 repeat buyers"
    )

funnel_counts = [
    float(
        funnel[
            "page_view_sessions"
        ]
    ),
    float(
        funnel[
            "add_to_cart_sessions"
        ]
    ),
    float(
        funnel[
            "checkout_sessions"
        ]
    ),
    float(
        funnel[
            "purchase_sessions"
        ]
    ),
]

if any(
    later > earlier
    for earlier, later in zip(
        funnel_counts,
        funnel_counts[1:],
    )
):

    failures.append(
        "Q16 funnel counts increase downstream"
    )

if failures:

    st.error(
        "Cross-query validation failed."
    )

    st.code(
        "; ".join(
            failures
        )
    )

    st.stop()

# ============================================================
# DERIVED METRICS
# ============================================================
FUNNEL_LOSSES = {
    "Page View → Add to Cart":
        100.0
        - float(
            funnel[
                "view_to_cart_pct"
            ]
        ),

    "Add to Cart → Checkout":
        100.0
        - float(
            funnel[
                "cart_to_checkout_pct"
            ]
        ),

    "Checkout → Purchase":
        100.0
        - float(
            funnel[
                "checkout_to_purchase_pct"
            ]
        ),
}

LARGEST_LOSS_STAGE = max(
    FUNNEL_LOSSES,
    key=FUNNEL_LOSSES.get,
)

LARGEST_LOSS_PCT = (
    FUNNEL_LOSSES[
        LARGEST_LOSS_STAGE
    ]
)

CART_TO_CHECKOUT_LOST = int(
    funnel[
        "add_to_cart_sessions"
    ]
    - funnel[
        "checkout_sessions"
    ]
)

REPEAT_ROW = (
    repeat_rows
    .iloc[0]
)

TOTAL_SEGMENT_REVENUE = float(
    segments[
        "revenue_usd"
    ].sum()
)

if TOTAL_SEGMENT_REVENUE <= 0:

    st.error(
        "Customer segment revenue must be greater than zero."
    )

    st.stop()

REPEAT_REVENUE_SHARE = (
    float(
        REPEAT_ROW[
            "revenue_usd"
        ]
    )
    / TOTAL_SEGMENT_REVENUE
    * 100.0
)

REPEAT_CUSTOMER_SHARE = (
    float(
        executive[
            "repeat_buyers"
        ]
    )
    / float(
        executive[
            "total_customers"
        ]
    )
    * 100.0
)

BEST_CHANNEL = (
    channels
    .sort_values(
        [
            "conversion_rate_pct",
            "sessions",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .iloc[0]
)

LARGEST_TRAFFIC = (
    channels
    .sort_values(
        "sessions",
        ascending=False,
    )
    .iloc[0]
)

CHANNEL_SPREAD = (
    float(
        channels[
            "conversion_rate_pct"
        ].max()
    )
    - float(
        channels[
            "conversion_rate_pct"
        ].min()
    )
)

# ============================================================
# ROUTING — FIXED HTML SIDEBAR, NEVER COLLAPSES
# ============================================================
PAGE_META = {
    "executive":
        (
            "01",
            "Executive Overview",
        ),

    "journey":
        (
            "02",
            "Customer Journey",
        ),

    "products":
        (
            "03",
            "Product Intelligence",
        ),

    "customers":
        (
            "04",
            "Customer & Channels",
        ),

    "graph":
        (
            "05",
            "Graph Explorer",
        ),

    "methodology":
        (
            "06",
            "Methodology",
        ),
}


def get_page() -> str:

    try:
        raw = st.query_params.get(
            "page",
            "executive",
        )

    except AttributeError:

        raw = (
            st.experimental_get_query_params()
            .get(
                "page",
                [
                    "executive"
                ],
            )
        )

    if isinstance(
        raw,
        list,
    ):

        raw = (
            raw[0]
            if raw
            else "executive"
        )

    raw = (
        str(raw)
        .strip()
        .lower()
    )

    return (
        raw
        if raw in PAGE_META
        else "executive"
    )


ACTIVE_PAGE = (
    get_page()
)

# ============================================================
# DARK BI THEME
# ============================================================
render_html(
    """
    <style>

    :root{
        --bg:#070C11;
        --sidebar:#05090D;
        --panel:#101820;
        --panel2:#0C141B;
        --border:#21323D;
        --text:#F4F7F9;
        --muted:#93A4AF;
        --teal:#2AB7A9;
        --blue:#5798C8;
        --amber:#E8A84E;
    }

    html,
    body,
    .stApp{
        background:#070C11!important;
        color:var(--text);

        font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
    }

    #MainMenu,
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stAppDeployButton"],
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"]{
        display:none!important;
        visibility:hidden!important;
    }

    [data-testid="stHeader"]{
        background:
            transparent!important;
    }

    .block-container{
        max-width:1680px!important;

        padding:
            1.2rem
            2.2rem
            3rem
            300px!important;
    }

    .fixed-sidebar{
        position:fixed;

        z-index:999999;

        top:0;
        left:0;
        bottom:0;

        width:265px;

        padding:
            1.65rem
            1.1rem
            1.4rem;

        overflow-y:auto;

        background:
            linear-gradient(
                180deg,
                #06101A 0%,
                #05090D 100%
            );

        border-right:
            1px solid #1A2B35;

        box-shadow:
            12px 0 36px
            rgba(0,0,0,.16);
    }

    .nav-mark{
        width:42px;
        height:42px;

        display:flex;

        align-items:center;
        justify-content:center;

        border-radius:10px;

        margin-bottom:.9rem;

        color:var(--teal);

        background:#10212A;

        border:
            1px solid #24404B;

        font-weight:900;
    }

    .nav-kicker{
        color:#5E7D8B;

        font-size:.58rem;

        font-weight:900;

        letter-spacing:.11rem;

        text-transform:uppercase;

        margin-bottom:.35rem;
    }

    .nav-title{
        color:#F4F7F9;

        font-size:1.03rem;

        line-height:1.25;

        font-weight:830;

        margin-bottom:.45rem;
    }

    .nav-copy{
        color:#71838F;

        font-size:.69rem;

        line-height:1.5;

        margin-bottom:1.15rem;
    }

    .nav-section{
        color:#526D7B;

        font-size:.57rem;

        font-weight:900;

        letter-spacing:.1rem;

        text-transform:uppercase;

        padding-top:.85rem;

        margin-bottom:.4rem;

        border-top:
            1px solid #14222B;
    }

    .nav-link{
        display:flex;

        align-items:center;

        gap:.58rem;

        padding:
            .67rem
            .72rem;

        margin-bottom:.22rem;

        border-radius:8px;

        border:
            1px solid transparent;

        color:
            #91A2AC!important;

        text-decoration:
            none!important;

        font-size:.76rem;

        font-weight:650;

        transition:.15s ease;
    }

    .nav-link:hover{
        color:#FFF!important;

        background:#0D1820;

        border-color:#1E333E;
    }

    .nav-link.active{
        color:#FFF!important;

        background:#11212A;

        border-color:#28434F;

        box-shadow:
            inset 3px 0 0
            var(--teal);

        font-weight:780;
    }

    .nav-num{
        width:20px;

        color:#5E8394;

        font-size:.59rem;

        font-weight:900;
    }

    .nav-meta{
        margin-top:1rem;

        padding:.82rem;

        border-radius:9px;

        color:#71848F;

        background:#0B141B;

        border:
            1px solid #172A34;

        font-size:.66rem;

        line-height:1.55;
    }

    .nav-meta strong{
        color:#D9E3E7;
    }

    .hero{
        display:flex;

        justify-content:
            space-between;

        align-items:
            flex-end;

        gap:1rem;

        padding:
            1.05rem
            1.15rem;

        margin-bottom:1rem;

        border-radius:12px;

        background:
            linear-gradient(
                110deg,
                #101A22 0%,
                #10202A 55%,
                #12303A 100%
            );

        border:
            1px solid #243640;

        box-shadow:
            0 14px 40px
            rgba(0,0,0,.12);
    }

    .hero-kicker,
    .section-number,
    .takeaway-label,
    .explain-label,
    .signal-label{
        color:var(--teal);

        font-size:.61rem;

        font-weight:900;

        letter-spacing:.09rem;

        text-transform:uppercase;
    }

    .hero-title{
        color:#F5F8FA;

        font-size:1.9rem;

        line-height:1.14;

        letter-spacing:-.03rem;

        font-weight:850;

        margin:
            .22rem
            0
            .3rem;
    }

    .hero-copy{
        color:#A0AFB8;

        font-size:.82rem;

        line-height:1.5;

        max-width:900px;
    }

    .status-chip{
        display:inline-flex;

        align-items:center;

        gap:.42rem;

        padding:
            .4rem
            .66rem;

        border-radius:999px;

        color:#BDD0D8;

        background:
            rgba(
                7,
                12,
                17,
                .42
            );

        border:
            1px solid #31505C;

        font-size:.68rem;

        font-weight:750;

        white-space:nowrap;
    }

    .status-dot{
        width:7px;
        height:7px;

        border-radius:50%;

        background:
            var(--teal);
    }

    .kpi{
        min-height:116px;

        padding:
            .92rem
            .95rem;

        border-radius:10px;

        background:
            var(--panel);

        border:
            1px solid
            var(--border);

        box-shadow:
            0 8px 24px
            rgba(0,0,0,.09);
    }

    .kpi-label{
        color:#81939E;

        font-size:.6rem;

        font-weight:850;

        letter-spacing:.055rem;

        text-transform:uppercase;

        margin-bottom:.4rem;
    }

    .kpi-value{
        color:#F5F8FA;

        font-size:1.48rem;

        line-height:1.05;

        font-weight:850;

        margin-bottom:.34rem;
    }

    .kpi-note{
        color:#71838E;

        font-size:.66rem;

        line-height:1.4;
    }

    .signal-grid{
        display:grid;

        grid-template-columns:
            repeat(
                3,
                1fr
            );

        gap:.75rem;

        margin-top:.85rem;
    }

    .signal-card{
        padding:
            .84rem
            .92rem;

        border-radius:9px;

        background:#0D161D;

        border:
            1px solid #20313B;
    }

    .signal-card.alert{
        border-top:
            3px solid
            var(--amber);
    }

    .signal-card.positive{
        border-top:
            3px solid
            var(--teal);
    }

    .signal-card.context{
        border-top:
            3px solid
            var(--blue);
    }

    .signal-value{
        color:#F3F7F9;

        font-size:1.08rem;

        font-weight:850;

        margin:
            .2rem
            0;
    }

    .signal-copy{
        color:#8FA0AA;

        font-size:.68rem;

        line-height:1.42;
    }

    .section-header{
        margin-top:1.45rem;

        margin-bottom:.6rem;
    }

    .section-title{
        color:#F2F6F8;

        font-size:1.3rem;

        font-weight:830;

        margin:
            .2rem
            0;
    }

    .section-copy{
        color:#899AA5;

        font-size:.8rem;

        line-height:1.5;

        max-width:1000px;
    }

    .source-note{
        margin:
            .38rem
            0
            0
            .05rem;

        color:#647985;

        font-size:.63rem;
    }

    .explain-grid{
        display:grid;

        grid-template-columns:
            1fr
            1fr;

        gap:.8rem;

        margin-top:.78rem;
    }

    .explain-card{
        padding:
            1rem
            1.05rem;

        border-radius:9px;

        background:
            var(--panel2);

        border:
            1px solid #20313B;
    }

    .explain-card.action{
        border-left:
            3px solid
            var(--teal);
    }

    .explain-title{
        color:#F1F5F7;

        font-size:1rem;

        font-weight:830;

        margin:
            .3rem
            0;
    }

    .explain-copy{
        color:#A3B1BA;

        font-size:.82rem;

        line-height:1.58;
    }

    .explain-copy strong{
        color:#FFF;
    }

    .takeaway{
        margin-top:1.1rem;

        padding:
            .95rem
            1rem;

        border-radius:10px;

        background:
            linear-gradient(
                90deg,
                rgba(
                    42,
                    183,
                    169,
                    .11
                ),
                rgba(
                    87,
                    152,
                    200,
                    .05
                )
            );

        border:
            1px solid #23414A;

        border-left:
            4px solid
            var(--teal);
    }

    .takeaway-copy{
        color:#CBD6DC;

        font-size:.82rem;

        line-height:1.58;

        margin-top:.28rem;
    }

    .takeaway-copy strong{
        color:#FFF;
    }

    .model-card{
        padding:
            1rem
            1.05rem;

        border:
            1px solid #20313B;

        border-radius:10px;

        background:#0C141A;
    }

    .model-card pre{
        margin:0;

        color:#BDD0D9;

        font-size:.78rem;

        line-height:1.8;

        white-space:pre-wrap;

        font-family:
            "Cascadia Code",
            Consolas,
            monospace;
    }

    button[data-baseweb="tab"]{
        color:
            #93A4AE!important;

        font-weight:
            700!important;
    }

    button[data-baseweb="tab"][aria-selected="true"]{
        color:
            #FFF!important;
    }

    div[data-baseweb="tab-highlight"]{
        background-color:
            var(--teal)!important;
    }

    [data-testid="stImage"] img{
        border-radius:8px;
    }

    .footer{
        display:flex;

        justify-content:
            space-between;

        margin-top:1.55rem;

        padding-top:.75rem;

        border-top:
            1px solid #1D2A33;

        color:#627682;

        font-size:.63rem;
    }

    @media(max-width:1000px){

        .fixed-sidebar{
            position:relative;

            width:auto;

            height:auto;

            margin:
                -1rem
                -1rem
                1rem;
        }

        .block-container{
            padding-left:
                1rem!important;

            padding-right:
                1rem!important;
        }

        .signal-grid,
        .explain-grid{
            grid-template-columns:
                1fr;
        }

        .hero{
            display:block;
        }

        .status-chip{
            margin-top:.7rem;
        }
    }

    </style>
    """
)

# Fixed sidebar links: always visible, no Streamlit collapse state.
nav_links = []

for key, (
    number,
    label,
) in PAGE_META.items():

    active = (
        " active"
        if key == ACTIVE_PAGE
        else ""
    )

    nav_links.append(
        f'<a class="nav-link{active}" '
        f'href="?page={key}" '
        f'target="_self">'
        f'<span class="nav-num">'
        f'{escape(number)}'
        f'</span>'
        f'<span>'
        f'{escape(label)}'
        f'</span>'
        f'</a>'
    )

render_html(
    f"""
    <aside class="fixed-sidebar">

        <div class="nav-mark">
            ◈
        </div>

        <div class="nav-kicker">
            Analytics Portfolio
        </div>

        <div class="nav-title">
            Customer Journey &amp;<br>
            Product Network Intelligence
        </div>

        <div class="nav-copy">
            Neo4j graph analytics translated into business intelligence,
            customer behaviour and product-network decisions.
        </div>

        <div class="nav-section">
            Report navigation
        </div>

        {''.join(nav_links)}

        <div class="nav-meta">

            <strong>
                Validated scale
            </strong>

            <br>

            {fmt_num(executive["total_customers"])}
            customers

            <br>

            {fmt_num(executive["total_sessions"])}
            sessions

            <br>

            {fmt_num(executive["total_orders"])}
            orders

            <br><br>

            <strong>
                Technology
            </strong>

            <br>

            Neo4j · Cypher

            <br>

            Python · Pandas

            <br>

            Streamlit

            <br><br>

            <strong>
                Analytics
            </strong>

            <br>

            13 validated Q16–Q28 outputs

        </div>

    </aside>
    """
)

# ============================================================
# SHARED UI COMPONENTS
# ============================================================
def report_header(
    kicker: str,
    title: str,
    subtitle: str,
) -> None:

    render_html(
        f"""
        <div class="hero">

            <div>

                <div class="hero-kicker">
                    {escape(kicker)}
                </div>

                <div class="hero-title">
                    {escape(title)}
                </div>

                <div class="hero-copy">
                    {escape(subtitle)}
                </div>

            </div>

            <div class="status-chip">

                <span class="status-dot">
                </span>

                Ruturaj Mokashi · Validated Neo4j Analytics

            </div>

        </div>
        """
    )


def section_header(
    number: str,
    title: str,
    copy: str,
) -> None:

    render_html(
        f"""
        <div class="section-header">

            <div class="section-number">
                {escape(number)}
            </div>

            <div class="section-title">
                {escape(title)}
            </div>

            <div class="section-copy">
                {escape(copy)}
            </div>

        </div>
        """
    )


def explain(
    finding_title: str,
    finding_copy: str,
    action_title: str,
    action_copy: str,
) -> None:

    render_html(
        f"""
        <div class="explain-grid">

            <div class="explain-card">

                <div class="explain-label">
                    Key finding
                </div>

                <div class="explain-title">
                    {escape(finding_title)}
                </div>

                <div class="explain-copy">
                    {finding_copy}
                </div>

            </div>

            <div class="explain-card action">

                <div class="explain-label">
                    Business interpretation
                </div>

                <div class="explain-title">
                    {escape(action_title)}
                </div>

                <div class="explain-copy">
                    {action_copy}
                </div>

            </div>

        </div>
        """
    )


def show_export(
    q: int,
    number: str,
    title: str,
    subtitle: str,
    finding_title: str,
    finding_copy: str,
    action_title: str,
    action_copy: str,
) -> None:

    section_header(
        number,
        title,
        subtitle,
    )

    st.image(
        str(
            PNG[q]
        ),
        width="stretch",
    )

    render_html(
        f"""
        <div class="source-note">
            Source: Neo4j analytical export Q{q}
            · synthetic e-commerce dataset
        </div>
        """
    )

    explain(
        finding_title,
        finding_copy,
        action_title,
        action_copy,
    )

# ============================================================
# NATIVE EXECUTIVE VISUALS
# ============================================================
def native_funnel() -> None:

    stages = [
        "Page View",
        "Add to Cart",
        "Checkout",
        "Purchase",
    ]

    values = [
        int(
            funnel[
                "page_view_sessions"
            ]
        ),
        int(
            funnel[
                "add_to_cart_sessions"
            ]
        ),
        int(
            funnel[
                "checkout_sessions"
            ]
        ),
        int(
            funnel[
                "purchase_sessions"
            ]
        ),
    ]

    rates = [
        None,
        float(
            funnel[
                "view_to_cart_pct"
            ]
        ),
        float(
            funnel[
                "cart_to_checkout_pct"
            ]
        ),
        float(
            funnel[
                "checkout_to_purchase_pct"
            ]
        ),
    ]

    colors = [
        "#29435C",
        "#4B76A5",
        "#6EA4C8",
        "#2AB7A9",
    ]

    fig, ax = plt.subplots(
        figsize=(
            14,
            5.5,
        )
    )

    fig.patch.set_facecolor(
        "#101820"
    )

    ax.set_facecolor(
        "#101820"
    )

    bars = ax.barh(
        stages,
        values,
        color=colors,
        height=0.56,
    )

    ax.invert_yaxis()

    maximum = max(
        values
    )

    for i, (
        bar,
        value,
    ) in enumerate(
        zip(
            bars,
            values,
        )
    ):

        label = (
            f"{value:,}"
        )

        if rates[i] is not None:

            label += (
                f"   |   "
                f"{rates[i]:.2f}% "
                f"from prior stage"
            )

        ax.text(
            value
            + maximum
            * 0.012,

            bar.get_y()
            + bar.get_height()
            / 2,

            label,

            va="center",

            color="#F4F7F9",

            fontsize=12,

            fontweight="bold",
        )

    cart_value = int(
        funnel[
            "add_to_cart_sessions"
        ]
    )

    checkout_value = int(
        funnel[
            "checkout_sessions"
        ]
    )

    y = 1.50

    ax.annotate(
        "",
        xy=(
            checkout_value,
            y,
        ),
        xytext=(
            cart_value,
            y,
        ),
        arrowprops={
            "arrowstyle":
                "<->",

            "color":
                "#E8A84E",

            "lw":
                2.2,
        },
    )

    ax.text(
        (
            cart_value
            + checkout_value
        )
        / 2,

        y
        - 0.10,

        (
            f"−{CART_TO_CHECKOUT_LOST:,} sessions"
            f"  |  "
            f"−{LARGEST_LOSS_PCT:.2f}%"
        ),

        ha="center",

        va="bottom",

        color="#E8A84E",

        fontsize=11,

        fontweight="bold",

        bbox={
            "boxstyle":
                "round,pad=0.28",

            "facecolor":
                "#101820",

            "edgecolor":
                "#E8A84E",

            "linewidth":
                0.8,

            "alpha":
                0.95,
        },
    )

    ax.set_xlim(
        0,
        maximum
        * 1.34,
    )

    ax.set_xlabel(
        "Sessions",
        color="#9FB0BA",
        fontsize=11,
        labelpad=9,
    )

    ax.tick_params(
        axis="x",
        colors="#81939E",
        labelsize=10,
    )

    ax.tick_params(
        axis="y",
        colors="#F1F5F7",
        labelsize=12,
    )

    ax.xaxis.grid(
        True,
        color="#22313B",
        linewidth=0.8,
    )

    ax.set_axisbelow(
        True
    )

    for spine in ax.spines.values():
        spine.set_visible(
            False
        )

    plt.tight_layout()

    st.pyplot(
        fig,
        width="stretch",
    )

    plt.close(
        fig
    )

    render_html(
        """
        <div class="source-note">
            Source: Neo4j analytical export Q16
            · synthetic e-commerce dataset
        </div>
        """
    )


def native_customer_value() -> None:

    plot_df = (
        segments
        .sort_values(
            "segment_order"
        )
        .iloc[::-1]
        .copy()
    )

    palette = {
        "No Purchase":
            "#596C79",

        "One-Time Buyer":
            "#5798C8",

        "Repeat Buyer":
            "#2AB7A9",
    }

    fig, ax = plt.subplots(
        figsize=(
            14,
            4.8,
        )
    )

    fig.patch.set_facecolor(
        "#101820"
    )

    ax.set_facecolor(
        "#101820"
    )

    bars = ax.barh(
        plot_df[
            "customer_segment"
        ],

        plot_df[
            "revenue_usd"
        ],

        color=[
            palette.get(
                x,
                "#5798C8",
            )
            for x in plot_df[
                "customer_segment"
            ]
        ],

        height=0.54,
    )

    total = float(
        plot_df[
            "revenue_usd"
        ].sum()
    )

    maximum = max(
        float(
            plot_df[
                "revenue_usd"
            ].max()
        ),
        1.0,
    )

    for bar, (
        _,
        row,
    ) in zip(
        bars,
        plot_df.iterrows(),
    ):

        revenue = float(
            row[
                "revenue_usd"
            ]
        )

        share = (
            0.0
            if total == 0
            else revenue
            / total
            * 100.0
        )

        ax.text(
            revenue
            + maximum
            * 0.012,

            bar.get_y()
            + bar.get_height()
            / 2,

            (
                f"${revenue:,.0f}"
                f"   |   "
                f"{share:.1f}% revenue"
                f"   |   "
                f"{int(row['customers']):,} customers"
            ),

            va="center",

            color="#F4F7F9",

            fontsize=12,

            fontweight="bold",
        )

    ax.set_xlim(
        0,
        maximum
        * 1.46,
    )

    ax.set_xlabel(
        "Revenue (USD)",
        color="#9FB0BA",
        fontsize=11,
        labelpad=9,
    )

    ax.tick_params(
        axis="x",
        colors="#81939E",
        labelsize=10,
    )

    ax.tick_params(
        axis="y",
        colors="#F1F5F7",
        labelsize=12,
    )

    ax.xaxis.grid(
        True,
        color="#22313B",
        linewidth=0.8,
    )

    ax.set_axisbelow(
        True
    )

    for spine in ax.spines.values():
        spine.set_visible(
            False
        )

    plt.tight_layout()

    st.pyplot(
        fig,
        width="stretch",
    )

    plt.close(
        fig
    )

    render_html(
        """
        <div class="source-note">
            Source: Neo4j analytical export Q26
            · synthetic e-commerce dataset
        </div>
        """
    )


def native_channel_heatmap() -> None:

    devices = [
        "desktop",
        "mobile",
        "tablet",
    ]

    sources = [
        "direct",
        "email",
        "organic",
        "paid",
        "referral",
        "social",
    ]

    rates = (
        channels
        .pivot(
            index="device",
            columns="source",
            values="conversion_rate_pct",
        )
        .reindex(
            index=devices,
            columns=sources,
        )
    )

    volumes = (
        channels
        .pivot(
            index="device",
            columns="source",
            values="sessions",
        )
        .reindex(
            index=devices,
            columns=sources,
        )
    )

    if (
        rates.isnull().any().any()
        or volumes.isnull().any().any()
    ):

        st.error(
            "Device/source matrix is incomplete."
        )

        return

    cmap = (
        LinearSegmentedColormap
        .from_list(
            "cjpn",
            [
                "#182B38",
                "#214C63",
                "#237476",
                "#2A9D8F",
            ],
        )
    )

    fig, ax = plt.subplots(
        figsize=(
            14,
            5.6,
        )
    )

    fig.patch.set_facecolor(
        "#101820"
    )

    ax.set_facecolor(
        "#101820"
    )

    image = ax.imshow(
        rates.values,
        cmap=cmap,
        aspect="auto",
        vmin=float(
            rates
            .min()
            .min()
        ),
        vmax=float(
            rates
            .max()
            .max()
        ),
    )

    ax.set_xticks(
        np.arange(
            len(
                sources
            )
        )
    )

    ax.set_xticklabels(
        [
            x.title()
            for x in sources
        ],
        color="#F1F5F7",
        fontsize=11,
    )

    ax.set_yticks(
        np.arange(
            len(
                devices
            )
        )
    )

    ax.set_yticklabels(
        [
            x.title()
            for x in devices
        ],
        color="#F1F5F7",
        fontsize=11,
    )

    for r in range(
        len(
            devices
        )
    ):

        for c in range(
            len(
                sources
            )
        ):

            ax.text(
                c,
                r,

                (
                    f"{float(rates.iloc[r, c]):.2f}%"
                    f"\n"
                    f"{int(volumes.iloc[r, c]):,} sessions"
                ),

                ha="center",

                va="center",

                color="#FFFFFF",

                fontsize=11,

                fontweight="bold",
            )

    colorbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.025,
        pad=0.025,
    )

    colorbar.set_label(
        "Conversion Rate (%)",
        color="#9FB0BA",
        fontsize=10,
    )

    colorbar.ax.tick_params(
        colors="#9FB0BA",
        labelsize=9,
    )

    colorbar.outline.set_visible(
        False
    )

    for spine in ax.spines.values():
        spine.set_visible(
            False
        )

    plt.tight_layout()

    st.pyplot(
        fig,
        width="stretch",
    )

    plt.close(
        fig
    )

    render_html(
        """
        <div class="source-note">
            Source: Neo4j analytical export Q27
            · synthetic e-commerce dataset
        </div>
        """
    )

# ============================================================
# INTERACTIVE GRAPH EXPLORER
# ============================================================
def build_graph_data() -> dict | None:

    df = DATA[22].copy()

    left = find_col(
        df,
        "product_a_name",
        "product_1_name",
        "product_name_a",
        "product_a",
        "product_1",
        "product_a_id",
        "product_1_id",
    )

    right = find_col(
        df,
        "product_b_name",
        "product_2_name",
        "product_name_b",
        "product_b",
        "product_2",
        "product_b_id",
        "product_2_id",
    )

    weight = find_col(
        df,
        "shared_orders",
        "copurchase_orders",
        "co_purchase_orders",
        "orders_together",
        "copurchase_count",
        "co_purchase_count",
    )

    cat_left = find_col(
        df,
        "category_a",
        "product_a_category",
        "category_1",
    )

    cat_right = find_col(
        df,
        "category_b",
        "product_b_category",
        "category_2",
    )

    if (
        not left
        or not right
        or not weight
    ):

        return None

    df[
        weight
    ] = pd.to_numeric(
        df[
            weight
        ],
        errors="coerce",
    )

    work = (
        df
        .dropna(
            subset=[
                left,
                right,
                weight,
            ]
        )
        .loc[
            lambda x:
                x[
                    weight
                ]
                > 0
        ]
        .sort_values(
            weight,
            ascending=False,
        )
        .head(
            10
        )
    )

    if work.empty:
        return None

    degree = {}
    node_category = {}
    raw_links = []

    for _, row in work.iterrows():

        a = str(
            row[
                left
            ]
        ).strip()

        b = str(
            row[
                right
            ]
        ).strip()

        w = float(
            row[
                weight
            ]
        )

        ca = (
            str(
                row[
                    cat_left
                ]
            ).strip()
            if (
                cat_left
                and pd.notna(
                    row[
                        cat_left
                    ]
                )
            )
            else "Product"
        )

        cb = (
            str(
                row[
                    cat_right
                ]
            ).strip()
            if (
                cat_right
                and pd.notna(
                    row[
                        cat_right
                    ]
                )
            )
            else "Product"
        )

        degree[a] = (
            degree.get(
                a,
                0.0,
            )
            + w
        )

        degree[b] = (
            degree.get(
                b,
                0.0,
            )
            + w
        )

        node_category[a] = ca
        node_category[b] = cb

        raw_links.append(
            (
                a,
                b,
                w,
            )
        )

    categories = sorted(
        set(
            node_category.values()
        )
    )

    category_index = {
        name:
            i
        for i, name in enumerate(
            categories
        )
    }

    palette = [
        "#2AB7A9",
        "#5798C8",
        "#78B7D8",
        "#A9C6D8",
        "#6C8FA3",
        "#3F728D",
        "#8ECAC2",
        "#4D8EA8",
    ]

    category_specs = [
        {
            "name":
                name,

            "itemStyle":
                {
                    "color":
                        palette[
                            i
                            % len(
                                palette
                            )
                        ]
                },
        }
        for i, name in enumerate(
            categories
        )
    ]

    max_degree = max(
        degree.values()
    )

    nodes = [
        {
            "name":
                name,

            "value":
                round(
                    score,
                    2,
                ),

            "category":
                category_index[
                    node_category[
                        name
                    ]
                ],

            "symbolSize":
                28
                + score
                / max_degree
                * 34,
        }
        for name, score in degree.items()
    ]

    links = [
        {
            "source":
                a,

            "target":
                b,

            "value":
                int(w),

            "lineStyle":
                {
                    "width":
                        1.5
                        + min(
                            w,
                            6,
                        )
                        * 0.6,

                    "opacity":
                        0.72,
                },
        }
        for a, b, w in raw_links
    ]

    return {
        "nodes":
            nodes,

        "links":
            links,

        "categories":
            category_specs,
    }


def interactive_graph() -> bool:

    if not hasattr(
        st,
        "echarts_chart",
    ):
        return False

    graph = (
        build_graph_data()
    )

    if not graph:
        return False

    spec = {
        "backgroundColor":
            "transparent",

        "tooltip":
            {
                "trigger":
                    "item"
            },

        "legend":
            {
                "top":
                    8,

                "textStyle":
                    {
                        "color":
                            "#A8B6BE",

                        "fontSize":
                            11,
                    },
            },

        "series":
            [
                {
                    "name":
                        "Co-purchase relationships",

                    "type":
                        "graph",

                    "layout":
                        "force",

                    "data":
                        graph[
                            "nodes"
                        ],

                    "links":
                        graph[
                            "links"
                        ],

                    "categories":
                        graph[
                            "categories"
                        ],

                    "roam":
                        True,

                    "draggable":
                        True,

                    "cursor":
                        "grab",

                    "label":
                        {
                            "show":
                                True,

                            "position":
                                "right",

                            "color":
                                "#EDF4F7",

                            "fontSize":
                                10,
                        },

                    "labelLayout":
                        {
                            "hideOverlap":
                                True
                        },

                    "edgeLabel":
                        {
                            "show":
                                True,

                            "formatter":
                                "{c}",

                            "color":
                                "#91A4AF",

                            "fontSize":
                                10,
                        },

                    "lineStyle":
                        {
                            "color":
                                "source",

                            "curveness":
                                0.08,

                            "opacity":
                                0.68,
                        },

                    "emphasis":
                        {
                            "focus":
                                "adjacency",

                            "lineStyle":
                                {
                                    "width":
                                        4,

                                    "opacity":
                                        1,
                                },
                        },

                    "force":
                        {
                            "repulsion":
                                380,

                            "edgeLength":
                                [
                                    140,
                                    225,
                                ],

                            "gravity":
                                0.055,
                        },
                }
            ],

        "aria":
            {
                "enabled":
                    True
            },
    }

    try:

        st.echarts_chart(
            spec,
            width="stretch",
            height=700,
            theme=None,
            key="product_network",
            renderer="svg",
        )

        render_html(
            """
            <div class="source-note">
                Interactive Neo4j Q22 network
                · drag nodes · zoom · pan · hover
            </div>
            """
        )

        return True

    except Exception:
        return False

# ============================================================
# REPORT PAGES
# ============================================================
def executive_page() -> None:

    report_header(
        "Executive Overview",

        "Customer Journey & Product Network Intelligence",

        (
            "Commercial performance, customer behaviour "
            "and graph-derived decision signals."
        ),
    )

    kpis = [
        (
            "Revenue",

            # CHANGE 1:
            # Compact executive display instead of $4,493,217.47
            f"${float(executive['total_revenue_usd']) / 1_000_000:.2f}M",

            "Recorded commerce revenue",
        ),
        (
            "Orders",
            fmt_num(
                executive[
                    "total_orders"
                ]
            ),
            "Completed transactions",
        ),
        (
            "Sessions",
            fmt_num(
                executive[
                    "total_sessions"
                ]
            ),
            "Observed sessions",
        ),
        (
            "Conversion",
            fmt_pct(
                executive[
                    "conversion_rate_pct"
                ]
            ),
            "Sessions ending in purchase",
        ),
        (
            "Avg. Order Value",
            fmt_money(
                executive[
                    "avg_order_value_usd"
                ]
            ),
            "Revenue per order",
        ),
        (
            "Repeat Buyers",
            fmt_pct(
                executive[
                    "repeat_buyer_pct_of_buyers"
                ]
            ),
            "Share of purchasing customers",
        ),
    ]

    for col, (
        label,
        value,
        note,
    ) in zip(
        st.columns(
            6,
            gap="medium",
        ),
        kpis,
    ):

        with col:

            render_html(
                f"""
                <div class="kpi">

                    <div class="kpi-label">
                        {escape(label)}
                    </div>

                    <div class="kpi-value">
                        {escape(value)}
                    </div>

                    <div class="kpi-note">
                        {escape(note)}
                    </div>

                </div>
                """
            )

    render_html(
        f"""
        <div class="signal-grid">

            <div class="signal-card alert">

                <div class="signal-label">
                    Largest funnel loss
                </div>

                <div class="signal-value">
                    {LARGEST_LOSS_PCT:.2f}%
                </div>

                <div class="signal-copy">
                    {escape(LARGEST_LOSS_STAGE)}
                </div>

            </div>

            <div class="signal-card positive">

                <div class="signal-label">
                    Repeat-buyer revenue
                </div>

                <div class="signal-value">
                    {REPEAT_REVENUE_SHARE:.1f}%
                </div>

                <div class="signal-copy">
                    Share of recorded revenue generated by repeat buyers.
                </div>

            </div>

            <div class="signal-card context">

                <div class="signal-label">
                    Purchasing customers
                </div>

                <div class="signal-value">
                    {float(executive["purchasing_customer_pct"]):.2f}%
                </div>

                <div class="signal-copy">
                    {fmt_num(executive["purchasing_customers"])}
                    of
                    {fmt_num(executive["total_customers"])}
                    customers purchased.
                </div>

            </div>

        </div>
        """
    )

    section_header(
        "Priority Signal",

        "Where the Customer Journey Breaks",

        (
            "Stage volume and stage-to-stage conversion "
            "across all observed sessions."
        ),
    )

    native_funnel()

    explain(
        f"{LARGEST_LOSS_STAGE} is the main leakage point",

        (
            f"The largest proportional loss is "
            f"<strong>{LARGEST_LOSS_PCT:.2f}%</strong>, "
            f"equal to "
            f"<strong>{CART_TO_CHECKOUT_LOST:,}</strong> "
            f"sessions between Add to Cart and Checkout. "
            f"Overall conversion is "
            f"<strong>{float(executive['conversion_rate_pct']):.2f}%</strong>."
        ),

        "Prioritise the largest friction point before buying more traffic",

        (
            "Diagnose cart-to-checkout friction first, "
            "then re-measure downstream conversion before "
            "shifting additional acquisition spend."
        ),
    )

    render_html(
        """
        <div class="takeaway">

            <div class="takeaway-label">
                Executive decision
            </div>

            <div class="takeaway-copy">

                Focus first on

                <strong>
                    checkout initiation
                </strong>,

                then protect

                <strong>
                    repeat purchasing
                </strong>.

                Channel performance is relatively tight,
                so acquisition decisions should balance
                conversion rate with

                <strong>
                    traffic scale and commercial value
                </strong>.

            </div>

        </div>
        """
    )


def customer_journey_page() -> None:

    report_header(
        "Customer Journey",

        "Conversion & Behaviour Intelligence",

        (
            "Where customers leave, how long conversion takes "
            "and which event sequences lead to purchase."
        ),
    )

    tabs = st.tabs(
        [
            "Funnel",
            "Abandonment",
            "Journey Length",
            "Time to Purchase",
            "Purchase Paths",
        ]
    )

    specs = [
        (
            16,
            "01 · Funnel",
            "Customer Conversion Funnel",
            "Stage volume and conversion through the purchase journey.",
            f"{LARGEST_LOSS_STAGE} has the largest proportional loss",
            (
                f"The largest stage loss is "
                f"<strong>{LARGEST_LOSS_PCT:.2f}%</strong>; "
                f"overall conversion is "
                f"<strong>{float(executive['conversion_rate_pct']):.2f}%</strong>."
            ),
            "Use the funnel as an optimisation priority map",
            "Fix the largest friction point first, then re-measure downstream conversion.",
        ),
        (
            17,
            "02 · Abandonment",
            "Where Customers Leave the Journey",
            "Sessions are separated into mutually exclusive final outcomes.",
            "Abandonment differs by intent stage",
            (
                "Browse-only, cart-abandonment and checkout-abandonment "
                "sessions represent different behavioural states."
            ),
            "Use stage-specific recovery tactics",
            (
                "Discovery, cart recovery and checkout completion require "
                "different interventions and messaging."
            ),
        ),
        (
            18,
            "03 · Journey Length",
            "Conversion Journey Length",
            "Number of customer events occurring before a completed purchase.",
            "Successful journeys require multiple interactions",
            (
                "Read average, median and range together; one mean does not "
                "describe the full customer journey pattern."
            ),
            "Design for non-linear exploration",
            (
                "Preserve cart state and navigation context while customers "
                "continue exploring products."
            ),
        ),
        (
            19,
            "04 · Conversion Time",
            "Time to Purchase",
            "Elapsed time from session start to the purchase event.",
            "Purchase decisions are not always immediate",
            (
                "Average, median and observed range together show the spread "
                "of conversion time."
            ),
            "Support longer decision windows",
            (
                "Persistent carts and consistent product context reduce friction "
                "when customers take longer to purchase."
            ),
        ),
        (
            20,
            "05 · Journey Paths",
            "Most Common Purchase Journeys",
            "Neo4j NEXT relationships reconstruct converted event sequences.",
            "Converted journeys follow multiple paths",
            (
                "The ranked sequences show that purchase behaviour is not "
                "limited to one idealised linear path."
            ),
            "Support browsing after cart",
            (
                "Keep carts persistent and use continued exploration as a "
                "relevant cross-sell opportunity."
            ),
        ),
    ]

    for tab, spec in zip(
        tabs,
        specs,
    ):

        with tab:
            show_export(
                *spec
            )


def product_intelligence_page() -> None:

    report_header(
        "Product Intelligence",

        "Product Opportunity & Basket Intelligence",

        (
            "Where product interest fails to convert and which relationships "
            "may support merchandising or cross-sell."
        ),
    )

    tabs = st.tabs(
        [
            "Weak Follow-Through",
            "Affinity",
            "Cross-Sell",
            "Category Matrix",
        ]
    )

    specs = [
        (
            21,
            "01 · Product Follow-Through",
            "High-Interest Products With Weak Purchase Follow-Through",
            "Products ranked by viewing sessions that did not result in purchase.",
            "The ranking highlights missed-volume products",
            (
                "Large missed volume means strong interest without equivalent "
                "purchase follow-through; it does not automatically mean the "
                "lowest conversion rate."
            ),
            "Investigate product-level friction before discounting",
            (
                "Check availability, pricing, product-detail quality, reviews "
                "and recommendation placement first."
            ),
        ),
        (
            23,
            "02 · Affinity",
            "Product Affinity: Lift vs. Evidence Base",
            (
                "Lift shows how much more often a product pair co-occurs "
                "than random expectation."
            ),
            "Lift must be read with evidence volume",
            (
                "A visually large lift can be created by sparse shared-order "
                "evidence, so support and confidence remain essential."
            ),
            "Use affinity as a hypothesis signal",
            (
                "Do not turn a high-lift pair into a recommendation rule "
                "without sufficient support."
            ),
        ),
        (
            24,
            "03 · Cross-Sell",
            "Cross-Sell Opportunity Shortlist",
            (
                "Purchased products are linked to products viewed in the same "
                "converted session but omitted from the final order."
            ),
            "These are behavioural candidates, not guarantees",
            (
                "The ranking identifies where observed browsing behaviour "
                "suggests a plausible cross-sell opportunity."
            ),
            "Run controlled recommendation tests",
            (
                "Use the pairs as basket-prompt candidates, then measure "
                "incremental conversion."
            ),
        ),
        (
            25,
            "04 · Category Basket",
            "Category Co-Purchase Matrix",
            "Frequency of category combinations appearing together in orders.",
            "Frequent combinations reveal basket structure",
            (
                "Raw co-purchase frequency is useful for merchandising but "
                "is not the same as normalized affinity."
            ),
            "Use frequency for merchandising decisions",
            (
                "Distinguish category popularity from unusually strong "
                "relationships before making recommendation claims."
            ),
        ),
    ]

    for tab, spec in zip(
        tabs,
        specs,
    ):

        with tab:
            show_export(
                *spec
            )


def customer_channels_page() -> None:

    report_header(
        "Customer & Channels",

        "Customer Value & Acquisition Performance",

        (
            "How customer segments contribute revenue and how "
            "device/source combinations perform."
        ),
    )

    customer_tab, channel_tab, exports_tab = st.tabs(
        [
            "Customer Value",
            "Device & Source",
            "Original BI Exports",
        ]
    )

    with customer_tab:

        section_header(
            "01 · Customer Economics",
            "Revenue Contribution by Customer Segment",
            (
                "Customer value shown through revenue contribution "
                "and segment size."
            ),
        )

        native_customer_value()

        explain(
            "Repeat buyers dominate commercial value",

            (
                f"Repeat buyers represent "
                f"<strong>{REPEAT_CUSTOMER_SHARE:.2f}%</strong> "
                f"of all customers and generate "
                f"<strong>{REPEAT_REVENUE_SHARE:.1f}%</strong> "
                f"of recorded revenue."
            ),

            "Retention is a major commercial lever",

            (
                "Prioritise CRM, loyalty, replenishment, personalised "
                "recommendations and win-back activity alongside acquisition."
            ),
        )

    with channel_tab:

        section_header(
            "02 · Acquisition",
            "Conversion Rate by Device and Traffic Source",
            (
                "Conversion efficiency shown together with the session "
                "volume behind each rate."
            ),
        )

        native_channel_heatmap()

        best_name = (
            f"{str(BEST_CHANNEL['device']).title()}"
            f" + "
            f"{str(BEST_CHANNEL['source']).title()}"
        )

        largest_name = (
            f"{str(LARGEST_TRAFFIC['device']).title()}"
            f" + "
            f"{str(LARGEST_TRAFFIC['source']).title()}"
        )

        explain(
            "Channel conversion differences are relatively narrow",

            (
                f"The observed spread is "
                f"<strong>{CHANNEL_SPREAD:.2f} percentage points</strong>. "
                f"The highest rate is "
                f"<strong>{float(BEST_CHANNEL['conversion_rate_pct']):.2f}%</strong> "
                f"for "
                f"<strong>{escape(best_name)}</strong> "
                f"across "
                f"<strong>{int(BEST_CHANNEL['sessions']):,}</strong> sessions."
            ),

            "Balance efficiency with traffic scale",

            (
                f"The largest traffic segment is "
                f"<strong>{escape(largest_name)}</strong> "
                f"with "
                f"<strong>{int(LARGEST_TRAFFIC['sessions']):,}</strong> sessions at "
                f"<strong>{float(LARGEST_TRAFFIC['conversion_rate_pct']):.2f}%</strong> "
                f"conversion."
            ),
        )

    with exports_tab:

        show_export(
            26,
            "03 · Original Export",
            "Customer Value Segments",
            (
                "Original portfolio visual from the Neo4j "
                "customer-value analysis."
            ),
            "The export supports the retention story",
            (
                f"Repeat buyers generate "
                f"<strong>{REPEAT_REVENUE_SHARE:.1f}%</strong> "
                f"of recorded revenue."
            ),
            "Keep the original analytical deliverable",
            (
                "The native chart is presentation-optimised; this tab "
                "preserves the approved BI output."
            ),
        )

        show_export(
            27,
            "04 · Original Export",
            "Device × Source Conversion",
            (
                "Original portfolio heatmap from the Neo4j "
                "channel analysis."
            ),
            "Rate alone is insufficient for channel decisions",
            (
                f"The full observed conversion-rate spread is "
                f"<strong>{CHANNEL_SPREAD:.2f} percentage points</strong>."
            ),
            "Read conversion and scale together",
            (
                "Small high-rate segments should not automatically "
                "outrank larger traffic sources."
            ),
        )


def graph_explorer_page() -> None:

    report_header(
        "Graph Explorer",

        "Interactive Product Relationship Network",

        (
            "Explore selected co-purchase relationships with "
            "pan, zoom, drag and adjacency focus."
        ),
    )

    interactive_tab, export_tab = st.tabs(
        [
            "Interactive Network",
            "Validated Export",
        ]
    )

    with interactive_tab:

        section_header(
            "01 · Interactive Network",
            "Top Product Co-Purchase Relationships",
            (
                "Node size reflects weighted connectivity; edge labels "
                "show shared-order counts."
            ),
        )

        if not interactive_graph():

            st.warning(
                "Interactive graph rendering is unavailable or the Q22 "
                "schema could not be mapped. The validated static network "
                "is shown below."
            )

            st.image(
                str(
                    PNG[22]
                ),
                width="stretch",
            )

        explain(
            "The network is a relationship-discovery view",

            (
                "Use node and edge structure to see which products connect, "
                "but always inspect the shared-order evidence behind a "
                "prominent link."
            ),

            "Treat network links as candidate signals",

            (
                "Use promising relationships for bundle or recommendation "
                "experiments, then validate them with support, confidence "
                "and incremental conversion."
            ),
        )

    with export_tab:

        show_export(
            22,
            "02 · Validated Export",
            "Product Co-Purchase Network",
            (
                "Presentation-ready static view of the strongest "
                "SKU-level relationships."
            ),
            "Graph topology makes product relationships visible",
            (
                "The network exposes connections that are difficult to "
                "recognise in a flat ranking table."
            ),
            "Validate relationship strength before operational use",
            (
                "Sparse co-purchase evidence can look visually important, "
                "so graph prominence should never replace evidence-volume checks."
            ),
        )


def methodology_page() -> None:

    report_header(
        "Methodology",

        "Graph Model & Analytical Validation",

        (
            "Data scope, graph relationships and validation controls used "
            "to make the analysis reproducible."
        ),
    )

    section_header(
        "01 · Neo4j Model",
        "Graph Relationship Design",
        "The exact relationship structure implemented in Neo4j.",
    )

    render_html(
        """
        <div class="model-card">

<pre>(Customer) ─[:STARTED]────────────→ (Session)
(Session)  ─[:HAS_EVENT]──────────→ (Event)
(Event)    ─[:NEXT]───────────────→ (Event)
(Event)    ─[:INTERACTED_WITH]────→ (Product)

(Customer) ─[:PLACED]─────────────→ (Order)
(Session)  ─[:CONVERTED_TO]───────→ (Order)
(Event)    ─[:GENERATED]──────────→ (Order)
(Order)    ─[:CONTAINS]────────────→ (Product)
(Order)    ─[:HAS_REVIEW]──────────→ (Review)
(Review)   ─[:ABOUT]───────────────→ (Product)</pre>

        </div>
        """
    )

    section_header(
        "02 · Validated Scale",
        "Analytical Coverage",
        "Headline entity counts from the validated executive export.",
    )

    items = [
        (
            "Customers",
            fmt_num(
                executive[
                    "total_customers"
                ]
            ),
        ),
        (
            "Sessions",
            fmt_num(
                executive[
                    "total_sessions"
                ]
            ),
        ),
        (
            "Orders",
            fmt_num(
                executive[
                    "total_orders"
                ]
            ),
        ),
        (
            "Reviews",
            fmt_num(
                executive[
                    "total_reviews"
                ]
            ),
        ),
    ]

    for col, (
        label,
        value,
    ) in zip(
        st.columns(
            4,
            gap="medium",
        ),
        items,
    ):

        with col:

            render_html(
                f"""
                <div class="kpi">

                    <div class="kpi-label">
                        {escape(label)}
                    </div>

                    <div class="kpi-value">
                        {escape(value)}
                    </div>

                    <div class="kpi-note">
                        Validated graph entities
                    </div>

                </div>
                """
            )

    show_export(
        28,
        "03 · Executive Validation",
        "Executive Commerce Performance",
        (
            "Headline measures generated from Neo4j and reconciled "
            "against supporting exports."
        ),
        "Commercial and behavioural totals reconcile",
        (
            f"The report validates "
            f"<strong>{fmt_num(executive['total_customers'])}</strong> customers, "
            f"<strong>{fmt_num(executive['total_sessions'])}</strong> sessions, "
            f"<strong>{fmt_num(executive['total_orders'])}</strong> orders and "
            f"<strong>{fmt_money(executive['total_revenue_usd'])}</strong> "
            f"recorded revenue."
        ),
        "Use this page in the technical discussion",
        (
            "It demonstrates graph modelling, Cypher analysis, "
            "Python validation and Streamlit reporting as one workflow."
        ),
    )

    render_html(
        """
        <div class="takeaway">

            <div class="takeaway-label">
                Data note
            </div>

            <div class="takeaway-copy">

                This portfolio uses a

                <strong>
                    synthetic e-commerce dataset
                </strong>.

                The project demonstrates analytical architecture,
                validation discipline, graph modelling,
                business interpretation and reporting workflow.

            </div>

        </div>
        """
    )

# ============================================================
# ROUTER + FOOTER
# ============================================================
ROUTES = {
    "executive":
        executive_page,

    "journey":
        customer_journey_page,

    "products":
        product_intelligence_page,

    "customers":
        customer_channels_page,

    "graph":
        graph_explorer_page,

    "methodology":
        methodology_page,
}

ROUTES[
    ACTIVE_PAGE
]()

render_html(
    """
    <div class="footer">

        <span>
            Neo4j Graph Analytics · E-Commerce Intelligence
        </span>

        <span>
            Ruturaj Mokashi · Analytics Portfolio
        </span>

    </div>
    """
)