"""Modern GUI for Tic-Tac-Toe game using CustomTkinter."""

import customtkinter as ctk
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
from utils.constants import PLAYER_X, PLAYER_O
from visualization.game_history import GameHistoryCollector
from visualization.game_visualizer import GameVisualizer
from visualization.tree_data import (
    MinimaxTreeCollector,
    AlphaBetaTreeCollector,
    AlphaBetaTTTreeCollector,
    AlphaBetaSymmetryTreeCollector
)
from visualization.tree_visualizer import TreeVisualizer
from visualization.comparison_visualizer import ComparisonVisualizer

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GameGUI:
    """Modern graphical user interface for Tic-Tac-Toe game."""

    # Theme colors
    COLORS = {
        'bg_dark': '#1a1a2e',
        'bg_card': '#16213e',
        'bg_cell': '#0f3460',
        'accent_x': '#4cc9f0',      # Cyan for X
        'accent_o': '#f72585',      # Pink for O
        'accent_green': '#4ade80',
        'accent_purple': '#a855f7',
        'accent_orange': '#fb923c',
        'text_primary': '#f1f5f9',
        'text_secondary': '#94a3b8',
        'border': '#334155',
    }

    PLAYER_TYPES = {
        'Minimax': MinimaxPlayer,
        'Alpha-Beta': AlphaBetaPlayer,
        'AB + Transposition': AlphaBetaTTPlayer,
        'AB + Simetria': AlphaBetaSymmetryPlayer,
        'Random': RandomPlayer
    }

    def __init__(self, root: ctk.CTk):
        """Initializes the game GUI."""
        self.root = root
        self.root.title("Jogo da Velha - IA")
        self.root.geometry("500x750")
        self.root.resizable(False, False)
        self.root.configure(fg_color=self.COLORS['bg_dark'])

        self.game_mode: Optional[str] = None
        self.board: Optional[Board] = None
        self.player_x: Optional[BasePlayer] = None
        self.player_o: Optional[BasePlayer] = None
        self.cell_buttons: list = []
        self.current_player = PLAYER_X

        self.score = {PLAYER_X: 0, PLAYER_O: 0, 'tie': 0}

        self.show_visualization = ctk.BooleanVar(value=True)
        self.history = GameHistoryCollector()
        self.game_finished = False

        # Main container
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self._create_main_menu()

    def _clear_container(self):
        """Clears all widgets from the container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def _create_main_menu(self):
        """Creates the modern main menu."""
        self._clear_container()

        # Title with X O decorations
        title_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        title_frame.pack(pady=(20, 10))

        # X symbol
        x_label = ctk.CTkLabel(
            title_frame,
            text="X",
            font=ctk.CTkFont(family="Arial", size=48, weight="bold"),
            text_color=self.COLORS['accent_x']
        )
        x_label.pack(side="left", padx=10)

        # Title
        title = ctk.CTkLabel(
            title_frame,
            text="Jogo da Velha",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title.pack(side="left", padx=10)

        # O symbol
        o_label = ctk.CTkLabel(
            title_frame,
            text="O",
            font=ctk.CTkFont(family="Arial", size=48, weight="bold"),
            text_color=self.COLORS['accent_o']
        )
        o_label.pack(side="left", padx=10)

        # Subtitle
        subtitle = ctk.CTkLabel(
            self.container,
            text="Inteligencia Artificial",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 30))

        # Game mode buttons
        modes_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        modes_frame.pack(fill="x", pady=10)

        modes_title = ctk.CTkLabel(
            modes_frame,
            text="Modo de Jogo",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        modes_title.pack(pady=(15, 10))

        btn_pvp = ctk.CTkButton(
            modes_frame,
            text="Jogador vs Jogador",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=self.COLORS['bg_cell'],
            hover_color=self.COLORS['accent_x'],
            command=lambda: self._start_game('PVP')
        )
        btn_pvp.pack(pady=8, padx=20, fill="x")

        btn_pve = ctk.CTkButton(
            modes_frame,
            text="Jogador vs IA",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=self.COLORS['bg_cell'],
            hover_color=self.COLORS['accent_o'],
            command=lambda: self._start_game('PVE')
        )
        btn_pve.pack(pady=8, padx=20, fill="x")

        btn_eve = ctk.CTkButton(
            modes_frame,
            text="IA vs IA",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=self.COLORS['bg_cell'],
            hover_color=self.COLORS['accent_purple'],
            command=self._show_ai_selection
        )
        btn_eve.pack(pady=(8, 15), padx=20, fill="x")

        # Tools section
        tools_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        tools_frame.pack(fill="x", pady=10)

        tools_title = ctk.CTkLabel(
            tools_frame,
            text="Ferramentas de Analise",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        tools_title.pack(pady=(15, 10))

        btn_tree = ctk.CTkButton(
            tools_frame,
            text="Visualizar Arvore de Busca",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=self.COLORS['accent_purple'],
            hover_color="#9333ea",
            command=self._show_tree_visualization_menu
        )
        btn_tree.pack(pady=8, padx=20, fill="x")

        btn_compare = ctk.CTkButton(
            tools_frame,
            text="Comparar Algoritmos",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color=self.COLORS['accent_orange'],
            hover_color="#ea580c",
            command=self._show_comparison_screen
        )
        btn_compare.pack(pady=(8, 15), padx=20, fill="x")

        # Settings
        settings_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        settings_frame.pack(fill="x", pady=(15, 10))

        self.chk_analysis = ctk.CTkCheckBox(
            settings_frame,
            text="Mostrar Analise ao Final da Partida",
            variable=self.show_visualization,
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary'],
            fg_color=self.COLORS['accent_x'],
            hover_color=self.COLORS['accent_x']
        )
        self.chk_analysis.pack(pady=3)

        info_label = ctk.CTkLabel(
            settings_frame,
            text="(Abre resumo da partida no navegador)",
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_secondary']
        )
        info_label.pack(pady=(0, 10))

    def _show_ai_selection(self):
        """Shows the AI selection screen."""
        self._clear_container()

        # Back button
        back_btn = ctk.CTkButton(
            self.container,
            text="< Voltar",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=self.COLORS['bg_card'],
            text_color=self.COLORS['text_secondary'],
            command=self._create_main_menu
        )
        back_btn.pack(anchor="w", pady=(0, 10))

        # Title
        title = ctk.CTkLabel(
            self.container,
            text="IA vs IA",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title.pack(pady=(10, 5))

        subtitle = ctk.CTkLabel(
            self.container,
            text="Selecione os algoritmos para batalha",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 30))

        # Player X selection
        x_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        x_frame.pack(fill="x", pady=10)

        x_header = ctk.CTkFrame(x_frame, fg_color="transparent")
        x_header.pack(fill="x", padx=20, pady=(15, 10))

        x_symbol = ctk.CTkLabel(
            x_header,
            text="X",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLORS['accent_x']
        )
        x_symbol.pack(side="left")

        x_label = ctk.CTkLabel(
            x_header,
            text="Jogador X",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        x_label.pack(side="left", padx=15)

        self.combo_x = ctk.CTkComboBox(
            x_frame,
            values=list(self.PLAYER_TYPES.keys()),
            width=250,
            height=40,
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=13),
            fg_color=self.COLORS['bg_cell'],
            border_color=self.COLORS['accent_x'],
            button_color=self.COLORS['accent_x'],
            button_hover_color=self.COLORS['accent_x']
        )
        self.combo_x.set("Minimax")
        self.combo_x.pack(padx=20, pady=(0, 15))

        # VS label
        vs_label = ctk.CTkLabel(
            self.container,
            text="VS",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['text_secondary']
        )
        vs_label.pack(pady=10)

        # Player O selection
        o_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        o_frame.pack(fill="x", pady=10)

        o_header = ctk.CTkFrame(o_frame, fg_color="transparent")
        o_header.pack(fill="x", padx=20, pady=(15, 10))

        o_symbol = ctk.CTkLabel(
            o_header,
            text="O",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLORS['accent_o']
        )
        o_symbol.pack(side="left")

        o_label = ctk.CTkLabel(
            o_header,
            text="Jogador O",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        o_label.pack(side="left", padx=15)

        self.combo_o = ctk.CTkComboBox(
            o_frame,
            values=list(self.PLAYER_TYPES.keys()),
            width=250,
            height=40,
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=13),
            fg_color=self.COLORS['bg_cell'],
            border_color=self.COLORS['accent_o'],
            button_color=self.COLORS['accent_o'],
            button_hover_color=self.COLORS['accent_o']
        )
        self.combo_o.set("Alpha-Beta")
        self.combo_o.pack(padx=20, pady=(0, 15))

        # Start button
        btn_start = ctk.CTkButton(
            self.container,
            text="Iniciar Batalha",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=12,
            fg_color=self.COLORS['accent_green'],
            hover_color="#22c55e",
            text_color=self.COLORS['bg_dark'],
            command=self._start_ai_vs_ai
        )
        btn_start.pack(pady=30, fill="x")

    def _start_ai_vs_ai(self):
        """Starts the AI vs AI game."""
        x_type = self.combo_x.get()
        o_type = self.combo_o.get()

        self.player_x = self.PLAYER_TYPES[x_type](PLAYER_X)
        self.player_o = self.PLAYER_TYPES[o_type](PLAYER_O)

        self._start_game('EVE')

    def _start_game(self, mode: str):
        """Starts a new game."""
        self.game_mode = mode
        self.board = Board()
        self.current_player = PLAYER_X
        self.cell_buttons = []
        self.history.clear()
        self.game_finished = False

        if mode == 'PVE':
            self.player_o = MinimaxPlayer(PLAYER_O)
        elif mode == 'EVE' and self.player_x is None:
            self.player_x = MinimaxPlayer(PLAYER_X)
            self.player_o = MinimaxPlayer(PLAYER_O)

        self._create_game_screen()

        if mode == 'EVE':
            self.root.after(500, self._ai_turn)

    def _create_game_screen(self):
        """Creates the game board screen."""
        self._clear_container()

        # Top bar
        top_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        back_btn = ctk.CTkButton(
            top_frame,
            text="< Menu",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=self.COLORS['bg_card'],
            text_color=self.COLORS['text_secondary'],
            command=self._back_to_menu
        )
        back_btn.pack(side="left")

        # Score display
        score_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=12)
        score_frame.pack(fill="x", pady=10)

        score_inner = ctk.CTkFrame(score_frame, fg_color="transparent")
        score_inner.pack(pady=15)

        # X score
        x_score_frame = ctk.CTkFrame(score_inner, fg_color="transparent")
        x_score_frame.pack(side="left", padx=20)
        ctk.CTkLabel(
            x_score_frame,
            text="X",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['accent_x']
        ).pack()
        self.lbl_score_x = ctk.CTkLabel(
            x_score_frame,
            text=str(self.score[PLAYER_X]),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        self.lbl_score_x.pack()

        # Tie score
        tie_frame = ctk.CTkFrame(score_inner, fg_color="transparent")
        tie_frame.pack(side="left", padx=30)
        ctk.CTkLabel(
            tie_frame,
            text="Empates",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_secondary']
        ).pack()
        self.lbl_score_tie = ctk.CTkLabel(
            tie_frame,
            text=str(self.score['tie']),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['text_secondary']
        )
        self.lbl_score_tie.pack()

        # O score
        o_score_frame = ctk.CTkFrame(score_inner, fg_color="transparent")
        o_score_frame.pack(side="left", padx=20)
        ctk.CTkLabel(
            o_score_frame,
            text="O",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLORS['accent_o']
        ).pack()
        self.lbl_score_o = ctk.CTkLabel(
            o_score_frame,
            text=str(self.score[PLAYER_O]),
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        self.lbl_score_o.pack()

        # Status label
        self.lbl_status = ctk.CTkLabel(
            self.container,
            text=f"Vez do Jogador X",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLORS['accent_x']
        )
        self.lbl_status.pack(pady=15)

        # Game board
        board_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        board_frame.pack(pady=10)

        board_inner = ctk.CTkFrame(board_frame, fg_color="transparent")
        board_inner.pack(padx=20, pady=20)

        for i in range(9):
            row, col = i // 3, i % 3
            cell = ctk.CTkButton(
                board_inner,
                text="",
                width=100,
                height=100,
                font=ctk.CTkFont(size=48, weight="bold"),
                fg_color=self.COLORS['bg_cell'],
                hover_color=self.COLORS['border'],
                corner_radius=12,
                border_width=2,
                border_color=self.COLORS['border'],
                command=lambda idx=i: self._on_cell_click(idx)
            )
            cell.grid(row=row, column=col, padx=5, pady=5)
            self.cell_buttons.append(cell)

        # Stats label
        self.lbl_stats = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['text_secondary']
        )
        self.lbl_stats.pack(pady=5)

        # Processing label
        self.lbl_processing = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['accent_x']
        )
        self.lbl_processing.pack(pady=5)

        # Control buttons
        controls_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=15)

        btn_restart = ctk.CTkButton(
            controls_frame,
            text="Reiniciar",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            corner_radius=10,
            fg_color=self.COLORS['bg_cell'],
            hover_color=self.COLORS['border'],
            command=lambda: self._start_game(self.game_mode)
        )
        btn_restart.pack(side="left", padx=5, expand=True)

        self.btn_analysis = ctk.CTkButton(
            controls_frame,
            text="Ver Analise",
            font=ctk.CTkFont(size=13),
            height=40,
            width=120,
            corner_radius=10,
            fg_color=self.COLORS['accent_purple'],
            hover_color="#9333ea",
            state="disabled",
            command=self._show_analysis
        )
        self.btn_analysis.pack(side="right", padx=5, expand=True)

    def _on_cell_click(self, index: int):
        """Handles cell click events."""
        if self.game_mode == 'EVE':
            return

        if self.game_finished or self.board.cells[index] != ' ':
            return

        self._make_move(index)

        if self.game_mode == 'PVE' and not GameLogic.is_terminal(self.board):
            self.lbl_processing.configure(text="IA pensando...")
            self.root.update()
            self.root.after(100, self._ai_turn)

    def _ai_turn(self):
        """Executes the AI's turn."""
        if GameLogic.is_terminal(self.board):
            return

        self.lbl_processing.configure(text="IA calculando melhor jogada...")
        self.root.update()

        player = self.player_x if self.current_player == PLAYER_X else self.player_o
        board_before = self.board.cells.copy()
        move, stats = player.get_move(self.board)

        if move != -1:
            self._make_move(move)

            if isinstance(player, (MinimaxPlayer, AlphaBetaPlayer, AlphaBetaTTPlayer,
                                   AlphaBetaSymmetryPlayer)):
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
            self.lbl_processing.configure(text="")

            if self.game_mode == 'EVE' and not GameLogic.is_terminal(self.board):
                self.root.after(500, self._ai_turn)

    def _show_stats(self, player_name: str, stats: Dict):
        """Displays AI statistics."""
        text = f"{player_name}: {stats['nodes_evaluated']:,} nos | {stats['time_ms']:.1f}ms"
        self.lbl_stats.configure(text=text)

    def _make_move(self, index: int):
        """Executes a move on the board."""
        player = self.current_player
        self.board.make_move(index, player)
        self.current_player = self.board.current_player

        # Update cell appearance
        color = self.COLORS['accent_x'] if player == PLAYER_X else self.COLORS['accent_o']
        self.cell_buttons[index].configure(
            text=player,
            text_color=color,
            fg_color=self.COLORS['bg_dark'],
            border_color=color
        )

        winner = GameLogic.check_winner(self.board)

        if winner:
            self._handle_game_end(winner)
        elif self.board.is_full():
            self._handle_game_end(None)
        else:
            # Update status
            next_color = self.COLORS['accent_x'] if self.current_player == PLAYER_X else self.COLORS['accent_o']
            self.lbl_status.configure(
                text=f"Vez do Jogador {self.current_player}",
                text_color=next_color
            )

    def _handle_game_end(self, winner: Optional[str]):
        """Handles end of game."""
        self.game_finished = True
        self.lbl_processing.configure(text="")

        if winner:
            self.score[winner] += 1
            color = self.COLORS['accent_x'] if winner == PLAYER_X else self.COLORS['accent_o']
            self.lbl_status.configure(
                text=f"Jogador {winner} Venceu!",
                text_color=self.COLORS['accent_green']
            )
            result = 'WIN_X' if winner == PLAYER_X else 'WIN_O'
        else:
            self.score['tie'] += 1
            self.lbl_status.configure(
                text="Empate!",
                text_color=self.COLORS['accent_orange']
            )
            result = 'TIE'

        # Update score display
        self.lbl_score_x.configure(text=str(self.score[PLAYER_X]))
        self.lbl_score_o.configure(text=str(self.score[PLAYER_O]))
        self.lbl_score_tie.configure(text=str(self.score['tie']))

        self.history.set_game_result(result)

        if self.history.has_moves():
            self.btn_analysis.configure(state="normal")

        if self.show_visualization.get() and self.history.has_moves():
            self.root.after(500, self._show_analysis)

        # Disable all cells
        for btn in self.cell_buttons:
            btn.configure(state="disabled")

        # Show result dialog
        self._show_result_dialog(winner)

    def _show_result_dialog(self, winner: Optional[str]):
        """Shows a modern result dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Fim de Jogo")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.COLORS['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        if winner:
            color = self.COLORS['accent_x'] if winner == PLAYER_X else self.COLORS['accent_o']
            title = f"Jogador {winner} Venceu!"
            symbol = winner
        else:
            color = self.COLORS['accent_orange']
            title = "Empate!"
            symbol = "="

        symbol_label = ctk.CTkLabel(
            dialog,
            text=symbol,
            font=ctk.CTkFont(size=64, weight="bold"),
            text_color=color
        )
        symbol_label.pack(pady=(20, 10))

        title_label = ctk.CTkLabel(
            dialog,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title_label.pack(pady=5)

        ok_btn = ctk.CTkButton(
            dialog,
            text="OK",
            width=100,
            height=35,
            corner_radius=10,
            fg_color=color,
            hover_color=self.COLORS['bg_cell'],
            command=dialog.destroy
        )
        ok_btn.pack(pady=20)

    def _show_analysis(self):
        """Shows the game analysis."""
        if self.history.has_moves():
            def show_in_thread():
                visualizer = GameVisualizer(self.history)
                visualizer.show()

            thread = threading.Thread(target=show_in_thread)
            thread.daemon = True
            thread.start()

    def _show_tree_visualization_menu(self):
        """Shows the tree visualization menu."""
        self._clear_container()

        # Back button
        back_btn = ctk.CTkButton(
            self.container,
            text="< Voltar",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=self.COLORS['bg_card'],
            text_color=self.COLORS['text_secondary'],
            command=self._create_main_menu
        )
        back_btn.pack(anchor="w", pady=(0, 10))

        # Title
        title = ctk.CTkLabel(
            self.container,
            text="Arvore de Busca",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        title.pack(pady=(10, 5))

        subtitle = ctk.CTkLabel(
            self.container,
            text="Visualize a arvore completa de decisao do algoritmo",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 20))

        # Settings card
        settings_frame = ctk.CTkFrame(self.container, fg_color=self.COLORS['bg_card'], corner_radius=15)
        settings_frame.pack(fill="x", pady=10)

        # Algorithm selection
        algo_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        algo_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            algo_frame,
            text="Algoritmo:",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w")

        self.combo_tree_algo = ctk.CTkComboBox(
            algo_frame,
            values=["Minimax", "Alpha-Beta", "Alpha-Beta + TT", "Alpha-Beta + Simetria"],
            width=300,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=self.COLORS['bg_cell'],
            border_color=self.COLORS['accent_purple'],
            button_color=self.COLORS['accent_purple']
        )
        self.combo_tree_algo.set("Minimax")
        self.combo_tree_algo.pack(pady=5)

        # Perspective selection
        persp_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        persp_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkLabel(
            persp_frame,
            text="Perspectiva da IA:",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS['text_secondary']
        ).pack(anchor="w")

        self.combo_perspective = ctk.CTkComboBox(
            persp_frame,
            values=["X (primeiro a jogar)", "O (segundo a jogar)"],
            width=300,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=self.COLORS['bg_cell'],
            border_color=self.COLORS['accent_purple'],
            button_color=self.COLORS['accent_purple']
        )
        self.combo_perspective.set("X (primeiro a jogar)")
        self.combo_perspective.pack(pady=5)

        # Visualization types
        viz_title = ctk.CTkLabel(
            self.container,
            text="Tipo de Visualizacao",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        )
        viz_title.pack(pady=(20, 10))

        btn_collapsible = ctk.CTkButton(
            self.container,
            text="Arvore Colapsavel",
            font=ctk.CTkFont(size=14),
            height=50,
            corner_radius=12,
            fg_color=self.COLORS['accent_x'],
            hover_color="#22d3ee",
            text_color=self.COLORS['bg_dark'],
            command=lambda: self._generate_tree_visualization("collapsible")
        )
        btn_collapsible.pack(pady=8, fill="x")

        ctk.CTkLabel(
            self.container,
            text="Nos expansiveis com zoom/pan interativo",
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_secondary']
        ).pack()

        btn_sunburst = ctk.CTkButton(
            self.container,
            text="Sunburst (Radial)",
            font=ctk.CTkFont(size=14),
            height=50,
            corner_radius=12,
            fg_color=self.COLORS['accent_orange'],
            hover_color="#ea580c",
            text_color=self.COLORS['bg_dark'],
            command=lambda: self._generate_tree_visualization("sunburst")
        )
        btn_sunburst.pack(pady=(15, 8), fill="x")

        ctk.CTkLabel(
            self.container,
            text="Hierarquia radial - cada anel = nivel de profundidade",
            font=ctk.CTkFont(size=11),
            text_color=self.COLORS['text_secondary']
        ).pack()

        # Processing label
        self.lbl_tree_processing = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.COLORS['accent_green']
        )
        self.lbl_tree_processing.pack(pady=20)

    def _generate_tree_visualization(self, viz_type: str):
        """Generates and displays the tree visualization."""
        perspective = self.combo_perspective.get()
        ai_symbol = PLAYER_X if "X" in perspective else PLAYER_O
        algorithm = self.combo_tree_algo.get()

        collector_map = {
            "Minimax": MinimaxTreeCollector,
            "Alpha-Beta": AlphaBetaTreeCollector,
            "Alpha-Beta + TT": AlphaBetaTTTreeCollector,
            "Alpha-Beta + Simetria": AlphaBetaSymmetryTreeCollector,
        }

        self.lbl_tree_processing.configure(text=f"Gerando arvore {algorithm}... Por favor aguarde.")
        self.root.update()

        def generate_and_show():
            board = Board()
            collector_class = collector_map.get(algorithm, MinimaxTreeCollector)
            collector = collector_class(ai_symbol)
            collector.build_tree(board)

            visualizer = TreeVisualizer(collector)

            if viz_type == "collapsible":
                visualizer.show_collapsible_tree()
            elif viz_type == "sunburst":
                visualizer.show_sunburst()

            stats = collector.get_statistics()
            msg = f"Arvore gerada! {stats.get('total_nodes', 0):,} nos"
            if 'nodes_pruned' in stats:
                msg += f", {stats['nodes_pruned']:,} podados"
            if 'tt_hits' in stats:
                msg += f", {stats['tt_hits']:,} TT hits"
            if 'symmetry_hits' in stats:
                msg += f", {stats['symmetry_hits']:,} simetrias"

            self.root.after(0, lambda: self.lbl_tree_processing.configure(text=msg))

        thread = threading.Thread(target=generate_and_show)
        thread.daemon = True
        thread.start()

    def _show_comparison_screen(self):
        """Shows the comparison report."""
        def run_comparison():
            visualizer = ComparisonVisualizer()
            visualizer.show()

        thread = threading.Thread(target=run_comparison)
        thread.daemon = True
        thread.start()

        # Show info dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Comparativo")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.COLORS['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="Gerando relatorio...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLORS['text_primary']
        ).pack(pady=(25, 10))

        ctk.CTkLabel(
            dialog,
            text="O navegador abrira automaticamente\nquando estiver pronto.",
            font=ctk.CTkFont(size=13),
            text_color=self.COLORS['text_secondary']
        ).pack(pady=5)

        ok_btn = ctk.CTkButton(
            dialog,
            text="OK",
            width=80,
            height=30,
            corner_radius=8,
            fg_color=self.COLORS['accent_orange'],
            command=dialog.destroy
        )
        ok_btn.pack(pady=15)

    def _back_to_menu(self):
        """Returns to the main menu."""
        self.player_x = None
        self.player_o = None
        self.history.clear()
        self._create_main_menu()
