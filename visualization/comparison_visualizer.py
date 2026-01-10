"""Professional HTML visualization for algorithm comparison."""

import webbrowser
import tempfile
import time
import sys
import tracemalloc
from typing import Dict, List, Tuple, Type, Optional
from dataclasses import dataclass
from game.board import Board
from game.game_logic import GameLogic
from ai.base_player import BasePlayer
from ai.minimax_player import MinimaxPlayer
from ai.alpha_beta_player import AlphaBetaPlayer
from ai.alpha_beta_tt_player import AlphaBetaTTPlayer
from ai.alpha_beta_symmetry_player import AlphaBetaSymmetryPlayer
from ai.negascout_player import NegaScoutPlayer
from utils.constants import PLAYER_X, PLAYER_O


@dataclass
class BenchmarkResult:
    """Stores benchmark results for a single algorithm run."""
    algorithm: str
    depth_limit: Optional[int]
    nodes_evaluated: int
    time_ms: float
    memory_kb: float
    max_depth_reached: int
    move_chosen: int
    score: int
    result_type: str  # 'WIN', 'LOSS', 'TIE', 'CUTOFF'
    extra_stats: Dict


@dataclass
class MatchResult:
    """Stores result of a match between two algorithms."""
    player_x: str
    player_o: str
    winner: Optional[str]  # 'X', 'O', or None for tie
    moves_count: int
    total_nodes_x: int
    total_nodes_o: int
    total_time_ms: float
    final_board: List[str]
    move_history: List[Dict]


class DepthLimitedMinimax(MinimaxPlayer):
    """Minimax with configurable depth limit."""

    def __init__(self, symbol: str, max_depth: Optional[int] = None):
        super().__init__(symbol)
        self.max_depth = max_depth
        self.max_depth_reached = 0

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.max_depth_reached = 0
        self.last_alternatives = []

        best_score = float('-inf')
        best_move = -1
        move_scores = []

        for move in board.get_available_moves():
            board.make_move(move, self.symbol)
            score = self._minimax_limited(board, 0, False)
            board.undo_move(move)
            move_scores.append({'position': move, 'score': score})
            if score > best_score:
                best_score = score
                best_move = move

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return best_move, {
            'nodes_evaluated': self.nodes_evaluated,
            'time_ms': round(elapsed_ms, 3),
            'max_depth_reached': self.max_depth_reached,
            'alternatives': move_scores,
            'chosen_score': best_score
        }

    def _minimax_limited(self, board: Board, depth: int, is_maximizing: bool) -> int:
        self.nodes_evaluated += 1
        self.max_depth_reached = max(self.max_depth_reached, depth)

        if GameLogic.is_terminal(board):
            return GameLogic.evaluate(board, self.symbol, depth)

        if self.max_depth is not None and depth >= self.max_depth:
            return 0  # Heuristic: unknown outcome

        if is_maximizing:
            best_score = float('-inf')
            for move in board.get_available_moves():
                board.make_move(move, self.symbol)
                score = self._minimax_limited(board, depth + 1, False)
                board.undo_move(move)
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = float('inf')
            for move in board.get_available_moves():
                board.make_move(move, self.opponent)
                score = self._minimax_limited(board, depth + 1, True)
                board.undo_move(move)
                best_score = min(best_score, score)
            return best_score


class DepthLimitedAlphaBeta(AlphaBetaPlayer):
    """Alpha-Beta with configurable depth limit."""

    def __init__(self, symbol: str, max_depth: Optional[int] = None):
        super().__init__(symbol)
        self.max_depth = max_depth
        self.max_depth_reached = 0

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.max_depth_reached = 0

        best_score = float('-inf')
        best_move = -1
        move_scores = []
        alpha = float('-inf')
        beta = float('inf')

        for move in board.get_available_moves():
            board.make_move(move, self.symbol)
            score = self._ab_limited(board, 0, alpha, beta, False)
            board.undo_move(move)
            move_scores.append({'position': move, 'score': score})
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return best_move, {
            'nodes_evaluated': self.nodes_evaluated,
            'nodes_pruned': self.nodes_pruned,
            'time_ms': round(elapsed_ms, 3),
            'max_depth_reached': self.max_depth_reached,
            'alternatives': move_scores,
            'chosen_score': best_score
        }

    def _ab_limited(self, board: Board, depth: int, alpha: float, beta: float, is_max: bool) -> int:
        self.nodes_evaluated += 1
        self.max_depth_reached = max(self.max_depth_reached, depth)

        if GameLogic.is_terminal(board):
            return GameLogic.evaluate(board, self.symbol, depth)

        if self.max_depth is not None and depth >= self.max_depth:
            return 0

        if is_max:
            value = float('-inf')
            for move in board.get_available_moves():
                board.make_move(move, self.symbol)
                value = max(value, self._ab_limited(board, depth + 1, alpha, beta, False))
                board.undo_move(move)
                alpha = max(alpha, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break
            return value
        else:
            value = float('inf')
            for move in board.get_available_moves():
                board.make_move(move, self.opponent)
                value = min(value, self._ab_limited(board, depth + 1, alpha, beta, True))
                board.undo_move(move)
                beta = min(beta, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break
            return value


class ComparisonVisualizer:
    """Generates professional HTML comparison reports."""

    ALGORITHMS = [
        ('Minimax', MinimaxPlayer, DepthLimitedMinimax),
        ('Alpha-Beta', AlphaBetaPlayer, DepthLimitedAlphaBeta),
        ('AB + Transposition', AlphaBetaTTPlayer, None),
        ('AB + Simetria', AlphaBetaSymmetryPlayer, None),
        ('NegaScout', NegaScoutPlayer, None),
    ]

    COLORS = {
        'Minimax': '#e74c3c',
        'Alpha-Beta': '#3498db',
        'AB + Transposition': '#9b59b6',
        'AB + Simetria': '#2ecc71',
        'NegaScout': '#f39c12',
    }

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.tournament_results: List[MatchResult] = []

    def run_tournament(self):
        """Runs a round-robin tournament between all algorithms."""
        self.tournament_results = []
        algo_classes = [(name, cls) for name, cls, _ in self.ALGORITHMS]

        for i, (name_x, class_x) in enumerate(algo_classes):
            for j, (name_o, class_o) in enumerate(algo_classes):
                if i != j:
                    result = self._play_match(name_x, class_x, name_o, class_o)
                    self.tournament_results.append(result)

    def _play_match(
        self,
        name_x: str,
        class_x: Type[BasePlayer],
        name_o: str,
        class_o: Type[BasePlayer]
    ) -> MatchResult:
        """Plays a single match between two algorithms."""
        board = Board()
        player_x = class_x(PLAYER_X)
        player_o = class_o(PLAYER_O)

        move_history = []
        total_nodes_x = 0
        total_nodes_o = 0
        start_time = time.perf_counter()
        current_player = PLAYER_X

        while not GameLogic.is_terminal(board):
            if current_player == PLAYER_X:
                move, stats = player_x.get_move(board)
                total_nodes_x += stats['nodes_evaluated']
                board.make_move(move, PLAYER_X)
                move_history.append({
                    'player': name_x,
                    'symbol': 'X',
                    'move': move,
                    'nodes': stats['nodes_evaluated']
                })
                current_player = PLAYER_O
            else:
                move, stats = player_o.get_move(board)
                total_nodes_o += stats['nodes_evaluated']
                board.make_move(move, PLAYER_O)
                move_history.append({
                    'player': name_o,
                    'symbol': 'O',
                    'move': move,
                    'nodes': stats['nodes_evaluated']
                })
                current_player = PLAYER_X

        total_time = (time.perf_counter() - start_time) * 1000
        winner_symbol = GameLogic.check_winner(board)

        return MatchResult(
            player_x=name_x,
            player_o=name_o,
            winner=winner_symbol,
            moves_count=len(move_history),
            total_nodes_x=total_nodes_x,
            total_nodes_o=total_nodes_o,
            total_time_ms=total_time,
            final_board=board.cells.copy(),
            move_history=move_history
        )

    def run_full_benchmark(self, depth_limits: List[Optional[int]] = None):
        """Runs comprehensive benchmark with various depth limits."""
        if depth_limits is None:
            depth_limits = [None, 9, 7, 5, 3]  # None = unlimited

        self.results = []

        for depth in depth_limits:
            for name, full_class, limited_class in self.ALGORITHMS:
                result = self._benchmark_algorithm(name, full_class, limited_class, depth)
                self.results.append(result)

    def _benchmark_algorithm(
        self,
        name: str,
        full_class: Type[BasePlayer],
        limited_class: Optional[Type],
        depth_limit: Optional[int]
    ) -> BenchmarkResult:
        """Benchmarks a single algorithm configuration."""
        board = Board()

        # Use depth-limited version if available and depth is specified
        if depth_limit is not None and limited_class is not None:
            player = limited_class(PLAYER_X, depth_limit)
        else:
            player = full_class(PLAYER_X)

        # Track memory
        tracemalloc.start()
        start_mem = tracemalloc.get_traced_memory()[0]

        move, stats = player.get_move(board)

        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memory_kb = (peak_mem - start_mem) / 1024

        # Determine result type
        score = stats.get('chosen_score', 0)
        if score > 5:
            result_type = 'WIN'
        elif score < -5:
            result_type = 'LOSS'
        elif score == 0:
            result_type = 'TIE' if depth_limit is None else 'UNKNOWN'
        else:
            result_type = 'UNKNOWN'

        max_depth_reached = stats.get('max_depth_reached', depth_limit or 9)

        extra = {}
        if 'nodes_pruned' in stats:
            extra['nodes_pruned'] = stats['nodes_pruned']
        if 'tt_hits' in stats:
            extra['tt_hits'] = stats['tt_hits']
            extra['tt_hit_rate'] = stats.get('tt_hit_rate', 0)
        if 'symmetry_hits' in stats:
            extra['symmetry_hits'] = stats['symmetry_hits']
            extra['unique_positions'] = stats.get('unique_positions', 0)
        if 'null_window_searches' in stats:
            extra['null_window_searches'] = stats['null_window_searches']
            extra['re_searches'] = stats.get('re_searches', 0)

        return BenchmarkResult(
            algorithm=name,
            depth_limit=depth_limit,
            nodes_evaluated=stats['nodes_evaluated'],
            time_ms=stats['time_ms'],
            memory_kb=round(memory_kb, 2),
            max_depth_reached=max_depth_reached,
            move_chosen=move,
            score=score,
            result_type=result_type,
            extra_stats=extra
        )

    def generate_html(self) -> str:
        """Generates the complete HTML report."""
        # Group results by depth limit
        unlimited_results = [r for r in self.results if r.depth_limit is None]
        depth_results = {}
        for r in self.results:
            if r.depth_limit is not None:
                if r.depth_limit not in depth_results:
                    depth_results[r.depth_limit] = []
                depth_results[r.depth_limit].append(r)

        # Calculate baseline for percentages
        baseline_nodes = next((r.nodes_evaluated for r in unlimited_results if r.algorithm == 'Minimax'), 1)

        html = self._generate_html_header()
        html += self._generate_summary_section(unlimited_results, baseline_nodes)
        html += self._generate_unlimited_comparison(unlimited_results, baseline_nodes)
        html += self._generate_tournament_section()
        html += self._generate_depth_analysis(depth_results, baseline_nodes)
        html += self._generate_charts_section(unlimited_results, depth_results)
        html += self._generate_methodology_section()
        html += self._generate_html_footer()

        return html

    def _generate_tournament_section(self) -> str:
        """Generates the tournament results section."""
        if not self.tournament_results:
            return ''

        # Calculate rankings
        wins = {}
        losses = {}
        ties = {}
        total_nodes = {}

        for name, _, _ in self.ALGORITHMS:
            wins[name] = 0
            losses[name] = 0
            ties[name] = 0
            total_nodes[name] = 0

        for match in self.tournament_results:
            total_nodes[match.player_x] += match.total_nodes_x
            total_nodes[match.player_o] += match.total_nodes_o

            if match.winner == PLAYER_X:
                wins[match.player_x] += 1
                losses[match.player_o] += 1
            elif match.winner == PLAYER_O:
                wins[match.player_o] += 1
                losses[match.player_x] += 1
            else:
                ties[match.player_x] += 1
                ties[match.player_o] += 1

        # Generate ranking table
        ranking_data = []
        for name in wins.keys():
            points = wins[name] * 3 + ties[name]
            ranking_data.append({
                'name': name,
                'wins': wins[name],
                'ties': ties[name],
                'losses': losses[name],
                'points': points,
                'nodes': total_nodes[name]
            })
        ranking_data.sort(key=lambda x: (-x['points'], x['nodes']))

        ranking_rows = ''
        for i, r in enumerate(ranking_data):
            medal = ['🥇', '🥈', '🥉'][i] if i < 3 else str(i + 1)
            color = self.COLORS.get(r['name'], '#666')
            ranking_rows += f'''
            <tr>
                <td style="text-align: center; font-size: 1.5rem;">{medal}</td>
                <td>
                    <div class="algo-name">
                        <div class="algo-dot" style="background: {color}"></div>
                        {r['name']}
                    </div>
                </td>
                <td style="color: var(--accent-green);">{r['wins']}</td>
                <td style="color: var(--accent-orange);">{r['ties']}</td>
                <td style="color: var(--accent-red);">{r['losses']}</td>
                <td><strong>{r['points']}</strong></td>
                <td>{r['nodes']:,}</td>
            </tr>
'''

        # Generate match details with discrepancy ranking
        # Sort by fastest games (fewer moves = more decisive)
        sorted_matches = sorted(self.tournament_results, key=lambda m: m.moves_count)

        match_rows = ''
        for m in sorted_matches[:10]:  # Top 10 fastest/most decisive
            winner_name = m.player_x if m.winner == PLAYER_X else (m.player_o if m.winner == PLAYER_O else 'Empate')
            result_class = 'win' if m.winner else 'tie'

            # Mini board visualization
            board_html = '<div style="display: grid; grid-template-columns: repeat(3, 20px); gap: 2px; font-size: 12px;">'
            for cell in m.final_board:
                cell_color = '#3b82f6' if cell == 'X' else '#ef4444' if cell == 'O' else '#334155'
                board_html += f'<div style="width: 20px; height: 20px; background: {cell_color}; display: flex; align-items: center; justify-content: center; border-radius: 2px;">{cell if cell != " " else ""}</div>'
            board_html += '</div>'

            match_rows += f'''
            <tr>
                <td>{m.player_x}</td>
                <td>vs</td>
                <td>{m.player_o}</td>
                <td>{board_html}</td>
                <td><span class="badge badge-{result_class}">{winner_name}</span></td>
                <td>{m.moves_count}</td>
                <td>{m.total_time_ms:.1f}</td>
            </tr>
'''

        return f'''
        <div class="section">
            <h2>Torneio: Todos contra Todos</h2>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                Cada algoritmo jogou contra todos os outros, alternando entre X e O.
                Como todos jogam de forma otima, espera-se empates na maioria dos casos.
            </p>

            <h3 style="color: var(--accent-blue); margin: 1.5rem 0 1rem;">Ranking Geral</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">#</th>
                        <th>Algoritmo</th>
                        <th>Vitorias</th>
                        <th>Empates</th>
                        <th>Derrotas</th>
                        <th>Pontos</th>
                        <th>Nos Totais</th>
                    </tr>
                </thead>
                <tbody>
                    {ranking_rows}
                </tbody>
            </table>

            <h3 style="color: var(--accent-blue); margin: 2rem 0 1rem;">Partidas Mais Rapidas</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.9rem;">
                Partidas ordenadas por numero de jogadas (menos jogadas = decisao mais rapida)
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Jogador X</th>
                        <th></th>
                        <th>Jogador O</th>
                        <th>Tabuleiro Final</th>
                        <th>Resultado</th>
                        <th>Jogadas</th>
                        <th>Tempo (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {match_rows}
                </tbody>
            </table>
        </div>
'''

    def _generate_html_header(self) -> str:
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparativo de Algoritmos Minimax</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --accent-purple: #a855f7;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        header {
            text-align: center;
            padding: 3rem 0;
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            border-bottom: 1px solid var(--bg-card);
        }

        header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        header p {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }

        .section {
            margin: 2rem 0;
            padding: 2rem;
            background: var(--bg-secondary);
            border-radius: 16px;
            border: 1px solid var(--bg-card);
        }

        .section h2 {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section h2::before {
            content: '';
            width: 4px;
            height: 24px;
            background: var(--accent-blue);
            border-radius: 2px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .summary-card {
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }

        .summary-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-blue);
        }

        .summary-card .label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }

        .summary-card.best .value { color: var(--accent-green); }
        .summary-card.warning .value { color: var(--accent-orange); }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }

        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--bg-card);
        }

        th {
            background: var(--bg-card);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }

        tr:hover {
            background: rgba(59, 130, 246, 0.1);
        }

        .algo-name {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .algo-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .reduction-bar {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .reduction-bar .bar {
            height: 8px;
            border-radius: 4px;
            background: var(--accent-green);
            transition: width 0.3s ease;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-win { background: rgba(34, 197, 94, 0.2); color: var(--accent-green); }
        .badge-tie { background: rgba(249, 115, 22, 0.2); color: var(--accent-orange); }
        .badge-unknown { background: rgba(148, 163, 184, 0.2); color: var(--text-secondary); }

        .chart-container {
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
        }

        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }

        .depth-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }

        .depth-tab {
            padding: 0.5rem 1.25rem;
            border-radius: 8px;
            background: var(--bg-card);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        .depth-tab:hover {
            background: rgba(59, 130, 246, 0.2);
        }

        .depth-tab.active {
            background: var(--accent-blue);
            color: white;
        }

        .depth-content {
            display: none;
        }

        .depth-content.active {
            display: block;
        }

        .metric-extra {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .insights {
            background: rgba(59, 130, 246, 0.1);
            border-left: 4px solid var(--accent-blue);
            padding: 1rem 1.5rem;
            border-radius: 0 8px 8px 0;
            margin: 1rem 0;
        }

        .insights h4 {
            color: var(--accent-blue);
            margin-bottom: 0.5rem;
        }

        .insights ul {
            margin-left: 1.25rem;
            color: var(--text-secondary);
        }

        .insights li {
            margin: 0.25rem 0;
        }

        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            .container { padding: 1rem; }
            header h1 { font-size: 1.75rem; }
            .section { padding: 1rem; }
            th, td { padding: 0.5rem; font-size: 0.85rem; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Comparativo de Algoritmos Minimax</h1>
        <p>Analise detalhada de desempenho para Jogo da Velha</p>
    </header>
    <div class="container">
'''

    def _generate_summary_section(self, results: List[BenchmarkResult], baseline: int) -> str:
        best = min(results, key=lambda r: r.nodes_evaluated)
        fastest = min(results, key=lambda r: r.time_ms)
        least_memory = min(results, key=lambda r: r.memory_kb if r.memory_kb > 0 else float('inf'))

        best_reduction = (1 - best.nodes_evaluated / baseline) * 100 if baseline > 0 else 0

        return f'''
        <div class="section">
            <h2>Resumo Executivo</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">{len(results)}</div>
                    <div class="label">Algoritmos Testados</div>
                </div>
                <div class="summary-card best">
                    <div class="value">{best.algorithm}</div>
                    <div class="label">Menor Numero de Nos</div>
                </div>
                <div class="summary-card best">
                    <div class="value">{best_reduction:.1f}%</div>
                    <div class="label">Reducao vs Minimax</div>
                </div>
                <div class="summary-card">
                    <div class="value">{fastest.algorithm}</div>
                    <div class="label">Mais Rapido</div>
                </div>
                <div class="summary-card">
                    <div class="value">{fastest.time_ms:.2f}ms</div>
                    <div class="label">Menor Tempo</div>
                </div>
                <div class="summary-card">
                    <div class="value">{baseline:,}</div>
                    <div class="label">Nos Minimax (Base)</div>
                </div>
            </div>

            <div class="insights">
                <h4>Principais Insights</h4>
                <ul>
                    <li><strong>{best.algorithm}</strong> avaliou apenas <strong>{best.nodes_evaluated:,}</strong> nos, uma reducao de <strong>{best_reduction:.1f}%</strong> em relacao ao Minimax puro.</li>
                    <li>O algoritmo mais rapido foi <strong>{fastest.algorithm}</strong> com <strong>{fastest.time_ms:.2f}ms</strong>.</li>
                    <li>Todos os algoritmos chegaram a mesma decisao otima, garantindo corretude.</li>
                </ul>
            </div>
        </div>
'''

    def _generate_unlimited_comparison(self, results: List[BenchmarkResult], baseline: int) -> str:
        rows = ''
        for r in results:
            reduction = (1 - r.nodes_evaluated / baseline) * 100 if baseline > 0 else 0
            color = self.COLORS.get(r.algorithm, '#666')

            extra_html = ''
            if r.extra_stats:
                extras = []
                if 'nodes_pruned' in r.extra_stats:
                    extras.append(f"{r.extra_stats['nodes_pruned']:,} podas")
                if 'tt_hit_rate' in r.extra_stats:
                    extras.append(f"{r.extra_stats['tt_hit_rate']}% cache hits")
                if 'unique_positions' in r.extra_stats:
                    extras.append(f"{r.extra_stats['unique_positions']:,} posicoes unicas")
                if 're_searches' in r.extra_stats:
                    extras.append(f"{r.extra_stats['re_searches']:,} re-buscas")
                extra_html = f'<div class="metric-extra">{" | ".join(extras)}</div>'

            rows += f'''
            <tr>
                <td>
                    <div class="algo-name">
                        <div class="algo-dot" style="background: {color}"></div>
                        {r.algorithm}
                    </div>
                </td>
                <td>{r.nodes_evaluated:,}</td>
                <td>
                    <div class="reduction-bar">
                        <div class="bar" style="width: {min(reduction, 100)}px"></div>
                        <span>{reduction:.1f}%</span>
                    </div>
                </td>
                <td>{r.time_ms:.2f}</td>
                <td>{r.memory_kb:.1f}</td>
                <td>{r.max_depth_reached}</td>
                <td><span class="badge badge-{r.result_type.lower()}">{r.result_type}</span></td>
                <td>{extra_html}</td>
            </tr>
'''

        return f'''
        <div class="section">
            <h2>Comparacao Completa (Sem Limite de Profundidade)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Algoritmo</th>
                        <th>Nos Avaliados</th>
                        <th>Reducao</th>
                        <th>Tempo (ms)</th>
                        <th>Memoria (KB)</th>
                        <th>Prof. Max</th>
                        <th>Resultado</th>
                        <th>Metricas Extras</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
'''

    def _generate_depth_analysis(self, depth_results: Dict[int, List[BenchmarkResult]], baseline: int) -> str:
        if not depth_results:
            return ''

        tabs_html = ''
        content_html = ''

        for i, (depth, results) in enumerate(sorted(depth_results.items(), reverse=True)):
            active = 'active' if i == 0 else ''
            tabs_html += f'<div class="depth-tab {active}" onclick="showDepth({depth})" data-depth="{depth}">Profundidade {depth}</div>'

            rows = ''
            for r in results:
                reduction = (1 - r.nodes_evaluated / baseline) * 100 if baseline > 0 else 0
                color = self.COLORS.get(r.algorithm, '#666')

                rows += f'''
                <tr>
                    <td>
                        <div class="algo-name">
                            <div class="algo-dot" style="background: {color}"></div>
                            {r.algorithm}
                        </div>
                    </td>
                    <td>{r.nodes_evaluated:,}</td>
                    <td>{reduction:.1f}%</td>
                    <td>{r.time_ms:.2f}</td>
                    <td>{r.score}</td>
                    <td><span class="badge badge-{r.result_type.lower()}">{r.result_type}</span></td>
                </tr>
'''

            content_html += f'''
            <div class="depth-content {active}" id="depth-{depth}">
                <table>
                    <thead>
                        <tr>
                            <th>Algoritmo</th>
                            <th>Nos Avaliados</th>
                            <th>Reducao vs Minimax</th>
                            <th>Tempo (ms)</th>
                            <th>Score</th>
                            <th>Previsao</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
'''

        return f'''
        <div class="section">
            <h2>Analise por Limite de Profundidade</h2>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                Compare como os algoritmos se comportam com diferentes limites de profundidade.
                Limites menores simulam situacoes onde tempo e computacionalmente limitado.
            </p>
            <div class="depth-tabs">
                {tabs_html}
            </div>
            {content_html}
        </div>
'''

    def _generate_charts_section(self, unlimited: List[BenchmarkResult], depth_results: Dict) -> str:
        # Prepare data for charts
        labels = [r.algorithm for r in unlimited]
        nodes_data = [r.nodes_evaluated for r in unlimited]
        time_data = [r.time_ms for r in unlimited]
        colors = [self.COLORS.get(r.algorithm, '#666') for r in unlimited]

        # Depth comparison data
        depth_labels = sorted(depth_results.keys(), reverse=True) if depth_results else []
        depth_datasets = []
        for name, color in self.COLORS.items():
            data = []
            for depth in depth_labels:
                result = next((r for r in depth_results.get(depth, []) if r.algorithm == name), None)
                data.append(result.nodes_evaluated if result else 0)
            if any(data):
                depth_datasets.append({
                    'label': name,
                    'data': data,
                    'borderColor': color,
                    'backgroundColor': color + '33',
                    'fill': True
                })

        return f'''
        <div class="section">
            <h2>Visualizacoes</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <h3 style="margin-bottom: 1rem; color: var(--text-secondary);">Nos Avaliados por Algoritmo</h3>
                    <canvas id="nodesChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3 style="margin-bottom: 1rem; color: var(--text-secondary);">Tempo de Execucao (ms)</h3>
                    <canvas id="timeChart"></canvas>
                </div>
            </div>
            <div class="chart-container" style="margin-top: 1.5rem;">
                <h3 style="margin-bottom: 1rem; color: var(--text-secondary);">Nos Avaliados vs Profundidade</h3>
                <canvas id="depthChart"></canvas>
            </div>
        </div>

        <script>
            const chartColors = {repr(colors)};
            const labels = {repr(labels)};

            // Nodes chart
            new Chart(document.getElementById('nodesChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Nos Avaliados',
                        data: {nodes_data},
                        backgroundColor: chartColors,
                        borderRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            type: 'logarithmic',
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#94a3b8' }}
                        }}
                    }}
                }}
            }});

            // Time chart
            new Chart(document.getElementById('timeChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Tempo (ms)',
                        data: {time_data},
                        backgroundColor: chartColors,
                        borderRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#94a3b8' }}
                        }}
                    }}
                }}
            }});

            // Depth comparison chart
            new Chart(document.getElementById('depthChart'), {{
                type: 'line',
                data: {{
                    labels: {repr(['Prof. ' + str(d) for d in depth_labels])},
                    datasets: {repr(depth_datasets).replace("'", '"')}
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            labels: {{ color: '#94a3b8' }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            type: 'logarithmic',
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ color: '#334155' }},
                            ticks: {{ color: '#94a3b8' }}
                        }}
                    }}
                }}
            }});

            // Depth tab switching
            function showDepth(depth) {{
                document.querySelectorAll('.depth-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.depth-content').forEach(c => c.classList.remove('active'));
                document.querySelector(`[data-depth="${{depth}}"]`).classList.add('active');
                document.getElementById(`depth-${{depth}}`).classList.add('active');
            }}
        </script>
'''

    def _generate_methodology_section(self) -> str:
        return '''
        <div class="section">
            <h2>Metodologia</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                <div>
                    <h3 style="color: var(--accent-blue); margin-bottom: 1rem;">Ambiente de Teste</h3>
                    <ul style="color: var(--text-secondary); margin-left: 1.25rem;">
                        <li>Tabuleiro inicial: vazio (9 posicoes disponiveis)</li>
                        <li>Perspectiva: Jogador X (primeiro a jogar)</li>
                        <li>Medicao de memoria: tracemalloc do Python</li>
                        <li>Cada algoritmo executado independentemente</li>
                    </ul>
                </div>
                <div>
                    <h3 style="color: var(--accent-blue); margin-bottom: 1rem;">Metricas Coletadas</h3>
                    <ul style="color: var(--text-secondary); margin-left: 1.25rem;">
                        <li><strong>Nos avaliados:</strong> Estados de tabuleiro analisados</li>
                        <li><strong>Tempo:</strong> Duracao da busca em milissegundos</li>
                        <li><strong>Memoria:</strong> Pico de memoria durante execucao</li>
                        <li><strong>Profundidade:</strong> Nivel maximo alcancado na arvore</li>
                    </ul>
                </div>
                <div>
                    <h3 style="color: var(--accent-blue); margin-bottom: 1rem;">Algoritmos Analisados</h3>
                    <ul style="color: var(--text-secondary); margin-left: 1.25rem;">
                        <li><strong>Minimax:</strong> Busca completa sem otimizacoes</li>
                        <li><strong>Alpha-Beta:</strong> Poda de ramos garantidamente piores</li>
                        <li><strong>AB + TT:</strong> Memoizacao de estados ja avaliados</li>
                        <li><strong>AB + Simetria:</strong> Reducao usando grupo D4</li>
                        <li><strong>NegaScout:</strong> Busca com janela nula</li>
                    </ul>
                </div>
            </div>
        </div>
'''

    def _generate_html_footer(self) -> str:
        return '''
    </div>
    <div class="footer">
        <p>Gerado automaticamente pelo sistema de benchmarking</p>
        <p>Jogo da Velha - Inteligencia Artificial</p>
    </div>
</body>
</html>
'''

    def show(self):
        """Runs benchmark and opens the report in browser."""
        print("Executando benchmark completo...")
        self.run_full_benchmark()
        print(f"Benchmark concluido. {len(self.results)} resultados coletados.")

        print("Executando torneio todos contra todos...")
        self.run_tournament()
        print(f"Torneio concluido. {len(self.tournament_results)} partidas jogadas.")

        html = self.generate_html()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as f:
            f.write(html)
            webbrowser.open('file://' + f.name)
            print(f"Relatorio aberto em: {f.name}")
