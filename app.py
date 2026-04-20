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
    "💸 Investimentos",
    "🎯 Metas",
    "📋 Histórico"
])

# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":

    vendas = carregar_df("vendas")
    custos = carregar_df("custos_mensais")
    produtos = carregar_df("produtos")
    embalagens = carregar_df("embalagens")
    invest = carregar_df("investimentos")

    faturamento = vendas["preco"].sum() if not vendas.empty else 0
    lucro = vendas["lucro"].sum() if not vendas.empty else 0
    custo_fixo = custos["valor"].sum() if not custos.empty else 0
    invest_total = invest["valor"].sum() if not invest.empty else 0

    lucro_real = lucro - custo_fixo - invest_total

    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento", f"R$ {faturamento:.2f}")
    col2.metric("Lucro Bruto", f"R$ {lucro:.2f}")
    col3.metric("Lucro Real", f"R$ {lucro_real:.2f}")

    # ALERTA ESTOQUE
    st.subheader("⚠️ Estoque Baixo")

    baixo_prod = produtos[produtos["estoque"] <= 5] if not produtos.empty else pd.DataFrame()
    baixo_emb = embalagens[embalagens["estoque"] <= 5] if not embalagens.empty else pd.DataFrame()

    if not baixo_prod.empty:
        st.write("📦 Produtos:")
        st.dataframe(baixo_prod[["nome", "estoque"]])

    if not baixo_emb.empty:
        st.write("📦 Embalagens:")
        st.dataframe(baixo_emb[["descricao", "estoque"]])

    if baixo_prod.empty and baixo_emb.empty:
        st.success("Tudo ok com estoque")

    # GRÁFICOS
    if not vendas.empty:
        st.subheader("📈 Lucro por Produto")
        st.bar_chart(vendas.groupby("produto")["lucro"].sum())

        st.subheader("📈 Lucro ao longo do tempo")
        st.line_chart(vendas.groupby("mes")["lucro"].sum())

# ---------------- VENDAS ----------------
elif menu == "💰 Vendas":

    st.title("💰 Nova Venda")

    produtos = carregar_df("produtos")
    embalagens = carregar_df("embalagens")

    if not produtos.empty:

        produto = st.selectbox("Produto", produtos["nome"])
        prod = produtos[produtos["nome"] == produto].iloc[0]

        if prod["estoque"] <= 0:
            st.error("Sem estoque do produto")
        else:

            emb = embalagens[embalagens["produto"] == produto]

            if not emb.empty:
                emb_desc = st.selectbox("Embalagem", emb["descricao"])
                emb_info = emb[emb["descricao"] == emb_desc].iloc[0]

                if emb_info["estoque"] <= 0:
                    st.error("Sem embalagem")
                else:

                    etiqueta = st.number_input("Etiqueta", value=0.10)
                    margem = st.slider("Margem desejada (%)", 0, 100, 30)

                    custo_base = (
                        float(prod["custo"]) +
                        float(emb_info["custo_unit"]) +
                        etiqueta
                    )

                    preco_sugerido = (custo_base + 6) / (1 - 0.12 - (margem/100))

                    st.info(f"💡 Preço sugerido: R$ {preco_sugerido:.2f}")

                    preco = st.number_input("Preço de venda", value=float(preco_sugerido))

                    taxa_ml = preco * 0.12 + 6
                    custo_total = custo_base + taxa_ml
                    lucro = preco - custo_total

                    margem_real = (lucro / preco) * 100 if preco > 0 else 0

                    st.subheader("📊 Análise")

                    st.write(f"Custo base: R$ {custo_base:.2f}")
                    st.write(f"Taxa ML: R$ {taxa_ml:.2f}")
                    st.write(f"Custo total: R$ {custo_total:.2f}")
                    st.write(f"Lucro: R$ {lucro:.2f}")
                    st.write(f"Margem real: {margem_real:.1f}%")

                    if margem_real < margem:
                        st.warning("⚠️ Margem abaixo da desejada!")

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
                                  "id", prod["id"])

                        atualizar("embalagens",
                                  {"estoque": int(emb_info["estoque"]) - 1},
                                  "id", emb_info["id"])

                        st.success("Venda registrada!")

# ---------------- PRODUTOS ----------------
elif menu == "📦 Produtos":

    st.title("📦 Produtos")

    df = carregar_df("produtos")

    nome = st.text_input("Nome")
    custo = st.number_input("Custo")
    estoque = st.number_input("Estoque", step=1)

    if st.button("Cadastrar"):
        inserir("produtos", {"nome": nome, "custo": custo, "estoque": estoque})
        st.success("Cadastrado")

    if not df.empty:
        prod_id = st.selectbox("Produto", df["id"])
        prod = df[df["id"] == prod_id].iloc[0]

        novo_nome = st.text_input("Nome", value=prod["nome"])
        novo_custo = st.number_input("Custo", value=float(prod["custo"]))
        novo_estoque = st.number_input("Estoque", value=int(prod["estoque"]))

        if st.button("Atualizar"):
            atualizar("produtos",
                      {"nome": novo_nome, "custo": novo_custo, "estoque": novo_estoque},
                      "id", prod_id)
            st.success("Atualizado")

        if st.button("Excluir"):
            deletar("produtos", "id", prod_id)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- EMBALAGENS ----------------
elif menu == "📦 Embalagens":

    st.title("📦 Embalagens")

    df = carregar_df("embalagens")
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
                "estoque": qtd
            })
            st.success("Cadastrado")

    if not df.empty:
        emb_id = st.selectbox("Embalagem", df["id"])
        emb = df[df["id"] == emb_id].iloc[0]

        nova_desc = st.text_input("Descrição", value=emb["descricao"])
        novo_custo = st.number_input("Custo unitário", value=float(emb["custo_unit"]))
        novo_estoque = st.number_input("Estoque", value=int(emb["estoque"]))

        if st.button("Atualizar"):
            atualizar("embalagens",
                      {"descricao": nova_desc, "custo_unit": novo_custo, "estoque": novo_estoque},
                      "id", emb_id)
            st.success("Atualizado")

        if st.button("Excluir"):
            deletar("embalagens", "id", emb_id)
            st.warning("Excluído")

    st.dataframe(df)

# ---------------- CUSTOS ----------------
elif menu == "📅 Custos":

    st.title("📅 Custos Mensais")

    df = carregar_df("custos_mensais")

    mes = st.text_input("Mês")
    valor = st.number_input("Valor")
    desc = st.text_input("Descrição")

    if st.button("Salvar"):
        inserir("custos_mensais", {"mes": mes, "valor": valor, "descricao": desc})
        st.success("Salvo")

    st.dataframe(df)

# ---------------- INVESTIMENTOS ----------------
elif menu == "💸 Investimentos":

    st.title("💸 Investimentos")

    df = carregar_df("investimentos")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")

    if st.button("Salvar"):
        inserir("investimentos", {
            "data": str(datetime.today()),
            "descricao": desc,
            "valor": valor
        })
        st.success("Salvo")

    st.dataframe(df)

# ---------------- METAS ----------------
elif menu == "🎯 Metas":

    st.title("🎯 Metas")

    df = carregar_df("metas")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")
    tipo = st.selectbox("Tipo", ["Reinvestir", "Retirada"])

    if st.button("Salvar"):
        inserir("metas", {"descricao": desc, "valor": valor, "tipo": tipo})
        st.success("Salvo")

    st.dataframe(df)

# ---------------- HISTÓRICO ----------------
elif menu == "📋 Histórico":

    st.title("📋 Histórico")

    df = carregar_df("vendas")

    if not df.empty:
        st.dataframe(df)
