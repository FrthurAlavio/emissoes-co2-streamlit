import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# 1. Carregar dados
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

st.title("🌀 Emissões de CO2 por Estado (1970-2023)")
st.markdown("📊 Fonte: [SEEG](https://seeg.eco.br/dados/)")

# Inputs usuário
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados, key="estado_selectbox")
ano_usuario = st.selectbox("Escolha o ano:", anos, key="ano_selectbox")

# Mostrar dados do estado e média nacional
if estado_usuario and ano_usuario:
    try:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()

        st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** em {ano_usuario}.")

        if media_nacional == 0:
            st.warning("A média nacional é zero, comparação não é possível.")
        else:
            razao = valor_estado / media_nacional
            if razao > 1:
                st.info(f"O valor está **{round(razao, 2)}x acima da média nacional**.")
            elif razao < 1:
                st.info(f"O valor está **{round(1 / razao, 2)}x abaixo da média nacional**.")
            else:
                st.info("O valor está igual à média nacional.")

        st.markdown(f"Média nacional de CO2e em {ano_usuario}: **{round(media_nacional, 2)}** Milhões de Toneladas.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

# 2. Carregar mapa dos estados do Brasil com geopandas
@st.cache_data
def carregar_mapa_estados():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    mapa = gpd.read_file(url)
    mapa['estado'] = mapa['name'].str.title()
    return mapa

mapa = carregar_mapa_estados()

# 3. Preparar dados para o mapa
df_mapa = df[['estado', ano_usuario]].copy()
df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')

# 4. Merge mapa com dados
mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

# 5. Converter para GeoJSON
geojson_data = mapa_merged.to_json()

# 6. Inspecionar propriedades do GeoJSON (remova depois de validar!)
geojson_dict = json.loads(geojson_data)
st.write("Chaves das propriedades do GeoJSON:", list(geojson_dict['features'][0]['properties'].keys()))

# 7. Criar mapa folium
mapa_folium = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

folium.Choropleth(
    geo_data=geojson_data,
    data=df_mapa,
    columns=['estado', ano_usuario],
    key_on='feature.properties.estado',  # ajuste se necessário conforme a saída acima
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f'Emissões de CO₂e (Milhões de Toneladas) - {ano_usuario}',
    nan_fill_color='lightgray',
).add_to(mapa_folium)

folium.LayerControl().add_to(mapa_folium)

# 8. Exibir mapa no Streamlit
st.markdown(f"## 🗺️ Mapa de emissões de CO₂ por estado ({ano_usuario})")
st_folium(mapa_folium, width=700, height=500)
