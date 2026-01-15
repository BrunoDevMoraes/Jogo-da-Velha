import webbrowser
import tempfile
import json
from typing import List, Dict
from visualization.game_history import GameHistoryCollector, MoveAnalysis


POSITION_NAMES = {
    0: "Superior Esquerdo", 1: "Superior Centro", 2: "Superior Direito",
    3: "Centro Esquerdo", 4: "Centro", 5: "Centro Direito",
    6: "Inferior Esquerdo", 7: "Inferior Centro", 8: "Inferior Direito"
}

# Explicações detalhadas para cada algoritmo
ALGO_EXPLANATIONS = {
    "Minimax": {
        "title": "Minimax Clássico",
        "desc": "O algoritmo fundamental de teoria dos jogos que garante matematicamente o melhor resultado possível, explorando todas as jogadas até o fim.",
        "steps": [
            ("Força Bruta", "Analisa todas as ramificações possíveis da árvore de jogo."),
            ("Maximização", "O jogador da vez escolhe a opção com maior valor."),
            ("Minimização", "Assume que o oponente sempre fará a jogada que piora o seu resultado."),
            ("Garantia", "Impossível de vencer se executado perfeitamente (empate garantido).")
        ]
    },
    "Alpha-Beta": {
        "title": "Poda Alpha-Beta",
        "desc": "Uma versão otimizada do Minimax que corta (poda) ramos da árvore que não precisam ser explorados, mantendo a mesma precisão.",
        "steps": [
            ("Poda Alpha", "Interrompe a busca se encontrar um lance 'bom demais' que o oponente evitaria."),
            ("Poda Beta", "Interrompe se encontrar um lance pior do que uma alternativa já garantida."),
            ("Eficiência", "Avalia muito menos nós que o Minimax puro, chegando ao mesmo resultado."),
            ("Profundidade", "Permite calcular jogadas mais profundas no mesmo tempo.")
        ]
    },
    "Alpha-Beta + TT": {
        "title": "Alpha-Beta com Tabela de Transposição",
        "desc": "Usa uma memória cache para armazenar posições já analisadas, evitando recálculos desnecessários.",
        "steps": [
            ("Hash Zobrist", "Gera uma assinatura única para cada disposição do tabuleiro."),
            ("Cache (TT)", "Armazena o valor e a profundidade de posições já visitadas."),
            ("Reutilização", "Se o jogo chegar à mesma posição por outra ordem de jogadas, usa o valor salvo."),
            ("Velocidade", "Acelera drasticamente a busca, especialmente em finais de jogo.")
        ]
    },
    "Alpha-Beta + Simetria": {
        "title": "Alpha-Beta com Simetria Geométrica",
        "desc": "Reduz o espaço de busca explorando as simetrias geométricas do tabuleiro (rotações e reflexos).",
        "steps": [
            ("Forma Canônica", "Gira e reflete o tabuleiro para encontrar sua representação padrão."),
            ("Redução", "Trata posições rotacionadas como se fossem a mesma."),
            ("Otimização", "Reduz o número de posições únicas em até 8 vezes."),
            ("Lógica", "Entende que jogar no canto superior esquerdo é estrategicamente igual ao inferior direito.")
        ]
    }
}


class GameVisualizer:
    """Creates a clean visualization of the game history."""

    def __init__(self, history: GameHistoryCollector):
        self.history = history

    def _board_to_html(self, board: List[str], highlight: int = -1) -> str:
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

    def _get_algorithm_explanation(self, algo_name: str) -> str:
        """Gera o bloco HTML explicativo para o algoritmo."""
        # Tenta encontrar a explicação mais próxima
        info = ALGO_EXPLANATIONS.get(algo_name)
        if not info:
            for key in ALGO_EXPLANATIONS:
                if key in algo_name:
                    info = ALGO_EXPLANATIONS[key]
                    break
        
        # Fallback para Minimax se não encontrar
        if not info:
            info = ALGO_EXPLANATIONS["Minimax"]

        steps_html = ""
        for i, (title, text) in enumerate(info['steps'], 1):
            steps_html += f'''
                <div class="explanation-step">
                    <div class="step-number">{i}</div>
                    <div class="step-content">
                        <strong>{title}</strong>
                        <p>{text}</p>
                    </div>
                </div>
            '''

        return f'''
        <div class="algo-explanation">
            <div class="algo-header">
                <h3>🧠 Inteligência: {info['title']}</h3>
            </div>
            <p class="algo-desc">{info['desc']}</p>
            <div class="explanation-steps">
                {steps_html}
            </div>
        </div>
        '''

    def _get_move_analysis(self, move: MoveAnalysis) -> str:
        """Gera a análise textual detalhada da jogada com detecção de lances críticos."""
        opponent = 'O' if move.player == 'X' else 'X'
        
        # Preparar dados das alternativas
        sorted_alts = sorted(move.alternatives, key=lambda x: x['score'], reverse=True)
        best_score = sorted_alts[0]['score'] if sorted_alts else 0
        worst_score = sorted_alts[-1]['score'] if sorted_alts else 0
        
        # Contar quantos lances levam ao melhor resultado
        best_moves_count = len([a for a in sorted_alts if a['score'] == best_score])
        
        # Lógica de Diagnóstico
        outcome = ""
        detail = ""
        explanation = ""
        badge_class = ""

        if move.chosen_score > 0:
            outcome = "Vitória Garantida"
            badge_class = "win"
            detail = f"Vitória em {10 - move.chosen_score} lances (jogo perfeito)."
            explanation = f"A IA encontrou uma sequência forçada de mate. O oponente não pode evitar a derrota."
            
        elif move.chosen_score == 0:
            # Análise especial para Empates (Score 0)
            other_moves_are_losing = False
            if len(sorted_alts) > 1:
                # Se todas as outras jogadas (que não a escolhida) forem negativas (<0)
                other_moves = [a for a in sorted_alts if a['score'] < 0]
                if len(other_moves) == len(sorted_alts) - 1: # -1 é a jogada escolhida (0)
                    other_moves_are_losing = True

            if other_moves_are_losing:
                outcome = "🛡️ Bloqueio Crítico"
                badge_class = "critical" # Vamos adicionar estilo para isto
                detail = "Única jogada que evita a derrota."
                explanation = f"Esta foi a <strong>única casa</strong> segura. Qualquer outra jogada resultaria em vitória imediata ou forçada para {opponent}."
            else:
                outcome = "Empate Estável"
                badge_class = "tie"
                detail = "Nenhum jogador vence com jogo perfeito."
                if best_moves_count > 1:
                    explanation = f"Existem {best_moves_count} opções seguras nesta posição. A IA escolheu uma delas para manter o equilíbrio."
                else:
                    explanation = "A melhor opção disponível leva ao empate, bloqueando as tentativas de vitória do oponente."

        else:
            outcome = "Derrota Provável"
            badge_class = "lose"
            detail = f"Derrota em {10 + move.chosen_score} lances."
            explanation = f"A IA está em <em>zugzwang</em> (posição perdida). Escolheu a linha que resiste por mais tempo."

        # HTML Resultante
        return f'''
        <div class="analysis-box">
            <div class="analysis-header">
                <span class="analysis-title">Análise da Decisão</span>
                <span class="analysis-meta">🔍 {move.nodes_evaluated:,} nós em {move.time_ms:.1f}ms</span>
            </div>
            
            <div class="analysis-grid">
                <div class="analysis-item">
                    <span class="label">Diagnóstico</span>
                    <div class="outcome-wrapper">
                        <span class="badge {badge_class}">{outcome}</span>
                    </div>
                    <p class="detail">{detail}</p>
                </div>
                
                <div class="analysis-item">
                    <span class="label">Interpretação</span>
                    <p class="detail"><strong>Por que {POSITION_NAMES.get(move.chosen_position, move.chosen_position)}?</strong></p>
                    <p class="detail">{explanation}</p>
                </div>
            </div>
        </div>
        '''

    def _create_alternatives_board(self, move: MoveAnalysis) -> str:
        """Cria o visualizador de alternativas (tabuleiro de calor)."""
        if not move.alternatives: return ""
        
        score_map = {alt['position']: alt['score'] for alt in move.alternatives}
        sorted_alts = sorted(move.alternatives, key=lambda x: x['score'], reverse=True)
        best_score = sorted_alts[0]['score'] if sorted_alts else 0

        html = '<div class="alt-section"><span class="label">Mapa de Decisão (Heatmap)</span><div class="alt-board">'
        for i in range(9):
            if move.board_before[i] != ' ':
                # Célula ocupada
                cell_cls = f"alt-cell occupied p-{move.board_before[i].lower()}"
                html += f'<div class="{cell_cls}">{move.board_before[i]}</div>'
            else:
                score = score_map.get(i, -99)
                is_chosen = (i == move.chosen_position)
                is_best = (score == best_score)
                
                classes = "alt-cell empty"
                if is_chosen: classes += " chosen"
                if is_best: classes += " best"
                
                # Cor baseada no score
                if score > 0: classes += " score-win"
                elif score < 0: classes += " score-lose"
                else: classes += " score-tie"

                tooltip_text = "Vitória" if score > 0 else "Empate" if score == 0 else "Derrota"

                html += f'''
                <div class="{classes}">
                    <span class="score">{score}</span>
                    {f'<div class="marker">✓</div>' if is_chosen else ''}
                    <div class="tooltip">
                        <strong>Score: {score}</strong><br>
                        {tooltip_text}
                    </div>
                </div>'''
        html += '</div></div>'
        return html

    def show(self):
        """Gera e abre o relatório HTML."""
        if not self.history.has_moves():
            print("Sem dados para visualizar.")
            return

        moves = self.history.get_ai_moves()
        # Pega o algoritmo do primeiro movimento (assumindo consistência ou ator principal)
        main_algo = moves[0].algorithm if moves else "Minimax"
        explanation = self._get_algorithm_explanation(main_algo)
        
        moves_html = ""
        for move in moves:
            player_class = "p-x" if move.player == 'X' else "p-o"
            icon = "❌" if move.player == 'X' else "⭕"
            
            moves_html += f'''
            <div class="card {player_class}">
                <div class="card-header">
                    <div class="turn-info">
                        <span class="turn-badge">#{move.move_number}</span>
                        <span class="algo-badge">{move.algorithm}</span>
                    </div>
                    <div class="player-info">{icon} Jogador {move.player}</div>
                </div>
                
                <div class="card-body">
                    <div class="board-flow">
                        <div class="board-state">
                            <span class="state-label">Antes</span>
                            {self._board_to_html(move.board_before)}
                        </div>
                        <div class="flow-arrow">➜</div>
                        <div class="board-state">
                            <span class="state-label">Depois</span>
                            {self._board_to_html(move.board_after, move.chosen_position)}
                        </div>
                    </div>
                    
                    {self._get_move_analysis(move)}
                    {self._create_alternatives_board(move)}
                </div>
            </div>
            '''

        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório da Partida - {main_algo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0f172a; --card-bg: #1e293b; --text: #f1f5f9; --subtext: #94a3b8;
            --accent: #3b82f6; --accent-hover: #2563eb;
            --win: #22c55e; --lose: #ef4444; --tie: #f59e0b;
            --x-color: #38bdf8; --o-color: #f472b6;
        }}
        
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text);
            margin: 0; padding: 40px 20px; line-height: 1.6;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}

        /* Header */
        header {{ text-align: center; margin-bottom: 50px; }}
        h1 {{ 
            font-size: 2.5rem; margin: 0 0 10px 0; letter-spacing: -1px;
            background: linear-gradient(135deg, #60a5fa, #c084fc);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        
        /* Stats Dashboard */
        .stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px;
            background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
            padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 40px; text-align: center;
        }}
        .stat-val {{ font-size: 2rem; font-weight: 800; color: var(--text); display: block; line-height: 1; margin-bottom: 5px; }}
        .stat-lbl {{ font-size: 0.85rem; color: var(--subtext); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}

        /* Explanation Box */
        .algo-explanation {{
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155; border-radius: 20px; padding: 30px; margin-bottom: 50px;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        }}
        .algo-header h3 {{ margin: 0; font-size: 1.4rem; color: var(--accent); }}
        .algo-desc {{ color: var(--subtext); margin: 15px 0 25px 0; font-size: 1.05rem; }}
        
        .explanation-steps {{ display: grid; gap: 15px; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
        .explanation-step {{ 
            display: flex; gap: 15px; background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px;
        }}
        .step-number {{ 
            background: var(--accent); color: white; width: 28px; height: 28px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;
        }}
        .step-content strong {{ display: block; color: var(--text); margin-bottom: 4px; }}
        .step-content p {{ margin: 0; color: var(--subtext); font-size: 0.9rem; line-height: 1.4; }}

        /* Game Cards */
        .card {{
            background: var(--card-bg); border-radius: 20px; overflow: hidden; margin-bottom: 30px;
            border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .card.p-x {{ border-top: 5px solid var(--x-color); }}
        .card.p-o {{ border-top: 5px solid var(--o-color); }}
        
        .card-header {{
            padding: 15px 25px; background: rgba(0,0,0,0.2); display: flex;
            justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .turn-badge {{ font-weight: 700; color: var(--subtext); background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 8px; margin-right: 10px; }}
        .algo-badge {{ color: var(--accent); font-size: 0.9rem; font-weight: 600; }}
        .player-info {{ font-weight: 700; font-size: 1.1rem; }}
        .p-x .player-info {{ color: var(--x-color); }}
        .p-o .player-info {{ color: var(--o-color); }}

        .card-body {{ padding: 25px; }}

        /* Board Flow */
        .board-flow {{ display: flex; justify-content: center; align-items: center; gap: 40px; margin-bottom: 30px; }}
        .board-state {{ text-align: center; }}
        .state-label {{ display: block; font-size: 0.8rem; color: var(--subtext); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}
        .flow-arrow {{ font-size: 2rem; color: var(--subtext); opacity: 0.2; transform: translateY(10px); }}
        
        .mini-board {{ display: grid; grid-template-columns: repeat(3, 45px); gap: 6px; }}
        .cell {{
            width: 45px; height: 45px; background: #0f172a; border-radius: 8px;
            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.4rem;
        }}
        .cell-x {{ color: var(--x-color); }} 
        .cell-o {{ color: var(--o-color); }}
        .cell-highlight {{ background: rgba(34, 197, 94, 0.15); border: 2px solid var(--win); }}

        /* Analysis Box */
        .analysis-box {{ background: rgba(0,0,0,0.2); border-radius: 16px; padding: 20px; margin-bottom: 25px; }}
        .analysis-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .analysis-title {{ font-weight: 700; color: var(--accent); }}
        .analysis-meta {{ font-size: 0.85rem; color: var(--subtext); font-family: monospace; }}
        
        .analysis-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 600px) {{ .analysis-grid {{ grid-template-columns: 1fr; }} }}
        
        .label {{ display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--subtext); margin-bottom: 8px; letter-spacing: 0.5px; }}
        .detail {{ font-size: 0.95rem; color: var(--text); margin: 0; line-height: 1.5; }}
        
        .badge {{ padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; display: inline-block; }}
        .badge.win {{ background: rgba(34, 197, 94, 0.15); color: var(--win); }}
        .badge.tie {{ background: rgba(245, 158, 11, 0.15); color: var(--tie); }}
        .badge.lose {{ background: rgba(239, 68, 68, 0.15); color: var(--lose); }}
        .badge.critical {{ 
            background: rgba(139, 92, 246, 0.2); 
            color: #c4b5fd; 
            border: 1px solid #8b5cf6;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
        }}

        /* Alternatives Board */
        .alt-section {{ text-align: center; margin-top: 20px; }}
        .alt-board {{ display: inline-grid; grid-template-columns: repeat(3, 60px); gap: 8px; background: #0f172a; padding: 10px; border-radius: 12px; }}
        .alt-cell {{
            width: 60px; height: 60px; background: #1e293b; border-radius: 8px; position: relative;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            transition: transform 0.2s; cursor: default;
        }}
        .alt-cell:hover .tooltip {{ opacity: 1; visibility: visible; transform: translateY(0); }}
        
        .alt-cell.occupied {{ font-size: 1.5rem; font-weight: bold; color: #334155; }}
        .alt-cell.p-x {{ color: var(--x-color); opacity: 0.5; }}
        .alt-cell.p-o {{ color: var(--o-color); opacity: 0.5; }}

        .alt-cell.empty {{ font-weight: 700; font-size: 1.1rem; }}
        .score-win {{ color: var(--win); }}
        .score-tie {{ color: var(--tie); }}
        .score-lose {{ color: var(--lose); }}
        
        .alt-cell.chosen {{ border: 2px solid var(--accent); background: rgba(59, 130, 246, 0.1); }}
        .alt-cell.best:not(.chosen) {{ border: 2px dashed var(--win); opacity: 0.5; }}
        
        .marker {{ position: absolute; top: 2px; right: 4px; font-size: 0.7rem; color: var(--accent); }}
        
        .tooltip {{
            position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%) translateY(10px);
            background: #0f172a; border: 1px solid #334155; padding: 8px 12px; border-radius: 8px;
            font-size: 0.8rem; white-space: nowrap; pointer-events: none; opacity: 0; visibility: hidden;
            transition: all 0.2s ease; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Relatório da Partida</h1>
            <p style="color: var(--subtext);">Análise da Inteligência Artificial</p>
        </header>

        <div class="stats">
            <div><span class="stat-val">{len(moves)}</span><span class="stat-lbl">Jogadas</span></div>
            <div><span class="stat-val">{self.history.get_total_nodes():,}</span><span class="stat-lbl">Nós Analisados</span></div>
            <div><span class="stat-val">{self.history.get_total_time():.0f}ms</span><span class="stat-lbl">Tempo Total</span></div>
        </div>

        {explanation}

        <div class="timeline">
            <h3 style="color: var(--text); margin-bottom: 20px; font-size: 1.2rem;">Timeline de Decisões</h3>
            {moves_html}
        </div>
        
        <footer style="text-align: center; color: var(--subtext); margin-top: 60px; font-size: 0.8rem;">
            Gerado pelo Jogo da Velha IA
        </footer>
    </div>
</body>
</html>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            webbrowser.open('file://' + f.name)