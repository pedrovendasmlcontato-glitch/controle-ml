import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(layout="wide")

# 🔐 CONEXÃO
SUPABASE_URL = "https://raktzwefuodxhazkasrb.supabase.co"
SUPABASE_KEY = "sb_publishable_KbXdp-zOKOq-NXt6Th7WUw_9Y9oolQm"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- FUNÇÕES ----------------
def carregar_df(tabela):
    res = supabase.table(tabela).select("*").execute()
    return pd.DataFrame(res.data)

def inserir(tabela, dados):
    supabase.table(tabela).insert(dados).execute()

def deletar(tabela, campo, valor):
    supabase.table(tabela).delete().eq(campo, valor).execute()

def atualizar(tabela, dados, campo, valor):
    supabase.table(tabela).update(dados).eq(campo, valor).execute()

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "💰 Vendas",
    "📦 Produtos",
    "📦 Embalagens",
    "📅 Custos",
    "🔁 Custos Fixos",
    "💸 Investimentos",
    "🎯 Metas",
    "📋 Histórico"
])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    vendas = carregar_df("vendas")
    custos = carregar_df("custos_mensais")
    fixos = carregar_df("custos_fixos")
    invest = carregar_df("investimentos")
    produtos = carregar_df("produtos")

    faturamento = vendas["preco"].sum() if not vendas.empty else 0
    lucro = vendas["lucro"].sum() if not vendas.empty else 0
    custo_fixo = fixos["valor"].sum() if not fixos.empty else 0
    invest_total = invest["valor"].sum() if not invest.empty else 0

    lucro_real = lucro - custo_fixo - invest_total

    st.title("📊 Dashboard")

    st.metric("Faturamento", f"R$ {faturamento:.2f}")
    st.metric("Lucro Bruto", f"R$ {lucro:.2f}")
    st.metric("Lucro REAL", f"R$ {lucro_real:.2f}")

    # Estoque baixo
    st.subheader("⚠️ Estoque baixo")
    if not produtos.empty:
        baixo = produtos[produtos["estoque"] <= 5]
        st.dataframe(baixo[["nome", "estoque"]])

    # Previsão
    st.subheader("📈 Previsão")
    if not vendas.empty:
        vendas_mes = vendas[vendas["mes"] == datetime.today().strftime("%m/%Y")]
        if not vendas_mes.empty:
            dias = datetime.today().day
            fat_prev = (vendas_mes["preco"].sum() / dias) * 30
            lucro_prev = (vendas_mes["lucro"].sum() / dias) * 30
            st.write(f"Faturamento previsto: R$ {fat_prev:.2f}")
            st.write(f"Lucro previsto: R$ {lucro_prev - custo_fixo:.2f}")

# ---------------- PRODUTOS ----------------
elif menu == "📦 Produtos":

    st.title("📦 Produtos")

    nome = st.text_input("Nome")
    custo = st.number_input("Custo")
    estoque = st.number_input("Estoque", step=1)

    if st.button("Cadastrar"):
        inserir("produtos", {"nome": nome, "custo": custo, "estoque": estoque, "ativo":1})

    df = carregar_df("produtos")
    st.dataframe(df)

    if not df.empty:
        prod = st.selectbox("Produto", df["nome"])

        if st.button("Desativar"):
            atualizar("produtos", {"ativo":0}, "nome", prod)

        if st.button("Excluir"):
            deletar("produtos", "nome", prod)

# ---------------- EMBALAGENS ----------------
elif menu == "📦 Embalagens":

    st.title("📦 Embalagens")

    produtos = carregar_df("produtos")

    if not produtos.empty:
        produto = st.selectbox("Produto", produtos["nome"])
        desc = st.text_input("Descrição")
        custo_total = st.number_input("Custo total")
        qtd = st.number_input("Quantidade", step=1)

        if st.button("Cadastrar"):
            inserir("embalagens", {
                "produto": produto,
                "descricao": desc,
                "custo_unit": custo_total/qtd,
                "estoque": qtd,
                "ativo":1
            })

    st.dataframe(carregar_df("embalagens"))

# ---------------- VENDAS ----------------
elif menu == "💰 Vendas":

    st.title("💰 Nova Venda")

    produtos = carregar_df("produtos")
    embalagens = carregar_df("embalagens")

    if not produtos.empty:

        produto = st.selectbox("Produto", produtos["nome"])
        prod = produtos[produtos["nome"] == produto].iloc[0]

        emb = embalagens[embalagens["produto"] == produto]

        if not emb.empty:
            emb_info = emb.iloc[0]

            margem = st.slider("Margem %", 0, 100, 30)

            custo_base = prod["custo"] + emb_info["custo_unit"] + 0.10
            preco_sug = (custo_base + 6) / (1 - 0.12 - margem/100)

            st.info(f"Preço sugerido: R$ {preco_sug:.2f}")

            preco = st.number_input("Preço", value=float(preco_sug))

            taxa = preco * 0.12 + 6
            custo_total = custo_base + taxa
            lucro = preco - custo_total

            st.write(f"Lucro: R$ {lucro:.2f}")

            if st.button("Confirmar venda"):

                inserir("vendas", {
                    "data": str(datetime.today()),
                    "produto": produto,
                    "preco": preco,
                    "custo_total": custo_total,
                    "lucro": lucro,
                    "mes": datetime.today().strftime("%m/%Y")
                })

                atualizar("produtos",
                          {"estoque": int(prod["estoque"]) - 1},
                          "nome", produto)

# ---------------- HISTÓRICO ----------------
elif menu == "📋 Histórico":

    st.title("📋 Histórico")

    df = carregar_df("vendas")

    if not df.empty:
        mes = st.selectbox("Mês", ["Todos"] + list(df["mes"].unique()))
        produto = st.selectbox("Produto", ["Todos"] + list(df["produto"].unique()))

        if mes != "Todos":
            df = df[df["mes"] == mes]

        if produto != "Todos":
            df = df[df["produto"] == produto]

        st.dataframe(df)