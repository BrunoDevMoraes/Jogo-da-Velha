# Jogo da Velha - Instrucoes de Instalacao

## Requisitos
- Python 3.8 ou superior

## Instalacao

### 1. Instalar dependencias

```bash
pip install customtkinter
```

Ou usando o arquivo requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Executar o jogo

```bash
python main.py
```

## Solucao de Problemas

### Erro: ModuleNotFoundError: No module named 'customtkinter'

Execute o comando de instalacao:
```bash
pip install customtkinter
```

Se estiver usando ambiente virtual (venv):
```bash
# Windows
.\venv\Scripts\activate
pip install customtkinter

# Linux/Mac
source venv/bin/activate
pip install customtkinter
```

### Erro de versao do Python

Verifique sua versao:
```bash
python --version
```

Se tiver multiplas versoes, tente:
```bash
python3 main.py
# ou
py main.py
```

## Funcionalidades

- **Jogador vs Jogador**: Dois jogadores humanos
- **Jogador vs IA**: Jogue contra algoritmos de IA
- **IA vs IA**: Assista batalhas entre algoritmos
- **Visualizar Arvore**: Veja a arvore de decisao dos algoritmos
- **Comparar Algoritmos**: Relatorio detalhado de performance

## Algoritmos Disponiveis

- Minimax
- Alpha-Beta Pruning
- Alpha-Beta + Transposition Table
- Alpha-Beta + Simetria (D4)
- NegaScout
- Random
