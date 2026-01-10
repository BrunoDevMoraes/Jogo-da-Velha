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

    def _get_move_analysis(self, move: MoveAnalysis) -> str:
        """Creates a concise analysis specific to this move."""
        opponent = 'O' if move.player == 'X' else 'X'

        sorted_alts = sorted(move.alternatives, key=lambda x: x['score'], reverse=True)
        best_score = sorted_alts[0]['score'] if sorted_alts else 0
        worst_score = sorted_alts[-1]['score'] if sorted_alts else 0
        ties_count = len([a for a in sorted_alts if a['score'] == best_score])

        # Determine outcome
        if move.chosen_score > 0:
            outcome = f"<span class='outcome-win'>Vitória de {move.player} garantida</span>"
            outcome_detail = f"{move.player} vence em {10 - move.chosen_score} jogadas com jogo perfeito."
        elif move.chosen_score == 0:
            outcome = "<span class='outcome-tie'>Empate garantido</span>"
            outcome_detail = "Nenhum jogador consegue vencer se ambos jogarem perfeitamente."
        else:
            outcome = f"<span class='outcome-lose'>Desvantagem para {move.player}</span>"
            outcome_detail = f"{opponent} vence em {10 + move.chosen_score} jogadas se jogar perfeitamente."

        # Why this move?
        if ties_count > 1:
            choice_reason = f"Havia {ties_count} jogadas com o mesmo score ({best_score}). A IA escolheu a primeira encontrada na ordem de varredura."
        elif best_score == worst_score:
            choice_reason = f"Todas as {len(sorted_alts)} opções levam ao mesmo resultado. Qualquer escolha é equivalente."
        else:
            choice_reason = f"Esta foi a única jogada com o melhor score possível ({move.chosen_score})."

        return f'''
        <div class="move-analysis">
            <div class="analysis-header">
                <span class="analysis-title">Análise da Jogada</span>
                <span class="analysis-stats">🔍 {move.nodes_evaluated:,} estados analisados em {move.time_ms:.1f}ms</span>
            </div>

            <div class="analysis-result">
                <div class="result-main">
                    <span class="result-label">Resultado esperado:</span>
                    {outcome}
                </div>
                <p class="result-detail">{outcome_detail}</p>
            </div>

            <div class="analysis-choice">
                <p><strong>Por que {POSITION_NAMES.get(move.chosen_position, move.chosen_position)}?</strong></p>
                <p>{choice_reason}</p>
            </div>
        </div>
        '''

    def _create_alternatives_board(self, move: MoveAnalysis) -> str:
        """Creates a board-style visualization of all alternatives with hover details."""
        if not move.alternatives:
            return ""

        opponent = 'O' if move.player == 'X' else 'X'

        # Create a map of position -> score
        score_map = {alt['position']: alt['score'] for alt in move.alternatives}

        sorted_alts = sorted(move.alternatives, key=lambda x: x['score'], reverse=True)
        best_score = sorted_alts[0]['score'] if sorted_alts else 0
        worst_score = sorted_alts[-1]['score'] if sorted_alts else 0

        html = f'''
        <div class="alternatives-board-section">
            <h4>📊 Mapa de Scores - Passe o mouse para detalhes</h4>
            <div class="board-legend">
                <span><span class="legend-color positive"></span> {move.player} vence</span>
                <span><span class="legend-color neutral"></span> Empate</span>
                <span><span class="legend-color negative"></span> {opponent} vence</span>
            </div>
            <div class="alternatives-board">'''

        for i in range(9):
            cell_content = move.board_before[i]

            if cell_content != ' ':
                # Cell already occupied
                cell_class = f"cell-occupied cell-{cell_content.lower()}"
                html += f'<div class="alt-cell {cell_class}">{cell_content}</div>'
            elif i in score_map:
                score = score_map[i]
                is_chosen = i == move.chosen_position

                # Determine color class
                if score > 0:
                    color_class = "cell-positive"
                    result_text = f"{move.player} vence em {10 - score} jogadas"
                    rank_text = "Leva à vitória"
                elif score == 0:
                    color_class = "cell-neutral"
                    result_text = "Empate garantido"
                    rank_text = "Leva ao empate"
                else:
                    color_class = "cell-negative"
                    result_text = f"{opponent} vence em {10 + score} jogadas"
                    rank_text = "Leva à derrota"

                # Determine if best/worst
                if score == best_score:
                    rank_class = "is-best"
                    rank_label = "MELHOR OPÇÃO"
                elif score == worst_score and best_score != worst_score:
                    rank_class = "is-worst"
                    rank_label = "PIOR OPÇÃO"
                else:
                    rank_class = ""
                    rank_label = f"Opção #{sorted_alts.index({'position': i, 'score': score}) + 1}"

                chosen_class = "is-chosen" if is_chosen else ""

                html += f'''
                <div class="alt-cell {color_class} {rank_class} {chosen_class}" data-pos="{i}">
                    <span class="cell-score">{score}</span>
                    {f'<span class="chosen-marker">✓</span>' if is_chosen else ''}
                    <div class="cell-tooltip">
                        <strong>{POSITION_NAMES.get(i, i)}</strong>
                        <div class="tooltip-rank">{rank_label}</div>
                        <div class="tooltip-result">{result_text}</div>
                        <div class="tooltip-score">Score: {score}</div>
                        {f'<div class="tooltip-chosen">← Jogada escolhida</div>' if is_chosen else ''}
                    </div>
                </div>'''
            else:
                html += '<div class="alt-cell cell-empty"></div>'

        html += '</div></div>'
        return html

    def show(self):
        """Opens the visualization in the browser."""
        if not self.history.has_moves():
            print("Nenhum movimento para visualizar.")
            return

        moves = self.history.get_ai_moves()
        total_nodes = self.history.get_total_nodes()
        total_time = self.history.get_total_time()

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

            moves_html += f'''
            <div class="move-card {player_class}">
                <div class="move-header">
                    <span class="move-number">Jogada {move.move_number}</span>
                    <span class="move-player">{player_icon} Jogador {move.player}</span>
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

                {self._get_move_analysis(move)}

                <div class="alternatives-section-label">Opções analisadas:</div>

                {self._create_alternatives_board(move)}

                {f'<div class="terminal-badge {result_class}">{result_text}</div>' if move.is_terminal else ''}
            </div>
            '''

        html_content = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Análise da Partida - Jogo da Velha com Minimax</title>
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

        /* Minimax explanation section */
        .minimax-explanation {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
        }}

        .minimax-explanation h3 {{
            color: #3498db;
            margin-bottom: 20px;
        }}

        .explanation-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}

        .explanation-step {{
            display: flex;
            gap: 12px;
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 8px;
        }}

        .step-number {{
            background: #3498db;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }}

        .step-text {{
            font-size: 0.9em;
            color: #bdc3c7;
            line-height: 1.5;
        }}

        .step-text strong {{
            color: #ecf0f1;
        }}

        .score-pos {{ color: #2ecc71; font-weight: bold; }}
        .score-neu {{ color: #f39c12; font-weight: bold; }}
        .score-neg {{ color: #e74c3c; font-weight: bold; }}

        .explanation-note {{
            background: rgba(243, 156, 18, 0.15);
            border-left: 4px solid #f39c12;
            padding: 12px 15px;
            border-radius: 0 8px 8px 0;
            font-size: 0.9em;
            color: #bdc3c7;
        }}

        .section-title {{
            color: #ecf0f1;
            margin: 20px 0 15px 0;
            padding-left: 30px;
        }}

        /* Move analysis styles */
        .move-analysis {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }}

        .analysis-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .analysis-title {{
            font-weight: bold;
            color: #9b59b6;
        }}

        .analysis-stats {{
            font-size: 0.85em;
            color: #7f8c8d;
        }}

        .analysis-result {{
            margin-bottom: 12px;
        }}

        .result-main {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .result-label {{
            color: #95a5a6;
            font-size: 0.9em;
        }}

        .outcome-win {{
            background: rgba(46, 204, 113, 0.2);
            color: #2ecc71;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}

        .outcome-tie {{
            background: rgba(243, 156, 18, 0.2);
            color: #f39c12;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}

        .outcome-lose {{
            background: rgba(231, 76, 60, 0.2);
            color: #e74c3c;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
        }}

        .result-detail {{
            font-size: 0.85em;
            color: #95a5a6;
            margin-top: 5px;
        }}

        .analysis-choice {{
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 12px;
        }}

        .analysis-choice p {{
            font-size: 0.9em;
            color: #bdc3c7;
            margin: 5px 0;
        }}

        /* Alternatives board styles */
        .alternatives-board-section {{
            margin-top: 15px;
        }}

        .alternatives-board-section h4 {{
            color: #95a5a6;
            font-size: 0.95em;
            margin-bottom: 10px;
        }}

        .board-legend {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            font-size: 0.8em;
            color: #95a5a6;
        }}

        .legend-color {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 3px;
            margin-right: 6px;
            vertical-align: middle;
        }}

        .legend-color.positive {{ background: rgba(46, 204, 113, 0.6); }}
        .legend-color.neutral {{ background: rgba(243, 156, 18, 0.6); }}
        .legend-color.negative {{ background: rgba(231, 76, 60, 0.6); }}

        .alternatives-board {{
            display: grid;
            grid-template-columns: repeat(3, 70px);
            gap: 5px;
            background: #2c3e50;
            padding: 8px;
            border-radius: 10px;
            width: fit-content;
        }}

        .alt-cell {{
            width: 70px;
            height: 70px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            position: relative;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .alt-cell:hover {{
            transform: scale(1.05);
            z-index: 10;
        }}

        .alt-cell.cell-occupied {{
            background: #34495e;
            cursor: default;
        }}

        .alt-cell.cell-occupied:hover {{
            transform: none;
        }}

        .alt-cell.cell-x {{ color: #3498db; font-size: 1.5em; font-weight: bold; }}
        .alt-cell.cell-o {{ color: #e74c3c; font-size: 1.5em; font-weight: bold; }}

        .alt-cell.cell-positive {{ background: rgba(46, 204, 113, 0.4); }}
        .alt-cell.cell-neutral {{ background: rgba(243, 156, 18, 0.4); }}
        .alt-cell.cell-negative {{ background: rgba(231, 76, 60, 0.4); }}

        .alt-cell.is-best {{ box-shadow: 0 0 0 3px #2ecc71; }}
        .alt-cell.is-worst {{ box-shadow: 0 0 0 3px #e74c3c; opacity: 0.7; }}
        .alt-cell.is-chosen {{ box-shadow: 0 0 0 3px #3498db, inset 0 0 10px rgba(52, 152, 219, 0.5); }}

        .cell-score {{
            font-size: 1.2em;
            font-weight: bold;
            color: white;
        }}

        .chosen-marker {{
            position: absolute;
            top: 3px;
            right: 5px;
            font-size: 0.8em;
            color: #3498db;
        }}

        .cell-tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #1a1a2e;
            border: 1px solid #3498db;
            border-radius: 8px;
            padding: 12px;
            min-width: 180px;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s, visibility 0.2s;
            z-index: 100;
            pointer-events: none;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
        }}

        .alt-cell:hover .cell-tooltip {{
            opacity: 1;
            visibility: visible;
        }}

        .cell-tooltip strong {{
            display: block;
            color: #ecf0f1;
            margin-bottom: 8px;
            font-size: 0.95em;
        }}

        .tooltip-rank {{
            font-size: 0.8em;
            padding: 3px 8px;
            border-radius: 3px;
            display: inline-block;
            margin-bottom: 8px;
        }}

        .is-best .tooltip-rank {{
            background: #2ecc71;
            color: white;
        }}

        .is-worst .tooltip-rank {{
            background: #e74c3c;
            color: white;
        }}

        .tooltip-result {{
            font-size: 0.85em;
            color: #bdc3c7;
            margin-bottom: 5px;
        }}

        .tooltip-score {{
            font-size: 0.85em;
            color: #95a5a6;
        }}

        .tooltip-chosen {{
            font-size: 0.8em;
            color: #3498db;
            margin-top: 8px;
            font-weight: bold;
        }}

        .alternatives-section-label {{
            color: #95a5a6;
            font-size: 0.9em;
            margin-top: 15px;
            margin-bottom: 10px;
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
            <p>Visualização completa do algoritmo Minimax em ação</p>
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

        <!-- Explicação do Minimax (uma vez só, no início) -->
        <div class="minimax-explanation">
            <h3>📚 Como funciona o Minimax?</h3>

            <div class="explanation-content">
                <div class="explanation-step">
                    <div class="step-number">1</div>
                    <div class="step-text">
                        <strong>Simulação completa:</strong> Para cada casa vazia, a IA simula todas as partidas possíveis até o final (vitória, derrota ou empate).
                    </div>
                </div>

                <div class="explanation-step">
                    <div class="step-number">2</div>
                    <div class="step-text">
                        <strong>Oponente inteligente:</strong> Durante a simulação, assume que o oponente sempre faz a melhor jogada possível.
                    </div>
                </div>

                <div class="explanation-step">
                    <div class="step-number">3</div>
                    <div class="step-text">
                        <strong>Pontuação:</strong> Cada resultado recebe um score: <span class="score-pos">+10</span> (vitória),
                        <span class="score-neu">0</span> (empate), <span class="score-neg">-10</span> (derrota).
                        O score é ajustado pela profundidade (vitória rápida vale mais).
                    </div>
                </div>

                <div class="explanation-step">
                    <div class="step-number">4</div>
                    <div class="step-text">
                        <strong>Escolha:</strong> A IA escolhe a jogada com o <strong>maior score</strong> do seu ponto de vista.
                    </div>
                </div>
            </div>

            <div class="explanation-note">
                <strong>Importante:</strong> Cada jogador (X e O) é maximizador da sua própria vitória.
                Quando X joga, +10 = X vence. Quando O joga, +10 = O vence.
            </div>
        </div>

        <h3 class="section-title">🎯 Histórico de Jogadas</h3>

        <div class="timeline">
            {moves_html}
        </div>

        <div class="info-section">
            <h3>📖 Resumo do Algoritmo</h3>
            <div class="info-grid">
                <div class="info-card">
                    <h4>🔄 Por que "Minimax"?</h4>
                    <p>O nome vem da alternância: nos níveis do jogador atual, escolhe o <strong>máximo</strong>;
                    nos níveis do oponente, escolhe o <strong>mínimo</strong> (simula o oponente jogando contra você).</p>
                </div>

                <div class="info-card">
                    <h4>⚡ Eficiência</h4>
                    <p>O Jogo da Velha tem ~362.880 estados máximos. A primeira jogada analisa ~549.000 estados,
                    mas as últimas analisam apenas dezenas (menos casas vazias = menos simulações).</p>
                </div>

                <div class="info-card">
                    <h4>🏆 Resultado</h4>
                    <p>Com duas IAs Minimax perfeitas, o jogo <strong>sempre termina em empate</strong>.
                    É matematicamente impossível vencer uma IA Minimax se você também jogar perfeitamente.</p>
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
