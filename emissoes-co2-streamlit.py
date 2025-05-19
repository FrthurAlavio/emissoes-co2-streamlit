import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit as st
import numpy as np
from folium.features import GeoJsonTooltip

# 1. Ler o CSV
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Configuração da página
st.set_page_config(layout="wide", page_title="Emissões de CO2 no Brasil")

# Título e descrição
st.title("🌎 Emissões de CO₂ por Estado Brasileiro (1970-2023)")
st.markdown("""
    Este painel apresenta dados históricos de emissões de gases de efeito estufa por estado brasileiro.
    Os valores são expressos em Milhões de Toneladas de CO₂ equivalente (CO₂e).
    """)
st.markdown("📊 **Fonte:** [SEEG - Sistema de Estimativas de Emissões de Gases de Efeito Estufa](https://seeg.eco.br/dados/)")

# Layout com duas colunas
col1, col2 = st.columns([1, 2])

with col1:
    # Dropdowns para seleção
    estados = sorted(df['estado'].unique())
    anos = sorted([col for col in df.columns if col != 'estado'])
    
    estado_usuario = st.selectbox("Escolha o estado:", estados)
    ano_usuario = st.selectbox("Escolha o ano:", anos)
    
    if estado_usuario and ano_usuario:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()
        valor_max = df[ano_usuario].max()
        estado_max = df.loc[df[ano_usuario] == valor_max, 'estado'].values[0]
        
        # Contexto adicional com métricas
        st.metric(
            label=f"Emissões em {estado_usuario} ({ano_usuario})", 
            value=f"{round(valor_estado):,} Mt CO₂e",
            delta=f"{round(valor_estado - media_nacional, 1)} Mt em relação à média nacional"
        )
        
        # Estatísticas comparativas
        st.markdown("### Comparação Nacional")
        st.markdown(f"- **Média nacional:** {round(media_nacional, 1):,} Mt CO₂e")
        st.markdown(f"- **Maior emissor:** {estado_max} ({round(valor_max):,} Mt CO₂e)")
        
        # Posição no ranking
        ranking = df[[ano_usuario, 'estado']].sort_values(by=ano_usuario, ascending=False)
        ranking = ranking.reset_index(drop=True)
        posicao = ranking[ranking['estado'] == estado_usuario].index[0] + 1
        st.markdown(f"- **Posição no ranking:** {posicao}º de {len(estados)} estados")
        
        # Contexto histórico se disponível
        if int(ano_usuario) > 1970:
            ano_anterior = str(int(ano_usuario) - 1)
            if ano_anterior in df.columns:
                valor_anterior = df.loc[df['estado'] == estado_usuario, ano_anterior].values[0]
                variacao = ((valor_estado - valor_anterior) / valor_anterior) * 100
                st.markdown(f"- **Variação desde {ano_anterior}:** {variacao:.1f}%")

with col2:
    # 2. Carregar mapa GeoJSON dos estados do Brasil
    @st.cache_data
    def carregar_mapa_estados():
        url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
        mapa = gpd.read_file(url)
        mapa['estado'] = mapa['name'].str.title()
        return mapa

    mapa = carregar_mapa_estados()

    # 3. Fazer merge dos dados
    df_mapa = df[['estado', ano_usuario]].copy()
    df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')
    df_mapa.rename(columns={ano_usuario: 'emissoes'}, inplace=True)

    mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

    # 4. Limpar o GeoDataFrame para deixar só as colunas necessárias antes de gerar geojson
    mapa_merged_limpo = mapa_merged[['estado', 'emissoes', 'geometry']].copy()
    
    # Adicionar um ranking para cada estado
    df_ranking = df_mapa[['estado', 'emissoes']].sort_values(by='emissoes', ascending=False)
    df_ranking['ranking'] = range(1, len(df_ranking) + 1)
    mapa_merged_limpo = mapa_merged_limpo.merge(df_ranking[['estado', 'ranking']], on='estado', how='left')

    # 5. Gerar GeoJSON para usar no Folium
    geojson_data = mapa_merged_limpo.to_json()

    # 6. Criar mapa interativo com Folium
    m = folium.Map(location=[-15.78, -47.93], zoom_start=4, tiles='CartoDB positron')

    # Criar uma escala de cores personalizada minimalista
    min_val = mapa_merged_limpo['emissoes'].min()
    max_val = mapa_merged_limpo['emissoes'].max()
    
    # Verificar valores min/max para garantir que são válidos
    if pd.isna(min_val) or pd.isna(max_val):
        min_val = 0
        max_val = 100
        
    # Garantir que min_val é diferente de max_val para evitar erro na escala
    if min_val == max_val:
        max_val = min_val + 1
        
    # Usar um esquema de cores mais clean e minimalista
    n_bins = 5
    
    # Criar escala usando quantis para melhor distribuição das cores
    # Isso evita problemas com valores extremos distorcendo a escala
    quantiles = np.linspace(0, 1, n_bins+1)
    threshold_scale = [round(mapa_merged_limpo['emissoes'].quantile(q)) for q in quantiles]
    
    # Garantir que todos os valores na escala são diferentes
    # Problema comum que causa erro no Choropleth
    unique_thresholds = []
    for val in threshold_scale:
        if val not in unique_thresholds:
            unique_thresholds.append(val)
    
    # Se não tivermos valores suficientes, criar uma escala linear
    if len(unique_thresholds) < 3:
        step = (max_val - min_val) / 4
        unique_thresholds = [min_val + step*i for i in range(5)]
    
    # Adicionar o choropleth melhorado
    choro = folium.Choropleth(
        geo_data=geojson_data,
        name='Emissões de CO₂',
        data=mapa_merged_limpo,
        columns=['estado', 'emissoes'],
        key_on='feature.properties.estado',
        fill_color='RdYlGn_r',  # Paleta invertida mais elegante
        fill_opacity=0.7,
        line_opacity=0.2,
        highlight=True,
        legend_name=None,  # Remover título da legenda padrão
        smooth_factor=0.5,
        threshold_scale=unique_thresholds
    ).add_to(m)
    
    # Personalizar a legenda após adicioná-la ao mapa
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 50px; 
        right: 50px; 
        width: 150px; 
        height: 120px; 
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
        font-size: 12px;
        padding: 10px;
        z-index: 9999;
        ">
        <p style="margin-top: 0;
                  margin-bottom: 5px;
                  font-weight: bold;
                  text-align: center;">
            CO₂e ({})
        </p>
        <div style="display: flex;
                    align-items: center;
                    margin-bottom: 5px;">
            <span style="display: inline-block;
                        height: 15px;
                        width: 30px;
                        background: #d73027;
                        margin-right: 5px;"></span>
            <span>Alto</span>
        </div>
        <div style="display: flex;
                    align-items: center;
                    margin-bottom: 5px;">
            <span style="display: inline-block;
                        height: 15px;
                        width: 30px;
                        background: #fc8d59;
                        margin-right: 5px;"></span>
            <span>Médio-Alto</span>
        </div>
        <div style="display: flex;
                    align-items: center;
                    margin-bottom: 5px;">
            <span style="display: inline-block;
                        height: 15px;
                        width: 30px;
                        background: #fee08b;
                        margin-right: 5px;"></span>
            <span>Médio</span>
        </div>
        <div style="display: flex;
                    align-items: center;
                    margin-bottom: 5px;">
            <span style="display: inline-block;
                        height: 15px;
                        width: 30px;
                        background: #d9ef8b;
                        margin-right: 5px;"></span>
            <span>Médio-Baixo</span>
        </div>
        <div style="display: flex;
                    align-items: center;">
            <span style="display: inline-block;
                        height: 15px;
                        width: 30px;
                        background: #91cf60;
                        margin-right: 5px;"></span>
            <span>Baixo</span>
        </div>
    </div>
    '''.format(ano_usuario)
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Adicionar tooltips para mostrar informações ao passar o mouse
    tooltip = GeoJsonTooltip(
        fields=['estado', 'emissoes', 'ranking'],
        aliases=['Estado:', 'Emissões (Mt CO₂e):', 'Ranking Nacional:'],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0F0F0;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px 3px 3px #888888;
            font-family: courier new;
            font-size: 12px;
            padding: 10px;
        """
    )
    
    # Adicionar a camada GeoJson com os tooltips
    folium.GeoJson(
        geojson_data,
        name='Estados',
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.0
        },
        tooltip=tooltip
    ).add_to(m)

    # Adicionar controle de camadas
    folium.LayerControl().add_to(m)

    # 7. Exibir mapa no Streamlit
    st.markdown(f"### 🗺️ Mapa Interativo de Emissões de CO₂e por Estado Brasileiro ({ano_usuario})")
    st.markdown("*Passe o mouse sobre os estados para ver informações detalhadas*")
    st_data = st_folium(m, width=800, height=600)

# Adicionar explicação sobre os dados
st.markdown("""
## ℹ️ Sobre os Dados
Os dados apresentados neste mapa representam as emissões de gases de efeito estufa (GEE) convertidas em CO₂ equivalente (CO₂e).
Esta medida considera o potencial de aquecimento global de diferentes gases (como metano e óxido nitroso) em relação ao CO₂.

### Como interpretar:
- **Toneladas de CO₂e**: Quantidade de gases de efeito estufa com o mesmo impacto de aquecimento global que uma tonelada de CO₂
- Os valores são expressos em **milhões de toneladas** (Mt)
- Os dados consideram emissões de diversos setores: energia, processos industriais, agropecuária, mudança de uso da terra e resíduos
""")
