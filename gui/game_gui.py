import tkinter as tk
from tkinter import font, messagebox, ttk
from typing import Optional, Dict
import threading
from game.board import Board
from game.game_logic import GameLogic
from ai.base_player import BasePlayer
from ai.random_player import RandomPlayer
from ai.minimax_player import MinimaxPlayer
from ai.alpha_beta_player import AlphaBetaPlayer
from ai.alpha_beta_tt_player import AlphaBetaTTPlayer
from ai.alpha_beta_symmetry_player import AlphaBetaSymmetryPlayer
from ai.negascout_player import NegaScoutPlayer
from utils.constants import PLAYER_X, PLAYER_O
from visualization.game_history import GameHistoryCollector
from visualization.game_visualizer import GameVisualizer
from visualization.tree_data import MinimaxTreeCollector
from visualization.tree_visualizer import TreeVisualizer
from visualization.comparison_visualizer import ComparisonVisualizer


class GameGUI:
    """Graphical user interface for Tic-Tac-Toe game."""

    PLAYER_TYPES = {
        'Minimax': MinimaxPlayer,
        'Alpha-Beta': AlphaBetaPlayer,
        'AB + Transposition': AlphaBetaTTPlayer,
        'AB + Simetria': AlphaBetaSymmetryPlayer,
        'NegaScout': NegaScoutPlayer,
        'Random': RandomPlayer
    }

    def __init__(self, root: tk.Tk):
        """
        Initializes the game GUI.

        Args:
            root: The tkinter root window.
        """
        self.root = root
        self.root.title("Jogo da Velha - IA")
        self.root.geometry("450x600")
        self.root.resizable(False, False)

        self.game_mode: Optional[str] = None
        self.board: Optional[Board] = None
        self.player_x: Optional[BasePlayer] = None
        self.player_o: Optional[BasePlayer] = None
        self.buttons: list = []
        self.current_player = PLAYER_X

        self.score = {PLAYER_X: 0, PLAYER_O: 0, 'tie': 0}

        self.show_visualization = tk.BooleanVar(value=True)
        self.history = GameHistoryCollector()
        self.game_finished = False

        self.frame_menu = tk.Frame(self.root)
        self.frame_game = tk.Frame(self.root)

        self._create_main_menu()

    def _create_main_menu(self):
        """Creates the main menu with game mode selection."""
        for widget in self.frame_menu.winfo_children():
            widget.destroy()

        self.frame_game.pack_forget()
        self.frame_menu.pack(fill="both", expand=True, pady=30)

        lbl_title = tk.Label(
            self.frame_menu,
            text="Jogo da Velha",
            font=("Helvetica", 24, "bold")
        )
        lbl_title.pack(pady=20)

        btn_pvp = tk.Button(
            self.frame_menu,
            text="Jogador vs Jogador",
            font=("Arial", 14),
            width=20,
            command=lambda: self._start_game('PVP')
        )
        btn_pvp.pack(pady=10)

        btn_pve = tk.Button(
            self.frame_menu,
            text="Jogador vs IA",
            font=("Arial", 14),
            width=20,
            command=lambda: self._start_game('PVE')
        )
        btn_pve.pack(pady=10)

        btn_eve = tk.Button(
            self.frame_menu,
            text="IA vs IA",
            font=("Arial", 14),
            width=20,
            command=self._show_ai_selection
        )
        btn_eve.pack(pady=10)

        sep1 = ttk.Separator(self.frame_menu, orient='horizontal')
        sep1.pack(fill='x', pady=20, padx=50)

        btn_tree_viz = tk.Button(
            self.frame_menu,
            text="Visualizar Arvore Minimax",
            font=("Arial", 14),
            width=20,
            command=self._show_tree_visualization_menu,
            bg="#9b59b6",
            fg="white"
        )
        btn_tree_viz.pack(pady=10)

        btn_compare = tk.Button(
            self.frame_menu,
            text="Comparar Algoritmos",
            font=("Arial", 14),
            width=20,
            command=self._show_comparison_screen,
            bg="#e67e22",
            fg="white"
        )
        btn_compare.pack(pady=10)

        sep2 = ttk.Separator(self.frame_menu, orient='horizontal')
        sep2.pack(fill='x', pady=20, padx=50)

        chk_viz = tk.Checkbutton(
            self.frame_menu,
            text="Mostrar Análise ao Final da Partida",
            variable=self.show_visualization,
            font=("Arial", 11)
        )
        chk_viz.pack(pady=5)

        lbl_viz_info = tk.Label(
            self.frame_menu,
            text="(Abre resumo da partida no navegador)",
            font=("Arial", 9),
            fg="gray"
        )
        lbl_viz_info.pack()

    def _show_ai_selection(self):
        """Shows the AI selection screen for AI vs AI mode."""
        for widget in self.frame_menu.winfo_children():
            widget.destroy()

        lbl_title = tk.Label(
            self.frame_menu,
            text="Selecionar IAs",
            font=("Helvetica", 20, "bold")
        )
        lbl_title.pack(pady=20)

        frame_x = tk.Frame(self.frame_menu)
        frame_x.pack(pady=10)
        tk.Label(frame_x, text="Jogador X:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.combo_x = ttk.Combobox(
            frame_x,
            values=list(self.PLAYER_TYPES.keys()),
            state="readonly",
            width=15
        )
        self.combo_x.set("Minimax")
        self.combo_x.pack(side=tk.LEFT, padx=10)

        frame_o = tk.Frame(self.frame_menu)
        frame_o.pack(pady=10)
        tk.Label(frame_o, text="Jogador O:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.combo_o = ttk.Combobox(
            frame_o,
            values=list(self.PLAYER_TYPES.keys()),
            state="readonly",
            width=15
        )
        self.combo_o.set("Minimax")
        self.combo_o.pack(side=tk.LEFT, padx=10)

        chk_viz = tk.Checkbutton(
            self.frame_menu,
            text="Mostrar Análise ao Final",
            variable=self.show_visualization,
            font=("Arial", 11)
        )
        chk_viz.pack(pady=15)

        btn_start = tk.Button(
            self.frame_menu,
            text="Iniciar",
            font=("Arial", 14),
            width=15,
            command=self._start_ai_vs_ai
        )
        btn_start.pack(pady=10)

        btn_back = tk.Button(
            self.frame_menu,
            text="< Voltar",
            command=self._create_main_menu
        )
        btn_back.pack()

    def _start_ai_vs_ai(self):
        """Starts the AI vs AI game with selected algorithms."""
        x_type = self.combo_x.get()
        o_type = self.combo_o.get()

        self.player_x = self.PLAYER_TYPES[x_type](PLAYER_X)
        self.player_o = self.PLAYER_TYPES[o_type](PLAYER_O)

        self._start_game('EVE')

    def _start_game(self, mode: str):
        """
        Initializes and starts a new game.

        Args:
            mode: Game mode ('PVP', 'PVE', or 'EVE').
        """
        self.game_mode = mode
        self.frame_menu.pack_forget()
        self.frame_game.pack(fill="both", expand=True)

        self.board = Board()
        self.current_player = PLAYER_X
        self.buttons = []
        self.history.clear()
        self.game_finished = False

        if mode == 'PVE':
            self.player_o = MinimaxPlayer(PLAYER_O)
        elif mode == 'EVE' and self.player_x is None:
            self.player_x = MinimaxPlayer(PLAYER_X)
            self.player_o = MinimaxPlayer(PLAYER_O)

        for widget in self.frame_game.winfo_children():
            widget.destroy()

        self._create_game_widgets()

        if mode == 'EVE':
            self.root.after(500, self._ai_turn)

    def _create_game_widgets(self):
        """Creates the game board and control widgets."""
        top_frame = tk.Frame(self.frame_game)
        top_frame.pack(fill='x', padx=10, pady=5)

        btn_back = tk.Button(
            top_frame,
            text="< Menu",
            command=self._back_to_menu
        )
        btn_back.pack(side=tk.LEFT)

        self.lbl_score = tk.Label(
            self.frame_game,
            text=self._get_score_text(),
            font=("Arial", 11)
        )
        self.lbl_score.pack(pady=5)

        frame_board = tk.Frame(self.frame_game)
        frame_board.pack(pady=10)

        btn_font = font.Font(family='Helvetica', size=20, weight='bold')

        for i in range(9):
            btn = tk.Button(
                frame_board,
                text=" ",
                font=btn_font,
                width=5,
                height=2,
                command=lambda idx=i: self._on_button_click(idx)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            self.buttons.append(btn)

        self.lbl_status = tk.Label(
            self.frame_game,
            text=f"Vez do Jogador: {self.current_player}",
            font=("Arial", 14)
        )
        self.lbl_status.pack(pady=10)

        self.lbl_stats = tk.Label(
            self.frame_game,
            text="",
            font=("Arial", 10),
            fg="gray"
        )
        self.lbl_stats.pack(pady=5)

        self.lbl_processing = tk.Label(
            self.frame_game,
            text="",
            font=("Arial", 10),
            fg="#3498db"
        )
        self.lbl_processing.pack(pady=5)

        btn_reset = tk.Button(
            self.frame_game,
            text="Reiniciar Partida",
            command=lambda: self._start_game(self.game_mode),
            bg="#dddddd"
        )
        btn_reset.pack(pady=5)

        self.btn_show_analysis = tk.Button(
            self.frame_game,
            text="Ver Análise da Partida",
            command=self._show_analysis,
            state="disabled",
            bg="#3498db",
            fg="white"
        )
        self.btn_show_analysis.pack(pady=10)

    def _get_score_text(self) -> str:
        """Returns formatted score text."""
        return f"Placar - X: {self.score[PLAYER_X]} | O: {self.score[PLAYER_O]} | Empates: {self.score['tie']}"

    def _on_button_click(self, index: int):
        """
        Handles button click events.

        Args:
            index: The clicked button index (0-8).
        """
        if self.game_mode == 'EVE':
            return

        if self.game_finished or self.board.cells[index] != ' ':
            return

        self._make_move(index)

        if self.game_mode == 'PVE' and not GameLogic.is_terminal(self.board):
            self.lbl_processing.config(text="IA pensando...")
            self.root.update()
            self.root.after(100, self._ai_turn)

    def _ai_turn(self):
        """Executes the AI's turn."""
        if GameLogic.is_terminal(self.board):
            return

        self.lbl_processing.config(text="IA calculando melhor jogada...")
        self.root.update()

        player = self.player_x if self.current_player == PLAYER_X else self.player_o

        board_before = self.board.cells.copy()
        move, stats = player.get_move(self.board)

        if move != -1:
            self._make_move(move)

            if isinstance(player, (MinimaxPlayer, AlphaBetaPlayer, AlphaBetaTTPlayer,
                                   AlphaBetaSymmetryPlayer, NegaScoutPlayer)):
                self.history.record_move(
                    player=player.symbol,
                    chosen_position=move,
                    chosen_score=stats.get('chosen_score', 0),
                    board_before=board_before,
                    board_after=self.board.cells.copy(),
                    alternatives=stats.get('alternatives', []),
                    nodes_evaluated=stats['nodes_evaluated'],
                    time_ms=stats['time_ms']
                )

            self._show_stats(player.get_name(), stats)
            self.lbl_processing.config(text="")

            if self.game_mode == 'EVE' and not GameLogic.is_terminal(self.board):
                self.root.after(500, self._ai_turn)

    def _show_stats(self, player_name: str, stats: Dict):
        """
        Displays AI statistics.

        Args:
            player_name: Name of the AI algorithm.
            stats: Dictionary with nodes_evaluated and time_ms.
        """
        text = f"{player_name}: {stats['nodes_evaluated']} nós | {stats['time_ms']:.1f}ms"
        self.lbl_stats.config(text=text)

    def _make_move(self, index: int):
        """
        Executes a move on the board and updates the GUI.

        Args:
            index: The move index (0-8).
        """
        player = self.current_player
        self.board.make_move(index, player)
        self.current_player = self.board.current_player

        color = "blue" if player == PLAYER_X else "red"
        self.buttons[index].config(text=player, fg=color)

        winner = GameLogic.check_winner(self.board)

        if winner:
            self.game_finished = True
            self.score[winner] += 1
            self.lbl_score.config(text=self._get_score_text())
            self.lbl_status.config(text=f"Vencedor: {winner}!", fg="green")
            self.lbl_processing.config(text="")
            self._disable_buttons()

            result = 'WIN_X' if winner == PLAYER_X else 'WIN_O'
            self.history.set_game_result(result)

            if self.history.has_moves():
                self.btn_show_analysis.config(state="normal")

            if self.show_visualization.get() and self.history.has_moves():
                self.root.after(500, self._show_analysis)

            messagebox.showinfo("Fim de Jogo", f"O jogador {winner} venceu!")

        elif self.board.is_full():
            self.game_finished = True
            self.score['tie'] += 1
            self.lbl_score.config(text=self._get_score_text())
            self.lbl_status.config(text="Empate!", fg="orange")
            self.lbl_processing.config(text="")

            self.history.set_game_result('TIE')

            if self.history.has_moves():
                self.btn_show_analysis.config(state="normal")

            if self.show_visualization.get() and self.history.has_moves():
                self.root.after(500, self._show_analysis)

            messagebox.showinfo("Fim de Jogo", "Empate!")
        else:
            self.lbl_status.config(
                text=f"Vez do Jogador: {self.current_player}",
                fg="black"
            )

    def _show_analysis(self):
        """Shows the game analysis in the browser."""
        if self.history.has_moves():
            def show_in_thread():
                visualizer = GameVisualizer(self.history)
                visualizer.show()

            thread = threading.Thread(target=show_in_thread)
            thread.daemon = True
            thread.start()

    def _disable_buttons(self):
        """Disables all board buttons."""
        for btn in self.buttons:
            btn.config(state="disabled")

    def _show_tree_visualization_menu(self):
        """Shows the tree visualization options screen."""
        for widget in self.frame_menu.winfo_children():
            widget.destroy()

        lbl_title = tk.Label(
            self.frame_menu,
            text="Visualizar Arvore Minimax",
            font=("Helvetica", 20, "bold")
        )
        lbl_title.pack(pady=20)

        lbl_info = tk.Label(
            self.frame_menu,
            text="Gera a arvore completa do algoritmo Minimax\na partir de um tabuleiro vazio.",
            font=("Arial", 10),
            fg="gray"
        )
        lbl_info.pack(pady=5)

        frame_ai = tk.Frame(self.frame_menu)
        frame_ai.pack(pady=15)
        tk.Label(
            frame_ai,
            text="Perspectiva da IA:",
            font=("Arial", 12)
        ).pack(side=tk.LEFT)
        self.combo_ai_perspective = ttk.Combobox(
            frame_ai,
            values=["X (primeiro a jogar)", "O (segundo a jogar)"],
            state="readonly",
            width=20
        )
        self.combo_ai_perspective.set("X (primeiro a jogar)")
        self.combo_ai_perspective.pack(side=tk.LEFT, padx=10)

        lbl_viz_type = tk.Label(
            self.frame_menu,
            text="Escolha o tipo de visualizacao:",
            font=("Arial", 12, "bold")
        )
        lbl_viz_type.pack(pady=(20, 10))

        btn_collapsible = tk.Button(
            self.frame_menu,
            text="Arvore Colapsavel",
            font=("Arial", 12),
            width=25,
            command=lambda: self._generate_tree_visualization("collapsible"),
            bg="#3498db",
            fg="white"
        )
        btn_collapsible.pack(pady=5)
        tk.Label(
            self.frame_menu,
            text="Nos expansiveis com zoom/pan interativo",
            font=("Arial", 9),
            fg="gray"
        ).pack()

        btn_sunburst = tk.Button(
            self.frame_menu,
            text="Sunburst (Radial)",
            font=("Arial", 12),
            width=25,
            command=lambda: self._generate_tree_visualization("sunburst"),
            bg="#f39c12",
            fg="white"
        )
        btn_sunburst.pack(pady=(15, 5))
        tk.Label(
            self.frame_menu,
            text="Hierarquia radial - cada anel = nivel de profundidade",
            font=("Arial", 9),
            fg="gray"
        ).pack()

        btn_treemap = tk.Button(
            self.frame_menu,
            text="Treemap",
            font=("Arial", 12),
            width=25,
            command=lambda: self._generate_tree_visualization("treemap"),
            bg="#2ecc71",
            fg="white"
        )
        btn_treemap.pack(pady=(15, 5))
        tk.Label(
            self.frame_menu,
            text="Retangulos aninhados - tamanho = numero de sub-nos",
            font=("Arial", 9),
            fg="gray"
        ).pack()

        btn_back = tk.Button(
            self.frame_menu,
            text="< Voltar",
            command=self._create_main_menu
        )
        btn_back.pack(pady=20)

    def _generate_tree_visualization(self, viz_type: str):
        """
        Generates and displays the tree visualization.

        Args:
            viz_type: Type of visualization ('collapsible', 'sunburst', 'treemap').
        """
        perspective = self.combo_ai_perspective.get()
        ai_symbol = PLAYER_X if "X" in perspective else PLAYER_O

        self.lbl_processing_tree = tk.Label(
            self.frame_menu,
            text="Gerando arvore... Por favor aguarde.",
            font=("Arial", 11),
            fg="#3498db"
        )
        self.lbl_processing_tree.pack(pady=10)
        self.root.update()

        def generate_and_show():
            board = Board()
            collector = MinimaxTreeCollector(ai_symbol)
            collector.build_tree(board)

            visualizer = TreeVisualizer(collector)

            if viz_type == "collapsible":
                visualizer.show_collapsible_tree()
            elif viz_type == "sunburst":
                visualizer.show_sunburst()
            elif viz_type == "treemap":
                visualizer.show_treemap()

            self.root.after(0, lambda: self.lbl_processing_tree.config(
                text=f"Arvore gerada! {collector.nodes_evaluated:,} nos avaliados."
            ))

        thread = threading.Thread(target=generate_and_show)
        thread.daemon = True
        thread.start()

    def _show_comparison_screen(self):
        """Shows the algorithm comparison report in browser."""
        def run_comparison():
            visualizer = ComparisonVisualizer()
            visualizer.show()

        thread = threading.Thread(target=run_comparison)
        thread.daemon = True
        thread.start()

        messagebox.showinfo(
            "Comparativo",
            "Gerando relatorio de comparacao...\n"
            "O navegador abrira automaticamente quando estiver pronto."
        )

    def _back_to_menu(self):
        """Returns to the main menu."""
        self.frame_game.pack_forget()
        self.player_x = None
        self.player_o = None
        self.history.clear()
        self._create_main_menu()
