import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk

# ==========================
# Estilização com CSS
# ==========================
st.markdown("""
    <style>
    .kpi-container {
        border: 1px solid #DDD;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        background-color: #f9f9f9;
        box-shadow: 1px 1px 8px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 16px;
        color: #555;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: bold;
        color: #222;
    }
    .main-title {
        text-align: center;
        font-size: 38px;
        margin-top: 20px;
        margin-bottom: 10px;
        color: #2e2e2e;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================
# Função de Carregamento
# ==========================
@st.cache_data
def load_data():
    df = pd.read_csv('base_vendas.csv')
    df.columns = df.columns.str.strip().str.lower()
    df['faturamento'] = df['quantidade'] * df['preco_unitario']
    df['custo'] = df['quantidade'] * df['custo_unitario']
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['unidades'] = df['quantidade']
    df['produto'] = df['produto'].str.title()
    return df

data = load_data()

# ==========================
# Menu Lateral
# ==========================
page = st.sidebar.radio("Navegação", ["Dashboard de Vendas", "Vendas por Localidade"])

# ==========================
# Página 1 - Dashboard
# ==========================
if page == "Dashboard de Vendas":
    st.markdown('<div class="main-title">Dashboard de Vendas - Cerveja Zorzi</div>', unsafe_allow_html=True)
    st.markdown("---")

    total_faturamento = data["faturamento"].sum()
    total_custo = data["custo"].sum()
    margem_lucro = ((total_faturamento - total_custo) / total_faturamento) * 100 if total_faturamento != 0 else 0
    avg_nps = data["avaliacao"].mean()
    ticket_medio = total_faturamento / data.shape[0] if data.shape[0] > 0 else 0
    total_unidades = data["unidades"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="kpi-container"><div class="kpi-title">Margem de Lucro</div><div class="kpi-value">%.2f%%</div></div>' % margem_lucro, unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="kpi-container"><div class="kpi-title">Avaliação Média</div><div class="kpi-value">%.1f ⭐</div></div>' % avg_nps, unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="kpi-container"><div class="kpi-title">Ticket Médio</div><div class="kpi-value">R$ %.2f</div></div>' % ticket_medio, unsafe_allow_html=True)

    st.markdown(" ")
    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="kpi-container"><div class="kpi-title">Faturamento Total</div><div class="kpi-value">R$ {:,.2f}</div></div>'.format(total_faturamento), unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="kpi-container"><div class="kpi-title">Unidades Vendidas</div><div class="kpi-value">{:,}</div></div>'.format(total_unidades), unsafe_allow_html=True)

    st.markdown("---")

    # Gráfico de Faturamento por Data
    df_time = data.groupby("data")["faturamento"].sum().reset_index()
    fig_time = px.line(df_time, x="data", y="faturamento", 
                       title="Faturamento ao Longo do Tempo",
                       labels={"faturamento": "Faturamento (R$)"})
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # Pódio de Produtos
    st.subheader("🥇 Pódio: Produtos Mais Vendidos")
    df_podio = data.groupby("produto").agg({"unidades": "sum", "faturamento": "sum"}).reset_index()
    df_podio = df_podio.sort_values(by="unidades", ascending=False)
    fig_podio = px.bar(df_podio, x="produto", y="unidades",
                       hover_data=["faturamento"],
                       title="Ranking de Vendas por Produto",
                       labels={"unidades": "Quantidade Vendida"})
    st.plotly_chart(fig_podio, use_container_width=True)

    st.markdown("---")

    # Método de Pagamento
    st.subheader("💳 Faturamento por Método de Pagamento")
    df_pag = data.groupby("metodo_pagamento").agg({"faturamento": "sum", "unidades": "sum"}).reset_index()
    fig_pag = px.pie(df_pag, values="faturamento", names="metodo_pagamento",
                     title="Participação no Faturamento")
    st.plotly_chart(fig_pag, use_container_width=True)

# ==========================
# Página 2 - Mapa
# ==========================
elif page == "Vendas por Localidade":
    st.title("📍 Mapa de Vendas por Localidade")

    df_mapa = data.groupby(['local', 'latitude', 'longitude']).agg(
        faturamento_total=('faturamento', 'sum'),
        vendas=('unidades', 'sum')
    ).reset_index()

    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=df_mapa['latitude'].mean(),
            longitude=df_mapa['longitude'].mean(),
            zoom=4,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df_mapa,
                pickable=True,
                opacity=0.8,
                stroked=True,
                filled=True,
                radius_scale=100,
                radius_min_pixels=5,
                radius_max_pixels=100,
                line_width_min_pixels=1,
                get_position='[longitude, latitude]',
                get_radius='faturamento_total',
                get_fill_color='[200, 30, 0, 160]',
                get_line_color=[0, 0, 0],
            )
        ],
        tooltip={
            "html": "<b>Local:</b> {local} <br/>"
                    "<b>Faturamento:</b> R$ {faturamento_total} <br/>"
                    "<b>Vendas:</b> {vendas} unidades",
            "style": {"backgroundColor": "white", "color": "black"}
        }
    ))

    st.markdown("Cada ponto no mapa representa um local de venda. O tamanho da bolha reflete o faturamento total da região.")

# ==========================
# Página 3 - Placeholder
# ==========================
else:
    st.title("📄 Outra Página")
    st.write("Conteúdo adicional pode ser inserido aqui.")
