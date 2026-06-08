import streamlit as st
from neo4j import GraphDatabase

# ==========================================
# 1. CONFIGURAÇÃO DE CONEXÃO
# ==========================================
URI = "neo4j+s://a6767905.databases.neo4j.io"
USUARIO = "a6767905"
SENHA = "KeVjb8qQN8bHzfvlmXfGNuVvp4tZffz0buYeXlfERFo"

class SpotifyGraphDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def fechar_conexao(self):
        self.driver.close()

    # --- SETUP INICIAL COM MASSA DE DADOS ---
    def criar_rede_musical(self):
        query = """
        CREATE (neo:Genero {nome: "Neo Soul"}), (rb:Genero {nome: "R&B"}), (hr:Genero {nome: "Hard Rock"}), (pop:Genero {nome: "Pop"}), (hiphop:Genero {nome: "Hip Hop"})
        CREATE (a1:Artista {nome: "Erykah Badu"})-[:TOCA]->(neo), (a2:Artista {nome: "Frank Ocean"})-[:TOCA]->(rb), (a3:Artista {nome: "Jorja Smith"})-[:TOCA]->(rb)
        CREATE (a4:Artista {nome: "Guns N' Roses"})-[:TOCA]->(hr), (a5:Artista {nome: "Aerosmith"})-[:TOCA]->(hr), (a6:Artista {nome: "The Weeknd"})-[:TOCA]->(pop)
        CREATE (a7:Artista {nome: "Kendrick Lamar"})-[:TOCA]->(hiphop), (a8:Artista {nome: "Dua Lipa"})-[:TOCA]->(pop)
        CREATE (u1:Usuario {nome: "Amanda", premium: true}), (u2:Usuario {nome: "Rogério", premium: true}), (u3:Usuario {nome: "João", premium: false})
        CREATE (u4:Usuario {nome: "Juliano", premium: true}), (u5:Usuario {nome: "Beatriz", premium: false})
        CREATE (u1)-[:SEGUE]->(u2), (u1)-[:SEGUE]->(u3), (u1)-[:SEGUE]->(u4)
        CREATE (u2)-[:SEGUE]->(u1), (u2)-[:SEGUE]->(u5), (u3)-[:SEGUE]->(u4)
        CREATE (u4)-[:SEGUE]->(u1), (u4)-[:SEGUE]->(u2), (u5)-[:SEGUE]->(u1), (u5)-[:SEGUE]->(u3)
        CREATE (u1)-[:OUVIU {vezes: 120}]->(a1), (u1)-[:OUVIU {vezes: 85}]->(a2), (u1)-[:OUVIU {vezes: 40}]->(a3)
        CREATE (u2)-[:OUVIU {vezes: 200}]->(a4), (u2)-[:OUVIU {vezes: 150}]->(a5), (u2)-[:OUVIU {vezes: 20}]->(a6)
        CREATE (u3)-[:OUVIU {vezes: 90}]->(a7), (u3)-[:OUVIU {vezes: 45}]->(a6)
        CREATE (u4)-[:OUVIU {vezes: 70}]->(a2), (u4)-[:OUVIU {vezes: 60}]->(a1), (u4)-[:OUVIU {vezes: 110}]->(a8)
        CREATE (u5)-[:OUVIU {vezes: 30}]->(a3), (u5)-[:OUVIU {vezes: 80}]->(a8), (u5)-[:OUVIU {vezes: 55}]->(a4)
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n") 
            session.run(query)
            return "Rede musical volumosa criada com sucesso!"

    # --- C: CREATE (INSERIR NÓ) ---
    def inserir_no_banco(self, tipo_no, nome_no):
        query = f"CREATE (n:{tipo_no} {{nome: $nome}}) RETURN n.nome AS Nome"
        with self.driver.session() as session:
            session.run(query, nome=nome_no)
            return f"✅ {tipo_no} '{nome_no}' inserido no banco com sucesso!"

    # --- C: CREATE (CRIAR RELACIONAMENTO) ---
    def criar_relacionamento(self, tipo_origem, nome_origem, tipo_relacionamento, tipo_destino, nome_destino, propriedades=None):
        query = f"""
        MATCH (a:{tipo_origem} {{nome: $nome_origem}})
        MATCH (b:{tipo_destino} {{nome: $nome_destino}})
        CREATE (a)-[r:{tipo_relacionamento} $props]->(b)
        RETURN a.nome, b.nome
        """
        props = propriedades if propriedades else {}
        with self.driver.session() as session:
            resultado = session.run(query, nome_origem=nome_origem, nome_destino=nome_destino, props=props)
            if resultado.peek():
                return f"✅ Vínculo criado com sucesso entre {nome_origem} e {nome_destino}!"
            return "❌ Erro: Não foi possível conectar. Verifique se os nomes existem."

    # --- R: READ (GRAFO PARA O PYVIS) ---
    def obter_dados_grafo(self):
        query = "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m"
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

    # --- R: READ (LISTAR TUDO) ---
# --- R: READ (LISTAR TUDO ATUALIZADO) ---
    def listar_tudo(self):
        # Buscamos a entidade inteira 'n' para conseguir acessar suas propriedades internas
        query = "MATCH (n) RETURN labels(n)[0] AS Tipo, n.nome AS Nome, n.premium AS Premium ORDER BY Tipo, Nome"
        with self.driver.session() as session:
            resultado = session.run(query)
            lista_dados = []
            for registro in resultado:
                tipo = registro["Tipo"]
                nome = registro["Nome"]
                is_premium = registro["Premium"]
                
                # Tratamento visual para a coluna Premium
                if tipo == "Usuario":
                    # Se for Usuário, mostra 'Sim' ou 'Não' baseado no booleano do banco
                    status_premium = "Sim 👑" if is_premium else "Não"
                else:
                    # Se for Artista ou Gênero, não faz sentido ter plano, então deixamos um traço
                    status_premium = "—"
                
                lista_dados.append({
                    "Tipo": tipo,
                    "Nome": nome,
                    "Plano Premium": status_premium
                })
            return lista_dados
        
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
        query = "MATCH (u:Usuario {nome: $nome}) SET u.premium = true RETURN u.nome AS Nome"
        with self.driver.session() as session:
            resultado = list(session.run(query, nome=nome_usuario))
            if resultado:
                return f"✅ O usuário '{nome_usuario}' foi atualizado para o plano Premium!"
            return "❌ Usuário não encontrado."

    # --- D: DELETE (Ajustado contra Deadlocks) ---
    def remover_entidade(self, tipo_no, nome_no):
        # DETACH DELETE apaga arestas e o nó em uma única transação segura!
        query = f"MATCH (n:{tipo_no} {{nome: $nome}}) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query, nome=nome_no)
            return f"🗑️ O(A) {tipo_no} '{nome_no}' e todas as suas conexões foram eliminados."

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
    ["Visualizar Grafo (Rede Completa)", "Listar Tudo (Ver Banco)", "Create (Inserir Dados e Conexões)", "Read (Recomendar Música)", "Update (Atualizar Plano Premium)", "Delete (Remover Dado)"]
)

# ----------------- VISUALIZAR GRAFO -----------------
if operacao == "Visualizar Grafo (Rede Completa)":
    st.header("Visualização Interativa do Grafo")
    
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
            
        net.save_graph('grafo_temp.html')
        with open('grafo_temp.html', 'r', encoding='utf-8') as HtmlFile:
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
elif operacao == "Create (Inserir Dados e Conexões)":
    st.header("CREATE: Inserir Dados e Criar Relacionamentos")
    
    aba1, aba2 = st.tabs(["1. Criar Novo Nó (Entidade)", "2. Criar Conexão (Relacionamento)"])
    
    with aba1:
        st.subheader("Cadastrar Novo Item no Banco")
        tipo_escolhido = st.text_input("Digite o TIPO da entidade (ex: Usuario, Artista, Genero):", key="tipo_no")
        nome_digitado = st.text_input("Digite o NOME dessa entidade:", key="nome_no")
        
        if st.button("Inserir no Banco", key="btn_inserir_no"):
            if tipo_escolhido.strip() == "" or nome_digitado.strip() == "":
                st.error("Preencha ambos os campos.")
            else:
                tipo_formatado = tipo_escolhido.strip().title().replace(" ", "")
                mensagem = db.inserir_no_banco(tipo_formatado, nome_digitado.strip())
                st.success(mensagem)

    with aba2:
        st.subheader("Conectar duas entidades existentes")
        
        dados_atuais = db.listar_tudo()
        if dados_atuais:
            with st.expander("Ver entidades disponíveis no banco"):
                st.dataframe(dados_atuais, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**NÓ DE ORIGEM**")
            tipo_origem = st.text_input("Tipo Origem (ex: Usuario):", "Usuario", key="t_origem")
            nome_origem = st.text_input("Nome Origem:", key="n_origem")
            
        with col2:
            st.markdown("**NÓ DE DESTINO**")
            tipo_destino = st.text_input("Tipo Destino (ex: Artista):", "Artista", key="t_destino")
            nome_destino = st.text_input("Nome Destino:", key="n_destino")
            
        st.divider()
        relacao_escolhida = st.selectbox("Escolha o Relacionamento:", ["SEGUE", "OUVIU", "TOCA"])
        
        propriedades = {}
        if relacao_escolhida == "OUVIU":
            vezes = st.number_input("Quantidade de vezes que ouviu:", min_value=1, value=10)
            propriedades = {"vezes": vezes}
            
        if st.button("Criar Link no Grafo"):
            if nome_origem.strip() == "" or nome_destino.strip() == "":
                st.error("Digite os nomes dos nós de origem e destino.")
            else:
                mensagem_rel = db.criar_relacionamento(tipo_origem, nome_origem.strip(), relacao_escolhida, tipo_destino, nome_destino.strip(), propriedades)
                st.success(mensagem_rel)

# ----------------- READ -----------------
elif operacao == "Read (Recomendar Música)":
    st.header("READ: Motor de Recomendação")
    usuario_alvo = st.text_input("Digite o nome do usuário para recomendar:", "Amanda")
    if st.button("Buscar Recomendações"):
        resultados = db.recomendar_musica(usuario_alvo)
        if resultados:
            st.table(resultados)
        else:
            st.info("Nenhuma nova recomendação encontrada.")

# ----------------- UPDATE -----------------
elif operacao == "Update (Atualizar Plano Premium)":
    st.header("UPDATE: Atualizar Propriedade")
    usuario_update = st.text_input("Digite o nome do usuário:")
    if st.button("Fazer Upgrade"):
        mensagem = db.atualizar_plano(usuario_update)
        st.success(mensagem)

# ----------------- DELETE -----------------
elif operacao == "Delete (Remover Dado)":
    st.header("DELETE: Remover Registro")
    tipo_delete = st.text_input("Digite o TIPO exato do registro (ex: Artista):")
    nome_delete = st.text_input("Digite o NOME exato do registro:")
    
    if st.button("Confirmar Exclusão"):
        if tipo_delete.strip() == "" or nome_delete.strip() == "":
            st.error("Preencha o tipo e o nome corretamente.")
        else:
            tipo_formatado = tipo_delete.strip().title().replace(" ", "")
            mensagem = db.remover_entidade(tipo_formatado, nome_delete.strip())
            st.warning(mensagem)