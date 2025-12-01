import tkinter as tk
from tkinter import font, messagebox
import random


class JogoDaVelhaLogica:
    def __init__(self):
        self.tabuleiro = [' ' for _ in range(9)]  # 3x3 tabuleiro
        self.jogador_atual = 'X'  # X sempre começa
        self.vencedor = None  # Nenhum vencedor no início

    # Retorna índices vazios
    def movimentos_disponiveis(self):
        return [i for i, x in enumerate(self.tabuleiro) if x == ' ']

    # Verifica se há quadrados vazios
    def quadrados_vazios(self):
        return ' ' in self.tabuleiro  

    # Conta quadrados vazios
    def numero_de_movimentos_vazios(self):
        return self.tabuleiro.count(' ')

    def realizar_movimento(self, quadrado, simbolo):
        if self.tabuleiro[quadrado] == ' ':  # Movimento válido
            self.tabuleiro[quadrado] = simbolo  # Coloca o simbolo no tabuleiro
            if self.verificar_vitoria(quadrado, simbolo):
                self.vencedor = simbolo
            self.jogador_atual = 'O' if simbolo == 'X' else 'X'  # Alterna jogador
            return True
        return False

    def verificar_vitoria(self, quadrado, simbolo):
        # Linha
        linha_idx = quadrado // 3  # Índice da linha
        linha = self.tabuleiro[linha_idx*3: (linha_idx+1)*3]
        if all([s == simbolo for s in linha]):
            return True
        # Coluna
        col_idx = quadrado % 3  # Índice da coluna
        coluna = [self.tabuleiro[col_idx+i*3] for i in range(3)]
        if all([s == simbolo for s in coluna]):
            return True
        # Diagonais
        if quadrado % 2 == 0:  # Apenas quadrados pares estão em diagonais
            diagonal1 = [self.tabuleiro[i] for i in [0, 4, 8]]
            if all([s == simbolo for s in diagonal1]):
                return True
            diagonal2 = [self.tabuleiro[i] for i in [2, 4, 6]]
            if all([s == simbolo for s in diagonal2]):
                return True
        return False


class IALogica:
    def __init__(self, letra_ia):
        self.letra_ia = letra_ia

    # Joga aleatório
    def obter_melhor_movimento(self, jogo_logica):
        possiveis = jogo_logica.movimentos_disponiveis()
        if possiveis:
            return random.choice(possiveis)
        return None

class JogoDaVelhaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo da Velha - Super Python")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        self.modo_jogo = None  # 'PVP' ou 'IA'
        self.ia = None

        # Frames
        self.frame_menu = tk.Frame(self.root)
        self.frame_jogo = tk.Frame(self.root)

        self.criar_menu_principal()

    def criar_menu_principal(self):

        for widget in self.frame_menu.winfo_children():
            widget.destroy()

        # Esconde o frame do jogo
        self.frame_jogo.pack_forget()
        self.frame_menu.pack(fill="both", expand=True, pady=50)

        lbl_titulo = tk.Label(
            self.frame_menu, text="Jogo da Velha", font=("Helvetica", 24, "bold"))
        lbl_titulo.pack(pady=20)

        btn_pvp = tk.Button(self.frame_menu, text="Jogador vs Jogador", font=("Arial", 14), width=20,
                            command=lambda: self.iniciar_jogo(modo='PVP'))
        btn_pvp.pack(pady=10)

        btn_ia = tk.Button(self.frame_menu, text="Jogador vs Computador", font=("Arial", 14), width=20,
                           command=lambda: self.iniciar_jogo(modo='IA'))
        btn_ia.pack(pady=10)

    def iniciar_jogo(self, modo):
        self.modo_jogo = modo
        self.frame_menu.pack_forget()  # Esconde o menu
        self.frame_jogo.pack(fill="both", expand=True)  # Mostra o jogo

        # Inicializa lógica
        self.jogo = JogoDaVelhaLogica()
        self.botoes = []

        # Se for contra IA, inicia a classe da IA (IA joga como 'O')
        if self.modo_jogo == 'IA':
            self.ia = IALogica(letra_ia='O')
        else:
            self.ia = None

        # Limpa widgets anteriores do frame de jogo se houver
        for widget in self.frame_jogo.winfo_children():
            widget.destroy()

        self.criar_widgets_jogo()

    def criar_widgets_jogo(self):
        # Botão Voltar ao Menu
        btn_voltar = tk.Button(
            self.frame_jogo, text="< Voltar ao Menu", command=self.voltar_menu)
        btn_voltar.pack(anchor="w", padx=10, pady=5)

        # Frame do Tabuleiro
        frame_tabuleiro = tk.Frame(self.frame_jogo)
        frame_tabuleiro.pack(pady=10)

        fonte_botao = font.Font(family='Helvetica', size=20, weight='bold')

        for i in range(9):
            btn = tk.Button(frame_tabuleiro, text=" ", font=fonte_botao, width=5, height=2,
                            command=lambda idx=i: self.clique_botao(idx))
            btn.grid(row=i//3, column=i % 3, padx=5, pady=5)
            self.botoes.append(btn)

        self.label_status = tk.Label(
            self.frame_jogo, text=f"Vez do Jogador: {self.jogo.jogador_atual}", font=('Arial', 14))
        self.label_status.pack(pady=10)

        btn_reset = tk.Button(self.frame_jogo, text="Reiniciar Partida",
                              command=self.reiniciar_partida, bg="#dddddd")
        btn_reset.pack(pady=5)

    def clique_botao(self, index):
        # Verifica se pode jogar
        if self.jogo.vencedor or self.jogo.tabuleiro[index] != ' ':
            return

        # Jogada Humana
        self.processar_jogada(index)

        # Jogada Computador
        if self.modo_jogo == 'IA' and not self.jogo.vencedor and self.jogo.quadrados_vazios():
            # Pequeno delay
            self.root.after(500, self.jogada_computador)

    def jogada_computador(self):
        if self.jogo.vencedor or not self.jogo.quadrados_vazios():
            return

        # Pega o movimento da classe de IA
        move = self.ia.obter_melhor_movimento(self.jogo)

        if move is not None:
            self.processar_jogada(move)

    def processar_jogada(self, index):
        jogador_atual = self.jogo.jogador_atual
        sucesso = self.jogo.realizar_movimento(index, jogador_atual)

        if sucesso:
            self.botoes[index].config(
                text=jogador_atual, fg="blue" if jogador_atual == "X" else "red")

            if self.jogo.vencedor:
                self.label_status.config(
                    text=f"Vencedor: {self.jogo.vencedor}!", fg="green")
                messagebox.showinfo(
                    "Fim de Jogo", f"O jogador {self.jogo.vencedor} venceu!")
                self.desabilitar_botoes()
            elif not self.jogo.quadrados_vazios():
                self.label_status.config(text="Empate!", fg="orange")
                messagebox.showinfo("Fim de Jogo", "Empate!")
            else:
                self.label_status.config(
                    text=f"Vez do Jogador: {self.jogo.jogador_atual}", fg="black")

    def desabilitar_botoes(self):
        for btn in self.botoes:
            btn.config(state="disabled")

    def reiniciar_partida(self):
        self.iniciar_jogo(self.modo_jogo)

    def voltar_menu(self):
        self.frame_jogo.pack_forget()
        self.criar_menu_principal()


if __name__ == "__main__":
    root = tk.Tk()
    app = JogoDaVelhaGUI(root)
    root.mainloop()
