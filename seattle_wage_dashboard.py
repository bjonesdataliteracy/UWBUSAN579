"""
Seattle City Wage Data — Interactive Dashboard
Run:  python seattle_wage_dashboard.py
Then open http://127.0.0.1:8050 in your browser.
"""

import pathlib, math
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, dash_table, Input, Output, callback

# ── Load & clean data ────────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).parent / "City_of_Seattle_Wage_Data_20260217.csv"
df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()
df["Hourly Rate"] = pd.to_numeric(df["Hourly Rate"], errors="coerce")
df["Annual Salary Est"] = (df["Hourly Rate"] * 2080).round(0)

ALL_DEPARTMENTS = sorted(df["Department"].unique())
RATE_MIN = math.floor(df["Hourly Rate"].min())
RATE_MAX = math.ceil(df["Hourly Rate"].max())

# ── Colour palette — light, modern aesthetic ─────────────────────────────────
COLORS = {
    "bg": "#f7f8fc",
    "card": "#ffffff",
    "border": "#e8ecf1",
    "accent": "#5b8def",
    "accent2": "#43b89c",
    "accent3": "#ef8b5e",
    "accent4": "#a878e8",
    "text": "#2d3748",
    "text_dim": "#8492a6",
    "heading": "#1a2332",
    "shadow": "0 2px 12px rgba(0,0,0,0.06)",
    "shadow_lg": "0 4px 24px rgba(0,0,0,0.08)",
}

CHART_COLORS = ["#5b8def", "#43b89c", "#ef8b5e", "#a878e8", "#f06595",
                "#fcc419", "#74c0fc", "#69db7c", "#ff8787", "#b197fc"]

PLOTLY_TEMPLATE = "plotly_white"

FONT_FAMILY = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"

# Google Fonts link for Inter
FONT_LINK = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"


# ── Reusable style helpers ───────────────────────────────────────────────────
def kpi_card(title, value_id, accent_color):
    return html.Div(
        [
            html.P(title, style={
                "margin": "0", "fontSize": "11px", "fontWeight": "500",
                "color": COLORS["text_dim"], "textTransform": "uppercase",
                "letterSpacing": "0.8px",
            }),
            html.H2(id=value_id, style={
                "margin": "6px 0 0 0", "color": COLORS["heading"],
                "fontSize": "26px", "fontWeight": "700",
            }),
        ],
        style={
            "background": COLORS["card"], "borderRadius": "12px",
            "padding": "20px 20px 20px 20px",
            "boxShadow": COLORS["shadow"],
            "flex": "1", "minWidth": "150px",
            "position": "relative", "overflow": "hidden",
            "borderLeft": f"4px solid {accent_color}",
        },
    )


def chart_card_style(extra=None):
    base = {
        "background": COLORS["card"],
        "borderRadius": "12px",
        "boxShadow": COLORS["shadow"],
        "padding": "8px",
    }
    if extra:
        base.update(extra)
    return base


# ── Layout ───────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "Seattle City Wages"

app.layout = html.Div(
    style={
        "background": COLORS["bg"], "minHeight": "100vh",
        "fontFamily": FONT_FAMILY, "color": COLORS["text"], "padding": "0",
    },
    children=[
        # Google Fonts
        html.Link(rel="stylesheet", href=FONT_LINK),

        # ── Header ──
        html.Div(
            style={
                "padding": "28px 40px 20px 40px",
                "background": COLORS["card"],
                "boxShadow": "0 1px 8px rgba(0,0,0,0.04)",
                "borderBottom": f"1px solid {COLORS['border']}",
            },
            children=[
                html.H1("City of Seattle — Employee Wage Dashboard", style={
                    "margin": "0", "fontSize": "24px", "fontWeight": "700",
                    "color": COLORS["heading"], "letterSpacing": "-0.3px",
                }),
                html.P(
                    "Explore hourly rates across 13,893 employees, 41 departments, and 1,178 job titles.",
                    style={
                        "margin": "6px 0 0 0", "color": COLORS["text_dim"],
                        "fontSize": "14px", "fontWeight": "400",
                    },
                ),
            ],
        ),

        # ── Filters row ──
        html.Div(
            style={
                "display": "flex", "gap": "24px", "padding": "24px 40px 8px 40px",
                "flexWrap": "wrap", "alignItems": "flex-end",
            },
            children=[
                html.Div([
                    html.Label("Departments", style={
                        "fontSize": "11px", "color": COLORS["text_dim"],
                        "marginBottom": "6px", "display": "block",
                        "fontWeight": "600", "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                    }),
                    dcc.Dropdown(
                        id="dept-filter",
                        options=[{"label": d, "value": d} for d in ALL_DEPARTMENTS],
                        value=[],
                        multi=True,
                        placeholder="All departments",
                        style={"minWidth": "360px"},
                    ),
                ], style={"flex": "2"}),

                html.Div([
                    html.Label("Hourly Rate Range", style={
                        "fontSize": "11px", "color": COLORS["text_dim"],
                        "marginBottom": "6px", "display": "block",
                        "fontWeight": "600", "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                    }),
                    dcc.RangeSlider(
                        id="rate-slider",
                        min=RATE_MIN, max=RATE_MAX, step=1,
                        value=[RATE_MIN, RATE_MAX],
                        marks={v: f"${v}" for v in range(0, RATE_MAX + 1, 25)},
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ], style={"flex": "2", "minWidth": "280px"}),

                html.Div([
                    html.Label("Job Title Search", style={
                        "fontSize": "11px", "color": COLORS["text_dim"],
                        "marginBottom": "6px", "display": "block",
                        "fontWeight": "600", "textTransform": "uppercase",
                        "letterSpacing": "0.5px",
                    }),
                    dcc.Input(
                        id="title-search",
                        type="text",
                        placeholder="e.g. Engineer, Police, Librarian…",
                        debounce=True,
                        style={
                            "width": "100%", "padding": "8px 14px",
                            "borderRadius": "8px",
                            "border": f"1px solid {COLORS['border']}",
                            "background": COLORS["card"],
                            "color": COLORS["text"], "fontSize": "14px",
                        },
                    ),
                ], style={"flex": "1", "minWidth": "200px"}),
            ],
        ),

        # ── KPI cards ──
        html.Div(
            id="kpi-row",
            style={
                "display": "flex", "gap": "16px",
                "padding": "20px 40px 20px 40px", "flexWrap": "wrap",
            },
            children=[
                kpi_card("Employees", "kpi-count", COLORS["accent"]),
                kpi_card("Departments", "kpi-depts", COLORS["accent4"]),
                kpi_card("Avg Hourly Rate", "kpi-mean", COLORS["accent2"]),
                kpi_card("Median Hourly Rate", "kpi-median", COLORS["accent3"]),
                kpi_card("Min Rate", "kpi-min", "#74c0fc"),
                kpi_card("Max Rate", "kpi-max", "#f06595"),
            ],
        ),

        # ── Charts row 1 ──
        html.Div(
            style={"display": "flex", "gap": "20px", "padding": "0 40px 20px 40px", "flexWrap": "wrap"},
            children=[
                html.Div(dcc.Graph(id="chart-histogram"),
                         style=chart_card_style({"flex": "3", "minWidth": "400px"})),
                html.Div(dcc.Graph(id="chart-salary-bands"),
                         style=chart_card_style({"flex": "2", "minWidth": "300px"})),
            ],
        ),

        # ── Charts row 2 ──
        html.Div(
            style={"display": "flex", "gap": "20px", "padding": "0 40px 20px 40px", "flexWrap": "wrap"},
            children=[
                html.Div(dcc.Graph(id="chart-dept-bar"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
                html.Div(dcc.Graph(id="chart-dept-box"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
            ],
        ),

        # ── Charts row 3 ──
        html.Div(
            style={"display": "flex", "gap": "20px", "padding": "0 40px 20px 40px", "flexWrap": "wrap"},
            children=[
                html.Div(dcc.Graph(id="chart-top-titles"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
                html.Div(dcc.Graph(id="chart-scatter"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
            ],
        ),

        # ── Charts row 4 ──
        html.Div(
            style={"display": "flex", "gap": "20px", "padding": "0 40px 20px 40px", "flexWrap": "wrap"},
            children=[
                html.Div(dcc.Graph(id="chart-cumulative"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
                html.Div(dcc.Graph(id="chart-heatmap"),
                         style=chart_card_style({"flex": "1", "minWidth": "400px"})),
            ],
        ),

        # ── Data table ──
        html.Div(
            style={"padding": "0 40px 40px 40px"},
            children=[
                html.Div(
                    style={
                        "background": COLORS["card"], "borderRadius": "12px",
                        "boxShadow": COLORS["shadow"], "padding": "24px",
                    },
                    children=[
                        html.H3("Employee Data Table", style={
                            "marginBottom": "16px", "fontWeight": "600",
                            "fontSize": "16px", "color": COLORS["heading"],
                            "marginTop": "0",
                        }),
                        dash_table.DataTable(
                            id="data-table",
                            columns=[
                                {"name": "Department", "id": "Department"},
                                {"name": "Last Name", "id": "Last Name"},
                                {"name": "First Name", "id": "First Name"},
                                {"name": "Job Title", "id": "Job Title"},
                                {"name": "Hourly Rate", "id": "Hourly Rate", "type": "numeric",
                                 "format": dash_table.FormatTemplate.money(2)},
                                {"name": "Est. Annual Salary", "id": "Annual Salary Est", "type": "numeric",
                                 "format": dash_table.FormatTemplate.money(0)},
                            ],
                            page_size=15,
                            sort_action="native",
                            sort_mode="multi",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_header={
                                "backgroundColor": "#f1f5f9",
                                "color": COLORS["heading"],
                                "fontWeight": "600",
                                "borderBottom": f"2px solid {COLORS['accent']}",
                                "fontSize": "12px",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.5px",
                                "padding": "12px 16px",
                            },
                            style_data={
                                "backgroundColor": COLORS["card"],
                                "color": COLORS["text"],
                                "borderBottom": f"1px solid {COLORS['border']}",
                                "fontSize": "13px",
                                "padding": "10px 16px",
                            },
                            style_filter={
                                "backgroundColor": "#f8fafc",
                                "color": COLORS["text"],
                                "padding": "6px 12px",
                            },
                            style_data_conditional=[
                                {"if": {"row_index": "odd"}, "backgroundColor": "#fafbfd"},
                                {"if": {"state": "active"}, "backgroundColor": "#eef2ff",
                                 "border": f"1px solid {COLORS['accent']}"},
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ── Helper: filter dataframe ────────────────────────────────────────────────
def filter_df(departments, rate_range, title_search):
    dff = df.copy()
    if departments:
        dff = dff[dff["Department"].isin(departments)]
    dff = dff[(dff["Hourly Rate"] >= rate_range[0]) & (dff["Hourly Rate"] <= rate_range[1])]
    if title_search:
        dff = dff[dff["Job Title"].str.contains(title_search, case=False, na=False)]
    return dff


# ── Master callback ──────────────────────────────────────────────────────────
@callback(
    Output("kpi-count", "children"),
    Output("kpi-depts", "children"),
    Output("kpi-mean", "children"),
    Output("kpi-median", "children"),
    Output("kpi-min", "children"),
    Output("kpi-max", "children"),
    Output("chart-histogram", "figure"),
    Output("chart-salary-bands", "figure"),
    Output("chart-dept-bar", "figure"),
    Output("chart-dept-box", "figure"),
    Output("chart-top-titles", "figure"),
    Output("chart-scatter", "figure"),
    Output("chart-cumulative", "figure"),
    Output("chart-heatmap", "figure"),
    Output("data-table", "data"),
    Input("dept-filter", "value"),
    Input("rate-slider", "value"),
    Input("title-search", "value"),
)
def update_dashboard(departments, rate_range, title_search):
    dff = filter_df(departments, rate_range, title_search)

    # ── KPIs ──
    n = len(dff)
    n_depts = dff["Department"].nunique()
    avg_rate = dff["Hourly Rate"].mean() if n else 0
    med_rate = dff["Hourly Rate"].median() if n else 0
    min_rate = dff["Hourly Rate"].min() if n else 0
    max_rate = dff["Hourly Rate"].max() if n else 0

    kpi_count = f"{n:,}"
    kpi_depts = f"{n_depts}"
    kpi_mean = f"${avg_rate:,.2f}"
    kpi_median = f"${med_rate:,.2f}"
    kpi_min = f"${min_rate:,.2f}"
    kpi_max = f"${max_rate:,.2f}"

    base_layout = dict(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=50, r=24, t=56, b=44),
        font=dict(family=FONT_FAMILY, size=12, color=COLORS["text"]),
        title_font=dict(size=15, color=COLORS["heading"], family=FONT_FAMILY),
        xaxis=dict(gridcolor="#edf2f7", zerolinecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#edf2f7", zerolinecolor="#e2e8f0"),
    )

    # ── 1. Histogram ──
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=dff["Hourly Rate"], nbinsx=50,
        marker_color=COLORS["accent"], opacity=0.8,
        marker_line=dict(width=0.5, color="white"),
        hovertemplate="$%{x:.0f}/hr<br>%{y} employees<extra></extra>",
    ))
    if n:
        fig_hist.add_vline(x=med_rate, line_dash="solid", line_color=COLORS["accent3"], line_width=2,
                           annotation_text=f"Median ${med_rate:.0f}", annotation_position="top right",
                           annotation_font_color=COLORS["accent3"])
        fig_hist.add_vline(x=avg_rate, line_dash="dash", line_color=COLORS["accent2"], line_width=2,
                           annotation_text=f"Mean ${avg_rate:.0f}", annotation_position="top left",
                           annotation_font_color=COLORS["accent2"])
    fig_hist.update_layout(**base_layout, title="Hourly Rate Distribution",
                           xaxis_title="Hourly Rate ($)", yaxis_title="Employees",
                           bargap=0.05)

    # ── 2. Salary bands donut ──
    if n:
        bands = [0, 50000, 75000, 100000, 125000, 150000, 200000, 600000]
        labels = ["<$50K", "$50-75K", "$75-100K", "$100-125K", "$125-150K", "$150-200K", "$200K+"]
        band_col = pd.cut(dff["Annual Salary Est"], bins=bands, labels=labels)
        band_counts = band_col.value_counts().reindex(labels).fillna(0).astype(int)
        fig_donut = go.Figure(go.Pie(
            labels=band_counts.index, values=band_counts.values,
            hole=0.55, marker_colors=CHART_COLORS[:len(labels)],
            textinfo="label+percent", textfont_size=11,
            hovertemplate="%{label}<br>%{value:,} employees (%{percent})<extra></extra>",
        ))
    else:
        fig_donut = go.Figure()
    fig_donut.update_layout(**base_layout, title="Est. Annual Salary Bands",
                            showlegend=False)

    # ── 3. Dept bar (headcount) ──
    dept_agg = dff.groupby("Department")["Hourly Rate"].agg(["count", "median"]).reset_index()
    dept_agg.columns = ["Department", "Employees", "Median Rate"]
    dept_agg = dept_agg.sort_values("Employees", ascending=True)
    fig_dept_bar = go.Figure(go.Bar(
        y=dept_agg["Department"], x=dept_agg["Employees"],
        orientation="h", marker_color=COLORS["accent"], opacity=0.85,
        marker_line=dict(width=0),
        customdata=dept_agg["Median Rate"],
        hovertemplate="%{y}<br>%{x:,} employees<br>Median: $%{customdata:.2f}/hr<extra></extra>",
    ))
    fig_dept_bar.update_layout(**base_layout, title="Employees per Department",
                               xaxis_title="Employees", yaxis_title="",
                               height=max(400, len(dept_agg) * 22 + 80))
    fig_dept_bar.update_layout(margin=dict(l=220, r=24, t=56, b=44))

    # ── 4. Dept box plots ──
    dept_med_order = dff.groupby("Department")["Hourly Rate"].median().sort_values().index.tolist()
    fig_dept_box = go.Figure()
    for dept in dept_med_order:
        rates = dff[dff["Department"] == dept]["Hourly Rate"]
        fig_dept_box.add_trace(go.Box(
            x=rates, y=[dept] * len(rates), name=dept,
            orientation="h", marker_color=COLORS["accent2"], opacity=0.7,
            line_color=COLORS["accent2"], boxmean=True, showlegend=False,
            hovertemplate="$%{x:.2f}/hr<extra></extra>",
        ))
    fig_dept_box.update_layout(**base_layout, title="Wage Spread by Department",
                               xaxis_title="Hourly Rate ($)", yaxis_title="",
                               height=max(400, len(dept_med_order) * 22 + 80))
    fig_dept_box.update_layout(margin=dict(l=220, r=24, t=56, b=44))

    # ── 5. Top 20 job titles ──
    if n:
        title_agg = dff.groupby("Job Title")["Hourly Rate"].agg(["count", "median"]).reset_index()
        title_agg.columns = ["Job Title", "Count", "Median Rate"]
        top20 = title_agg.nlargest(20, "Count").sort_values("Count", ascending=True)
        fig_titles = go.Figure(go.Bar(
            y=top20["Job Title"], x=top20["Count"],
            orientation="h",
            marker_color=top20["Median Rate"],
            marker_colorscale="Tealgrn",
            marker_colorbar=dict(title="Median<br>$/hr"),
            customdata=top20["Median Rate"],
            hovertemplate="%{y}<br>%{x} employees<br>Median: $%{customdata:.2f}/hr<extra></extra>",
        ))
    else:
        fig_titles = go.Figure()
    fig_titles.update_layout(**base_layout, title="Top 20 Job Titles by Headcount (color = median pay)",
                             xaxis_title="Employees", yaxis_title="",
                             height=550)
    fig_titles.update_layout(margin=dict(l=280, r=24, t=56, b=44))

    # ── 6. Dept size vs median pay scatter ──
    if n and len(dept_agg) > 0:
        fig_scatter = go.Figure(go.Scatter(
            x=dept_agg["Employees"], y=dept_agg["Median Rate"],
            mode="markers+text",
            marker=dict(size=np.sqrt(dept_agg["Employees"]) * 3,
                        color=dept_agg["Median Rate"], colorscale="Tealgrn",
                        colorbar=dict(title="Median<br>$/hr"),
                        line=dict(width=1, color="white"), opacity=0.8),
            text=[d[:20] + ".." if len(d) > 20 else d for d in dept_agg["Department"]],
            textposition="top center", textfont_size=8,
            hovertemplate="%{text}<br>%{x:,} employees<br>Median: $%{y:.2f}/hr<extra></extra>",
        ))
    else:
        fig_scatter = go.Figure()
    fig_scatter.update_layout(**base_layout, title="Department Size vs. Median Pay",
                              xaxis_title="Number of Employees",
                              yaxis_title="Median Hourly Rate ($)", height=550)

    # ── 7. Cumulative distribution ──
    if n:
        sorted_rates = np.sort(dff["Hourly Rate"].dropna().values)
        cum_pct = np.arange(1, len(sorted_rates) + 1) / len(sorted_rates) * 100
        fig_cum = go.Figure(go.Scatter(
            x=sorted_rates, y=cum_pct, mode="lines",
            fill="tozeroy", line_color=COLORS["accent"],
            fillcolor="rgba(91,141,239,0.12)",
            hovertemplate="$%{x:.2f}/hr<br>%{y:.1f}% earn this or less<extra></extra>",
        ))
        for pct in [25, 50, 75, 90]:
            rate_at_pct = np.percentile(sorted_rates, pct)
            fig_cum.add_annotation(x=rate_at_pct, y=pct,
                                   text=f"  {pct}th: ${rate_at_pct:.0f}",
                                   showarrow=True, arrowhead=2,
                                   arrowcolor=COLORS["text_dim"],
                                   font=dict(size=10, color=COLORS["text"]),
                                   bgcolor=COLORS["card"],
                                   bordercolor=COLORS["border"])
    else:
        fig_cum = go.Figure()
    fig_cum.update_layout(**base_layout, title="Cumulative Distribution of Hourly Wages",
                          xaxis_title="Hourly Rate ($)",
                          yaxis_title="Cumulative % of Employees",
                          yaxis_range=[0, 105])

    # ── 8. Pay-band heatmap by department ──
    if n and n_depts > 0:
        pay_bands = [0, 30, 40, 50, 60, 75, 100, 300]
        pay_labels = ["<$30", "$30-40", "$40-50", "$50-60", "$60-75", "$75-100", "$100+"]
        dff_copy = dff.copy()
        dff_copy["Pay Band"] = pd.cut(dff_copy["Hourly Rate"], bins=pay_bands, labels=pay_labels)
        cross = pd.crosstab(dff_copy["Department"], dff_copy["Pay Band"], normalize="index") * 100
        dept_order_hm = dff_copy.groupby("Department")["Hourly Rate"].median().sort_values(ascending=False).index
        cross = cross.reindex(dept_order_hm).fillna(0)

        fig_heatmap = go.Figure(go.Heatmap(
            z=cross.values, x=pay_labels, y=cross.index.tolist(),
            colorscale="Blues", hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>",
            text=np.where(cross.values >= 5, np.round(cross.values).astype(int).astype(str) + "%", ""),
            texttemplate="%{text}", textfont={"size": 10},
            colorbar=dict(title="% of Dept"),
        ))
    else:
        fig_heatmap = go.Figure()
    fig_heatmap.update_layout(**base_layout, title="% of Department in Each Pay Band",
                              xaxis_title="Pay Band", yaxis_title="",
                              height=max(400, n_depts * 22 + 80))
    fig_heatmap.update_layout(margin=dict(l=220, r=24, t=56, b=44))

    # ── Data table ──
    table_data = dff.to_dict("records")

    return (kpi_count, kpi_depts, kpi_mean, kpi_median, kpi_min, kpi_max,
            fig_hist, fig_donut, fig_dept_bar, fig_dept_box,
            fig_titles, fig_scatter, fig_cum, fig_heatmap, table_data)


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
