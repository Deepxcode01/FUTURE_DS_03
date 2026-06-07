import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Funnel Dashboard | FUTURE_DS_03",
    page_icon="📊",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        text-align: center;
    }
    .metric-label { font-size: 13px; color: #6c757d; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; color: #1a1a2e; }
    .metric-sub   { font-size: 12px; color: #aaa; margin-top: 2px; }
    .section-header {
    font-size: 18px; font-weight: 600;
    color: #e0e0e0;   /* light grey */
    margin: 1.5rem 0 0.5rem;
    border-left: 4px solid #2ecc71; /* fresh green */
    padding-left: 10px;
   
    }
    .insight-box {
        background: #eaf4fb; border-left: 4px solid #2E86AB;
        border-radius: 0 8px 8px 0; padding: 0.8rem 1rem;
        margin: 0.4rem 0; font-size: 14px; color: #1a1a2e;
    }
    .insight-box.warn { background: #fff8ec; border-left-color: #f4a261; }
    .insight-box.good { background: #eafaf1; border-left-color: #2ecc71; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    mql = pd.read_csv('dataset/olist_marketing_qualified_leads_dataset.csv')
    deals = pd.read_csv('dataset/olist_closed_deals_dataset.csv')
    df = mql.merge(deals, on='mql_id', how='left')
    df['converted'] = df['won_date'].notna().astype(int)
    df['first_contact_date'] = pd.to_datetime(df['first_contact_date'])
    df['won_date']           = pd.to_datetime(df['won_date'])
    df['contact_month']      = df['first_contact_date'].dt.to_period('M').astype(str)
    df['contact_quarter']    = df['first_contact_date'].dt.to_period('Q').astype(str)
    df['days_to_convert']    = (df['won_date'] - df['first_contact_date']).dt.days
    df['origin']             = df['origin'].fillna('unknown')
    df['origin_clean']       = df['origin'].str.replace('_', ' ').str.title()
    df['business_segment']   = df['business_segment'].fillna('Not Converted')
    df['lead_type']          = df['lead_type'].fillna('Not Converted')
    df['business_type']      = df['business_type'].fillna('Not Converted')
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/combo-chart--v2.png", width=60)
st.sidebar.title("📊 Filter Panel")

all_channels = sorted(df['origin_clean'].unique().tolist())
sel_channels = st.sidebar.multiselect("Acquisition Channel", all_channels, default=all_channels)

months = sorted(df['contact_month'].unique().tolist())
sel_months = st.sidebar.select_slider(
    "Date Range (Month)",
    options=months,
    value=(months[0], months[-1])
)

# Apply filters
mask = (
    df['origin_clean'].isin(sel_channels) &
    (df['contact_month'] >= sel_months[0]) &
    (df['contact_month'] <= sel_months[1])
)
fdf = df[mask]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📊 Marketing Funnel & Conversion Performance Dashboard")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_leads   = len(fdf)
total_conv    = int(fdf['converted'].sum())
overall_cvr   = fdf['converted'].mean() * 100
not_converted = total_leads - total_conv
avg_days      = fdf[fdf['converted']==1]['days_to_convert'].mean()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Total MQLs</div>
        <div class="metric-value">{total_leads:,}</div>
        <div class="metric-sub">Marketing Qualified Leads</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Conversions</div>
        <div class="metric-value" style="color:#2ecc71">{total_conv:,}</div>
        <div class="metric-sub">Closed Deals</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Overall CVR</div>
        <div class="metric-value" style="color:#2E86AB">{overall_cvr:.2f}%</div>
        <div class="metric-sub">Visitor to Customer</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Not Converted</div>
        <div class="metric-value" style="color:#e63946">{not_converted:,}</div>
        <div class="metric-sub">Lost Leads</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Avg Days to Convert</div>
        <div class="metric-value">{avg_days:.0f}</div>
        <div class="metric-sub">Days</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Funnel + Channel CVR ───────────────────────────────────────────────
col1, col2 = st.columns([1, 1.6])

with col1:
    st.markdown('<div class="section-header">Conversion Funnel</div>', unsafe_allow_html=True)
    fig_funnel = go.Figure(go.Funnel(
        y=['Total MQLs', 'Contacted', 'Converted'],
        x=[total_leads, total_leads, total_conv],
        textinfo='value+percent initial',
        marker=dict(color=['#2E86AB', '#A8DADC', '#2ecc71'])
    ))
    fig_funnel.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_funnel, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">Conversion Rate by Channel</div>', unsafe_allow_html=True)
    cvr_ch = fdf.groupby('origin_clean').agg(
        total=('converted','count'), converted=('converted','sum')
    ).reset_index()
    cvr_ch['cvr'] = (cvr_ch['converted'] / cvr_ch['total'] * 100).round(2)
    cvr_ch = cvr_ch.sort_values('cvr', ascending=True)
    fig_ch = px.bar(cvr_ch, x='cvr', y='origin_clean', orientation='h',
                    text='cvr', color='cvr', color_continuous_scale='Blues',
                    labels={'cvr':'CVR (%)','origin_clean':'Channel'})
    fig_ch.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_ch.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                         coloraxis_showscale=False)
    st.plotly_chart(fig_ch, use_container_width=True)

# ── Row 2: Monthly Trend ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">Monthly Lead Volume & CVR Trend</div>', unsafe_allow_html=True)
monthly = fdf.groupby('contact_month').agg(
    leads=('mql_id','count'), conversions=('converted','sum')
).reset_index()
monthly['cvr'] = (monthly['conversions'] / monthly['leads'] * 100).round(2)

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
fig_trend.add_trace(go.Bar(x=monthly['contact_month'], y=monthly['leads'],
    name='Total Leads', marker_color='#A8DADC'), secondary_y=False)
fig_trend.add_trace(go.Scatter(x=monthly['contact_month'], y=monthly['cvr'],
    name='CVR (%)', mode='lines+markers',
    line=dict(color='#e63946', width=2.5)), secondary_y=True)
fig_trend.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10),
                        legend=dict(orientation='h', y=1.1))
fig_trend.update_yaxes(title_text="Lead Count", secondary_y=False)
fig_trend.update_yaxes(title_text="Conversion Rate (%)", secondary_y=True)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Row 3: Segment Treemap + Lead Type ───────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="section-header">Top Business Segments (Converted)</div>', unsafe_allow_html=True)
    seg = fdf[fdf['converted']==1]['business_segment'].value_counts().head(10).reset_index()
    seg.columns = ['Segment', 'Count']
    fig_seg = px.treemap(seg, path=['Segment'], values='Count',
                         color='Count', color_continuous_scale='Blues')
    fig_seg.update_layout(height=340, margin=dict(l=5, r=5, t=20, b=5))
    st.plotly_chart(fig_seg, use_container_width=True)

with col4:
    st.markdown('<div class="section-header">Lead Type — Volume vs CVR</div>', unsafe_allow_html=True)
    lt = fdf[fdf['lead_type']!='Not Converted'].groupby('lead_type').agg(
        total=('converted','count'), converted=('converted','sum')
    ).reset_index()
    lt['cvr'] = (lt['converted'] / lt['total'] * 100).round(2)
    fig_lt = px.scatter(lt, x='total', y='cvr', text='lead_type',
                        size='converted', color='cvr', color_continuous_scale='Blues',
                        labels={'total':'Lead Volume','cvr':'CVR (%)'},
                        size_max=40)
    fig_lt.update_traces(textposition='top center')
    fig_lt.update_layout(height=340, margin=dict(l=5,r=5,t=20,b=5),
                         coloraxis_showscale=False)
    st.plotly_chart(fig_lt, use_container_width=True)

# ── Row 4: Days to Convert + Business Type ────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="section-header">Days to Convert Distribution</div>', unsafe_allow_html=True)
    conv_df = fdf[(fdf['converted']==1) & (fdf['days_to_convert']>=0)].dropna(subset=['days_to_convert'])
    fig_days = px.histogram(conv_df, x='days_to_convert', nbins=30,
                            color_discrete_sequence=['#2E86AB'],
                            labels={'days_to_convert':'Days to Conversion'})
    fig_days.update_layout(height=300, margin=dict(l=5,r=5,t=20,b=5))
    st.plotly_chart(fig_days, use_container_width=True)

with col6:
    st.markdown('<div class="section-header">Business Type of Converted Leads</div>', unsafe_allow_html=True)
    bt = fdf[fdf['converted']==1]['business_type'].value_counts().reset_index()
    bt.columns = ['Type','Count']
    bt = bt[bt['Type']!='Not Converted']
    fig_bt = px.pie(bt, names='Type', values='Count',
                    color_discrete_sequence=['#2E86AB','#A8DADC','#E63946'],
                    hole=0.4)
    fig_bt.update_layout(height=300, margin=dict(l=5,r=5,t=20,b=5))
    st.plotly_chart(fig_bt, use_container_width=True)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Key Insights & Recommendations</div>', unsafe_allow_html=True)
insights = [
    ("warn", "Only 10.53% of MQLs convert — 89.47% of leads are lost without conversion. This is the primary area to fix."),
    ("warn", "Unknown origin accounts for 1,099 leads — UTM tracking is missing. Implement proper attribution immediately."),
    ("good", "Referral and Direct Traffic show highest intent and conversion rates — invest in referral programs."),
    ("good", "Home Decor & Health/Beauty dominate conversions — these segments should be primary outbound targets."),
    ("", "Organic Search brings 28.7% of leads but may underperform on CVR — nurture with email sequences."),
    ("", "Online Medium lead type has the most conversions — sales team should prioritize this segment."),
]
for style, text in insights:
    st.markdown(f'<div class="insight-box {style}">{text}</div>', unsafe_allow_html=True)

st.markdown("---")
