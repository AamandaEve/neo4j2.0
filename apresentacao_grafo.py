from neo4j import GraphDatabase

# ==========================================
# 1. CONFIGURAÇÃO DE CONEXÃO
# ==========================================
URI = "neo4j+s://a6767905.databases.neo4j.io" # Pegue no painel do Aura
USUARIO = "neo4j"
SENHA = "COLOQUE_SUA_SENHA_AQUI"

class SpotifyGraphDB:
    def __init__(self, uri, user, password):
        # Conecta ao banco de dados
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def fechar_conexao(self):
        self.driver.close()

    # ==========================================
    # C - CREATE (Inserção de Dados)
    # ==========================================
    def criar_rede_musical(self):
        query = """
        // Gêneros
        CREATE (pop:Genero {nome: 'Pop'})
        CREATE (rock:Genero {nome: 'Rock Indie'})
        CREATE (hiphop:Genero {nome: 'Hip Hop'})

        // Artistas
        CREATE (a1:Artista {nome: 'Arctic Monkeys'})-[:TOCA]->(rock)
        CREATE (a2:Artista {nome: 'The Strokes'})-[:TOCA]->(rock)
        CREATE (a3:Artista {nome: 'Dua Lipa'})-[:TOCA]->(pop)
        CREATE (a4:Artista {nome: 'Kendrick Lamar'})-[:TOCA]->(hiphop)
        CREATE (a5:Artista {nome: 'The Weeknd'})-[:TOCA]->(pop)

        // Usuários
        CREATE (u1:Usuario {nome: 'Amanda', premium: true})
        CREATE (u2:Usuario {nome: 'Carlos', premium: false})
        CREATE (u3:Usuario {nome: 'Beatriz', premium: true})

        // Relacionamentos: Quem segue quem
        CREATE (u1)-[:SEGUE]->(u2)
        CREATE (u1)-[:SEGUE]->(u3)

        // Relacionamentos: Histórico (Quem ouviu o quê)
        CREATE (u1)-[:OUVIU]->(a1)
        CREATE (u2)-[:OUVIU]->(a2)
        CREATE (u3)-[:OUVIU]->(a3)
        CREATE (u3)-[:OUVIU]->(a5)
        """
        with self.driver.session() as session:
            # Apaga tudo antes para evitar dados duplicados se rodar duas vezes
            session.run("MATCH (n) DETACH DELETE n") 
            session.run(query)
            print("✅ CREATE: Rede musical (Usuários, Artistas e Gêneros) criada com sucesso!")

    # ==========================================
    # R - READ (Consulta/Recomendação)
    # ==========================================
    def recomendar_musica(self, nome_usuario):
        query = """
        MATCH (eu:Usuario {nome: $nome})-[:SEGUE]->(amigo:Usuario)-[:OUVIU]->(recomendacao:Artista)
        WHERE NOT (eu)-[:OUVIU]->(recomendacao)
        RETURN recomendacao.nome AS Recomendacao, amigo.nome AS Amigo
        """
        with self.driver.session() as session:
            resultado = session.run(query, nome=nome_usuario)
            print(f"\n🔍 READ: Recomendações para '{nome_usuario}':")
            encontrou = False
            for registro in resultado:
                encontrou = True
                print(f" -> Ouça {registro['Recomendacao']} (recomendado porque {registro['Amigo']} ouviu)")
            
            if not encontrou:
                print(" -> Nenhuma recomendação nova no momento.")

    # ==========================================
    # U - UPDATE (Atualização)
    # ==========================================
    def atualizar_plano(self, nome_usuario):
        query = """
        MATCH (u:Usuario {nome: $nome})
        SET u.premium = true
        RETURN u.nome AS Nome, u.premium AS Status
        """
        with self.driver.session() as session:
            resultado = session.run(query, nome=nome_usuario)
            for registro in resultado:
                status = "Premium" if registro['Status'] else "Gratuito"
                print(f"\n🆙 UPDATE: O usuário '{registro['Nome']}' agora é assinante {status}!")

    # ==========================================
    # D - DELETE (Exclusão)
    # ==========================================
    def remover_artista(self, nome_artista):
        query = """
        MATCH (a:Artista {nome: $nome})-[r]-()
        DELETE r, a
        """
        with self.driver.session() as session:
            session.run(query, nome=nome_artista)
            print(f"\n🗑️ DELETE: O artista '{nome_artista}' e todos os seus vínculos foram removidos da plataforma.")

# ==========================================
# 3. EXECUÇÃO DO PROGRAMA (A Apresentação)
# ==========================================
if __name__ == "__main__":
    # Inicia a conexão
    app = SpotifyGraphDB(URI, USUARIO, SENHA)

    print("--- INICIANDO SISTEMA DE RECOMENDAÇÃO (NEO4J) ---\n")

    # 1. CREATE
    app.criar_rede_musical()

    # 2. READ (Motor de Recomendação)
    # A Amanda segue o Carlos e a Beatriz. 
    # Carlos ouviu The Strokes. Beatriz ouviu Dua Lipa e The Weeknd.
    app.recomendar_musica("Amanda")

    # 3. UPDATE
    app.atualizar_plano("Carlos")

    # 4. DELETE
    app.remover_artista("Kendrick Lamar")

    print("\n--- OPERAÇÕES CONCLUÍDAS COM SUCESSO ---")

    # Fecha a conexão
    app.fechar_conexao()