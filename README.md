# Sistema de Biblioteca

Projeto de Python que fiz pra praticar Programação Orientada a Objetos. 

Esse projeto começou como um trabalho da faculdade, e depois fui voltando nele e adicionando/melhorando algumas coisas por conta própria (tratamento de erros, cálculo de multa, organização do código).

## O que ele faz

- Cadastra livros e usuários
- Faz empréstimo de livro (verifica se tem exemplar disponível e se o usuário não está com pendência em atraso)
- Faz devolução e calcula multa automaticamente se atrasou
- Lista livros, usuários e empréstimos (todos, em aberto ou atrasados)
- Salva tudo em arquivos JSON, então os dados continuam lá mesmo depois de fechar o programa

## Regras que usei

- Prazo de empréstimo: 14 dias
- Multa: R$ 1,50 por dia de atraso
- Se o usuário estiver com empréstimo atrasado, não consegue pegar outro livro até devolver

## Tecnologias

Só Python puro, usando bibliotecas que já vêm nativas (`json`, `os`, `datetime`). Não precisa instalar nada, só rodar.

## Como rodar

```bash
python biblioteca.py
```

Abre um menu no terminal. Na primeira vez que rodar, ele cria sozinho uma pasta `dados/` pra guardar os arquivos JSON.

## Como o código está organizado

Deixei tudo em um arquivo só, dividido em partes:

1. Classes (`Livro`, `Usuario`, `Emprestimo`)
2. Funções pra salvar/carregar os JSON
3. Classe `Biblioteca` com as regras de negócio (emprestar, devolver, calcular multa)
4. Menu do terminal
