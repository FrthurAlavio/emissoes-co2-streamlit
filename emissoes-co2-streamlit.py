import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Abrir e ler a tabela
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

# 2. Padronizar o nome da coluna de estados
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Título do app
st.title("🌀 Emissões de CO₂ por Estado (1970-2023)")
st.markdown("📊 Fonte: [SEEG](https://seeg.eco.br/dados/)")

# 3. Inputs do usuário com dropdowns
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados, key="estado_selectbox")
ano_usuario = st.selectbox("Escolha o ano:", anos, key="ano_selectbox")

# 4. Lógica de análise e exibição
if estado_usuario and ano_usuario:
    try:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()

        st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** no ano de **{ano_usuario}**.")

        if media_nacional != 0:
            razao = valor_estado / media_nacional
            if razao > 1:
                st.info(f"O valor está **{round(razao, 2)}x acima da média nacional**.")
            elif razao < 1:
                st.info(f"O valor está **{round(1 / razao, 2)}x abaixo da média nacional**.")
            else:
                st.info("O valor está igual à média nacional.")
        else:
            st.warning("A média nacional é zero, comparação não é possível.")

                st.markdown(f"Média nacional de CO2e em {ano_usuario}: **{round(media_nacional, 2)}**")


    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

# 5. Mapa interativo
@st.cache_data
def carregar_mapa_estados():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    mapa = gpd.read_file(url)
    mapa['estado'] = mapa['name'].str.title()
    return mapa

mapa = carregar_mapa_estados()

# Junta dados
df_mapa = df[['estado', ano_usuario]].copy()
df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')

# Converte valores para float padrão do Python
df_mapa[ano_usuario] = df_mapa[ano_usuario].astype(float)

mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

# Reduz as colunas a apenas o necessário para o GeoJson
mapa_geojson = mapa_merged[['estado', ano_usuario, 'geometry']].copy()

# Cria mapa
m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

# Choropleth
folium.Choropleth(
    geo_data=mapa_geojson.to_json(),
    name="choropleth",
    data=df_mapa,
    columns=["estado", ano_usuario],
    key_on="feature.properties.estado",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f"Emissões de CO₂e em {ano_usuario} (milhões de toneladas)",
    nan_fill_color="lightgray"
).add_to(m)

# Tooltip
folium.GeoJson(
    data=mapa_geojson.to_json(),
    name="tooltip",
    tooltip=folium.GeoJsonTooltip(
        fields=["estado"],
        aliases=["Estado:"]
    )
).add_to(m)

# Exibe no Streamlit
st.markdown("## 🌎 Mapa Interativo de Emissões")
st_folium(m, width=800, height=600)
