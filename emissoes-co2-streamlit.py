import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit as st
import numpy as np
import branca.colormap as cm
import json
from folium.features import GeoJsonTooltip

# ============ 1. Ler CSV ===============
caminho_arquivo = 'co2estados(1972-2023).csv'
df = pd.read_csv(caminho_arquivo)
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# ============ 2. Carregar GeoJSON ===============
with open('br_states.json', encoding='utf-8') as f:
    geojson_data = json.load(f)

# ============ 3. Configurar página Streamlit ===============
st.set_page_config(layout="wide", page_title="Emissões de CO2 no Brasil")

st.title("🌎 Emissões de CO₂ por Estado Brasileiro (1970-2023)")
st.markdown("""
    Este painel apresenta dados históricos de emissões de gases de efeito estufa por estado brasileiro.
    Os valores são expressos em Milhões de Toneladas de CO₂ equivalente (CO₂e).
""")
st.markdown("📊 **Fonte:** [SEEG](https://seeg.eco.br/dados/)")

# ============ 4. Layout: seleções e métricas ===============
col1, col2 = st.columns([1, 2])

with col1:
    estados = sorted(df['estado'].unique())
    anos = sorted([col for col in df.columns if col != 'estado'])
    
    estado_usuario = st.selectbox("Escolha o estado:", estados)
    ano_usuario = st.selectbox("Escolha o ano:", anos)
    
    if estado_usuario and ano_usuario:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()
        valor_max = df[ano_usuario].max()
        estado_max = df.loc[df[ano_usuario] == valor_max, 'estado'].values[0]
        
        st.metric(
            label=f"Emissões em {estado_usuario} ({ano_usuario})", 
            value=f"{round(valor_estado):,} Mt CO₂e",
            delta=f"{round(valor_estado - media_nacional, 1)} Mt em relação à média nacional"
        )
        
        st.markdown("### Comparação Nacional")
        st.markdown(f"- **Média nacional:** {round(media_nacional, 1):,} Mt CO₂e")
        st.markdown(f"- **Maior emissor:** {estado_max} ({round(valor_max):,} Mt CO₂e)")
        
        ranking = df[[ano_usuario, 'estado']].sort_values(by=ano_usuario, ascending=False).reset_index(drop=True)
        posicao = ranking[ranking['estado'] == estado_usuario].index[0] + 1
        st.markdown(f"- **Posição no ranking:** {posicao}º de {len(estados)} estados")
        
        if int(ano_usuario) > 1970:
            ano_anterior = str(int(ano_usuario) - 1)
            if ano_anterior in df.columns:
                valor_anterior = df.loc[df['estado'] == estado_usuario, ano_anterior].values[0]
                variacao = ((valor_estado - valor_anterior) / valor_anterior) * 100
                st.markdown(f"- **Variação desde {ano_anterior}:** {variacao:.1f}%")

# ============ 5. Visualização do mapa no col2 ===============
with col2:
    # Criar DataFrame com dados do ano selecionado
    df_ano = df[['estado', ano_usuario]].copy()
    df_ano.columns = ['estado', 'valor']
    
    # Mapear nomes para siglas (usadas no GeoJSON)
    estado_para_sigla = {feature['properties']['ESTADO'].title(): feature['properties']['SIGLA'] for feature in geojson_data['features']}
    df_ano['sigla'] = df_ano['estado'].map(estado_para_sigla)
    
    # Normalizar valores para color mapping
    max_val = df_ano['valor'].max()
    min_val = df_ano['valor'].min()
    colormap = cm.linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = f'Emissões de CO₂e em {ano_usuario} (Mt)'
    
    # Criar mapa
    m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4, tiles="cartodbpositron")
    
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=df_ano,
        columns=["sigla", "valor"],
        key_on="feature.properties.SIGLA",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=f"Emissões de CO₂e em {ano_usuario} (Mt)",
        highlight=True,
    ).add_to(m)
    
    # Tooltip
    folium.GeoJsonTooltip(
        fields=["ESTADO", "SIGLA"],
        aliases=["Estado:", "Sigla:"],
        localize=True
    ).add_to(choropleth.geojson)

    colormap.add_to(m)

    # Exibir o mapa
    st_data = st_folium(m, width=900, height=600)

# ============ 6. Explicação adicional ===============
st.markdown("""
## ℹ️ Sobre os Dados
Os dados apresentados neste mapa representam as emissões de gases de efeito estufa (GEE) convertidas em CO₂ equivalente (CO₂e).
Esta medida considera o potencial de aquecimento global de diferentes gases (como metano e óxido nitroso) em relação ao CO₂.

### Como interpretar:
- **Toneladas de CO₂e**: Quantidade de gases de efeito estufa com o mesmo impacto de aquecimento global que uma tonelada de CO₂
- Os valores são expressos em **milhões de toneladas** (Mt)
- Os dados consideram emissões de diversos setores: energia, processos industriais, agropecuária, mudança de uso da terra e resíduos
""")
