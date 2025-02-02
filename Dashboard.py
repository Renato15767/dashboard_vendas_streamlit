import streamlit as st
import requests
import pandas as pd
import plotly.express as px


# COMANDOS IMPORTANTES

# - Ativar ambiente virtual: .\venv\Scripts/activate
# - Rodar Streamlit: streamlit run Dashboard.py
# Desativar ambiente virtual: deactivate


st.set_page_config(layout='wide')

# ================DEFS()================


def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} Milhões'


# ================MAIN()================


st.title("DASHBOARD")

# Request > Json > Dataframe
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Norte', 'Nordeste',
           'Sul', 'Sudeste']  # Regiões que serão filtradas

# =================================Filtros=================================

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)  # Select Box para filtro

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox(
    'Dados de todo o período', value=True)  # Checkbox para ano
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

# Query para filtragem dos dados
query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)  # Request
# Transforma JSON em um Dataframe
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(
    dados['Data da Compra'], format='%d/%m/%Y')

# Faz filtro de vendedores
filtro_vendedores = st.sidebar.multiselect(
    'Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    # Filtra a tabela 'dados' pelo vendedor
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# =================================Tabelas=================================

# Tabela de Estado
receitas_estados = dados.groupby('Local da compra')[['Preço']].sum()
receitas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    receitas_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

# Tabela de receita
receita_mensal = dados.set_index('Data da Compra').groupby(
    pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

# Tabela de Categorias
# Agrupado por "Categoria do Produto", onde os preços são somados e organizados do Menor até Maior
receita_categorias = dados.groupby('Categoria do Produto')[
    ['Preço']].sum().sort_values('Preço', ascending=False)

# Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')[
                          'Preço'].agg(['sum', 'count']))

# Construir um gráfico de mapa com a quantidade de vendas por estado.
qty_vendas_estado = dados.groupby(
    ['lat', 'lon', 'Local da compra']).size().reset_index(name='Quantidade Vendas')

# Construir um gráfico de linhas com a quantidade de vendas mensal.
qty_vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(
    pd.Grouper(freq='M'))['Preço'].count()).reset_index()
qty_vendas_mensal['Ano'] = qty_vendas_mensal['Data da Compra'].dt.year
qty_vendas_mensal['Mes'] = qty_vendas_mensal['Data da Compra'].dt.month_name()

# Construir um gráfico de barras com os 5 estados com maior quantidade de vendas.
# Tabela qty_estado
qty_estado = dados.groupby(['Local da compra']).size(
).reset_index(name='Quantidade Vendas').sort_values('Quantidade Vendas', ascending=False)

# Construir um gráfico de barras com a quantidade de vendas por categoria de produto.
qty_categoria_produto = dados.groupby('Categoria do Produto').size().reset_index(
    name='Quantidade Vendas').sort_values('Quantidade Vendas', ascending=False)


# =================================Gráficos=================================
# Gráfico do mapa
fig_mapa_receita = px.scatter_geo(receitas_estados,
                                  lat='lat',  # latitude
                                  lon='lon',  # longitude
                                  scope='south america',  # Região focada
                                  size='Preço',  # Alteração do tamanho
                                  template='seaborn',  # Template do seaborn
                                  hover_name='Local da compra',  # Apareçerá esse campo ao passar o mouse
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estado'
                                  )

# Gráfico da receita mensal (Linhas)
fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal')

# Altera label do eixo y
fig_receita_mensal.update_layout(yaxis_title='Receita')

# o px cria um gráfico a partir do plotly
# Gráfico de barras
fig_receita_estados = px.bar(receitas_estados.head(),
                             x='Local da compra',
                             y='Preço',
                             text_auto=True,
                             title='Top estados (receita)'
                             )

# Altera label do eixo y
fig_receita_estados.update_layout(yaxis_title='Receita')

# OBS: Não é preciso passar X e Y, pq na tabela 'receita_categorias' só existe 2 informações
fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por categoria'
                                )

fig_receita_categorias.update_layout(yaxis_title='Receita')


# Gráfico do mapa de qty de vendas por estado
fig_mapa_qty_vendas = px.scatter_geo(qty_vendas_estado,
                                     lat='lat',  # latitude
                                     lon='lon',  # longitude
                                     scope='south america',  # Região focada
                                     size='Quantidade Vendas',  # Alteração do tamanho
                                     template='seaborn',  # Template do seaborn
                                     hover_name='Local da compra',  # Apareçerá esse campo ao passar o mouse
                                     hover_data={'lat': False, 'lon': False},
                                     title='Qty de Vendas por Estado'
                                     )

# Gráfico da quantidade mensal por tempo
fig_quantidade_mensal = px.line(qty_vendas_mensal,
                                x='Mes',
                                y='Preço',
                                markers=True,
                                range_y=(0, qty_vendas_mensal.max()),
                                color='Ano',
                                line_dash='Ano',
                                title='Quantidade Mensal')

# Altera label do eixo y
fig_quantidade_mensal.update_layout(yaxis_title='Quantidade')

# gráfico de barras com os 5 estados com maior quantidade de vendas.
fig_qty_estados = px.bar(qty_estado.head(),
                         x='Local da compra',
                         y='Quantidade Vendas',
                         text_auto=True,
                         title='Top estados (Qty vendida)'
                         )


# Gráfico de barras com a qty vendas por categoria
fig_qty_categorias = px.bar(qty_categoria_produto,
                            x='Categoria do Produto',
                            y='Quantidade Vendas',
                            text_auto=True,
                            title='Quantidade de Vendas por Categoria'
                            )


# =================================Visualização=================================

# Nome de cada aba
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])
# st.dataframe(qty_vendas_estado)
# st.dataframe(vendas_estados)

with aba1:  # Receita
    # Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        # Soma essa coluna do df
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with coluna2:
        # Botão do Streamlit
        # qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
        # conta o conteúdo das linhas
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)
        # st.dataframe(receita_mensal)


with aba2:  # Quantidade de Vendas
    # Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        # Soma essa coluna do df
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_qty_vendas, use_container_width=True)
        st.plotly_chart(fig_qty_estados, use_container_width=True)
        # st.dataframe(qty_categoria_produto)

    with coluna2:
        # conta o conteúdo das linhas
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_quantidade_mensal, use_container_width=True)
        st.plotly_chart(fig_qty_categorias, use_container_width=True)


with aba3:  # Vendedores
    # Botão do Streamlit
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    # Visualização no streamlit
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        # Botão do Streamlit
        # qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
        # Soma essa coluna do df
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))

        fig_receita_vendedores = px.bar(
            vendedores[['sum']].sort_values(
                'sum', ascending=False).head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values(
                'sum', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
        )

        fig_receita_vendedores.update_layout(yaxis_title='Vendedores')
        fig_receita_vendedores.update_layout(xaxis_title='Receita')

        st.plotly_chart(fig_receita_vendedores)

    with coluna2:
        # conta o conteúdo das linhas
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(
            vendedores[['count']].sort_values(
                'count', ascending=False).head(qtd_vendedores),
            x='count',
            y=vendedores[['count']].sort_values(
                'count', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (Qty)'
        )

        fig_vendas_vendedores.update_layout(yaxis_title='Vendedores')
        fig_vendas_vendedores.update_layout(xaxis_title='Quantidade de vendas')

        st.plotly_chart(fig_vendas_vendedores)

    # st.dataframe(vendedores)
# st.dataframe(dados)  # imprimi os dados do df
# st.dataframe(vendedores)
