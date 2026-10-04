import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

@st.cache_data
def carregar_tri_financas():
    tri_financas = pd.read_csv(
        "/home/fe007/VS Code/Apps Streamlit/dados_vale(Tri Financeiro).csv",
        encoding="ISO-8859-1",
        sep=";",)
    tri_financas.columns = (
        tri_financas.columns.str.strip())  # remove espaços antes e depois dos nomes
    return tri_financas

@st.cache_data
def carregar_anual_financas():
    anual_financas = pd.read_csv(
        "/home/fe007/VS Code/Apps Streamlit/dados_vale(Anual Financeiro).csv",
        encoding="ISO-8859-1",
        sep=";",)
    anual_financas.columns = anual_financas.columns.str.strip()
    # Converte coluna de Ano para texto limpo
    anual_financas["Ano"] = (
        anual_financas["Ano"].dropna().astype(int).astype(str))
    return anual_financas


tri_financas = carregar_tri_financas()
anual_financas = carregar_anual_financas()

# FUNÇÕES UTILITÁRIAS DE CONVERSÃO E FORMATAÇÃO
# ============================================================


def conv_pct(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace("%", "").replace(",", ".").strip()
    try:
        return float(val_str)
    except ValueError:
        return None


def conv_preco(val):
    if pd.isna(val):
        return None
    val_str = (
        str(val)
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
    val_clean = str(val).replace("(R$ bi)", "").replace(",", ".").strip()
    try:
        num = float(val_clean)
        return num / 1000.0 if abs(num) >= 100 else num
    except ValueError:
        return None


# CARDS EXPANSÍVEIS
# ============================================================


def card_expansivel_acao(
    titulo,
    coluna,
    dados_tri,
    tabela_validos,
    key_slider,
    simbolo="",
    col_tempo="Trimestre",):
    with st.container(border=True):
        st.metric(titulo, f"{simbolo}{dados_tri[coluna]}")
        with st.expander("📈 Histórico"):
            qtd_tri_card = st.slider(
                "Períodos:",
                min_value=3,
                max_value=len(tabela_validos),
                value=min(8, len(tabela_validos)),
                key=key_slider,)

            df_mini = tabela_validos.tail(qtd_tri_card).copy()
            df_mini[coluna] = df_mini[coluna].apply(conv_preco)
            n = len(df_mini)

            fig_mini = px.line(
                df_mini,
                x=col_tempo,
                y=coluna,
                markers=True,
                color_discrete_sequence=["#00A859"],)

            fig_mini.update_layout(
                margin=dict(l=0, r=30, t=0, b=0),
                height=190,
                xaxis_title="",
                yaxis_title="",
                hovermode="x unified",)

            fig_mini.update_xaxes(
                showticklabels=True,
                tickangle=-45,
                tickfont=dict(size=10),
                nticks=6,
                automargin=True,
                range=[-0.3, n - 0.7],)
            fig_mini.update_yaxes(
                automargin=False,
                ticklabelposition="inside",
                tickfont=dict(size=10),)
            fig_mini.update_traces(cliponaxis=False)

            st.plotly_chart(
                fig_mini,
                use_container_width=True,
                config={"displayModeBar": False},)


def card_expansivel_real(
    titulo,
    coluna,
    dados_tri,
    tabela_validos,
    key_slider,
    col_tempo="Trimestre",):
    with st.container(border=True):
        valor_texto = str(dados_tri[coluna]).replace(",00", "").strip()
        st.metric(titulo, f"R$ {valor_texto}")

        with st.expander("📈 Histórico"):
            qtd_tri_card = st.slider(
                "Períodos:",
                min_value=3,
                max_value=len(tabela_validos),
                value=min(8, len(tabela_validos)),
                key=key_slider,)

            df_mini = tabela_validos.tail(qtd_tri_card).copy()
            df_mini[coluna] = df_mini[coluna].apply(f_bilhoes)
            n = len(df_mini)

            fig_mini = px.line(
                df_mini,
                x=col_tempo,
                y=coluna,
                markers=True,
                color_discrete_sequence=["#00529B"],)

            fig_mini.update_layout(
                margin=dict(l=0, r=30, t=0, b=0),
                height=190,
                xaxis_title="",
                yaxis_title="",
                hovermode="x unified",)

            fig_mini.update_xaxes(
                showticklabels=True,
                tickangle=-45,
                tickfont=dict(size=10),
                nticks=6,
                automargin=True,
                range=[-0.3, n - 0.7],)
            fig_mini.update_yaxes(
                automargin=False,
                ticklabelposition="inside",
                tickfont=dict(size=10),)
            fig_mini.update_traces(cliponaxis=False)

            st.plotly_chart(
                fig_mini,
                use_container_width=True,
                config={"displayModeBar": False},)


def card_expansivel_geral(
    titulo,
    coluna,
    dados_tri,
    tabela_validos,
    key_slider,
    col_tempo="Trimestre",):
    with st.container(border=True):
        st.metric(titulo, f"{dados_tri[coluna]}")

        with st.expander("📈 Histórico"):
            qtd_tri_card = st.slider(
                "Períodos:",
                min_value=3,
                max_value=len(tabela_validos),
                value=min(8, len(tabela_validos)),
                key=key_slider,)

            df_mini = tabela_validos.tail(qtd_tri_card).copy()
            df_mini[coluna] = df_mini[coluna].apply(conv_pct)
            n = len(df_mini)

            fig_mini = px.line(
                df_mini,
                x=col_tempo,
                y=coluna,
                markers=True,
                color_discrete_sequence=["#00529B"],)

            fig_mini.update_layout(
                margin=dict(l=0, r=30, t=0, b=0),
                height=190,
                xaxis_title="",
                yaxis_title="",
                hovermode="x unified",)

            fig_mini.update_xaxes(
                showticklabels=True,
                tickangle=-45,
                tickfont=dict(size=10),
                nticks=6,
                automargin=True,
                range=[-0.3, n - 0.7],)
            fig_mini.update_yaxes(
                automargin=False,
                ticklabelposition="inside",
                tickfont=dict(size=10),)
            fig_mini.update_traces(cliponaxis=False)

            st.plotly_chart(
                fig_mini,
                use_container_width=True,
                config={"displayModeBar": False},)


def marcacao_preta():
    st.markdown(
        """
       <hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">
       """,
        unsafe_allow_html=True,)


# CONFIGURAÇÃO E SIDEBAR DA PÁGINA
# ============================================================

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

# PÁGINA FINANCEIRO
# ============================================================

if pagina == "Financeiro":

    visao = st.radio(
        "Selecione a Visão:", ["Trimestral", "Anual"], horizontal=True)

    if visao == "Trimestral":
        tabela_financas = tri_financas
        col_tempo = "Trimestre"
        col_ebit = "EBIT/ Resultado Operacional"
        col_vale3 = "VALE3 (B3 - BRL)"
        col_vale_usd = "VALE (NYSE - USD)"
        col_xvalo = "XVALO (Latibex - EUR)"
        col_divida = "Dívida Líquida (MM)"

        # Liquidez Corrente apenas no modo Trimestral
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Ativo Circulante"]
            / tabela_financas["Passivo Circulante"])
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Liquidez Corrente"]
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0))
    else:
        tabela_financas = anual_financas
        col_tempo = "Ano"
        col_ebit = "EBIT"
        col_vale3 = "VALE3 (Fim do Ano)"
        col_vale_usd = "VALE (Fim do Ano)"
        col_xvalo = "XVALO (Fim do Ano)"
        col_divida = "Dívida Líquida"

    lista_periodos = tabela_financas[col_tempo].dropna().unique().tolist()
    periodo_selecionado = st.selectbox(
        f"Selecione o {col_tempo}:", options=lista_periodos)

    dados_tri = tabela_financas[
        tabela_financas[col_tempo] == periodo_selecionado
    ].iloc[0]
    tabela_validos = tabela_financas.dropna(subset=[col_tempo])

    # LINHA 1 DE CARDS --------------------------------------------------
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

    # LINHA 2 DE CARDS --------------------------------------------------
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

    # FILTRO DE PERÍODO (SLIDER GERAL)
    qtd_trimestres = st.slider(
        f"Selecione a quantidade de {col_tempo.lower()}s para visualizar nos gráficos:",
        min_value=3,
        max_value=len(tabela_validos),
        value=min(12 if visao == "Trimestral" else 6, len(tabela_validos)),
        step=1,)

    tabela_periodo = tabela_validos.tail(qtd_trimestres)

    # PAINEL INFERIOR COM OS 4 GRÁFICOS GRANDES
    # --------------------------------------------------
    col11, col12 = st.columns(2)

    with col11:

        st.subheader("Evolução do Resultado (Receita, EBITDA e Lucro Líquido)")

        # gráfico 1
        df_graf = tabela_periodo.assign(
            **{
                "Receita Líquida": tabela_periodo["Receita Líquida"].apply(
                    f_bilhoes
                ),
                "EBITDA": tabela_periodo["EBITDA"].apply(f_bilhoes),
                "Lucro Líquido": tabela_periodo["Lucro Líquido"].apply(
                    f_bilhoes),})

        fig_resultado = px.line(
            df_graf,
            x=col_tempo,
            y=["Receita Líquida", "EBITDA", "Lucro Líquido"],
            markers=True,
            labels={"value": "R$ (Bilhões)", "variable": "Indicador"},)

        fig_resultado.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, title=""),
            xaxis_title=col_tempo,
            yaxis_title="R$ (Bilhões)",)

        st.plotly_chart(fig_resultado, use_container_width=True)

        # gráfico 2
        st.subheader("Composição de Capital / Estrutura")

        cols_balanco = (
            [
                "Passivo Circulante",
                "Passivo Não Circulante",
                "Patrimônio Líquido",
            ]
            if visao == "Trimestral"
            else ["Dívida Bruta", "Dívida Líquida"])

        fig_balanco = px.bar(
            tabela_periodo,
            x=col_tempo,
            y=cols_balanco,
            barmode="group",
            labels={"value": "R$ (Bilhões)", "variable": "Estrutura"},)

        fig_balanco.update_layout(
            bargap=0.15,
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, title=""),
            xaxis_title=col_tempo,
            yaxis_title="R$ (Bilhões)",)

        st.plotly_chart(fig_balanco, use_container_width=True)

    with col12:

        # gráfico 3
        st.subheader("Geração de Caixa: Operacional (FCO) vs. Livre (FCL)")

        df_fcl = tabela_periodo.assign(
            **{
                "Fluxo de Caixa Livre": tabela_periodo[
                    "Fluxo de Caixa Livre"
                ].apply(f_bilhoes),
                "Fluxo de Caixa Operacional": tabela_periodo[
                    "Fluxo de Caixa Operacional"
                ].apply(f_bilhoes),})

        fig_caixa = go.Figure()

        fig_caixa.add_trace(
            go.Bar(
                x=df_fcl[col_tempo],
                y=df_fcl["Fluxo de Caixa Operacional"],
                name="FCO (Operacional)",))

        fig_caixa.add_trace(
            go.Bar(
                x=df_fcl[col_tempo],
                y=df_fcl["Fluxo de Caixa Livre"],
                name="FCL (Livre)",))

        fig_caixa.update_layout(
            barmode="group",
            bargap=0.15,
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, title=""),
            xaxis_title=col_tempo,
            yaxis_title="R$ (Bilhões)",)

        st.plotly_chart(fig_caixa, use_container_width=True)

        # gráfico 4
        st.subheader("Desempenho das Ações: VALE3 (B3) vs. VALE (NYSE)")

        df_acoes = tabela_periodo.assign(
            VALE3_num=tabela_periodo[col_vale3].apply(conv_preco),
            VALE_USD_num=tabela_periodo[col_vale_usd].apply(conv_preco),)

        fig_acoes = go.Figure()

        fig_acoes.add_trace(
            go.Scatter(
                x=df_acoes[col_tempo],
                y=df_acoes["VALE3_num"],
                name="VALE3 (B3)",
                mode="lines+markers",
                line=dict(color="#00529B", width=2.5),))

        fig_acoes.add_trace(
            go.Scatter(
                x=df_acoes[col_tempo],
                y=df_acoes["VALE_USD_num"],
                name="VALE (NYSE)",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color="#00A859", width=2.5),))

        fig_acoes.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, title=""),
            xaxis_title=col_tempo,
            yaxis=dict(title="Preço VALE3"),
            yaxis2=dict(title="Preço VALE (USD)", overlaying="y", side="right"),)

        st.plotly_chart(fig_acoes, use_container_width=True)

    with st.expander("📄 Visualizar Tabela de Dados Brutos do Período"):
        st.dataframe(tabela_periodo, use_container_width=True)
