import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

@st.cache_data
def carregar_tri_financas():
    tri_financas = pd.read_csv(
        "dados_vale(Tri Financeiro).csv", encoding="ISO-8859-1", sep=";",)
    tri_financas.columns = (tri_financas.columns.str.strip())  #remove espaços antes e depois dos nomes
    return tri_financas

@st.cache_data
def carregar_anual_financas():
    anual_financas = pd.read_csv(
        "dados_vale(Anual Financeiro).csv", encoding="ISO-8859-1", sep=";",)
    anual_financas.columns = anual_financas.columns.str.strip()
    #converte coluna de ano para texto limpo:
    anual_financas["Ano"] = (
        anual_financas["Ano"].dropna().astype(int).astype(str))
    return anual_financas

@st.cache_data
def carregar_tri_producao():
    tri_producao = pd.read_csv(
        "dados_vale(Tri Produção).csv", encoding="ISO-8859-1", sep=";",)
    tri_producao.columns = tri_producao.columns.str.strip() #remove espaços em branco no início e no final dos nomes das colunas
    tri_producao["Produto"] = tri_producao["Produto"].astype(str).str.strip() #converte a coluna para texto remove espaços em branco
    tri_producao["Local"] = tri_producao["Local"].astype(str).str.strip()
    return tri_producao #retorna a tabela limpa

@st.cache_data
def carregar_anual_producao():
    anual_prod = pd.read_csv(
        "dados_vale(Anual Produção).csv", encoding="ISO-8859-1", sep=";",)
    anual_prod.columns = anual_prod.columns.str.strip()
    anual_prod["Ano"] = anual_prod["Ano"].dropna().astype(int).astype(str)
    return anual_prod

@st.cache_data
def carregar_tri_mercado():
    tri_mercado = pd.read_csv(
        "dados_vale(Tri Mercado e Economia).csv", encoding="ISO-8859-1", sep=";")
    tri_mercado.columns = tri_mercado.columns.str.strip()
    return tri_mercado

@st.cache_data
def carregar_anual_mercado():
    anual_mercado = pd.read_csv(
        "dados_vale(Anual Mercado e Economia ).csv", encoding="ISO-8859-1", sep=";")
    anual_mercado.columns = anual_mercado.columns.str.strip()
    anual_mercado["Ano"] = anual_mercado["Ano"].dropna().astype(int).astype(str)
    return anual_mercado

tri_mercado = carregar_tri_mercado()
anual_mercado = carregar_anual_mercado()
anual_producao = carregar_anual_producao()
tri_producao = carregar_tri_producao()
tri_financas = carregar_tri_financas()
anual_financas = carregar_anual_financas()

#==========================================================

def conv_pct(val):
    if pd.isna(val): #verifica se o valor é nulo ou ausente
        return None #retorna None cao o valor seja nulo
    val_str = str(val).replace("%", "").replace(",", ".").strip()
    try: #tentativa de converter o texto em número decimal
        return float(val_str) #converte a string tratada para float
    except ValueError: #captura o erro caso o texto não seja um número válido
        return None

def conv_preco(val):
    if pd.isna(val):
        return None
    val_str = (
        str(val)
        .replace("US$", "")
        .replace("US", "")
        .replace("R$", "")
        .replace("$", "")
        .replace("€", "")
        .replace("\x80", "")
        .strip()
        .replace(",", "."))
    try:
        return float(val_str)
    except ValueError:
        return None

def f_bilhoes(val):
    if pd.isna(val):
        return None

    val_str = str(val).replace("(R$ bi)", "").replace("R$", "").strip()

    #se a string contém vírgula e ponto (ex: "235.120,00" ou "235,12")
    if "," in val_str: #verifica se existe uma vírgula no texto
        val_str = val_str.replace(".", "").replace(",", ".")
    else: #executa se a string não tiver vírgula
        #se contém apenas um ponto e 3 casas decimais (ex: 235.120 -> milhar do CSV)
        parts = val_str.split(".") #divide em partes onde tiver ponto
        if len(parts) == 2 and len(parts[1]) == 3 and float(parts[0]) > 10: #checa se tem duas partes
            val_str = val_str.replace(".", "")

    try:
        num = float(val_str)
    except ValueError:
        return None

    #se o número resultante for >= 100, significa que está em Milhões (ex: 48000 -> 48 Bi)
    if abs(num) >= 100:
        return num / 1000.0

    return num

#CARDS EXPANSÍVEIS =====================================

def _card_base(titulo, valor, coluna, tabela, key_slider, conversor, cor, col_tempo):
    with st.container(border=True):
        st.metric(titulo, valor)

        with st.expander("Histórico"):
            n = st.slider("Períodos:", 3, len(tabela), min(8, len(tabela)), key=key_slider) #slider para escolher o número de períodos

            df = tabela.tail(n).copy() #pega os últimos 'n' registros
            df[coluna] = df[coluna].apply(conversor) #converte os dados para número
            df[col_tempo] = df[col_tempo].astype(str) #converte para string

            fig = px.line(df, x=col_tempo, y=coluna, markers=True, #cria gráfico de linha
                          color_discrete_sequence=[cor])
            fig.update_layout(margin=dict(l=10, r=30, t=10, b=10), height=190,
                              xaxis_title="", yaxis_title="", hovermode="x unified") #remove títulos dos eixos e unifica os hovers
            fig.update_xaxes(tickangle=-45, tickfont=dict(size=10), #inclina rótulos do eixo X
                             type="category", automargin=True)
            fig.update_yaxes(automargin=False, ticklabelposition="inside", #coloca os valores do eixo Y para dentro
                             tickfont=dict(size=10))
            fig.update_traces(cliponaxis=False)

            st.plotly_chart(fig, use_container_width=True, #exibe gráfico na largura do card
                            config={"displayModeBar": False}) #oculta a barra de ferramentas do plotly

def card_expansivel_real(titulo, coluna, dados_tri, tabela_validos, key_slider, col_tempo="Trimestre"):
    valor = f"R$ {str(dados_tri[coluna]).replace(',00', '').strip()}" #remove os decimais
    _card_base(titulo, valor, coluna, tabela_validos, key_slider, f_bilhoes, "#00529B", col_tempo) #chama o card base com conversor de bilhões

def card_expansivel_geral(titulo, coluna, dados_tri, tabela_validos, key_slider, col_tempo="Trimestre"):
    _card_base(titulo, f"{dados_tri[coluna]}", coluna, tabela_validos, key_slider, conv_pct, "#00529B", col_tempo) #conversor de percentual

def card_expansivel_acao(titulo, coluna, dados_tri, tabela_validos, key_slider, simbolo="", col_tempo="Trimestre"):
    _card_base(titulo, f"{simbolo}{dados_tri[coluna]}", coluna, tabela_validos, key_slider, conv_preco, "#00A859", col_tempo) #conversor de preço e símbolo personalizável

def marcacao_preta():
    st.markdown(
        """
       <hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">
       """,
        unsafe_allow_html=True,)

#CONFIGURAÇÃO E SIDEBAR DA PÁGINA =========================================================

st.set_page_config(layout="wide")

st.markdown(
    """
   <style>
       .main .block-container {
           max-width: 100%;
           padding-left: 0.5rem;
           padding-right: 0.5rem;
           padding-top: 1rem;
           padding-bottom: 0rem;
       }
       [data-testid="stSidebar"] {
           width: 100px !important;
       }
       [data-testid="stExpander"] details > div {
           padding: 0.25rem 1rem 0.25rem 0.25rem;
       }
       [data-testid="stVerticalBlockBorderWrapper"] {
           padding: 0.5rem;
       }
   </style>
""",
    unsafe_allow_html=True,)

st.sidebar.title("Menu de Navegação")
pagina = st.sidebar.radio(
    "Escolha uma página:", ["Visão Geral", "Financeiro", "Produção", "Mercado"])

st.sidebar.write(
    "Criado por Fernando Henrique M. Rossignolli, Israel Gomes Galdino, "
    "Luis Felipe de Souza Ferreira e João Pedro Barreto de Almeida")

#PÁGINA VISÃO GERAL ===================================================================================================================

if pagina == "Visão Geral":
    st.title("Visão Geral — Vale S.A.")
    st.markdown("##### Resumo Executivo: Desempenho Financeiro, Operacional e de Mercado")

    #funções necessárias recriadas localmente ----------------------------------
    def local_f_bilhoes(val):
        if pd.isna(val):
            return None
        val_str = str(val).replace("(R$ bi)", "").replace("R$", "").strip()
        if "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            parts = val_str.split(".")
            if len(parts) == 2 and len(parts[1]) == 3 and float(parts[0]) > 10:
                val_str = val_str.replace(".", "")
        try:
            num = float(val_str)
        except ValueError:
            return None
        if abs(num) >= 100:
            return num / 1000.0
        return num

    def local_conv_vol(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip()
        if "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        try:
            num = float(val_str)
            if num >= 100 and "." not in val_str and "," not in str(val):
                return num / 1000.0
            return num
        except ValueError:
            return 0.0

    def local_conv_preco(val):
        if pd.isna(val):
            return None
        val_str = (
            str(val)
            .replace("US$", "")
            .replace("US", "")
            .replace("R$", "")
            .replace("$", "")
            .replace("€", "")
            .replace("\x80", "")
            .strip())
        if "," in val_str and "." in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        elif "," in val_str:
            val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None

    def local_layout(fig, col_tempo, **extra):
        fig.update_layout( #atualiza as configurações de layout da figura
            hovermode="x unified", #unifica as informações no balão ao passar o mouse pelo eixo X
            legend=dict(orientation="h", y=1.1, title=""), #posiciona a legenda na horizontal acima e oculta o título
            xaxis_title=col_tempo, #define título no eixo X
            **extra,)
        return fig

    def local_mostrar(fig):
        st.plotly_chart(fig, use_container_width=True)

    def local_marcacao():
        st.markdown(
            '<hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">',
            unsafe_allow_html=True,)

    #1. alinhamento de período -------------------------------------------------
    df_tri_f_valid = tri_financas.dropna(subset=["Trimestre"]).copy() #remove linhas sem trimestre
    periodos_list = df_tri_f_valid["Trimestre"].unique().tolist() #pega a lista de trimestres únicos disponíveis
    tri_sel = st.selectbox("Selecione o Trimestre para Análise:", options=periodos_list, index=len(periodos_list) - 1) #caixa de seleção de trimestre

    dados_fin = df_tri_f_valid[df_tri_f_valid["Trimestre"] == tri_sel].iloc[0] #pega a linha com os trimestres financeiros selecionado
    df_prod_tri = tri_producao[tri_producao["Trimestre"] == tri_sel].copy() #filtra a tabela de produção para o tri selescionado
    df_merc_tri = tri_mercado[tri_mercado["Trimestre"] == tri_sel].copy() #filtra a tabela de mercado para o tri selescionado

    #2. cards principais de destaque --------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        rec_val = local_f_bilhoes(dados_fin["Receita Líquida"])
        st.metric("Receita Líquida", f"R$ {rec_val:,.2f} Bi" if rec_val else "N/A")

    with c2:
        lucro_val = local_f_bilhoes(dados_fin["Lucro Líquido"])
        st.metric("Lucro Líquido", f"R$ {lucro_val:,.2f} Bi" if lucro_val else "N/A")

    with c3:
        totais_excluir = [
            "Total Norte", "Total Sudeste:", "Total Sul", "Total Centro-Oeste",
            "Produção Total de Minério de Ferro", "Total Canadá", "Produção Total de Níquel",
            "Total Brasil", "Produção Total de Cobre", "Total Sudeste", "Produção Pelotas",
            "Produção Total de Cobalto",]
        sub_fe = df_prod_tri[(df_prod_tri["Produto"] == "Minério de Ferro") & (~df_prod_tri["Local"].isin(totais_excluir))] #filtra excluindo as linhas total e subtotal
        vol_fe = sub_fe["Extração (Mil Toneladas Métricas)"].apply(local_conv_vol).sum() if not sub_fe.empty else 0.0
        st.metric("Produção de Minério de Ferro", f"{vol_fe:,.1f} kt")

    with c4:
        if not df_merc_tri.empty:
            pr_fe = local_conv_preco(df_merc_tri.iloc[0]["Preço Realizado Ferro/t"])
            st.metric("Preço Realizado (Ferro)", f"US$ {pr_fe:,.2f}/t" if pr_fe else "N/A")
        else:
            st.metric("Preço Realizado (Ferro)", "N/A")

    local_marcacao()

    #3. profundidade histórica -------------------------------------------------
    qtd_p = st.slider("Selecione a quantidade de trimestres para visualização histórica:", min_value=3, max_value=len(df_tri_f_valid), value=min(8, len(df_tri_f_valid)), step=1)

    tabela_f_sub = df_tri_f_valid.tail(qtd_p).copy() #seleciona os últimos 'qtd_p' trimestres da tabela financeira para os gráficos
    tabela_m_sub = tri_mercado.tail(qtd_p).copy()

    #4. painel de gráficos cruzados (2x2) --------------------------------------
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Evolução da Receita Líquida vs. Lucro Líquido")
        df_fin_bi = tabela_f_sub.assign( #cria colunas temporárias com o valor em bilhões
            Receita=tabela_f_sub["Receita Líquida"].apply(local_f_bilhoes),
            Lucro=tabela_f_sub["Lucro Líquido"].apply(local_f_bilhoes))

        fig_fin_vis = go.Figure([
            go.Bar(x=df_fin_bi["Trimestre"], y=df_fin_bi["Receita"], name="Receita Líquida", marker_color="#00529B"), #adiciona barras azuis da receita líquida
            go.Scatter(x=df_fin_bi["Trimestre"], y=df_fin_bi["Lucro"], name="Lucro Líquido", mode="lines+markers", line=dict(color="#00A859", width=3))]) #adiciona a linha verde do lucro liquido
        local_mostrar(local_layout(fig_fin_vis, "Trimestre", yaxis_title="R$ (Bilhões)", height=380))

        st.subheader("Preço Realizado Vale vs. Mercado (Minério de Ferro)")
        df_m_clean = tabela_m_sub.assign(
            Realizado=tabela_m_sub["Preço Realizado Ferro/t"].apply(local_conv_preco),
            Mercado=tabela_m_sub["Minério de Ferro"].apply(local_conv_preco))

        fig_merc_vis = go.Figure([
            go.Scatter(x=df_m_clean["Trimestre"], y=df_m_clean["Realizado"], name="Realizado Vale", mode="lines+markers", line=dict(color="#00529B", width=2.5)),
            go.Scatter(x=df_m_clean["Trimestre"], y=df_m_clean["Mercado"], name="Mercado Mundial", mode="lines+markers", line=dict(color="#D97706", width=2.5))])
        local_mostrar(local_layout(fig_merc_vis, "Trimestre", yaxis_title="USD / Tonelada", height=380))

    with g2:
        st.subheader(f"Mix de Produção por Mineral ({tri_sel})")
        df_prod_operacional = df_prod_tri[~df_prod_tri["Local"].isin(totais_excluir)].copy()
        df_prod_operacional["Vol"] = df_prod_operacional["Extração (Mil Toneladas Métricas)"].apply(local_conv_vol)
        df_mix = df_prod_operacional.groupby("Produto")["Vol"].sum().reset_index()

        fig_mix = px.pie(df_mix, values="Vol", names="Produto", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2) #cria o gráfico de rosca
        fig_mix.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0)) #limpa e converte a cotção do dólar para número
        st.plotly_chart(fig_mix, use_container_width=True)

        st.subheader("Desempenho VALE3 (B3) vs. Cotação Dólar (USD/BRL)")
        df_m_clean["Dolar"] = tabela_m_sub["Média Trimestral Dólar (USD/BRL)"].apply(local_conv_preco)
        df_m_clean["VALE3"] = tabela_f_sub.tail(len(df_m_clean))["VALE3 (B3 - BRL)"].apply(local_conv_preco).values

        fig_macro = go.Figure([
            go.Scatter(x=df_m_clean["Trimestre"], y=df_m_clean["VALE3"], name="VALE3 (R$)", mode="lines+markers", line=dict(color="#00A859", width=2.5)), #linha verde para o preço da vale3
            go.Scatter(x=df_m_clean["Trimestre"], y=df_m_clean["Dolar"], name="USD/BRL (R$)", mode="lines+markers", yaxis="y2", line=dict(color="#2563EB", width=2.5))]) #linha azul para cotação do dólar no eixo
        local_layout(fig_macro, "Trimestre", yaxis=dict(title="Preço VALE3 (R$)"), yaxis2=dict(title="Dólar (USD/BRL)", overlaying="y", side="right"), height=380) #configura os dois eixos y e o layout
        local_mostrar(fig_macro)

#PÁGINA FINANCEIRA =====================================================================================

if pagina == "Financeiro":

    st.title("Dados Financeiros da Vale S.A.")


    visao = st.radio(
        "Selecione a Visão:", ["Trimestral", "Anual"], horizontal=True)

    if visao == "Trimestral":
        tabela_financas = tri_financas.copy()
        col_tempo = "Trimestre"
        col_ebit = "EBIT/ Resultado Operacional"
        col_vale3 = "VALE3 (B3 - BRL)"
        col_vale_usd = "VALE (NYSE - USD)"
        col_xvalo = "XVALO (Latibex - EUR)"
        col_divida = "Dívida Líquida (MM)"

        #liquidez corrente apenas no modo Trimestral
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Ativo Circulante"]
            / tabela_financas["Passivo Circulante"])
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Liquidez Corrente"]
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0))
    else:
        tabela_financas = anual_financas.copy()
        col_tempo = "Ano"
        col_ebit = "EBIT"
        col_vale3 = "VALE3 (Fim do Ano)"
        col_vale_usd = "VALE (Fim do Ano)"
        col_xvalo = "XVALO (Fim do Ano)"
        col_divida = "Dívida Líquida"

    #garante a filtragem correta das linhas válidas do período ativo
    tabela_validos = tabela_financas.dropna(subset=[col_tempo]).copy()

    lista_periodos = tabela_validos[col_tempo].unique().tolist()
    periodo_selecionado = st.selectbox(
        f"Selecione o {col_tempo}:", options=lista_periodos)

    dados_tri = tabela_validos[tabela_validos[col_tempo] == periodo_selecionado].iloc[0] #seleciona a linha de dados escolhida

    #LINHA 1 DE CARDS --------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        card_expansivel_real(
            "Receita Líquida",
            "Receita Líquida",
            dados_tri,
            tabela_validos,
            "slider_rec",
            col_tempo=col_tempo,)

    with col2:
        card_expansivel_real(
            "EBITDA (LAJIDA)",
            "EBITDA",
            dados_tri,
            tabela_validos,
            "slider_ebitda",
            col_tempo=col_tempo,)

    with col3:
        card_expansivel_real(
            "Lucro Líquido",
            "Lucro Líquido",
            dados_tri,
            tabela_validos,
            "slider_lucro",
            col_tempo=col_tempo,)

    with col4:
        card_expansivel_geral(
            "Margem Bruta (%)",
            "Margem Bruta (%)",
            dados_tri,
            tabela_validos,
            "slider_margem",
            col_tempo=col_tempo,)

    with col5:
        card_expansivel_real(
            "Dívida Líquida",
            col_divida,
            dados_tri,
            tabela_validos,
            "slider_divliq",
            col_tempo=col_tempo,)

    #LINHA 2 DE CARDS --------------------------------------------------
    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        if visao == "Trimestral":
            dados_tri_copy = dados_tri.copy()
            dados_tri_copy["Liquidez Corrente"] = round(
                dados_tri_copy["Liquidez Corrente"], 3)
            card_expansivel_real(
                "Liquidez Corrente",
                "Liquidez Corrente",
                dados_tri_copy,
                tabela_validos,
                "slider_liqcor",
                col_tempo=col_tempo,)
        else:
            card_expansivel_real(
                "Caixa e Equiv.",
                "Caixa e Equivalentes de Caixa",
                dados_tri,
                tabela_validos,
                "slider_caixa_eq",
                col_tempo=col_tempo,)

    with col7:
        card_expansivel_real(
            "EBIT / Res. Operacional",
            col_ebit,
            dados_tri,
            tabela_validos,
            "slider_resultoper",
            col_tempo=col_tempo,)

    with col8:
        card_expansivel_acao(
            "VALE3 (B3)",
            col_vale3,
            dados_tri,
            tabela_validos,
            "slider_vale3",
            col_tempo=col_tempo,)

    with col9:
            card_expansivel_acao(
                "VALE (NYSE)",
                col_vale_usd,
                dados_tri,
                tabela_validos,
                "slider_vale_usd",
                simbolo="US$ " if visao == "Trimestral" else "",
                col_tempo=col_tempo,)

    with col10:
        card_expansivel_acao(
            "XVALO (Latibex)",
            col_xvalo,
            dados_tri,
            tabela_validos,
            "slider_xvalo",
            simbolo="€",
            col_tempo=col_tempo,)

    marcacao_preta()

    #FILTRO DE PERÍODO (SLIDER GERAL)
    qtd_trimestres = st.slider(
        f"Selecione a quantidade de {col_tempo.lower()}s para visualizar nos gráficos:",
        min_value=3, #define o limite mínimo de 3 períodos
        max_value=len(tabela_validos), #define o máximo como o total de períodos disponíveis
        value=min(12 if visao == "Trimestral" else 6, len(tabela_validos)),
        step=1,)

    tabela_periodo = tabela_validos.tail(qtd_trimestres)

    #PAINEL INFERIOR COM 4 GRÁFICOS GRANDES ==========================================
    col11, col12 = st.columns(2)

    with col11:

        st.subheader("Evolução do Resultado (Receita, EBITDA e Lucro Líquido)")

        def _bi(df, cols):
            #converte as colunas existentes para bilhões
            return df.assign(**{c: df[c].apply(f_bilhoes) for c in cols if c in df.columns})

        def _layout(fig, col_tempo, **extra):
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title=col_tempo,
                **extra,)
            return fig

        def _mostrar(fig):
            st.plotly_chart(fig, use_container_width=True)

        #gráfico 1
        cols_res = ["Receita Líquida", "EBITDA", "Lucro Líquido"]
        fig_resultado = px.line(
            _bi(tabela_periodo, cols_res), x=col_tempo, y=cols_res, markers=True,
            labels={"value": "R$ (Bilhões)", "variable": "Indicador"},)
        _mostrar(_layout(fig_resultado, col_tempo, yaxis_title="R$ (Bilhões)"))

        #gráfico 2
        st.subheader("Composição de Capital / Estrutura")
        cols_balanco = (
            ["Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido"]
            if visao == "Trimestral"
            else ["Dívida Bruta", "Dívida Líquida"])
        fig_balanco = px.bar(
            _bi(tabela_periodo, cols_balanco), x=col_tempo, y=cols_balanco, barmode="group",
            labels={"value": "R$ (Bilhões)", "variable": "Estrutura"},)
        _mostrar(_layout(fig_balanco, col_tempo, bargap=0.15, yaxis_title="R$ (Bilhões)"))

    with col12:

        #gráfico 3
        st.subheader("Geração de Caixa: Operacional (FCO) vs. Livre (FCL)")
        df_fcl = _bi(tabela_periodo, ["Fluxo de Caixa Operacional", "Fluxo de Caixa Livre"])

        fig_caixa = go.Figure([
            go.Bar(x=df_fcl[col_tempo], y=df_fcl["Fluxo de Caixa Operacional"], name="FCO (Operacional)"),
            go.Bar(x=df_fcl[col_tempo], y=df_fcl["Fluxo de Caixa Livre"], name="FCL (Livre)"),])
        _mostrar(_layout(fig_caixa, col_tempo, barmode="group", bargap=0.15, yaxis_title="R$ (Bilhões)"))

        #gráfico 4
        st.subheader("Desempenho das Ações: VALE3 (B3) vs. VALE (NYSE)")
        fig_acoes = go.Figure([
            go.Scatter(
                x=tabela_periodo[col_tempo], y=tabela_periodo[col].apply(conv_preco),
                name=nome, mode="lines+markers", yaxis=eixo,
                line=dict(color=cor, width=2.5),
            )
            for col, nome, eixo, cor in [
                (col_vale3, "VALE3 (B3)", "y", "#00529B"),
                (col_vale_usd, "VALE (NYSE)", "y2", "#00A859"),]])
        _layout(
            fig_acoes, col_tempo,
            yaxis=dict(title="Preço VALE3"),
            yaxis2=dict(title="Preço VALE (USD)", overlaying="y", side="right"),)
        _mostrar(fig_acoes)

    with st.expander("📄 Visualizar Tabela de Dados Brutos do Período"):
        st.dataframe(tabela_periodo, use_container_width=True)

#PÁGINA PRODUÇÃO ===================================================================================================================

if pagina == "Produção":
    st.title("Produção e Operações da Vale S.A.")
    st.markdown("### Mil Toneladas Métricas (kt/Mt)")

    visao_prod = st.radio(
        "Selecione a Visão da Produção:", ["Trimestral", "Anual"], horizontal=True)

    def conv_num_limpo(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).replace(",", ".").strip()
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    #VISÃO ANUAL DE PRODUÇÃO ==============================================================

    if visao_prod == "Anual":
        df_anual_p = anual_producao.copy()
        
        cols_num = [c for c in df_anual_p.columns if c != "Ano"]
        for c in cols_num:
            df_anual_p[c] = df_anual_p[c].apply(conv_num_limpo)

        anos_list = df_anual_p["Ano"].unique().tolist()
        ano_sel = st.selectbox("Selecione o Ano:", options=anos_list, index=len(anos_list) - 1)

        dados_ano = df_anual_p[df_anual_p["Ano"] == ano_sel].iloc[0]

        #KPIs do Ano Selecionado
        st.markdown("### Resumo da Produção do Ano")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                "Minério de Ferro",
                f"{dados_ano['Produção Minério de Ferro']:,.1f} Mt",
                delta=f"Vendas: {dados_ano['Vendas de Minério de Ferro']:,.1f} Mt")
        with k2:
            st.metric(
                "Pelotas",
                f"{dados_ano['Produção de Pelotas']:,.1f} Mt",
                delta=f"Vendas: {dados_ano['Vendas de Pelotas']:,.1f} Mt")
        with k3:
            st.metric(
                "Cobre",
                f"{dados_ano['Produção de Cobre']:,.1f} kt",
                delta=f"Vendas: {dados_ano['Vendas de Cobre']:,.1f} kt")
        with k4:
            st.metric(
                "Níquel",
                f"{dados_ano['Produção de Níquel']:,.1f} kt",
                delta=f"Vendas: {dados_ano['Vendas de Níquel']:,.1f} kt")

        marcacao_preta()

        #gráficos de Produção vs Vendas
        g_col1, g_col2 = st.columns(2)

        with g_col1:
            st.subheader("Minério de Ferro: Produção vs. Vendas (Mt)")
            fig_fe = go.Figure([
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Produção Minério de Ferro"], name="Produção (Mt)", marker_color="#00529B"),
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Vendas de Minério de Ferro"], name="Vendas (Mt)", marker_color="#00A859")])
            fig_fe.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified", #agrupa as barras lado a lado e determina o espaço entre elas
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Milhões de Toneladas (Mt)", height=400)
            st.plotly_chart(fig_fe, use_container_width=True)

            st.subheader("Cobre: Produção vs. Vendas (kt)")
            fig_cu = go.Figure([
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Produção de Cobre"], name="Produção (kt)", marker_color="#D97706"),
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Vendas de Cobre"], name="Vendas (kt)", marker_color="#059669")])
            fig_cu.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Mil Toneladas (kt)", height=400)
            st.plotly_chart(fig_cu, use_container_width=True)

        with g_col2:
            st.subheader("Pelotas: Produção vs. Vendas (Mt)")
            fig_pel = go.Figure([
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Produção de Pelotas"], name="Produção (Mt)", marker_color="#2563EB"),
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Vendas de Pelotas"], name="Vendas (Mt)", marker_color="#10B981")])
            fig_pel.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Milhões de Toneladas (Mt)", height=400)
            st.plotly_chart(fig_pel, use_container_width=True)

            st.subheader("Níquel: Produção vs. Vendas (kt)")
            fig_ni = go.Figure([
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Produção de Níquel"], name="Produção (kt)", marker_color="#7C3AED"),
                go.Bar(x=df_anual_p["Ano"], y=df_anual_p["Vendas de Níquel"], name="Vendas (kt)", marker_color="#EC4899")])
            fig_ni.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Mil Toneladas (kt)", height=400)
            st.plotly_chart(fig_ni, use_container_width=True)

        with st.expander("Visualizar Tabela de Dados Brutos da Produção Anual"):
            st.dataframe(df_anual_p, use_container_width=True)

    #VISÃO TRIMESTRAL DE PRODUÇÃO ==========================================

    else:
        #dicionário de Coordenadas Geográficas das Unidades Operacionais
        coords_vale = {
            "Serra Norte e Leste": {
                "lat": -6.0658,
                "lon": -50.1772,
                "regiao": "PA, Brasil",},
            "S11D": {"lat": -6.4026, "lon": -50.3664, "regiao": "PA, Brasil"},
            "Itabira": {"lat": -19.6178, "lon": -43.2269, "regiao": "MG, Brasil"},
            "Minas Centrais": {
                "lat": -19.9833,
                "lon": -43.8333,
                "regiao": "MG, Brasil",},
            "Mariana": {"lat": -20.3778, "lon": -43.4161, "regiao": "MG, Brasil"},
            "Paraopeba": {"lat": -20.1481, "lon": -44.1350, "regiao": "MG, Brasil"},
            "Vargem Grande": {
                "lat": -20.1472,
                "lon": -43.9861,
                "regiao": "MG, Brasil",},
            "Minas Itabirito": {
                "lat": -20.2528,
                "lon": -43.8033,
                "regiao": "MG, Brasil",},
            "Corumbá": {"lat": -19.0089, "lon": -57.6528, "regiao": "MS, Brasil"},
            "Sossego": {"lat": -6.4350, "lon": -50.0570, "regiao": "PA, Brasil"},
            "Salobo": {"lat": -5.7860, "lon": -50.5370, "regiao": "PA, Brasil"},
            "São Luís": {"lat": -2.5297, "lon": -44.3028, "regiao": "MA, Brasil"},
            "Tubarão 1 e 2": {
                "lat": -20.2858,
                "lon": -40.2447,
                "regiao": "ES, Brasil",},
            "Sudbury, Canadá": {
                "lat": 46.4900,
                "lon": -80.9900,
                "regiao": "Canadá",},
            "Thompson, Canadá": {
                "lat": 55.7433,
                "lon": -97.8558,
                "regiao": "Canadá",},
            "Voisey's Bay, Canadá": {
                "lat": 56.3340,
                "lon": -62.0890,
                "regiao": "Canadá",},
            "Indonésia": {"lat": -2.5500, "lon": 121.3500, "regiao": "Indonésia"},
            "Nova Caledônia": {
                "lat": -22.2700,
                "lon": 166.4500,
                "regiao": "Oceania",},
            "Omã": {"lat": 24.3600, "lon": 56.7100, "regiao": "Omã"},}

        def conv_vol(val):
            if pd.isna(val):
                return 0.0
            val_str = str(val).strip()
            
            #trata vírgula como separador decimal
            if "," in val_str:
                val_str = val_str.replace(".", "").replace(",", ".")
            
            try:
                num = float(val_str)
                #se for um inteiro puro sem ponto/vírgula >= 100 (ex: 978, 909, 145, 200),
                #significa que está em toneladas puras e precisa ser dividido por 1000 para virar Mil Toneladas
                if num >= 100 and "." not in val_str and "," not in str(val):
                    return num / 1000.0
                return num
            except ValueError:
                return 0.0

        tri_producao["Volume_Num"] = tri_producao["Extração (Mil Toneladas Métricas)"].apply(conv_vol)

        #2. filtros Superiores do Mapa
        c_f1, c_f2, c_f3 = st.columns([1, 1, 1])

        with c_f1:
            tri_prod_list = tri_producao["Trimestre"].dropna().unique().tolist()
            tri_prod_sel = st.selectbox(
                "Selecione o Trimestre:",
                options=tri_prod_list, #lista com os trimestres
                index=len(tri_prod_list) - 1,) #seleciona por padrão o trimestre mais recente

        with c_f2:
            prod_list = [
                "Todos os Produtos"] + tri_producao["Produto"].dropna().unique().tolist()
            prod_sel = st.selectbox("Filtrar por Produto:", options=prod_list)

        with c_f3:
            foco_mapa = st.radio(
                "Foco do Mapa:", ["Brasil", "Mundo"], horizontal=True)

        #3. filtragem de dados
        df_tri_p = tri_producao[tri_producao["Trimestre"] == tri_prod_sel].copy()

        totais_excluir = [
            "Total Norte",
            "Total Sudeste:",
            "Total Sul",
            "Total Centro-Oeste",
            "Produção Total de Minério de Ferro",
            "Total Canadá",
            "Produção Total de Níquel",
            "Total Brasil",
            "Produção Total de Cobre",
            "Total Sudeste",
            "Produção Pelotas",
            "Produção Total de Cobalto",]

        #cards de Resumo (KPIs) dinâmicos por trimestre
        st.markdown("### Resumo da Produção do Trimestre")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        def obter_total_prod(produto_nome):
            sub = df_tri_p[df_tri_p["Produto"] == produto_nome]
            if not sub.empty:
                return sub[~sub["Local"].isin(totais_excluir)]["Volume_Num"].sum()
            return 0.0

        with kpi1:
            st.metric(
                "Minério de Ferro",
                f"{obter_total_prod('Minério de Ferro'):,.1f} kt")
        with kpi2:
            st.metric(
                "Pelotas",
                f"{obter_total_prod('Pelotas'):,.1f} kt")
        with kpi3:
            st.metric(
                "Cobre",
                f"{obter_total_prod('Cobre'):,.1f} kt")
        with kpi4:
            st.metric(
                "Níquel",
                f"{obter_total_prod('Níquel'):,.1f} kt")

        #aplica filtro de produto selecionado após cálculo dos KPIs
        if prod_sel != "Todos os Produtos":
            df_tri_p_filtro = df_tri_p[df_tri_p["Produto"] == prod_sel].copy()
        else:
            df_tri_p_filtro = df_tri_p.copy()

        df_mapa = df_tri_p_filtro[~df_tri_p_filtro["Local"].isin(totais_excluir)].copy()

        #mapeia coordenadas geográficas
        df_mapa["lat"] = df_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("lat", None))
        df_mapa["lon"] = df_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("lon", None))
        df_mapa["regiao"] = df_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("regiao", "Global"))

        df_mapa_valid = df_mapa.dropna(subset=["lat", "lon"]).copy()
        df_mapa_valid = df_mapa_valid[df_mapa_valid["Volume_Num"] > 0]

        #escala visual ajustada para visibilidade dos metais valiosos (Níquel e Cobre)
        df_mapa_valid["Tamanho_Bolha"] = df_mapa_valid["Volume_Num"].apply(lambda x: (x**0.35) + 5)

        #4. renderização do Mapa Principal
        st.subheader(f"Mapa de Operações e Unidades de Extração ({tri_prod_sel})")

        if not df_mapa_valid.empty:
            if foco_mapa == "Brasil":
                #filtra pontos em território brasileiro
                df_mapa_br = df_mapa_valid[df_mapa_valid["regiao"].str.contains("Brasil")].copy()

                if not df_mapa_br.empty:
                    fig_mapa = px.scatter_geo(
                        df_mapa_br,
                        lat="lat",
                        lon="lon",
                        size="Tamanho_Bolha",
                        color="Produto",
                        hover_name="Local",
                        hover_data={
                            "Volume_Num": ":,.1f",
                            "regiao": True,
                            "Tamanho_Bolha": False,
                            "lat": False,
                            "lon": False,},
                        labels={
                            "Volume_Num": "Extração (Mil Ton)",
                            "regiao": "Estado",},
                        size_max=28,
                        scope="south america",)

                    #ajusta a câmera para enquadrar O BRASIL INTEIRO com estados
                    fig_mapa.update_geos(
                        visible=True,
                        resolution=50,
                        showcoastlines=True,
                        coastlinecolor="#777777",
                        showland=True,
                        landcolor="#f8f9fa",
                        showcountries=True,
                        countrycolor="#444444",
                        countrywidth=1.5,
                        showsubunits=True,  #exibe a divisão dos estados
                        subunitcolor="#a0a0a0",
                        subunitwidth=1.0,
                        lonaxis_range=[-74, -34],  #enquadra a longitude do Brasil inteiro
                        lataxis_range=[-34, 6],)    #enquadra a latitude do Brasil inteiro
                else:
                    st.info(
                        "Nenhum ponto no Brasil encontrado para os filtros selecionados.")
                    fig_mapa = None
            else:
                fig_mapa = px.scatter_geo(
                    df_mapa_valid,
                    lat="lat",
                    lon="lon",
                    size="Tamanho_Bolha",
                    color="Produto",
                    hover_name="Local",
                    hover_data={
                        "Volume_Num": ":,.1f",
                        "regiao": True,
                        "Tamanho_Bolha": False,
                        "lat": False,
                        "lon": False,},
                    labels={
                        "Volume_Num": "Extração (Mil Ton)",
                        "regiao": "Localização",},
                    size_max=28,
                    projection="natural earth",)

                fig_mapa.update_geos(
                    showcountries=True,
                    countrycolor="lightgray",
                    projection_scale=1.1,)

            if fig_mapa is not None:
                fig_mapa.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=520,
                    legend=dict(orientation="h", y=1.05, x=0),)
                st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

        marcacao_preta()

        #5. painel Inferior: gráficos complementares
        c_p1, c_p2 = st.columns(2)

        with c_p1:
            st.subheader("Ranking de Extração por Unidade")
            df_bar = (
                df_mapa_valid.groupby("Local")["Volume_Num"]
                .sum().reset_index().sort_values(by="Volume_Num", ascending=True))

            fig_bar_prod = px.bar(
                df_bar,
                x="Volume_Num",
                y="Local",
                orientation="h",
                labels={
                    "Volume_Num": "Mil Toneladas Métricas",
                    "Local": "Unidade Operacional",},
                color_discrete_sequence=["#00A859"],)
            fig_bar_prod.update_layout(
                height=400, margin=dict(l=0, r=20, t=20, b=0))
            st.plotly_chart(fig_bar_prod, use_container_width=True)

        with c_p2:
            st.subheader("Participação da Produção por Mineral")
            df_pie = (
                df_tri_p_filtro[~df_tri_p_filtro["Local"].isin(totais_excluir)]
                .groupby("Produto")["Volume_Num"].sum().reset_index())

            fig_pie = px.pie(
                df_pie,
                values="Volume_Num",
                names="Produto",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,)
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

#PÁGINA MERCADO =====================================================================================================

if pagina == "Mercado":
    st.title("Mercado e Economia")

    def conv_moeda(val): #limpeza de moeda
        if pd.isna(val):
            return None
        val_str = (
            str(val)
            .replace("US$", "")
            .replace("R$", "")
            .replace("$", "")
            .strip())
        if "," in val_str and "." in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        elif "," in val_str:
            val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None

    visao_merc = st.radio(
        "Selecione a Visão:", ["Trimestral", "Anual"], horizontal=True)

    #VISÃO ANUAL =========================================================

    if visao_merc == "Anual":
        df_anual_m = anual_mercado.copy()

        cols_num = df_anual_m.columns.drop("Ano")
        df_anual_m[cols_num] = df_anual_m[cols_num].map(conv_moeda)

        anos_list = df_anual_m["Ano"].unique().tolist()
        ano_sel = st.selectbox(
            "Selecione o Ano:", options=anos_list, index=len(anos_list) - 1)

        idx_sel = df_anual_m[df_anual_m["Ano"] == ano_sel].index[0]
        dados_ano = df_anual_m.loc[idx_sel]
        dados_ano_ant = df_anual_m.loc[idx_sel - 1] if idx_sel > 0 else None

        def calc_delta(coluna, prefixo="US$"):
            val_atual = dados_ano[coluna]
            if dados_ano_ant is not None and pd.notna(val_atual):
                val_ant = dados_ano_ant[coluna]
                if pd.notna(val_ant) and val_ant != 0:
                    diff = val_atual - val_ant
                    pct = diff / val_ant * 100
                    return (
                        f"{diff:+,.2f} ({pct:+,.1f}%) vs {dados_ano_ant['Ano']}")
            return "Sem dados do ano anterior"

        st.markdown(f"### Indicadores Anuais ({ano_sel})")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                "USD/BRL Médio",
                f"R$ {dados_ano['USD/BRL Médio']:,.2f}",
                delta=calc_delta("USD/BRL Médio", "R$"),)
        with k2:
            st.metric(
                "Preço Realizado Ferro",
                f"US$ {dados_ano['Preço Realizado Ferro']:,.2f}/t",
                delta=calc_delta("Preço Realizado Ferro"),)
        with k3:
            st.metric(
                "Preço Realizado Cobre",
                f"US$ {dados_ano['Preço Realizado Cobre']:,.2f}/t",
                delta=calc_delta("Preço Realizado Cobre"),)
        with k4:
            st.metric(
                "Preço Realizado Níquel",
                f"US$ {dados_ano['Preço Realizado Níquel']:,.2f}/t",
                delta=calc_delta("Preço Realizado Níquel"),)

        marcacao_preta()

        #Gráficos Anuais
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("Minério de Ferro: Realizado Vale vs. Média Mundial")
            fig_fe_a = go.Figure([
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Realizado Ferro"],
                    name="Realizado Vale (USD/t)",
                    marker_color="#00529B",),
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Médio do Ferro (Mundial)"],
                    name="Média Mundial (BRL/t)",
                    marker_color="#00A859",),])
            fig_fe_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="Preço",
                height=400,)
            st.plotly_chart(fig_fe_a, use_container_width=True)

            st.subheader("Cobre: Realizado Vale vs. Média Mundial (USD/t)")
            fig_cu_a = go.Figure([
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Realizado Cobre"],
                    name="Realizado Vale",
                    marker_color="#D97706",),
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Médio do Cobre (Mundial)"],
                    name="Média Mundial",
                    marker_color="#059669",
                ),])
            fig_cu_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="USD / Tonelada",
                height=400,)
            st.plotly_chart(fig_cu_a, use_container_width=True)

        with g2:
            st.subheader("Evolução Anual da Cotação do Dólar (USD/BRL)")
            fig_usd_a = px.line(
                df_anual_m,
                x="Ano",
                y="USD/BRL Médio",
                markers=True,
                color_discrete_sequence=["#2563EB"],
                labels={"USD/BRL Médio": "Cotação (R$)"},)
            fig_usd_a.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(fig_usd_a, use_container_width=True)

            st.subheader("Níquel: Realizado Vale vs. Média Mundial (USD/t)")
            fig_ni_a = go.Figure([
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Realizado Níquel"],
                    name="Realizado Vale",
                    marker_color="#7C3AED",),
                go.Bar(
                    x=df_anual_m["Ano"],
                    y=df_anual_m["Preço Médio do Níquel (Mundial)"],
                    name="Média Mundial",
                    marker_color="#EC4899",
                ),])
            fig_ni_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="USD / Tonelada",
                height=400,)
            st.plotly_chart(fig_ni_a, use_container_width=True)

        with st.expander(
            "Visualizar Tabela de Dados Brutos de Mercado (Anual)"):
            st.dataframe(df_anual_m, use_container_width=True)

    #VISÃO TRIMESTRAL =====================================================

    else:
        df_tri_m = tri_mercado.copy()

        cols_num = df_tri_m.columns.drop("Trimestre")
        df_tri_m[cols_num] = df_tri_m[cols_num].map(conv_moeda)

        tri_list = df_tri_m["Trimestre"].dropna().unique().tolist()
        tri_sel = st.selectbox(
            "Selecione o Trimestre:", options=tri_list, index=len(tri_list) - 1)

        idx_sel = df_tri_m[df_tri_m["Trimestre"] == tri_sel].index[0]
        dados_tri_m = df_tri_m.loc[idx_sel]

        st.markdown(f"### Indicadores do Trimestre ({tri_sel})")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            val_dol = dados_tri_m["Média Trimestral Dólar (USD/BRL)"]
            st.metric(
                "Dólar Médio",
                f"R$ {val_dol:,.2f}" if pd.notna(val_dol) else "N/A",)
        with k2:
            val_fe = dados_tri_m["Preço Realizado Ferro/t"]
            st.metric(
                "Realizado Ferro",
                f"US$ {val_fe:,.2f}/t" if pd.notna(val_fe) else "N/A",)
        with k3:
            val_cu = dados_tri_m["Preço Realizado Cobre/t"]
            st.metric(
                "Realizado Cobre",
                f"US$ {val_cu:,.2f}/t" if pd.notna(val_cu) else "N/A",)
        with k4:
            val_ni = dados_tri_m["Preço Realizado Níquel/t"]
            st.metric(
                "Realizado Níquel",
                f"US$ {val_ni:,.2f}/t" if pd.notna(val_ni) else "N/A",)

        marcacao_preta()

        qtd_tri_m = st.slider(
            "Selecione a quantidade de trimestres nos gráficos:",
            min_value=3,
            max_value=len(df_tri_m),
            value=min(12, len(df_tri_m)),
            step=1,)

        df_tri_m_sub = df_tri_m.tail(qtd_tri_m)

        g1, g2 = st.columns(2)

        with g1:
            st.subheader(
                "Minério de Ferro: Realizado Vale vs. Mercado (USD/t)")
            fig_fe_t = go.Figure([
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Preço Realizado Ferro/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#00529B", width=2.5),),
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Minério de Ferro"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#00A859", width=2.5),),])
            fig_fe_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_fe_t, use_container_width=True)

            st.subheader("Cobre: Realizado Vale vs. Mercado (USD/t)")
            fig_cu_t = go.Figure([
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Preço Realizado Cobre/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#D97706", width=2.5),),
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Cobre"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#059669", width=2.5),
                ),])
            fig_cu_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_cu_t, use_container_width=True)

        with g2:
            st.subheader("Evolução do Câmbio USD/BRL")
            fig_usd_t = px.line(
                df_tri_m_sub,
                x="Trimestre",
                y="Média Trimestral Dólar (USD/BRL)",
                markers=True,
                color_discrete_sequence=["#2563EB"],
                labels={"Média Trimestral Dólar (USD/BRL)": "R$"},)
            fig_usd_t.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(fig_usd_t, use_container_width=True)

            st.subheader("Níquel: Realizado Vale vs. Mercado (USD/t)")
            fig_ni_t = go.Figure([
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Preço Realizado Níquel/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#7C3AED", width=2.5),),
                go.Scatter(
                    x=df_tri_m_sub["Trimestre"],
                    y=df_tri_m_sub["Níquel"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#EC4899", width=2.5),
                ),])
            fig_ni_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_ni_t, use_container_width=True)

        with st.expander(
            "Visualizar Tabela de Dados Brutos de Mercado (Trimestral)"):
            st.dataframe(df_tri_m, use_container_width=True)
