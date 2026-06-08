import streamlit as st
from neo4j import GraphDatabase
import os

# python -m pip install pyvis
# python -m pip install streamlit
# streamlit run app_interface.py


# ==========================================
# 1. CONFIGURAÇÃO DE CONEXÃO
# ==========================================
URI = "neo4j+s://a6767905.databases.neo4j.io"
USUARIO = "a6767905"
SENHA = "KeVjb8qQN8bHzfvlmXfGNuVvp4tZffz0buYeXlfERFo" # <-- DIGITE SUA SENHA AQUI

class SpotifyGraphDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def fechar_conexao(self):
        self.driver.close()

    # --- SETUP INICIAL ---
    def criar_rede_musical(self):
        query = """
        // 1. Criar Gêneros Musicais
        CREATE (neo:Genero {nome: "Neo Soul"})
        CREATE (rb:Genero {nome: "R&B"})
        CREATE (hr:Genero {nome: "Hard Rock"})
        CREATE (pop:Genero {nome: "Pop"})
        CREATE (hiphop:Genero {nome: "Hip Hop"})

        // 2. Criar Artistas e conectá-los aos Gêneros
        CREATE (a1:Artista {nome: "Erykah Badu"})-[:TOCA]->(neo)
        CREATE (a2:Artista {nome: "Frank Ocean"})-[:TOCA]->(rb)
        CREATE (a3:Artista {nome: "Jorja Smith"})-[:TOCA]->(rb)
        CREATE (a4:Artista {nome: "Guns N' Roses"})-[:TOCA]->(hr)
        CREATE (a5:Artista {nome: "Aerosmith"})-[:TOCA]->(hr)
        CREATE (a6:Artista {nome: "The Weeknd"})-[:TOCA]->(pop)
        CREATE (a7:Artista {nome: "Kendrick Lamar"})-[:TOCA]->(hiphop)
        CREATE (a8:Artista {nome: "Dua Lipa"})-[:TOCA]->(pop)

        // 3. Criar Usuários
        CREATE (u1:Usuario {nome: "Amanda", premium: true})
        CREATE (u2:Usuario {nome: "Rogério", premium: true})
        CREATE (u3:Usuario {nome: "João", premium: false})
        CREATE (u4:Usuario {nome: "Juliano", premium: true})
        CREATE (u5:Usuario {nome: "Beatriz", premium: false})

        // 4. Criar a Rede Social (Conexões densas)
        CREATE (u1)-[:SEGUE]->(u2), (u1)-[:SEGUE]->(u3), (u1)-[:SEGUE]->(u4)
        CREATE (u2)-[:SEGUE]->(u1), (u2)-[:SEGUE]->(u5)
        CREATE (u3)-[:SEGUE]->(u4)
        CREATE (u4)-[:SEGUE]->(u1), (u4)-[:SEGUE]->(u2)
        CREATE (u5)-[:SEGUE]->(u1), (u5)-[:SEGUE]->(u3)

        // 5. Criar o Histórico de Reprodução
        CREATE (u1)-[:OUVIU {vezes: 120}]->(a1), (u1)-[:OUVIU {vezes: 85}]->(a2), (u1)-[:OUVIU {vezes: 40}]->(a3)
        CREATE (u2)-[:OUVIU {vezes: 200}]->(a4), (u2)-[:OUVIU {vezes: 150}]->(a5), (u2)-[:OUVIU {vezes: 20}]->(a6)
        CREATE (u3)-[:OUVIU {vezes: 90}]->(a7), (u3)-[:OUVIU {vezes: 45}]->(a6)
        CREATE (u4)-[:OUVIU {vezes: 70}]->(a2), (u4)-[:OUVIU {vezes: 60}]->(a1), (u4)-[:OUVIU {vezes: 110}]->(a8)
        CREATE (u5)-[:OUVIU {vezes: 30}]->(a3), (u5)-[:OUVIU {vezes: 80}]->(a8), (u5)-[:OUVIU {vezes: 55}]->(a4)
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n") # Limpa o banco antes
            session.run(query)
            return "Rede musical volumosa criada com sucesso!"

    # --- C: CREATE LIVRE ---
    def inserir_no_banco(self, tipo_no, nome_no):
        query = f"CREATE (n:{tipo_no} {{nome: $nome}}) RETURN n.nome AS Nome"
        with self.driver.session() as session:
            session.run(query, nome=nome_no)
            return f"✅ {tipo_no} '{nome_no}' inserido no banco com sucesso!"

    # --- R: READ (GRAFO INTERATIVO) ---
    def obter_dados_grafo(self):
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        """
        with self.driver.session() as session:
            resultado = session.run(query)
            nos = {}
            arestas = []
            
            for record in resultado:
                n = record["n"]
                tipo_n = list(n.labels)[0] if n.labels else "Desconhecido"
                if n.element_id not in nos:
                    nos[n.element_id] = {"id": n.element_id, "label": n.get("nome", "Sem Nome"), "grupo": tipo_n}

                m = record["m"]
                r = record["r"]
                
                if m is not None and r is not None:
                    tipo_m = list(m.labels)[0] if m.labels else "Desconhecido"
                    if m.element_id not in nos:
                        nos[m.element_id] = {"id": m.element_id, "label": m.get("nome", "Sem Nome"), "grupo": tipo_m}
                    arestas.append({"source": n.element_id, "target": m.element_id, "label": r.type})

            return list(nos.values()), arestas

    # --- R: READ (LISTA GERAL) ---
    def listar_tudo(self):
        query = """
        MATCH (n) 
        RETURN labels(n)[0] AS Tipo, n.nome AS Nome 
        ORDER BY Tipo, Nome
        """
        with self.driver.session() as session:
            resultado = session.run(query)
            return [{"Tipo": registro["Tipo"], "Nome": registro["Nome"]} for registro in resultado]

    # --- R: READ (RECOMENDAÇÃO) ---
    def recomendar_musica(self, nome_usuario):
        query = """
        MATCH (eu:Usuario {nome: $nome})-[:SEGUE]->(amigo:Usuario)-[:OUVIU]->(recomendacao:Artista)
        WHERE NOT (eu)-[:OUVIU]->(recomendacao)
        RETURN recomendacao.nome AS Recomendacao, amigo.nome AS Amigo
        """
        with self.driver.session() as session:
            resultado = session.run(query, nome=nome_usuario)
            return [{"Musica": rec["Recomendacao"], "Motivo": f"Seu amigo(a) {rec['Amigo']} ouviu"} for rec in resultado]

    # --- U: UPDATE ---
    def atualizar_plano(self, nome_usuario):
        query = """
        MATCH (u:Usuario {nome: $nome})
        SET u.premium = true
        RETURN u.nome AS Nome
        """
        with self.driver.session() as session:
            resultado = list(session.run(query, nome=nome_usuario))
            if resultado:
                return f"✅ O usuário '{nome_usuario}' foi atualizado para o plano Premium!"
            return "❌ Usuário não encontrado."

    # --- D: DELETE ---
    def remover_entidade(self, tipo_no, nome_no):
        query = f"MATCH (n:{tipo_no} {{nome: $nome}})-[r]-() DELETE r, n"
        query_isolado = f"MATCH (n:{tipo_no} {{nome: $nome}}) DELETE n"
        with self.driver.session() as session:
            session.run(query, nome=nome_no)
            session.run(query_isolado, nome=nome_no)
            return f"🗑️ O(A) {tipo_no} '{nome_no}' foi removido(a) do banco."


# ==========================================
# 2. INTERFACE GRÁFICA (STREAMLIT)
# ==========================================
@st.cache_resource
def iniciar_conexao():
    return SpotifyGraphDB(URI, USUARIO, SENHA)

db = iniciar_conexao()

st.set_page_config(page_title="CRUD Neo4j - Spotify", page_icon="🎵", layout="wide")
st.title("🎵 Sistema de Recomendação - Banco de Grafos")
st.markdown("Interface interativa para demonstrar operações CRUD no banco **Neo4j**.")
st.divider()

# Menu lateral
operacao = st.sidebar.radio(
    "Escolha a Operação:", 
    [
        "Visualizar Grafo (Rede Completa)", 
        "Listar Tudo (Ver Banco)", 
        "Create (Criar Dado)", 
        "Read (Recomendar Música)", 
        "Update (Atualizar Plano Premium)", 
        "Delete (Remover Dado)"
    ]
)

# ----------------- VISUALIZAR GRAFO -----------------
if operacao == "Visualizar Grafo (Rede Completa)":
    st.header("Visualização Interativa do Grafo")
    st.write("Estrutura real do banco NoSQL. Você pode arrastar os nós e dar zoom!")
    
    nos, arestas = db.obter_dados_grafo()
    
    if nos:
        from pyvis.network import Network
        import streamlit.components.v1 as components
        
        net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white', directed=True)
        cores = {"Usuario": "#ADD8E6", "Artista": "#FFB6C1", "Genero": "#FFFACD"}
        
        for no in nos:
            cor = cores.get(no["grupo"], "#90EE90") 
            net.add_node(no["id"], label=no["label"], title=no["grupo"], color=cor)
            
        for aresta in arestas:
            net.add_edge(aresta["source"], aresta["target"], title=aresta["label"])
            
        caminho_arquivo = 'grafo_temp.html'
        net.save_graph(caminho_arquivo)
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as HtmlFile:
            components.html(HtmlFile.read(), height=650)
    else:
        st.info("O banco de dados está vazio. Adicione dados ou resete o banco.")

# ----------------- LISTAR TUDO -----------------
elif operacao == "Listar Tudo (Ver Banco)":
    st.header("Visualização Geral do Banco de Dados")
    dados = db.listar_tudo()
    if dados:
        st.dataframe(dados, use_container_width=True)
    else:
        st.info("O banco de dados está vazio.")
        
    st.divider()
    with st.expander("🛠️ Ferramenta de Setup (Resetar Banco)"):
        st.write("Use este botão para construir a rede musical volumosa padrão.")
        if st.button("Executar Inserção Inicial Completa"):
            mensagem_setup = db.criar_rede_musical()
            st.success(mensagem_setup)
            st.rerun()

# ----------------- CREATE -----------------
elif operacao == "Create (Criar Dado)":
    st.header("CREATE: Inserir Novo Dado")
    tipo_escolhido = st.text_input("Digite o TIPO da entidade (ex: Album, Podcast, Artista, Pais):")
    nome_digitado = st.text_input("Digite o NOME dessa entidade:")
    
    if st.button("Inserir no Banco"):
        if tipo_escolhido.strip() == "" or nome_digitado.strip() == "":
            st.error("Por favor, preencha ambos os campos.")
        else:
            tipo_formatado = tipo_escolhido.strip().title().replace(" ", "")
            mensagem = db.inserir_no_banco(tipo_formatado, nome_digitado)
            st.success(mensagem)

# ----------------- READ -----------------
elif operacao == "Read (Recomendar Música)":
    st.header("READ: Motor de Recomendação")
    usuario_alvo = st.text_input("Digite o nome do usuário para recomendar (ex: Amanda, João):", "Amanda")
    if st.button("Buscar Recomendações"):
        resultados = db.recomendar_musica(usuario_alvo)
        if resultados:
            st.write(f"**Recomendações para {usuario_alvo}:**")
            st.table(resultados)
        else:
            st.info("Nenhuma nova recomendação encontrada para este usuário.")

# ----------------- UPDATE -----------------
elif operacao == "Update (Atualizar Plano Premium)":
    st.header("UPDATE: Atualizar Propriedade")
    st.write("Simulação: Um usuário gratuito decidiu assinar o aplicativo.")
    
    todos_dados = db.listar_tudo()
    usuarios = [d["Nome"] for d in todos_dados if d["Tipo"] == "Usuario"]
    st.caption(f"Usuários no banco: {', '.join(usuarios) if usuarios else 'Nenhum'}")
    
    usuario_update = st.text_input("Digite o nome do usuário (ex: João, Beatriz):")
    if st.button("Fazer Upgrade"):
        mensagem = db.atualizar_plano(usuario_update)
        if "✅" in mensagem:
            st.success(mensagem)
        else:
            st.error(mensagem)

# ----------------- DELETE -----------------
elif operacao == "Delete (Remover Dado)":
    st.header("DELETE: Remover Registro")
    
    dados_atuais = db.listar_tudo()
    if dados_atuais:
        with st.expander("Ver dados disponíveis para exclusão"):
            st.dataframe(dados_atuais, use_container_width=True)
    
    tipo_delete = st.text_input("Digite o TIPO exato do registro (ex: Artista, Genero):")
    nome_delete = st.text_input("Digite o NOME exato do registro:")
    
    if st.button("Confirmar Exclusão"):
        if tipo_delete.strip() == "" or nome_delete.strip() == "":
            st.error("Preencha o tipo e o nome corretamente.")
        else:
            tipo_formatado = tipo_delete.strip().title().replace(" ", "")
            mensagem = db.remover_entidade(tipo_formatado, nome_delete)
            st.warning(mensagem)