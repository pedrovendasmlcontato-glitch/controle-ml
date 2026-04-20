import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(layout="wide")

# ---------------- LOGIN ----------------
usuarios = {
    "raul": "123",
    "pedro": "123",
    "vini": "123"
}

if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_login():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == senha:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

def logout():
    st.session_state.logado = False
    st.rerun()

if not st.session_state.logado:
    tela_login()
    st.stop()

# ---------------- CONEXÃO ----------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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
st.sidebar.write(f"👤 {st.session_state.usuario}")

if st.sidebar.button("Sair"):
    logout()

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

    faturamento = vendas["preco"].sum() if not vendas.empty else 0
    lucro = vendas["lucro"].sum() if not vendas.empty else 0
    custo_fixo = fixos["valor"].sum() if not fixos.empty else 0
    invest_total = invest["valor"].sum() if not invest.empty else 0

    st.title("📊 Dashboard")

    st.metric("Faturamento", f"R$ {faturamento:.2f}")
    st.metric("Lucro Bruto", f"R$ {lucro:.2f}")
    st.metric("Lucro Real", f"R$ {lucro - custo_fixo - invest_total:.2f}")

# ---------------- PRODUTOS ----------------
elif menu == "📦 Produtos":

    st.title("📦 Produtos")

    df = carregar_df("produtos")

    st.subheader("➕ Novo Produto")
    nome = st.text_input("Nome")
    custo = st.number_input("Custo")
    estoque = st.number_input("Estoque", step=1)

    if st.button("Cadastrar"):
        inserir("produtos", {"nome": nome, "custo": custo, "estoque": estoque, "ativo":1})
        st.success("Cadastrado")

    st.divider()

    if not df.empty:
        st.subheader("✏️ Editar / Excluir")

        prod_id = st.selectbox("Produto", df["id"])
        prod = df[df["id"] == prod_id].iloc[0]

        novo_nome = st.text_input("Nome", value=prod["nome"])
        novo_custo = st.number_input("Custo", value=float(prod["custo"]))
        novo_estoque = st.number_input("Estoque", value=int(prod["estoque"]))

        col1, col2 = st.columns(2)

        if col1.button("Atualizar Produto"):
            atualizar("produtos",
                      {"nome": novo_nome, "custo": novo_custo, "estoque": novo_estoque},
                      "id", prod_id)
            st.success("Atualizado")

        if col2.button("Excluir Produto"):
            deletar("produtos", "id", prod_id)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- EMBALAGENS ----------------
elif menu == "📦 Embalagens":

    st.title("📦 Embalagens")

    df = carregar_df("embalagens")
    produtos = carregar_df("produtos")

    st.subheader("➕ Nova Embalagem")

    if not produtos.empty:
        produto = st.selectbox("Produto", produtos["nome"])
        desc = st.text_input("Descrição")
        custo_total = st.number_input("Custo total")
        qtd = st.number_input("Quantidade", step=1)

        if st.button("Cadastrar Embalagem"):
            inserir("embalagens", {
                "produto": produto,
                "descricao": desc,
                "custo_unit": custo_total/qtd,
                "estoque": qtd,
                "ativo":1
            })
            st.success("Cadastrado")

    st.divider()

    if not df.empty:
        st.subheader("✏️ Editar / Excluir")

        emb_id = st.selectbox("Embalagem", df["id"])
        emb = df[df["id"] == emb_id].iloc[0]

        nova_desc = st.text_input("Descrição", value=emb["descricao"])
        novo_custo = st.number_input("Custo unitário", value=float(emb["custo_unit"]))
        novo_estoque = st.number_input("Estoque", value=int(emb["estoque"]))

        col1, col2 = st.columns(2)

        if col1.button("Atualizar Embalagem"):
            atualizar("embalagens",
                      {"descricao": nova_desc, "custo_unit": novo_custo, "estoque": novo_estoque},
                      "id", emb_id)
            st.success("Atualizado")

        if col2.button("Excluir Embalagem"):
            deletar("embalagens", "id", emb_id)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- CUSTOS ----------------
elif menu == "📅 Custos":

    st.title("📅 Custos Mensais")

    df = carregar_df("custos_mensais")

    st.subheader("➕ Novo Custo")

    mes = st.text_input("Mês")
    valor = st.number_input("Valor")
    desc = st.text_input("Descrição")

    if st.button("Salvar Custo"):
        inserir("custos_mensais", {"mes": mes, "valor": valor, "descricao": desc})
        st.success("Salvo")

    st.divider()

    if not df.empty:
        st.subheader("✏️ Editar / Excluir")

        cid = st.selectbox("Custo", df["id"])
        c = df[df["id"] == cid].iloc[0]

        novo_mes = st.text_input("Mês", value=c["mes"])
        novo_valor = st.number_input("Valor", value=float(c["valor"]))
        nova_desc = st.text_input("Descrição", value=c["descricao"])

        col1, col2 = st.columns(2)

        if col1.button("Atualizar Custo"):
            atualizar("custos_mensais",
                      {"mes": novo_mes, "valor": novo_valor, "descricao": nova_desc},
                      "id", cid)
            st.success("Atualizado")

        if col2.button("Excluir Custo"):
            deletar("custos_mensais", "id", cid)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- INVESTIMENTOS ----------------
elif menu == "💸 Investimentos":

    st.title("💸 Investimentos")

    df = carregar_df("investimentos")

    st.subheader("➕ Novo Investimento")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")

    if st.button("Salvar Investimento"):
        inserir("investimentos", {
            "data": str(datetime.today()),
            "descricao": desc,
            "valor": valor
        })
        st.success("Salvo")

    st.divider()

    if not df.empty:
        st.subheader("✏️ Editar / Excluir")

        iid = st.selectbox("Investimento", df["id"])
        i = df[df["id"] == iid].iloc[0]

        nova_desc = st.text_input("Descrição", value=i["descricao"])
        novo_valor = st.number_input("Valor", value=float(i["valor"]))

        col1, col2 = st.columns(2)

        if col1.button("Atualizar Investimento"):
            atualizar("investimentos",
                      {"descricao": nova_desc, "valor": novo_valor},
                      "id", iid)
            st.success("Atualizado")

        if col2.button("Excluir Investimento"):
            deletar("investimentos", "id", iid)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- METAS ----------------
elif menu == "🎯 Metas":

    st.title("🎯 Metas")

    df = carregar_df("metas")

    st.subheader("➕ Nova Meta")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")
    tipo = st.selectbox("Tipo", ["Reinvestir", "Retirada"])

    if st.button("Salvar Meta"):
        inserir("metas", {"descricao": desc, "valor": valor, "tipo": tipo})
        st.success("Salvo")

    st.divider()

    if not df.empty:
        st.subheader("✏️ Editar / Excluir")

        mid = st.selectbox("Meta", df["id"])
        m = df[df["id"] == mid].iloc[0]

        nova_desc = st.text_input("Descrição", value=m["descricao"])
        novo_valor = st.number_input("Valor", value=float(m["valor"]))
        novo_tipo = st.selectbox("Tipo", ["Reinvestir", "Retirada"],
                                 index=0 if m["tipo"]=="Reinvestir" else 1)

        col1, col2 = st.columns(2)

        if col1.button("Atualizar Meta"):
            atualizar("metas",
                      {"descricao": nova_desc, "valor": novo_valor, "tipo": novo_tipo},
                      "id", mid)
            st.success("Atualizado")

        if col2.button("Excluir Meta"):
            deletar("metas", "id", mid)
            st.warning("Excluído")

    st.dataframe(df)

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
