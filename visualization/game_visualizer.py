import webbrowser
import tempfile
import json
from typing import List
from visualization.game_history import GameHistoryCollector, MoveAnalysis


POSITION_NAMES = {
    0: "Superior Esquerdo", 1: "Superior Centro", 2: "Superior Direito",
    3: "Centro Esquerdo", 4: "Centro", 5: "Centro Direito",
    6: "Inferior Esquerdo", 7: "Inferior Centro", 8: "Inferior Direito"
}


class GameVisualizer:
    """Creates a clean visualization of the game history."""

    def __init__(self, history: GameHistoryCollector):
        """
        Initializes the visualizer with game history.

        Args:
            history: GameHistoryCollector with recorded moves.
        """
        self.history = history

    def _board_to_html(self, board: List[str], highlight: int = -1) -> str:
        """Creates an HTML representation of the board."""
        html = '<div class="mini-board">'
        for i, cell in enumerate(board):
            cell_class = "cell"
            if cell == 'X':
                cell_class += " cell-x"
            elif cell == 'O':
                cell_class += " cell-o"
            if i == highlight:
                cell_class += " cell-highlight"
            display = cell if cell != ' ' else '&nbsp;'
            html += f'<div class="{cell_class}">{display}</div>'
        html += '</div>'
        return html

    def _get_decision_explanation(self, move: MoveAnalysis) -> str:
        """Creates a detailed explanation of the decision process."""
        player_type = "maximizador" if move.player == 'X' else "minimizador"
        objective = "MAIOR" if move.player == 'X' else "MENOR"
        
        # Determina o nome do algoritmo
        if move.algorithm_name:
            algorithm_display = move.algorithm_name.replace('Player', '')
            if 'AlphaBeta' in move.algorithm_name:
                algorithm_title = f"Alpha-Beta Pruning"
            else:
                algorithm_title = algorithm_display
        else:
            algorithm_title = "Minimax"

        sorted_alts = sorted(
            move.alternatives,
            key=lambda x: x['score'],
            reverse=(move.player == 'X')
        )

        best_alt = sorted_alts[0] if sorted_alts else None
        worst_alt = sorted_alts[-1] if sorted_alts else None

        explanation = f'''
        <div class="decision-explanation">
            <h4>🧠 Processo de Decisão do {algorithm_title}</h4>

            <div class="step">
                <span class="step-num">1</span>
                <div class="step-content">
                    <strong>Geração de Movimentos</strong>
                    <p>A IA identificou <strong>{len(move.alternatives)}</strong> posições disponíveis para jogar.</p>
                </div>
            </div>

            <div class="step">
                <span class="step-num">2</span>
                <div class="step-content">
                    <strong>Simulação Recursiva</strong>
                    <p>Para cada posição, o algoritmo simulou <strong>todas as partidas possíveis</strong> até o final,
                    avaliando <strong>{move.nodes_evaluated:,}</strong> estados do tabuleiro.</p>
                    {'<p class="highlight-text">⚡ Com Alpha-Beta Pruning, alguns ramos foram cortados para otimizar a busca!</p>' if 'AlphaBeta' in str(move.algorithm_name) else ''}
                </div>
            </div>

            <div class="step">
                <span class="step-num">3</span>
                <div class="step-content">
                    <strong>Avaliação de Scores</strong>
                    <p>Cada caminho recebeu uma pontuação:</p>
                    <ul>
                        <li><span class="score-tag positive">+10</span> Vitória da IA (ajustado pela profundidade)</li>
                        <li><span class="score-tag negative">-10</span> Derrota da IA (ajustado pela profundidade)</li>
                        <li><span class="score-tag neutral">0</span> Empate</li>
                    </ul>
                </div>
            </div>

            <div class="step">
                <span class="step-num">4</span>
                <div class="step-content">
                    <strong>Seleção do Movimento ({player_type.upper()})</strong>
                    <p>Como jogador <strong>{player_type}</strong>, a IA escolheu a jogada com o <strong>{objective}</strong> score.</p>
                    {f'<p class="highlight-text">Melhor opção: <strong>{POSITION_NAMES.get(best_alt["position"], best_alt["position"])}</strong> com score <strong>{best_alt["score"]}</strong></p>' if best_alt else ''}
                    {f'<p class="dim-text">Pior opção evitada: {POSITION_NAMES.get(worst_alt["position"], worst_alt["position"])} com score {worst_alt["score"]}</p>' if worst_alt and len(sorted_alts) > 1 else ''}
                </div>
            </div>

            <div class="step">
                <span class="step-num">5</span>
                <div class="step-content">
                    <strong>Tempo de Processamento</strong>
                    <p>Todo este processo levou apenas <strong>{move.time_ms:.2f}ms</strong>!</p>
                </div>
            </div>
        </div>
        '''
        return explanation

    def _create_alternatives_html(self, move: MoveAnalysis) -> str:
        """Creates HTML for the alternatives analysis."""
        if not move.alternatives:
            return ""

        html = '<div class="alternatives"><h4>📊 Alternativas Avaliadas:</h4><div class="alt-grid">'

        sorted_alts = sorted(
            move.alternatives,
            key=lambda x: x['score'],
            reverse=(move.player == 'X')
        )

        for i, alt in enumerate(sorted_alts):
            pos = alt['position']
            score = alt['score']
            is_chosen = pos == move.chosen_position

            score_class = "score-positive" if score > 0 else "score-negative" if score < 0 else "score-neutral"
            chosen_class = " chosen" if is_chosen else ""
            rank_class = "rank-best" if i == 0 else "rank-worst" if i == len(sorted_alts) - 1 else ""

            rank_badge = ""
            if i == 0:
                rank_badge = '<span class="rank-badge best">MELHOR</span>'
            elif i == len(sorted_alts) - 1 and len(sorted_alts) > 1:
                rank_badge = '<span class="rank-badge worst">PIOR</span>'

            html += f'''
            <div class="alt-item{chosen_class} {rank_class}" title="Posição {pos}: Se jogar aqui, o melhor resultado possível leva ao score {score}">
                <div class="alt-header">
                    <div class="alt-pos">{POSITION_NAMES.get(pos, pos)}</div>
                    {rank_badge}
                </div>
                <div class="alt-score {score_class}">Score: {score}</div>
                <div class="alt-meaning">
                    {self._get_score_meaning(score)}
                </div>
                {"<div class='chosen-badge'>✓ ESCOLHIDO</div>" if is_chosen else ""}
            </div>
            '''

        html += '</div></div>'
        return html

    def _get_score_meaning(self, score: int) -> str:
        """Returns a human-readable meaning for a score."""
        if score > 5:
            return "Caminho para vitória rápida"
        elif score > 0:
            return "Caminho para vitória"
        elif score == 0:
            return "Caminho para empate"
        elif score > -5:
            return "Risco de derrota"
        else:
            return "Caminho para derrota"

    def show(self):
        """Opens the visualization in the browser."""
        if not self.history.has_moves():
            print("Nenhum movimento para visualizar.")
            return

        moves = self.history.get_ai_moves()
        total_nodes = self.history.get_total_nodes()
        total_time = self.history.get_total_time()
        
        # Detecta quais algoritmos foram usados
        algorithms_used = set()
        for move in moves:
            if move.algorithm_name:
                algo_name = move.algorithm_name.replace('Player', '').replace('AlphaBeta', 'Alpha-Beta')
                algorithms_used.add(algo_name)
        
        if algorithms_used:
            algorithm_description = " e ".join(sorted(algorithms_used))
        else:
            algorithm_description = "Minimax"

        result_text = ""
        result_class = ""
        if moves and moves[-1].result:
            if moves[-1].result == 'WIN_X':
                result_text = "Vitória do X!"
                result_class = "result-x"
            elif moves[-1].result == 'WIN_O':
                result_text = "Vitória do O!"
                result_class = "result-o"
            else:
                result_text = "Empate!"
                result_class = "result-tie"

        moves_html = ""
        for move in moves:
            player_class = "player-x" if move.player == 'X' else "player-o"
            player_icon = "🔵" if move.player == 'X' else "🔴"
            
            # Usa o nome do algoritmo se disponível, senão usa MAX/MIN baseado no jogador
            if move.algorithm_name:
                algorithm_display = move.algorithm_name.replace('Player', '').replace('AlphaBeta', 'Alpha-Beta')
                player_role = f"{algorithm_display} ({'Maximizador' if move.player == 'X' else 'Minimizador'})"
            else:
                player_role = "MAX (Maximizador)" if move.player == 'X' else "MIN (Minimizador)"

            moves_html += f'''
            <div class="move-card {player_class}">
                <div class="move-header">
                    <span class="move-number">Jogada {move.move_number}</span>
                    <span class="move-player">{player_icon} Jogador {move.player} - {player_role}</span>
                </div>

                <div class="move-content">
                    <div class="board-section">
                        <div class="board-label">Antes</div>
                        {self._board_to_html(move.board_before)}
                    </div>

                    <div class="arrow-section">
                        <div class="arrow">→</div>
                        <div class="move-info">
                            <div class="position-name">{POSITION_NAMES.get(move.chosen_position, move.chosen_position)}</div>
                            <div class="move-score">Score: {move.chosen_score}</div>
                        </div>
                    </div>

                    <div class="board-section">
                        <div class="board-label">Depois</div>
                        {self._board_to_html(move.board_after, move.chosen_position)}
                    </div>
                </div>

                <div class="move-stats">
                    <span title="Tempo que a IA levou para calcular">⏱️ {move.time_ms:.1f}ms</span>
                    <span title="Quantidade de estados do tabuleiro analisados">🔍 {move.nodes_evaluated:,} nós avaliados</span>
                    {f'<span title="Nós podados pelo Alpha-Beta">✂️ {move.nodes_pruned:,} nós podados</span>' if move.nodes_pruned and move.nodes_pruned > 0 else ''}
                </div>

                {self._get_decision_explanation(move)}

                {self._create_alternatives_html(move)}

                {f'<div class="terminal-badge {result_class}">{result_text}</div>' if move.is_terminal else ''}
            </div>
            '''

        html_content = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Análise da Partida - Jogo da Velha com {algorithm_description}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(90deg, #3498db, #2ecc71, #f39c12);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .header p {{
            color: #bdc3c7;
            font-size: 1.1em;
        }}

        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 20px 0;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #3498db;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #95a5a6;
        }}

        .timeline {{
            position: relative;
            padding-left: 30px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #3498db, #2ecc71);
            border-radius: 2px;
        }}

        .move-card {{
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 25px;
            position: relative;
            border-left: 4px solid #3498db;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .move-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .move-card.player-x {{
            border-left-color: #3498db;
        }}

        .move-card.player-o {{
            border-left-color: #e74c3c;
        }}

        .move-card::before {{
            content: '';
            position: absolute;
            left: -37px;
            top: 25px;
            width: 16px;
            height: 16px;
            background: #3498db;
            border-radius: 50%;
            border: 3px solid #1a1a2e;
        }}

        .move-card.player-o::before {{
            background: #e74c3c;
        }}

        .move-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .move-number {{
            font-size: 0.9em;
            color: #95a5a6;
        }}

        .move-player {{
            font-weight: bold;
            font-size: 1.1em;
        }}

        .move-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}

        .board-section {{
            text-align: center;
        }}

        .board-label {{
            font-size: 0.8em;
            color: #95a5a6;
            margin-bottom: 8px;
        }}

        .mini-board {{
            display: grid;
            grid-template-columns: repeat(3, 45px);
            gap: 3px;
            background: #2c3e50;
            padding: 5px;
            border-radius: 8px;
        }}

        .cell {{
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #34495e;
            font-size: 1.3em;
            font-weight: bold;
            border-radius: 4px;
        }}

        .cell-x {{ color: #3498db; }}
        .cell-o {{ color: #e74c3c; }}
        .cell-highlight {{
            background: #2ecc71 !important;
            animation: pulse 1s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}

        .arrow-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
        }}

        .arrow {{
            font-size: 2em;
            color: #2ecc71;
        }}

        .move-info {{
            text-align: center;
        }}

        .position-name {{
            font-size: 0.9em;
            color: #f39c12;
            font-weight: bold;
        }}

        .move-score {{
            font-size: 0.85em;
            color: #2ecc71;
        }}

        .move-stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            font-size: 0.85em;
            color: #7f8c8d;
            margin: 10px 0;
        }}

        .move-stats span {{
            cursor: help;
        }}

        /* Decision Explanation Styles */
        .decision-explanation {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border-left: 3px solid #9b59b6;
        }}

        .decision-explanation h4 {{
            color: #9b59b6;
            margin-bottom: 15px;
            font-size: 1.1em;
        }}

        .step {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            align-items: flex-start;
        }}

        .step:last-child {{
            margin-bottom: 0;
        }}

        .step-num {{
            background: #9b59b6;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
            flex-shrink: 0;
        }}

        .step-content {{
            flex: 1;
        }}

        .step-content strong {{
            color: #ecf0f1;
            display: block;
            margin-bottom: 5px;
        }}

        .step-content p {{
            color: #bdc3c7;
            font-size: 0.9em;
            line-height: 1.5;
        }}

        .step-content ul {{
            list-style: none;
            margin-top: 8px;
        }}

        .step-content li {{
            padding: 4px 0;
            font-size: 0.85em;
            color: #bdc3c7;
        }}

        .score-tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 8px;
        }}

        .score-tag.positive {{ background: rgba(46, 204, 113, 0.3); color: #2ecc71; }}
        .score-tag.negative {{ background: rgba(231, 76, 60, 0.3); color: #e74c3c; }}
        .score-tag.neutral {{ background: rgba(243, 156, 18, 0.3); color: #f39c12; }}

        .highlight-text {{
            color: #2ecc71 !important;
            font-size: 0.95em !important;
        }}

        .dim-text {{
            color: #7f8c8d !important;
            font-size: 0.85em !important;
        }}

        /* Alternatives Styles */
        .alternatives {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}

        .alternatives h4 {{
            font-size: 0.95em;
            color: #95a5a6;
            margin-bottom: 12px;
        }}

        .alt-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 10px;
        }}

        .alt-item {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            font-size: 0.85em;
            position: relative;
            cursor: help;
            transition: transform 0.2s, background 0.2s;
        }}

        .alt-item:hover {{
            transform: scale(1.02);
            background: rgba(0,0,0,0.3);
        }}

        .alt-item.chosen {{
            background: rgba(46, 204, 113, 0.2);
            border: 2px solid #2ecc71;
        }}

        .alt-item.rank-best {{
            border-top: 3px solid #2ecc71;
        }}

        .alt-item.rank-worst {{
            border-top: 3px solid #e74c3c;
            opacity: 0.7;
        }}

        .alt-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }}

        .alt-pos {{
            font-weight: bold;
            color: #ecf0f1;
        }}

        .rank-badge {{
            font-size: 0.65em;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}

        .rank-badge.best {{
            background: #2ecc71;
            color: white;
        }}

        .rank-badge.worst {{
            background: #e74c3c;
            color: white;
        }}

        .alt-score {{
            font-size: 0.9em;
            margin: 5px 0;
        }}

        .score-positive {{ color: #2ecc71; }}
        .score-negative {{ color: #e74c3c; }}
        .score-neutral {{ color: #f39c12; }}

        .alt-meaning {{
            font-size: 0.75em;
            color: #7f8c8d;
            font-style: italic;
        }}

        .chosen-badge {{
            font-size: 0.7em;
            background: #2ecc71;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            margin-top: 8px;
            display: inline-block;
        }}

        .terminal-badge {{
            text-align: center;
            padding: 12px;
            margin-top: 15px;
            border-radius: 8px;
            font-size: 1.3em;
            font-weight: bold;
        }}

        .result-x {{
            background: rgba(52, 152, 219, 0.3);
            color: #3498db;
        }}

        .result-o {{
            background: rgba(231, 76, 60, 0.3);
            color: #e74c3c;
        }}

        .result-tie {{
            background: rgba(243, 156, 18, 0.3);
            color: #f39c12;
        }}

        .info-section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }}

        .info-section h3 {{
            color: #3498db;
            margin-bottom: 20px;
            font-size: 1.3em;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}

        .info-card {{
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
        }}

        .info-card h4 {{
            color: #f39c12;
            margin-bottom: 10px;
            font-size: 1em;
        }}

        .info-card p {{
            color: #bdc3c7;
            font-size: 0.9em;
            line-height: 1.6;
        }}

        .info-card ul {{
            list-style: none;
            margin-top: 10px;
        }}

        .info-card li {{
            padding: 5px 0;
            color: #bdc3c7;
            font-size: 0.85em;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}

        .info-card li:last-child {{
            border-bottom: none;
        }}

        @media (max-width: 600px) {{
            .move-content {{
                flex-direction: column;
            }}

            .arrow {{
                transform: rotate(90deg);
            }}

            .alt-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Análise da Partida</h1>
            <p>Visualização completa do algoritmo {algorithm_description} em ação</p>
        </div>

        <div class="stats-bar">
            <div class="stat">
                <div class="stat-value">{len(moves)}</div>
                <div class="stat-label">Jogadas da IA</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_nodes:,}</div>
                <div class="stat-label">Nós Avaliados</div>
            </div>
            <div class="stat">
                <div class="stat-value">{total_time:.0f}ms</div>
                <div class="stat-label">Tempo Total</div>
            </div>
        </div>

        <div class="timeline">
            {moves_html}
        </div>

        <div class="info-section">
            <h3>📚 Como funciona o Algoritmo {algorithm_description}?</h3>
            <div class="info-grid">
                <div class="info-card">
                    <h4>🎯 O que é o Minimax?</h4>
                    <p>O Minimax é um algoritmo de busca em árvore usado em jogos de dois jogadores.
                    Ele simula todas as jogadas possíveis até o final do jogo para encontrar o movimento ótimo.</p>
                    {'<p><strong>Alpha-Beta Pruning:</strong> Uma otimização que corta ramos desnecessários da árvore de decisão, mantendo o mesmo resultado mas avaliando menos nós!</p>' if 'Alpha-Beta' in algorithm_description else ''}
                </div>

                <div class="info-card">
                    <h4>🔵 Jogador MAX (X)</h4>
                    <p>O jogador X é o <strong>maximizador</strong>. Ele sempre escolhe o movimento
                    que leva ao <strong>maior</strong> score possível, buscando a vitória.</p>
                </div>

                <div class="info-card">
                    <h4>🔴 Jogador MIN (O)</h4>
                    <p>O jogador O é o <strong>minimizador</strong>. Ele sempre escolhe o movimento
                    que leva ao <strong>menor</strong> score, tentando impedir a vitória do oponente.</p>
                </div>

                <div class="info-card">
                    <h4>📊 Sistema de Pontuação</h4>
                    <ul>
                        <li><strong>+10:</strong> Vitória do X (MAX)</li>
                        <li><strong>-10:</strong> Vitória do O (MIN)</li>
                        <li><strong>0:</strong> Empate</li>
                        <li><strong>Ajuste de profundidade:</strong> Vitórias rápidas valem mais!</li>
                    </ul>
                </div>

                <div class="info-card">
                    <h4>⚡ Por que é eficiente?</h4>
                    <p>Apesar de avaliar milhares de possibilidades, o algoritmo é muito rápido
                    (milissegundos) porque o Jogo da Velha tem um espaço de estados limitado.</p>
                </div>

                <div class="info-card">
                    <h4>🏆 Resultado Garantido</h4>
                    <p>Com dois jogadores usando algoritmos perfeitos ({algorithm_description}), o jogo <strong>sempre termina em empate</strong>.
                    É impossível vencer uma IA com esses algoritmos se você também jogar perfeitamente!</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            webbrowser.open('file://' + f.name)
