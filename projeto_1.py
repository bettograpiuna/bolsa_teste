# Projeto 1 - Backtest modelo de investimento Magic Formula.
# Desafio: Testar se a regra de investimento da fórmula mágica, do Joel Grenblatt, funcionou no Brasil nos últimos anos.

# --- Passo 1: Importando os módulos necessários ---
# Importamos as bibliotecas necessárias para o Streamlit, manipulação de dados e plotagem de gráficos.
import streamlit as st
import pandas as pd
import quantstats as qs
import plotly.express as px
import matplotlib.pyplot as plt # Necessário para exibir os gráficos do quantstats

# --- Configuração da Página ---
# Define o título da página, o ícone e o layout para ocupar a largura inteira.
st.set_page_config(
    page_title="Análise Bolsa de Valores",
    page_icon="📊",
    layout="wide",
)

st.title("Backtest da Estratégia Magic Formula")
st.markdown("### Análise de Rentabilidade Acumulada e Mensal vs. Ibovespa")

# --- Carregando os dados ---
# Usamos um bloco try-except para lidar com a possibilidade dos arquivos não existirem.
try:
    dados_empresas = pd.read_csv("dados_empresas.csv")
    ibov = pd.read_csv('ibov.csv')
    st.success("Dados carregados com sucesso!")
except FileNotFoundError:
    st.error("Erro: Verifique se os arquivos 'dados_empresas.csv' e 'ibov.csv' estão no mesmo diretório do seu script.")
    st.stop() # Interrompe a execução para evitar erros.

# --- Passo 3: Calcular os retornos mensais das empresas. ---
dados_empresas['retorno'] = dados_empresas.groupby('ticker')['preco_fechamento_ajustado'].pct_change()
dados_empresas['retorno'] = dados_empresas.groupby('ticker')['retorno'].shift(-1)

# --- Passo 4: Filtrar liquidez. ---
dados_empresas = dados_empresas[dados_empresas['volume_negociado'] > 1000000]

# --- Passo 5: Cria o ranking dos indicadores. ---
dados_empresas['ranking_ev_ebit'] = dados_empresas.groupby('data')['ebit_ev'].rank(ascending = False)
dados_empresas['ranking_roic'] = dados_empresas.groupby('data')['roic'].rank(ascending = False)
dados_empresas['ranking_final'] = dados_empresas['ranking_ev_ebit'] + dados_empresas['ranking_roic']
dados_empresas['ranking_final'] = dados_empresas.groupby('data')['ranking_final'].rank()

# --- Passo 6: Criar as carteiras. ---
# Mantivemos esta etapa, mas agora usaremos a mesma lógica para exibir as ações mês a mês.
carteira_mensal = dados_empresas[dados_empresas['ranking_final'] <= 10]

# --- Passo 7: Calcular a rentabilidade por carteira. ---
rentabilidade_por_carteiras = carteira_mensal.groupby('data')['retorno'].mean()
rentabilidade_por_carteiras = rentabilidade_por_carteiras.to_frame()

# --- Passo 8: Calcular a rentabilidade do modelo. ---
rentabilidade_por_carteiras['Magic Formula'] = (rentabilidade_por_carteiras['retorno'] + 1).cumprod() - 1
rentabilidade_por_carteiras = rentabilidade_por_carteiras.shift(1)
rentabilidade_por_carteiras = rentabilidade_por_carteiras.dropna()

# --- Passo 9: Calcular a rentabilidade do Ibovespa no mesmo período. ---
retornos_ibov = ibov['fechamento'].pct_change().dropna()
retorno_acum_ibov = (1 + retornos_ibov).cumprod() - 1
rentabilidade_por_carteiras['Ibovespa'] = retorno_acum_ibov.values
rentabilidade_por_carteiras = rentabilidade_por_carteiras.drop('retorno', axis = 1)

# --- Passo 10: Analisar os resultados e exibir no Streamlit. ---
qs.extend_pandas()
rentabilidade_por_carteiras.index = pd.to_datetime(rentabilidade_por_carteiras.index)

# Criando e exibindo um gráfico de linha interativo para a rentabilidade acumulada
st.header("1. Comparação de Rentabilidade Acumulada")
st.write("O gráfico abaixo mostra o desempenho da 'Magic Formula' em relação ao Ibovespa ao longo do tempo.")
fig_line = px.line(rentabilidade_por_carteiras, 
                   x=rentabilidade_por_carteiras.index, 
                   y=['Magic Formula', 'Ibovespa'],
                   title='Rentabilidade Acumulada: Magic Formula vs. Ibovespa',
                   labels={'value': 'Retorno Acumulado', 'index': 'Data', 'variable': 'Estratégia'})
st.plotly_chart(fig_line, use_container_width=True)


# Criando e exibindo o mapa de calor da Magic Formula
st.header("2. Análise de Rentabilidade Mensal da Magic Formula")
st.write("Este mapa de calor ilustra a performance mensal da estratégia 'Magic Formula'. Cores mais escuras indicam meses de pior desempenho.")
fig_magic_heatmap = rentabilidade_por_carteiras['Magic Formula'].plot_monthly_heatmap(show=False)
st.pyplot(fig_magic_heatmap)
plt.close(fig_magic_heatmap)


# Criando e exibindo o mapa de calor do Ibovespa
st.header("3. Análise de Rentabilidade Mensal do Ibovespa")
st.write("Este mapa de calor mostra a performance mensal do Ibovespa para comparação.")
fig_ibov_heatmap = rentabilidade_por_carteiras['Ibovespa'].plot_monthly_heatmap(show=False)
st.pyplot(fig_ibov_heatmap)
plt.close(fig_ibov_heatmap)


# --- Nova Seção: Composição da Carteira Mês a Mês ---
st.header("4. Composição Mensal da Carteira Magic Formula")
st.write("Abaixo, você pode ver quais as 10 ações selecionadas pela Magic Formula em cada mês de rebalanceamento.")

# Itera sobre as datas do DataFrame de rentabilidade para encontrar a composição de cada mês
datas_rebalanceamento = carteira_mensal['data'].unique()
for data in sorted(datas_rebalanceamento):
    # Filtra os dados para a data específica
    carteira_mes = carteira_mensal[carteira_mensal['data'] == data].sort_values('ranking_final')
    
    # Cria uma lista de tickers
    lista_acoes = carteira_mes['ticker'].tolist()
    
    # Exibe a lista em um expander para organizar a visualização
    with st.expander(f"Carteira para o mês de: {pd.to_datetime(data).strftime('%B de %Y')}"):
        st.write(lista_acoes)