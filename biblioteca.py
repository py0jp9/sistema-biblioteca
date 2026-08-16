"""
biblioteca.py
=============
Sistema de biblioteca em Python puro, num arquivo só.

Guarda os dados em arquivos .json (não é banco de dados, é só um arquivo
de texto organizado — feito com a biblioteca padrão `json`, que já vem
dentro do Python).

Seções do arquivo (tudo que estava separado em models.py, persistencia.py,
biblioteca.py e main.py, agora junto, na ordem em que o programa é lido):

1. Classes (Livro, Usuario, Emprestimo)
2. Funções de salvar/carregar JSON
3. Classe Biblioteca (regras de negócio: emprestar, devolver, multa)
4. Menu / interface de terminal
"""

import json
import os
from datetime import date, timedelta


# =====================================================================
# 1. CLASSES (Livro, Usuario, Emprestimo)
# =====================================================================

class Livro:
    def __init__(self, isbn, titulo, autor, quantidade_total, quantidade_disponivel=None):
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.quantidade_total = quantidade_total
        # Se não informar quantidade_disponivel, assume que começa igual ao total
        self.quantidade_disponivel = (
            quantidade_disponivel if quantidade_disponivel is not None else quantidade_total
        )

    def to_dict(self):
        return {
            "isbn": self.isbn,
            "titulo": self.titulo,
            "autor": self.autor,
            "quantidade_total": self.quantidade_total,
            "quantidade_disponivel": self.quantidade_disponivel,
        }

    @staticmethod
    def from_dict(d):
        return Livro(
            isbn=d["isbn"],
            titulo=d["titulo"],
            autor=d["autor"],
            quantidade_total=d["quantidade_total"],
            quantidade_disponivel=d["quantidade_disponivel"],
        )

    def __str__(self):
        return f"[{self.isbn}] {self.titulo} - {self.autor} ({self.quantidade_disponivel}/{self.quantidade_total} disponíveis)"


class Usuario:
    def __init__(self, id_usuario, nome, email):
        self.id_usuario = id_usuario
        self.nome = nome
        self.email = email

    def to_dict(self):
        return {"id_usuario": self.id_usuario, "nome": self.nome, "email": self.email}

    @staticmethod
    def from_dict(d):
        return Usuario(id_usuario=d["id_usuario"], nome=d["nome"], email=d["email"])

    def __str__(self):
        return f"[{self.id_usuario}] {self.nome} <{self.email}>"


class Emprestimo:
    """
    Representa o empréstimo de um livro para um usuário.

    Datas ficam como objetos `date` do Python enquanto o programa roda,
    e viram string (formato 'AAAA-MM-DD') só na hora de salvar em JSON,
    porque JSON não sabe o que é um `date`.
    """

    def __init__(
        self,
        id_emprestimo,
        isbn,
        id_usuario,
        data_emprestimo,
        data_devolucao_prevista,
        data_devolucao_real=None,
        devolvido=False,
    ):
        self.id_emprestimo = id_emprestimo
        self.isbn = isbn
        self.id_usuario = id_usuario
        self.data_emprestimo = data_emprestimo
        self.data_devolucao_prevista = data_devolucao_prevista
        self.data_devolucao_real = data_devolucao_real
        self.devolvido = devolvido

    def to_dict(self):
        return {
            "id_emprestimo": self.id_emprestimo,
            "isbn": self.isbn,
            "id_usuario": self.id_usuario,
            "data_emprestimo": self.data_emprestimo.isoformat(),
            "data_devolucao_prevista": self.data_devolucao_prevista.isoformat(),
            "data_devolucao_real": (
                self.data_devolucao_real.isoformat() if self.data_devolucao_real else None
            ),
            "devolvido": self.devolvido,
        }

    @staticmethod
    def from_dict(d):
        return Emprestimo(
            id_emprestimo=d["id_emprestimo"],
            isbn=d["isbn"],
            id_usuario=d["id_usuario"],
            data_emprestimo=date.fromisoformat(d["data_emprestimo"]),
            data_devolucao_prevista=date.fromisoformat(d["data_devolucao_prevista"]),
            data_devolucao_real=(
                date.fromisoformat(d["data_devolucao_real"]) if d["data_devolucao_real"] else None
            ),
            devolvido=d["devolvido"],
        )

    def __str__(self):
        status = "devolvido" if self.devolvido else "em aberto"
        return (
            f"Empréstimo #{self.id_emprestimo} - Livro {self.isbn} - Usuário {self.id_usuario} "
            f"- prevista: {self.data_devolucao_prevista} - status: {status}"
        )


# =====================================================================
# 2. SALVAR / CARREGAR JSON
# =====================================================================

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

ARQUIVO_LIVROS = os.path.join(PASTA_DADOS, "livros.json")
ARQUIVO_USUARIOS = os.path.join(PASTA_DADOS, "usuarios.json")
ARQUIVO_EMPRESTIMOS = os.path.join(PASTA_DADOS, "emprestimos.json")


def carregar_json(caminho):
    """Carrega uma lista de dicionários de um arquivo JSON."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read().strip()
        return json.loads(conteudo) if conteudo else []


def salvar_json(caminho, dados):
    """Salva uma lista de dicionários em um arquivo JSON, formatado (indent=2)."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


# =====================================================================
# 3. CLASSE BIBLIOTECA (regras de negócio)
# =====================================================================

PRAZO_PADRAO_DIAS = 14      # prazo de empréstimo: 14 dias
VALOR_MULTA_POR_DIA = 1.50  # R$ 1,50 por dia de atraso


class BibliotecaError(Exception):
    pass


class Biblioteca:
    def __init__(self):
        self.livros = {}
        self.usuarios = {}
        self.emprestimos = []
        self._proximo_id_usuario = 1
        self._proximo_id_emprestimo = 1
        self._carregar_dados()

    def _carregar_dados(self):
        dados_livros = carregar_json(ARQUIVO_LIVROS)
        self.livros = {d["isbn"]: Livro.from_dict(d) for d in dados_livros}

        dados_usuarios = carregar_json(ARQUIVO_USUARIOS)
        self.usuarios = {d["id_usuario"]: Usuario.from_dict(d) for d in dados_usuarios}
        if self.usuarios:
            self._proximo_id_usuario = max(self.usuarios.keys()) + 1

        dados_emprestimos = carregar_json(ARQUIVO_EMPRESTIMOS)
        self.emprestimos = [Emprestimo.from_dict(d) for d in dados_emprestimos]
        if self.emprestimos:
            self._proximo_id_emprestimo = max(e.id_emprestimo for e in self.emprestimos) + 1

    def salvar(self):
        salvar_json(ARQUIVO_LIVROS, [l.to_dict() for l in self.livros.values()])
        salvar_json(ARQUIVO_USUARIOS, [u.to_dict() for u in self.usuarios.values()])
        salvar_json(ARQUIVO_EMPRESTIMOS, [e.to_dict() for e in self.emprestimos])

    # ---------------- Livros ----------------
    def cadastrar_livro(self, isbn, titulo, autor, quantidade):
        if isbn in self.livros:
            livro = self.livros[isbn]
            livro.quantidade_total += quantidade
            livro.quantidade_disponivel += quantidade
        else:
            self.livros[isbn] = Livro(isbn, titulo, autor, quantidade)
        self.salvar()
        return self.livros[isbn]

    def listar_livros(self):
        return list(self.livros.values())

    # ---------------- Usuários ----------------
    def cadastrar_usuario(self, nome, email):
        usuario = Usuario(self._proximo_id_usuario, nome, email)
        self.usuarios[usuario.id_usuario] = usuario
        self._proximo_id_usuario += 1
        self.salvar()
        return usuario

    def listar_usuarios(self):
        return list(self.usuarios.values())

    # ---------------- Empréstimos ----------------
    def emprestar_livro(self, isbn, id_usuario, prazo_dias=PRAZO_PADRAO_DIAS):
        livro = self.livros.get(isbn)
        if livro is None:
            raise BibliotecaError(f"Livro com ISBN {isbn} não encontrado.")
        if self.usuarios.get(id_usuario) is None:
            raise BibliotecaError(f"Usuário {id_usuario} não encontrado.")
        if livro.quantidade_disponivel <= 0:
            raise BibliotecaError(f"Não há exemplares disponíveis de '{livro.titulo}'.")

        for emp in self.emprestimos:
            if (
                emp.id_usuario == id_usuario
                and not emp.devolvido
                and emp.data_devolucao_prevista < date.today()
            ):
                raise BibliotecaError(
                    "Usuário possui empréstimo em atraso. Regularize antes de pegar outro livro."
                )

        hoje = date.today()
        emprestimo = Emprestimo(
            id_emprestimo=self._proximo_id_emprestimo,
            isbn=isbn,
            id_usuario=id_usuario,
            data_emprestimo=hoje,
            data_devolucao_prevista=hoje + timedelta(days=prazo_dias),
        )
        self._proximo_id_emprestimo += 1

        livro.quantidade_disponivel -= 1
        self.emprestimos.append(emprestimo)
        self.salvar()
        return emprestimo

    def devolver_livro(self, id_emprestimo, data_devolucao=None):
        """Marca o empréstimo como devolvido e retorna o valor da multa (0.0 se não houve atraso)."""
        emprestimo = self._buscar_emprestimo(id_emprestimo)
        if emprestimo is None:
            raise BibliotecaError(f"Empréstimo #{id_emprestimo} não encontrado.")
        if emprestimo.devolvido:
            raise BibliotecaError(f"Empréstimo #{id_emprestimo} já foi devolvido.")

        emprestimo.data_devolucao_real = data_devolucao or date.today()
        emprestimo.devolvido = True

        livro = self.livros.get(emprestimo.isbn)
        if livro:
            livro.quantidade_disponivel += 1

        multa = self.calcular_multa(emprestimo)
        self.salvar()
        return multa

    def _buscar_emprestimo(self, id_emprestimo):
        for emp in self.emprestimos:
            if emp.id_emprestimo == id_emprestimo:
                return emp
        return None

    def calcular_multa(self, emprestimo):
        """
        Regra:
        - Não devolvido ainda: compara a data prevista com HOJE (atraso "acontecendo agora").
        - Já devolvido: compara a data prevista com a data real de devolução.
        - Diferença <= 0 dias -> sem multa.
        - Cada dia de atraso custa VALOR_MULTA_POR_DIA.

        Cuidado: nunca subtrair data_devolucao_real direto sem checar `devolvido`,
        porque se o livro não foi devolvido, data_devolucao_real é None, e não dá
        pra fazer conta de data com None (é aqui que costuma quebrar).
        """
        data_referencia = emprestimo.data_devolucao_real if emprestimo.devolvido else date.today()
        dias_atraso = (data_referencia - emprestimo.data_devolucao_prevista).days

        if dias_atraso <= 0:
            return 0.0
        return round(dias_atraso * VALOR_MULTA_POR_DIA, 2)

    def listar_emprestimos(self, somente_em_aberto=False, somente_atrasados=False):
        resultado = self.emprestimos
        if somente_em_aberto:
            resultado = [e for e in resultado if not e.devolvido]
        if somente_atrasados:
            resultado = [
                e for e in resultado
                if not e.devolvido and e.data_devolucao_prevista < date.today()
            ]
        return resultado


# =====================================================================
# 4. MENU / INTERFACE DE TERMINAL
# =====================================================================

def menu():
    print("\n===== SISTEMA DE BIBLIOTECA =====")
    print("1. Cadastrar livro")
    print("2. Cadastrar usuário")
    print("3. Emprestar livro")
    print("4. Devolver livro")
    print("5. Listar livros")
    print("6. Listar usuários")
    print("7. Listar empréstimos em aberto")
    print("8. Listar empréstimos atrasados")
    print("0. Sair")
    return input("Escolha uma opção: ").strip()


def acao_cadastrar_livro(biblioteca):
    isbn = input("ISBN: ").strip()
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    quantidade = int(input("Quantidade de exemplares: ").strip())
    livro = biblioteca.cadastrar_livro(isbn, titulo, autor, quantidade)
    print(f"Livro cadastrado: {livro}")


def acao_cadastrar_usuario(biblioteca):
    nome = input("Nome: ").strip()
    email = input("Email: ").strip()
    usuario = biblioteca.cadastrar_usuario(nome, email)
    print(f"Usuário cadastrado: {usuario}")


def acao_emprestar_livro(biblioteca):
    isbn = input("ISBN do livro: ").strip()
    id_usuario = int(input("ID do usuário: ").strip())
    emprestimo = biblioteca.emprestar_livro(isbn, id_usuario)
    print(f"Empréstimo realizado: {emprestimo}")
    print(f"Devolução prevista para: {emprestimo.data_devolucao_prevista}")


def acao_devolver_livro(biblioteca):
    id_emprestimo = int(input("ID do empréstimo: ").strip())
    multa = biblioteca.devolver_livro(id_emprestimo)
    if multa > 0:
        print(f"Livro devolvido com atraso. Multa: R$ {multa:.2f}")
    else:
        print("Livro devolvido dentro do prazo. Sem multa.")


def acao_listar_livros(biblioteca):
    livros = biblioteca.listar_livros()
    print("Nenhum livro cadastrado." if not livros else "")
    for livro in livros:
        print(livro)


def acao_listar_usuarios(biblioteca):
    usuarios = biblioteca.listar_usuarios()
    print("Nenhum usuário cadastrado." if not usuarios else "")
    for usuario in usuarios:
        print(usuario)


def acao_listar_emprestimos_em_aberto(biblioteca):
    emprestimos = biblioteca.listar_emprestimos(somente_em_aberto=True)
    print("Nenhum empréstimo em aberto." if not emprestimos else "")
    for emp in emprestimos:
        print(emp)


def acao_listar_emprestimos_atrasados(biblioteca):
    emprestimos = biblioteca.listar_emprestimos(somente_atrasados=True)
    print("Nenhum empréstimo atrasado." if not emprestimos else "")
    for emp in emprestimos:
        multa = biblioteca.calcular_multa(emp)
        print(f"{emp} - multa atual: R$ {multa:.2f}")


def main():
    biblioteca = Biblioteca()

    acoes = {
        "1": acao_cadastrar_livro,
        "2": acao_cadastrar_usuario,
        "3": acao_emprestar_livro,
        "4": acao_devolver_livro,
        "5": acao_listar_livros,
        "6": acao_listar_usuarios,
        "7": acao_listar_emprestimos_em_aberto,
        "8": acao_listar_emprestimos_atrasados,
    }

    while True:
        opcao = menu()
        if opcao == "0":
            print("Até mais!")
            break

        acao = acoes.get(opcao)
        if acao is None:
            print("Opção inválida.")
            continue

        try:
            acao(biblioteca)
        except BibliotecaError as e:
            print(f"Erro: {e}")
        except ValueError:
            print("Entrada inválida. Verifique os números digitados.")


if __name__ == "__main__":
    main()