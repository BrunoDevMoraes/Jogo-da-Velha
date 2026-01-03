import webbrowser
import tempfile
import os
from typing import Dict, List, Optional
from visualization.node_collector import NodeCollector, TreeNode

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


POSITION_NAMES = {
    0: "Superior Esquerdo",
    1: "Superior Centro",
    2: "Superior Direito",
    3: "Centro Esquerdo",
    4: "Centro",
    5: "Centro Direito",
    6: "Inferior Esquerdo",
    7: "Inferior Centro",
    8: "Inferior Direito"
}

COLORS = {
    'max_node': '#3498db',
    'min_node': '#e74c3c',
    'terminal_win': '#27ae60',
    'terminal_lose': '#8e44ad',
    'terminal_tie': '#f39c12',
    'optimal_edge': '#2ecc71',
    'normal_edge': '#bdc3c7',
    'background': '#1a1a2e',
    'text': '#ffffff'
}


class TreeVisualizer:
    """Creates interactive visualizations of the Minimax search tree."""

    def __init__(self, collector: NodeCollector):
        """
        Initializes the visualizer with collected node data.

        Args:
            collector: NodeCollector with tree data.
        """
        self.collector = collector
        self.positions: Dict[int, tuple] = {}

    def _get_explanation(self, node: TreeNode) -> str:
        """
        Returns a didactic explanation for the node in Portuguese.

        Args:
            node: The tree node.

        Returns:
            Explanation text in Portuguese.
        """
        if node.depth == 0:
            return (
                "🎯 INÍCIO DA BUSCA!<br>"
                "A IA analisa todas as jogadas<br>"
                "possíveis para encontrar o<br>"
                "melhor movimento."
            )

        if node.node_type == 'TERMINAL':
            if node.terminal_type == 'WIN':
                return (
                    "🏆 VITÓRIA ENCONTRADA!<br>"
                    f"Score: {node.score}<br>"
                    "Quanto mais rápido ganhar,<br>"
                    "melhor o score!"
                )
            elif node.terminal_type == 'LOSE':
                return (
                    "❌ DERROTA ENCONTRADA!<br>"
                    f"Score: {node.score}<br>"
                    "Quanto mais demorar para<br>"
                    "perder, menor a penalidade."
                )
            else:
                return (
                    "🤝 EMPATE ENCONTRADO!<br>"
                    "Score: 0<br>"
                    "Nenhum jogador vence<br>"
                    "neste caminho."
                )

        if node.is_optimal_path:
            return (
                "⭐ CAMINHO ESCOLHIDO!<br>"
                f"Score: {node.score}<br>"
                "Este é o movimento ótimo<br>"
                "escolhido pela IA."
            )

        if node.node_type == 'MAX':
            return (
                "🔵 TURNO DA IA (MAX)<br>"
                f"Score: {node.score}<br>"
                "A IA quer MAXIMIZAR.<br>"
                "Escolhe o filho com<br>"
                "MAIOR valor."
            )
        else:
            return (
                "🔴 TURNO OPONENTE (MIN)<br>"
                f"Score: {node.score}<br>"
                "O oponente quer MINIMIZAR.<br>"
                "Escolhe o filho com<br>"
                "MENOR valor."
            )

    def _get_board_display(self, board: List[str]) -> str:
        """
        Creates a text representation of the board.

        Args:
            board: Board state as list.

        Returns:
            Formatted board string.
        """
        rows = []
        for i in range(0, 9, 3):
            row = f"{board[i]}│{board[i+1]}│{board[i+2]}"
            rows.append(row)
        return "<br>─┼─┼─<br>".join(rows)

    def _calculate_positions(self):
        """Calculates x,y positions for each node in a tree layout."""
        nodes = self.collector.get_nodes()
        if not nodes:
            return

        depth_nodes: Dict[int, List[TreeNode]] = {}
        for node in nodes:
            if node.depth not in depth_nodes:
                depth_nodes[node.depth] = []
            depth_nodes[node.depth].append(node)

        max_depth = max(depth_nodes.keys()) if depth_nodes else 0

        for depth, nodes_at_depth in depth_nodes.items():
            y = -depth * 1.5
            count = len(nodes_at_depth)
            width = max(count * 1.2, 2)

            for i, node in enumerate(nodes_at_depth):
                if count == 1:
                    x = 0
                else:
                    x = -width/2 + (i * width / (count - 1))
                self.positions[node.node_id] = (x, y)

    def _get_node_color(self, node: TreeNode) -> str:
        """
        Determines the color for a node.

        Args:
            node: The tree node.

        Returns:
            Hex color string.
        """
        if node.node_type == 'TERMINAL':
            if node.terminal_type == 'WIN':
                return COLORS['terminal_win']
            elif node.terminal_type == 'LOSE':
                return COLORS['terminal_lose']
            else:
                return COLORS['terminal_tie']

        if node.node_type == 'MAX':
            return COLORS['max_node']
        else:
            return COLORS['min_node']

    def generate_figure(self) -> Optional[go.Figure]:
        """
        Generates the Plotly figure for the tree.

        Returns:
            Plotly Figure object or None if Plotly not available.
        """
        if not PLOTLY_AVAILABLE:
            return None

        self._calculate_positions()
        nodes = self.collector.get_nodes()
        edges = self.collector.get_edges()

        if not nodes:
            return None

        edge_traces = []
        for parent_id, child_id in edges:
            if parent_id in self.positions and child_id in self.positions:
                x0, y0 = self.positions[parent_id]
                x1, y1 = self.positions[child_id]

                parent_node = nodes[parent_id]
                child_node = nodes[child_id]
                is_optimal = parent_node.is_optimal_path and child_node.is_optimal_path

                edge_traces.append(go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(
                        width=4 if is_optimal else 2,
                        color=COLORS['optimal_edge'] if is_optimal else COLORS['normal_edge']
                    ),
                    hoverinfo='none',
                    showlegend=False
                ))

        node_x = []
        node_y = []
        node_colors = []
        node_sizes = []
        node_symbols = []
        hover_texts = []

        for node in nodes:
            if node.node_id in self.positions:
                x, y = self.positions[node.node_id]
                node_x.append(x)
                node_y.append(y)
                node_colors.append(self._get_node_color(node))
                node_sizes.append(35 if node.is_optimal_path else 25)

                if node.node_type == 'MAX':
                    node_symbols.append('circle')
                elif node.node_type == 'MIN':
                    node_symbols.append('square')
                else:
                    node_symbols.append('diamond')

                move_text = ""
                if node.move is not None:
                    move_text = f"<br>Jogada: {POSITION_NAMES.get(node.move, node.move)}"

                board_display = self._get_board_display(node.board_state)
                explanation = self._get_explanation(node)

                hover_text = (
                    f"<b>{'MAX' if node.node_type == 'MAX' else 'MIN' if node.node_type == 'MIN' else 'TERMINAL'}</b>"
                    f"<br>Profundidade: {node.depth}"
                    f"{move_text}"
                    f"<br>Score: {node.score if node.score is not None else '?'}"
                    f"<br><br>{board_display}"
                    f"<br><br>{explanation}"
                )
                hover_texts.append(hover_text)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                symbol=node_symbols,
                line=dict(width=2, color='white')
            ),
            text=hover_texts,
            hoverinfo='text',
            hoverlabel=dict(
                bgcolor='rgba(0,0,0,0.8)',
                font=dict(size=12, family='Courier New'),
                align='left'
            ),
            showlegend=False
        )

        score_x = []
        score_y = []
        score_texts = []

        for node in nodes:
            if node.node_id in self.positions and node.score is not None:
                x, y = self.positions[node.node_id]
                score_x.append(x)
                score_y.append(y - 0.3)
                score_texts.append(str(node.score))

        score_trace = go.Scatter(
            x=score_x,
            y=score_y,
            mode='text',
            text=score_texts,
            textfont=dict(size=10, color='white'),
            hoverinfo='none',
            showlegend=False
        )

        fig = go.Figure(data=edge_traces + [node_trace, score_trace])

        stats = self.collector.get_statistics()

        fig.update_layout(
            title=dict(
                text=(
                    f"<b>🌳 Árvore de Busca Minimax</b><br>"
                    f"<sup>Nós avaliados: {stats['total_nodes']} | "
                    f"Profundidade máxima: {stats.get('max_depth', 0)} | "
                    f"Nós terminais: {stats.get('terminal_nodes', 0)}</sup>"
                ),
                font=dict(size=18, color='white'),
                x=0.5
            ),
            showlegend=False,
            hovermode='closest',
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            margin=dict(l=40, r=40, t=80, b=40),
            annotations=[
                dict(
                    text=(
                        "<b>Legenda:</b> "
                        "🔵 MAX (IA) | 🔴 MIN (Oponente) | "
                        "💎 Terminal | ━━ Caminho Ótimo"
                    ),
                    xref="paper", yref="paper",
                    x=0.5, y=-0.05,
                    showarrow=False,
                    font=dict(size=12, color='white'),
                    align='center'
                )
            ]
        )

        return fig

    def show(self):
        """Opens the visualization in the default web browser."""
        if not PLOTLY_AVAILABLE:
            print("Plotly nao esta instalado. Execute: pip install plotly")
            return

        fig = self.generate_figure()
        if fig is None:
            print("Nenhum dado para visualizar.")
            return

        stats = self.collector.get_statistics()

        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Visualizacao Minimax - Jogo da Velha</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats-container {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px 25px;
            text-align: center;
            color: white;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            font-size: 12px;
            color: #bdc3c7;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: white;
            font-size: 14px;
        }}
        .legend-circle {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
        }}
        .legend-square {{
            width: 16px;
            height: 16px;
        }}
        .legend-diamond {{
            width: 12px;
            height: 12px;
            transform: rotate(45deg);
        }}
        .info-panel {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            margin: 20px auto;
            max-width: 800px;
            color: white;
        }}
        .info-panel h3 {{
            margin-top: 0;
            color: #3498db;
        }}
        .info-panel ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .info-panel li {{
            margin: 8px 0;
            color: #ecf0f1;
        }}
        #plotly-chart {{
            background: rgba(255,255,255,0.02);
            border-radius: 10px;
            padding: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Arvore de Busca Minimax</h1>
        <p style="color: #bdc3c7; margin-top: 5px;">Passe o mouse sobre os nos para ver detalhes</p>
    </div>

    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">{stats['total_nodes']}</div>
            <div class="stat-label">Nos Avaliados</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{stats.get('max_depth', 0)}</div>
            <div class="stat-label">Profundidade Maxima</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{stats.get('terminal_nodes', 0)}</div>
            <div class="stat-label">Estados Terminais</div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-circle" style="background: #3498db;"></div>
            <span>MAX (IA maximiza)</span>
        </div>
        <div class="legend-item">
            <div class="legend-square" style="background: #e74c3c;"></div>
            <span>MIN (Oponente minimiza)</span>
        </div>
        <div class="legend-item">
            <div class="legend-diamond" style="background: #27ae60;"></div>
            <span>Vitoria</span>
        </div>
        <div class="legend-item">
            <div class="legend-diamond" style="background: #8e44ad;"></div>
            <span>Derrota</span>
        </div>
        <div class="legend-item">
            <div class="legend-diamond" style="background: #f39c12;"></div>
            <span>Empate</span>
        </div>
        <div class="legend-item">
            <div style="width: 30px; height: 4px; background: #2ecc71;"></div>
            <span>Caminho Otimo</span>
        </div>
    </div>

    <div id="plotly-chart"></div>

    <div class="info-panel">
        <h3>Como funciona o Minimax?</h3>
        <ul>
            <li><strong>MAX (Azul):</strong> A IA tenta MAXIMIZAR seu score. Ela escolhe o movimento que leva ao maior valor possivel.</li>
            <li><strong>MIN (Vermelho):</strong> O oponente tenta MINIMIZAR o score da IA. Ele escolhe o movimento que leva ao menor valor.</li>
            <li><strong>Score +10:</strong> Vitoria da IA (quanto menor a profundidade, melhor - vitoria rapida)</li>
            <li><strong>Score -10:</strong> Derrota da IA (quanto maior a profundidade, melhor - derrota lenta)</li>
            <li><strong>Score 0:</strong> Empate - nenhum jogador vence</li>
            <li><strong>Caminho Verde:</strong> O caminho otimo escolhido pela IA apos analisar todas as possibilidades</li>
        </ul>
    </div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        var figData = {fig.to_json()};
        Plotly.newPlot('plotly-chart', figData.data, figData.layout, {{responsive: true}});
    </script>
</body>
</html>
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            webbrowser.open('file://' + f.name)

    def save_html(self, filepath: str):
        """
        Saves the visualization as an HTML file.

        Args:
            filepath: Path to save the HTML file.
        """
        if not PLOTLY_AVAILABLE:
            print("Plotly não está instalado. Execute: pip install plotly")
            return

        fig = self.generate_figure()
        if fig is None:
            print("Nenhum dado para visualizar.")
            return

        fig.write_html(filepath, include_plotlyjs='cdn')
        print(f"Visualização salva em: {filepath}")
