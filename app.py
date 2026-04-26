import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Seismic Dashboard",
    page_icon="eq",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #12121A;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #E63946;
        margin: 0;
    }
    .metric-label {
        font-size: 12px;
        color: #888;
        margin: 4px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .insight-card {
        background: #12121A;
        border-left: 3px solid #E63946;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .insight-title {
        font-size: 13px;
        font-weight: 600;
        color: #E63946;
        margin: 0 0 4px 0;
    }
    .insight-text {
        font-size: 13px;
        color: #ccc;
        margin: 0;
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #fff;
        margin: 8px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a2a3a;
    }
    .stDownloadButton > button {
        background-color: #E63946;
        color: white;
        border: none;
        border-radius: 8px;
        width: 100%;
    }
    div[data-testid="stSidebarContent"] {
        background: #0d0d14;
    }
    .empty-state {
        text-align: center;
        padding: 40px;
        color: #888;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("earthquakes_2020_2024.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True, format='mixed')
    df['date'] = pd.to_datetime(df['date'])
    df['depth'] = df['depth'].clip(lower=0)

    def get_region(place):
        if pd.isna(place):
            return "Unknown"
        parts = place.split(",")
        return parts[-1].strip() if len(parts) >= 2 else place.strip()

    def get_continent(region):
        pacific = ["Japan", "Philippines", "Indonesia", "Papua New Guinea",
                   "Tonga", "Vanuatu", "Solomon Islands", "New Zealand",
                   "Fiji", "Samoa", "Kermadec Islands region", "Taiwan",
                   "south of the Fiji Islands", "South Sandwich Islands region",
                   "southeast of the Loyalty Islands", "south of the Kermadec Islands"]
        americas = ["Chile", "Peru", "Alaska", "Mexico", "Ecuador",
                    "Colombia", "Argentina", "Bolivia", "California",
                    "Nevada", "Hawaii", "Guatemala", "Costa Rica"]
        asia = ["China", "Russia", "India", "Iran", "Turkey",
                "Afghanistan", "Pakistan", "Nepal", "Myanmar", "Kyrgyzstan",
                "Kazakhstan", "Tajikistan", "Uzbekistan"]
        europe = ["Greece", "Italy", "Portugal", "Iceland", "Romania",
                  "Albania", "North Macedonia", "Spain"]
        africa = ["Ethiopia", "Tanzania", "Congo", "Kenya", "Malawi",
                  "South Africa", "Morocco", "Algeria"]
        middle_east = ["Iraq", "Iran", "Yemen", "Syria", "Lebanon",
                       "Jordan", "Saudi Arabia", "Israel"]
        if any(r in region for r in pacific):
            return "Pacific / Oceania"
        elif any(r in region for r in americas):
            return "Americas"
        elif any(r in region for r in asia):
            return "Asia"
        elif any(r in region for r in europe):
            return "Europe"
        elif any(r in region for r in africa):
            return "Africa"
        elif any(r in region for r in middle_east):
            return "Middle East"
        else:
            return "Other"

    df['region'] = df['place'].apply(get_region)
    df['continent'] = df['region'].apply(get_continent)

    mag_bins = [4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 8.5]
    mag_labels = ["4.5–5.0", "5.0–5.5", "5.5–6.0", "6.0–6.5", "6.5–7.0", "7.0+"]
    df['mag_category'] = pd.cut(df['mag'], bins=mag_bins, labels=mag_labels, right=False)

    depth_bins = [0, 70, 300, 700]
    depth_labels = ["Shallow (0–70km)", "Intermediate (70–300km)", "Deep (300km+)"]
    df['depth_category'] = pd.cut(df['depth'], bins=depth_bins, labels=depth_labels, right=False)

    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Global Seismic Dashboard")
    st.markdown("*Analysing earthquake activity 2020–2024*")
    st.markdown("---")
    st.markdown("### Filters")

    selected_years = st.multiselect(
        "Year", sorted(df['year'].unique()), default=sorted(df['year'].unique())
    )

    mag_range = st.slider(
        "Magnitude Range", 4.5, 8.5, (4.5, 8.5), step=0.1
    )

    continents = ["All"] + sorted(df['continent'].unique())
    selected_continent = st.selectbox("Region / Continent", continents)

    event_types = st.multiselect(
        "Event Type", df['type'].unique().tolist(), default=df['type'].unique().tolist()
    )

    depth_cats = st.multiselect(
        "Depth Category",
        ["Shallow (0–70km)", "Intermediate (70–300km)", "Deep (300km+)"],
        default=["Shallow (0–70km)", "Intermediate (70–300km)", "Deep (300km+)"]
    )

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This dashboard presents global seismic events with magnitude ≥ 4.5 from 2020–2024.

    **Data source:** USGS Earthquake Hazards Program via Humanitarian Data Exchange (HDX)

    **Total records:** 37,205
    """)

# ── Filter data ───────────────────────────────────────────────────────────────
filtered = df[
    (df['year'].isin(selected_years)) &
    (df['mag'] >= mag_range[0]) &
    (df['mag'] <= mag_range[1]) &
    (df['type'].isin(event_types)) &
    (df['depth_category'].isin(depth_cats))
]
if selected_continent != "All":
    filtered = filtered[filtered['continent'] == selected_continent]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# Global Seismic Activity Dashboard")
st.markdown("*Interactive analysis of worldwide earthquake events (2020–2024) for disaster resilience and sustainability planning.*")
st.markdown("---")

# ── Empty state guard ─────────────────────────────────────────────────────────
if len(filtered) == 0:
    st.markdown('<div class="empty-state">No events match the current filters. Please adjust the filters in the sidebar.</div>', unsafe_allow_html=True)
    st.stop()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
kpi_data = [
    (c1, f"{len(filtered):,}", "Total Events"),
    (c2, f"{filtered['mag'].mean():.2f}", "Avg Magnitude"),
    (c3, f"{filtered['mag'].max():.1f}", "Max Magnitude"),
    (c4, f"{filtered['depth'].mean():.0f} km", "Avg Depth"),
    (c5, f"{filtered['region'].nunique()}", "Regions Affected"),
]
for col, val, label in kpi_data:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{val}</p>
            <p class="metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">Global Earthquake Map</p>', unsafe_allow_html=True)

map_sample = filtered if len(filtered) <= 15000 else filtered.sample(15000, random_state=42)

fig_map = px.scatter_geo(
    map_sample,
    lat="latitude",
    lon="longitude",
    color="mag",
    size="mag",
    size_max=15,
    color_continuous_scale=[
        [0.0, "#FFF3CD"],
        [0.3, "#FFB347"],
        [0.6, "#E63946"],
        [1.0, "#7B0D1E"]
    ],
    hover_name="place",
    hover_data={
        "mag": ":.1f",
        "depth": ":.1f",
        "year": True,
        "type": True,
        "latitude": False,
        "longitude": False
    },
    projection="natural earth",
    color_continuous_midpoint=6.0,
)
fig_map.update_layout(
    paper_bgcolor="#0A0A0F",
    plot_bgcolor="#0A0A0F",
    geo=dict(
        bgcolor="#0d1117",
        landcolor="#1a1a2e",
        oceancolor="#0d1117",
        showocean=True,
        showland=True,
        showcoastlines=True,
        coastlinecolor="#2a2a4a",
        showcountries=True,
        countrycolor="#2a2a4a",
        showframe=False,
    ),
    coloraxis_colorbar=dict(
        title=dict(text="Magnitude", font=dict(color="#fff")),
        tickfont=dict(color="#fff"),
    ),
    margin=dict(l=0, r=0, t=0, b=0),
    height=500,
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# ── Row 1: Bar + Line ─────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.markdown('<p class="section-title">Events Per Year</p>', unsafe_allow_html=True)
    yearly = filtered.groupby('year').size().reset_index(name='count')
    fig_bar = px.bar(
        yearly, x='year', y='count',
        color='count',
        color_continuous_scale=[[0, "#FFB347"], [1, "#E63946"]],
        text='count',
        labels={'count': 'Number of Events', 'year': 'Year'},
    )
    fig_bar.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_color='white')
    fig_bar.update_layout(
        paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
        font_color="white", coloraxis_showscale=False,
        xaxis=dict(tickmode='linear', dtick=1, gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(t=10, b=10), height=350,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    st.markdown('<p class="section-title">Monthly Frequency Trend</p>', unsafe_allow_html=True)
    filtered['year_month'] = filtered['time'].dt.to_period('M').astype(str)
    monthly = filtered.groupby('year_month').size().reset_index(name='count')
    fig_line = px.line(
        monthly, x='year_month', y='count',
        labels={'count': 'Events', 'year_month': 'Month'},
        color_discrete_sequence=["#E63946"],
    )
    fig_line.update_traces(line_width=2, fill='tozeroy', fillcolor='rgba(230,57,70,0.15)')
    fig_line.update_layout(
        paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
        font_color="white",
        xaxis=dict(tickangle=45, nticks=15, gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(t=10, b=10), height=350,
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ── Row 2: Heatmap + Histogram ────────────────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.markdown('<p class="section-title">Activity Heatmap (Month × Year)</p>', unsafe_allow_html=True)
    heatmap_data = filtered.groupby(['year', 'month']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='month', columns='year', values='count').fillna(0)
    month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                   7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    heatmap_pivot.index = [month_names.get(m, m) for m in heatmap_pivot.index]
    fig_heat = px.imshow(
        heatmap_pivot,
        color_continuous_scale=[[0,"#12121A"],[0.3,"#FFB347"],[1,"#E63946"]],
        aspect="auto",
        labels=dict(x="Year", y="Month", color="Events"),
    )
    fig_heat.update_layout(
        paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
        font_color="white",
        coloraxis_colorbar=dict(tickfont=dict(color="#fff"), title=dict(font=dict(color="#fff"))),
        margin=dict(t=10, b=10), height=350,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_d:
    st.markdown('<p class="section-title">Magnitude Distribution</p>', unsafe_allow_html=True)
    fig_hist = px.histogram(
        filtered, x='mag', nbins=35,
        color_discrete_sequence=["#E63946"],
        labels={'mag': 'Magnitude', 'count': 'Frequency'},
    )
    fig_hist.update_layout(
        paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
        font_color="white",
        xaxis=dict(gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e", title="Number of Events"),
        bargap=0.05,
        margin=dict(t=10, b=10), height=350,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ── Row 3: Scatter + Pie ──────────────────────────────────────────────────────
col_e, col_f = st.columns(2)

with col_e:
    st.markdown('<p class="section-title">Magnitude vs Depth</p>', unsafe_allow_html=True)
    scatter_data = filtered.sample(min(5000, len(filtered)), random_state=42)
    fig_scatter = px.scatter(
        scatter_data, x='depth', y='mag',
        color='mag',
        color_continuous_scale=[[0,"#FFB347"],[0.5,"#E63946"],[1,"#7B0D1E"]],
        opacity=0.6,
        hover_data=['place', 'year'],
        labels={'depth': 'Depth (km)', 'mag': 'Magnitude'},
        trendline="lowess",
        trendline_color_override="#ffffff",
    )
    fig_scatter.update_layout(
        paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
        font_color="white",
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="#1a1a2e"),
        yaxis=dict(gridcolor="#1a1a2e"),
        margin=dict(t=10, b=10), height=350,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_f:
    st.markdown('<p class="section-title">Events by Continent</p>', unsafe_allow_html=True)
    continent_counts = filtered['continent'].value_counts().reset_index()
    continent_counts.columns = ['Continent', 'Count']
    fig_pie = px.pie(
        continent_counts, names='Continent', values='Count',
        color_discrete_sequence=["#E63946","#FFB347","#FF6B6B","#C9184A","#FF4D6D","#590D22","#A4133C"],
        hole=0.45,
    )
    fig_pie.update_traces(textfont_color='white', textinfo='percent+label')
    fig_pie.update_layout(
        paper_bgcolor="#0A0A0F",
        font_color="white",
        legend=dict(font=dict(color="white")),
        margin=dict(t=10, b=10), height=350,
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Top Regions Bar ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Top 15 Most Affected Regions</p>', unsafe_allow_html=True)
top_regions = filtered['region'].value_counts().head(15).reset_index()
top_regions.columns = ['Region', 'Count']
fig_regions = px.bar(
    top_regions, x='Count', y='Region',
    orientation='h',
    color='Count',
    color_continuous_scale=[[0,"#FFB347"],[1,"#E63946"]],
    text='Count',
    labels={'Count': 'Number of Events', 'Region': ''},
)
fig_regions.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_color='white')
fig_regions.update_layout(
    paper_bgcolor="#0A0A0F", plot_bgcolor="#0A0A0F",
    font_color="white", coloraxis_showscale=False,
    yaxis=dict(autorange="reversed", gridcolor="#1a1a2e"),
    xaxis=dict(gridcolor="#1a1a2e"),
    margin=dict(t=10, b=10), height=420,
)
st.plotly_chart(fig_regions, use_container_width=True)

# ── Key Insights ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Key Insights</p>', unsafe_allow_html=True)

busiest_year = filtered.groupby('year').size().idxmax()
busiest_year_count = filtered.groupby('year').size().max()
biggest_quake = filtered.loc[filtered['mag'].idxmax()]
top_region = filtered['region'].value_counts().index[0]
top_region_count = filtered['region'].value_counts().iloc[0]
pct_shallow = round(len(filtered[filtered['depth_category'] == 'Shallow (0–70km)']) / len(filtered) * 100, 1)
avg_mag_trend = filtered.groupby('year')['mag'].mean()
trend_dir = "increasing" if avg_mag_trend.iloc[-1] > avg_mag_trend.iloc[0] else "relatively stable"

insights = [
    ("Busiest Year", f"{busiest_year} recorded the highest seismic activity with {busiest_year_count:,} events — suggesting elevated tectonic stress during this period."),
    ("Strongest Event", f"The most powerful earthquake was magnitude {biggest_quake['mag']:.1f} near {biggest_quake['place']}, occurring in {int(biggest_quake['year'])}."),
    ("Most Active Region", f"{top_region} was the most seismically active region with {top_region_count:,} events — likely due to its position on major tectonic plate boundaries."),
    ("Depth Patterns", f"{pct_shallow}% of all recorded events were shallow earthquakes (0–70km depth), which are typically the most destructive to surface infrastructure."),
    ("Magnitude Trend", f"Average earthquake magnitude has been {trend_dir} over the 2020–2024 period, providing important signals for disaster preparedness planning."),
]

col1, col2 = st.columns(2)
for i, (title, text) in enumerate(insights):
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"""
        <div class="insight-card">
            <p class="insight-title">{title}</p>
            <p class="insight-text">{text}</p>
        </div>
        """, unsafe_allow_html=True)

# ── Top 10 Table ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Top 10 Strongest Earthquakes</p>', unsafe_allow_html=True)
top10 = filtered.nlargest(10, 'mag')[['time', 'place', 'mag', 'depth', 'type', 'year']].copy()
top10['time'] = top10['time'].dt.strftime('%Y-%m-%d %H:%M UTC')
top10['depth'] = top10['depth'].round(1).astype(str) + ' km'
top10.columns = ['Time (UTC)', 'Location', 'Magnitude', 'Depth', 'Type', 'Year']
top10 = top10.reset_index(drop=True)
top10.index += 1
st.markdown(top10.to_html(), unsafe_allow_html=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Export Filtered Data</p>', unsafe_allow_html=True)
col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
with col_dl1:
    csv_buffer = io.StringIO()
    filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        label=f"Download CSV ({len(filtered):,} rows)",
        data=csv_buffer.getvalue(),
        file_name=f"earthquakes_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
with col_dl2:
    st.markdown(f"**{len(filtered):,}** events match current filters")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#555; font-size:12px;'>"
    "Data: USGS Earthquake Hazards Program via HDX &nbsp;|&nbsp; "
    "Magnitude ≥ 4.5 &nbsp;|&nbsp; 2020–2024 &nbsp;|&nbsp; "
    "5DATA004C Data Science Project Lifecycle"
    "</p>",
    unsafe_allow_html=True
)
