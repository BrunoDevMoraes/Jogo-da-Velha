"""Tree visualization module with multiple visualization techniques for all algorithms."""

import webbrowser
import tempfile
import json
from typing import Dict, Any, Optional


class TreeVisualizer:
    """Visualizes game search trees using various techniques.

    Supports algorithm-specific visualizations:
    - Minimax: Basic tree structure
    - Alpha-Beta: Pruned branches highlighted
    - Alpha-Beta + TT: Transposition table hits highlighted
    - Alpha-Beta + Symmetry: Symmetric positions highlighted
    - NegaScout: Null-window and re-search nodes highlighted
    """

    def __init__(self, collector):
        """
        Initializes the visualizer.

        Args:
            collector: Any tree collector with built tree data.
        """
        self.collector = collector
        self.ai_symbol = collector.ai_symbol
        self.algorithm = self._detect_algorithm()

    def _detect_algorithm(self) -> str:
        """Detects which algorithm the collector represents."""
        stats = self.collector.get_statistics()
        return stats.get('algorithm', 'Minimax')

    def _open_in_browser(self, html_content: str):
        """Opens HTML content in the default browser."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as f:
            f.write(html_content)
            webbrowser.open('file://' + f.name)

    def show_collapsible_tree(self):
        """Shows the tree as a collapsible D3.js tree."""
        if not self.collector.root:
            print("No tree data available.")
            return

        tree_data = self.collector.root.to_dict()
        stats = self.collector.get_statistics()
        html = self._generate_collapsible_tree_html(tree_data, stats)
        self._open_in_browser(html)

    def show_sunburst(self):
        """Shows the tree as a sunburst chart."""
        if not self.collector.root:
            print("No tree data available.")
            return

        tree_data = self.collector.root.to_dict()
        stats = self.collector.get_statistics()
        html = self._generate_sunburst_html(tree_data, stats)
        self._open_in_browser(html)

    def show_treemap(self):
        """Shows the tree as a treemap."""
        if not self.collector.root:
            print("No tree data available.")
            return

        tree_data = self.collector.root.to_dict()
        stats = self.collector.get_statistics()
        html = self._generate_treemap_html(tree_data, stats)
        self._open_in_browser(html)

    def _get_algorithm_stats_html(self, stats: Dict) -> str:
        """Generates algorithm-specific statistics HTML."""
        base_stats = f'''
            <div class="stat">
                <div class="stat-value">{stats.get('total_nodes', 0):,}</div>
                <div class="stat-label">Total de Nos</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('leaf_nodes', 0):,}</div>
                <div class="stat-label">Folhas</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('max_depth', 0)}</div>
                <div class="stat-label">Profundidade</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('root_score', 0)}</div>
                <div class="stat-label">Score Raiz</div>
            </div>
        '''

        # Algorithm-specific stats
        if 'nodes_pruned' in stats:
            base_stats += f'''
            <div class="stat">
                <div class="stat-value" style="color: #e74c3c;">{stats['nodes_pruned']:,}</div>
                <div class="stat-label">Nos Podados</div>
            </div>
            '''

        if 'tt_hits' in stats:
            base_stats += f'''
            <div class="stat">
                <div class="stat-value" style="color: #f1c40f;">{stats['tt_hits']:,}</div>
                <div class="stat-label">TT Hits</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #f1c40f;">{stats.get('tt_hit_rate', 0)}%</div>
                <div class="stat-label">Taxa TT</div>
            </div>
            '''

        if 'symmetry_hits' in stats:
            base_stats += f'''
            <div class="stat">
                <div class="stat-value" style="color: #9b59b6;">{stats['symmetry_hits']:,}</div>
                <div class="stat-label">Simetrias</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #9b59b6;">{stats.get('unique_positions', 0):,}</div>
                <div class="stat-label">Pos. Unicas</div>
            </div>
            '''

        if 'null_window_searches' in stats:
            base_stats += f'''
            <div class="stat">
                <div class="stat-value" style="color: #e67e22;">{stats['null_window_searches']:,}</div>
                <div class="stat-label">Null-Window</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #3498db;">{stats.get('re_searches', 0):,}</div>
                <div class="stat-label">Re-Searches</div>
            </div>
            '''

        return base_stats

    def _get_algorithm_legend_html(self) -> str:
        """Generates algorithm-specific legend HTML."""
        ai_symbol = self.ai_symbol
        opponent = 'O' if ai_symbol == 'X' else 'X'

        base_legend = f'''
        <div class="legend-item"><div class="legend-color" style="background: #3498db;"></div><span>MAX ({ai_symbol})</span></div>
        <div class="legend-item"><div class="legend-color" style="background: #9b59b6;"></div><span>MIN ({opponent})</span></div>
        <div class="legend-item"><div class="legend-color" style="background: #2ecc71;"></div><span>{ai_symbol} Vence</span></div>
        <div class="legend-item"><div class="legend-color" style="background: #f39c12;"></div><span>Empate</span></div>
        <div class="legend-item"><div class="legend-color" style="background: #e74c3c;"></div><span>{ai_symbol} Perde</span></div>
        '''

        # Algorithm-specific legend items
        if 'Alpha-Beta' in self.algorithm:
            base_legend += '''
            <div class="legend-item"><div class="legend-color" style="background: #c0392b; border: 2px dashed #fff;"></div><span>Podado</span></div>
            '''

        if 'TT' in self.algorithm:
            base_legend += '''
            <div class="legend-item"><div class="legend-color" style="background: #f1c40f;"></div><span>TT Hit</span></div>
            '''

        if 'Symmetry' in self.algorithm:
            base_legend += '''
            <div class="legend-item"><div class="legend-color" style="background: #8e44ad;"></div><span>Simetria</span></div>
            '''

        if 'NegaScout' in self.algorithm:
            base_legend += '''
            <div class="legend-item"><div class="legend-color" style="background: #e67e22;"></div><span>Null-Window</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #2980b9;"></div><span>Re-Search</span></div>
            '''

        return base_legend

    def _generate_collapsible_tree_html(self, tree_data: Dict, stats: Dict) -> str:
        """Generates HTML for collapsible tree visualization with algorithm-specific styling."""
        tree_json = json.dumps(tree_data)
        ai_symbol = self.ai_symbol
        opponent = 'O' if ai_symbol == 'X' else 'X'
        algorithm = self.algorithm
        stats_html = self._get_algorithm_stats_html(stats)
        legend_html = self._get_algorithm_legend_html()

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Arvore {algorithm}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
        }}
        .header {{
            padding: 20px;
            text-align: center;
            background: rgba(0,0,0,0.3);
        }}
        .header h1 {{ font-size: 1.8em; margin-bottom: 10px; }}
        .algorithm-badge {{
            display: inline-block;
            padding: 5px 15px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            border-radius: 20px;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        .stat {{ text-align: center; min-width: 80px; }}
        .stat-value {{ font-size: 1.3em; font-weight: bold; color: #3498db; }}
        .stat-label {{ font-size: 0.8em; color: #95a5a6; }}
        .controls {{
            padding: 15px;
            background: rgba(0,0,0,0.2);
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .controls button {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
        }}
        .btn-expand {{ background: #2ecc71; color: white; }}
        .btn-collapse {{ background: #e74c3c; color: white; }}
        .btn-reset {{ background: #3498db; color: white; }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            font-size: 0.8em;
            flex-wrap: wrap;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 15px; height: 15px; border-radius: 3px; }}
        #tree-container {{ width: 100%; height: calc(100vh - 250px); overflow: hidden; }}
        .node circle {{ cursor: pointer; stroke-width: 2px; }}
        .node text {{ font-size: 10px; fill: white; }}
        .link {{ fill: none; stroke: #555; stroke-width: 1.5px; }}
        .link-pruned {{ stroke: #e74c3c; stroke-dasharray: 5,5; }}
        .tooltip {{
            position: absolute;
            background: #1a1a2e;
            border: 1px solid #3498db;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            z-index: 1000;
            max-width: 300px;
        }}
        .score-positive {{ color: #2ecc71; }}
        .score-negative {{ color: #e74c3c; }}
        .score-neutral {{ color: #f39c12; }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 5px;
        }}
        .badge-pruned {{ background: #e74c3c; }}
        .badge-tt {{ background: #f1c40f; color: #000; }}
        .badge-symmetry {{ background: #9b59b6; }}
        .badge-null {{ background: #e67e22; }}
        .badge-research {{ background: #3498db; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="algorithm-badge">{algorithm}</div>
        <h1>Arvore de Busca - Visualizacao Colapsavel</h1>
        <p>Clique nos nos para expandir/colapsar. Arraste para mover. Scroll para zoom.</p>
        <div class="stats">
            {stats_html}
        </div>
    </div>
    <div class="controls">
        <button class="btn-expand" onclick="expandAll()">Expandir Tudo</button>
        <button class="btn-collapse" onclick="collapseAll()">Colapsar Tudo</button>
        <button class="btn-reset" onclick="resetView()">Resetar Visao</button>
    </div>
    <div class="legend">
        {legend_html}
    </div>
    <div id="tree-container"></div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const treeData = {tree_json};
        const aiSymbol = '{ai_symbol}';
        const algorithm = '{algorithm}';
        const container = document.getElementById('tree-container');
        const width = container.clientWidth;
        const height = container.clientHeight;
        const svg = d3.select('#tree-container').append('svg').attr('width', width).attr('height', height);
        const g = svg.append('g').attr('transform', `translate(${{width/2}}, 50)`);
        const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (e) => g.attr('transform', e.transform));
        svg.call(zoom);
        const tree = d3.tree().nodeSize([25, 80]);
        const tooltip = d3.select('#tooltip');

        function transformData(data) {{ return {{ data: data, children: data.children ? data.children.map(c => transformData(c)) : null }}; }}
        let root = d3.hierarchy(transformData(treeData), d => d.children);
        root.x0 = 0; root.y0 = 0;
        root.descendants().forEach((d) => {{ if (d.depth > 2) {{ d._children = d.children; d.children = null; }} }});

        function getNodeColor(d) {{
            const data = d.data.data;

            // Algorithm-specific coloring
            if (data.tt_hit) return '#f1c40f';  // TT hit - yellow
            if (data.is_symmetric_duplicate) return '#8e44ad';  // Symmetry - purple
            if (data.is_null_window_search && !data.was_re_searched) return '#e67e22';  // Null-window - orange
            if (data.was_re_searched) return '#2980b9';  // Re-search - blue

            // Terminal state coloring
            if (data.is_terminal) {{
                if (data.result === 'WIN_' + aiSymbol) return '#2ecc71';
                if (data.result === 'TIE') return '#f39c12';
                return '#e74c3c';
            }}

            return data.is_max ? '#3498db' : '#9b59b6';
        }}

        function getNodeStroke(d) {{
            const data = d.data.data;
            if (data.pruned_children_count > 0) return '#e74c3c';  // Has pruned children
            const score = data.score || 0;
            if (score > 0) return '#2ecc71';
            if (score < 0) return '#e74c3c';
            return '#f39c12';
        }}

        function getNodeRadius(d) {{
            const data = d.data.data;
            if (data.tt_hit || data.is_symmetric_duplicate) return 10;
            if (data.was_re_searched) return 10;
            return 8;
        }}

        function boardToString(board) {{
            let str = '';
            for (let i = 0; i < 9; i++) {{
                str += board[i] === ' ' ? '.' : board[i];
                if (i % 3 === 2 && i < 8) str += '\\n';
            }}
            return str;
        }}

        function getTooltipContent(d) {{
            const data = d.data.data;
            const scoreClass = data.score > 0 ? 'score-positive' : data.score < 0 ? 'score-negative' : 'score-neutral';
            let resultText = data.is_terminal ? (data.result === 'WIN_X' ? 'X venceu!' : data.result === 'WIN_O' ? 'O venceu!' : 'Empate!') : '';
            const moveName = data.move !== null ? ['TL','TC','TR','ML','MC','MR','BL','BC','BR'][data.move] : 'Raiz';

            let badges = '';
            if (data.pruned_children_count > 0) badges += `<span class="badge badge-pruned">${{data.pruned_children_count}} podados</span>`;
            if (data.tt_hit) badges += `<span class="badge badge-tt">TT Hit (${{data.tt_flag}})</span>`;
            if (data.is_symmetric_duplicate) badges += '<span class="badge badge-symmetry">Simetria</span>';
            if (data.is_null_window_search) badges += '<span class="badge badge-null">Null-Window</span>';
            if (data.was_re_searched) badges += '<span class="badge badge-research">Re-Search</span>';

            let extraInfo = '';
            if (data.alpha !== null && data.alpha !== undefined) {{
                extraInfo += `<div><strong>Alpha:</strong> ${{data.alpha === -Infinity ? '-inf' : data.alpha}}</div>`;
                extraInfo += `<div><strong>Beta:</strong> ${{data.beta === Infinity ? '+inf' : data.beta}}</div>`;
            }}
            if (data.null_window_score !== null && data.null_window_score !== undefined) {{
                extraInfo += `<div><strong>Null-Window Score:</strong> ${{data.null_window_score}}</div>`;
            }}

            return `<div><strong>Profundidade:</strong> ${{data.depth}} ${{badges}}</div>
                <div><strong>Jogador:</strong> ${{data.player}} (${{data.is_max ? 'MAX' : 'MIN'}})</div>
                <div><strong>Movimento:</strong> ${{moveName}}</div>
                <div class="${{scoreClass}}"><strong>Score:</strong> ${{data.score}}</div>
                ${{resultText ? '<div><strong>Resultado:</strong> ' + resultText + '</div>' : ''}}
                ${{extraInfo}}
                <div><strong>Filhos:</strong> ${{(d.children || d._children || []).length}}</div>
                <pre style="margin-top:8px">${{boardToString(data.board)}}</pre>`;
        }}

        function update(source) {{
            const treeData = tree(root);
            const nodes = treeData.descendants();
            const links = treeData.links();
            nodes.forEach(d => d.y = d.depth * 100);

            const node = g.selectAll('.node').data(nodes, d => d.data.data.board.join(''));
            const nodeEnter = node.enter().append('g').attr('class', 'node')
                .attr('transform', d => `translate(${{source.x0 || 0}}, ${{source.y0 || 0}})`)
                .on('click', (e, d) => {{
                    if (d.children) {{ d._children = d.children; d.children = null; }}
                    else if (d._children) {{ d.children = d._children; d._children = null; }}
                    update(d);
                }})
                .on('mouseover', (e, d) => {{
                    tooltip.html(getTooltipContent(d))
                    .style('opacity', 1).style('left', (e.pageX + 15) + 'px').style('top', (e.pageY - 10) + 'px');
                }})
                .on('mouseout', () => tooltip.style('opacity', 0));

            nodeEnter.append('circle')
                .attr('r', d => getNodeRadius(d))
                .attr('fill', d => getNodeColor(d))
                .attr('stroke', d => getNodeStroke(d))
                .attr('stroke-dasharray', d => d.data.data.pruned_children_count > 0 ? '3,3' : 'none');
            nodeEnter.append('text').attr('dy', 3).attr('text-anchor', 'middle')
                .text(d => {{ const data = d.data.data; if (d._children) return '+'; if (!d.children && !d._children) return data.score; return ''; }});

            const nodeUpdate = nodeEnter.merge(node);
            nodeUpdate.transition().duration(300).attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
            nodeUpdate.select('circle').attr('fill', d => getNodeColor(d)).attr('r', d => getNodeRadius(d));
            nodeUpdate.select('text').text(d => {{ const data = d.data.data; if (d._children) return '+'; if (!d.children && !d._children) return data.score; return ''; }});
            node.exit().transition().duration(300).attr('transform', d => `translate(${{source.x}}, ${{source.y}})`).remove();

            const link = g.selectAll('.link').data(links, d => d.target.data.data.board.join(''));
            const linkEnter = link.enter().insert('path', 'g').attr('class', d => {{
                return 'link' + (d.target.data.data.was_pruned ? ' link-pruned' : '');
            }}).attr('d', d => {{ const o = {{x: source.x0 || 0, y: source.y0 || 0}}; return diagonal(o, o); }});
            linkEnter.merge(link).transition().duration(300).attr('d', d => diagonal(d.source, d.target));
            link.exit().transition().duration(300).attr('d', d => {{ const o = {{x: source.x, y: source.y}}; return diagonal(o, o); }}).remove();
            nodes.forEach(d => {{ d.x0 = d.x; d.y0 = d.y; }});
        }}

        function diagonal(s, d) {{ return `M${{s.x}},${{s.y}}C${{s.x}},${{(s.y + d.y) / 2}} ${{d.x}},${{(s.y + d.y) / 2}} ${{d.x}},${{d.y}}`; }}
        function expandAll() {{ root.descendants().forEach(d => {{ if (d._children) {{ d.children = d._children; d._children = null; }} }}); update(root); }}
        function collapseAll() {{ root.descendants().forEach(d => {{ if (d.children && d.depth > 0) {{ d._children = d.children; d.children = null; }} }}); update(root); }}
        function resetView() {{ svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity.translate(width/2, 50)); }}

        update(root);
        resetView();
    </script>
</body>
</html>'''

    def _generate_sunburst_html(self, tree_data: Dict, stats: Dict) -> str:
        """Generates HTML for sunburst visualization with algorithm-specific styling."""
        tree_json = json.dumps(tree_data)
        ai_symbol = self.ai_symbol
        opponent = 'O' if ai_symbol == 'X' else 'X'
        algorithm = self.algorithm
        stats_html = self._get_algorithm_stats_html(stats)
        legend_html = self._get_algorithm_legend_html()

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Arvore {algorithm} - Sunburst</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            padding: 20px;
            text-align: center;
            background: rgba(0,0,0,0.3);
        }}
        .header h1 {{ font-size: 1.8em; margin-bottom: 10px; }}
        .algorithm-badge {{
            display: inline-block;
            padding: 5px 15px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            border-radius: 20px;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 15px; flex-wrap: wrap; }}
        .stat {{ text-align: center; min-width: 80px; }}
        .stat-value {{ font-size: 1.3em; font-weight: bold; color: #3498db; }}
        .stat-label {{ font-size: 0.8em; color: #95a5a6; }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            font-size: 0.8em;
            flex-wrap: wrap;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 15px; height: 15px; border-radius: 3px; }}
        .breadcrumb {{ text-align: center; padding: 10px; background: rgba(0,0,0,0.2); font-size: 0.9em; }}
        .container {{ flex: 1; display: flex; justify-content: center; align-items: center; padding: 20px; }}
        #sunburst-container {{ position: relative; }}
        .tooltip {{
            position: absolute;
            background: #1a1a2e;
            border: 1px solid #3498db;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            z-index: 1000;
        }}
        .center-label {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            pointer-events: none;
        }}
        .center-label .depth {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .center-label .label {{ font-size: 0.9em; color: #95a5a6; }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 5px;
        }}
        .badge-pruned {{ background: #e74c3c; }}
        .badge-tt {{ background: #f1c40f; color: #000; }}
        .badge-symmetry {{ background: #9b59b6; }}
        .badge-null {{ background: #e67e22; }}
        .badge-research {{ background: #3498db; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="algorithm-badge">{algorithm}</div>
        <h1>Arvore de Busca - Sunburst</h1>
        <p>Cada anel = um nivel. Clique para zoom. Centro = raiz.</p>
        <div class="stats">
            {stats_html}
        </div>
    </div>
    <div class="legend">
        {legend_html}
    </div>
    <div class="breadcrumb" id="breadcrumb">Raiz</div>
    <div class="container">
        <div id="sunburst-container">
            <div class="center-label">
                <div class="depth" id="center-depth">0</div>
                <div class="label">Profundidade</div>
            </div>
        </div>
    </div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const treeData = {tree_json};
        const aiSymbol = '{ai_symbol}';
        const width = Math.min(window.innerWidth - 40, 700);
        const height = width;
        const radius = width / 2;

        const svg = d3.select('#sunburst-container').append('svg').attr('width', width).attr('height', height)
            .append('g').attr('transform', `translate(${{width/2}}, ${{height/2}})`);
        const tooltip = d3.select('#tooltip');

        function transformForHierarchy(data) {{
            return {{ ...data, value: data.children && data.children.length > 0 ? undefined : 1,
                children: data.children ? data.children.map(transformForHierarchy) : undefined }};
        }}

        const root = d3.hierarchy(transformForHierarchy(treeData)).sum(d => d.value || 0).sort((a, b) => (b.value || 0) - (a.value || 0));
        const partition = d3.partition().size([2 * Math.PI, radius]);
        partition(root);

        const arc = d3.arc().startAngle(d => d.x0).endAngle(d => d.x1).innerRadius(d => d.y0).outerRadius(d => d.y1 - 1);

        function getColor(d) {{
            const data = d.data;
            if (data.tt_hit) return '#f1c40f';
            if (data.is_symmetric_duplicate) return '#8e44ad';
            if (data.is_null_window_search && !data.was_re_searched) return '#e67e22';
            if (data.was_re_searched) return '#2980b9';
            if (data.is_terminal) {{
                if (data.result === 'WIN_' + aiSymbol) return '#2ecc71';
                if (data.result === 'TIE') return '#f39c12';
                return '#e74c3c';
            }}
            return data.is_max ? '#3498db' : '#9b59b6';
        }}

        function boardToString(board) {{
            let str = '';
            for (let i = 0; i < 9; i++) {{ str += board[i] === ' ' ? '.' : board[i]; if (i % 3 === 2 && i < 8) str += '\\n'; }}
            return str;
        }}

        function getTooltipContent(d) {{
            const data = d.data;
            const scoreStyle = data.score > 0 ? 'color:#2ecc71' : data.score < 0 ? 'color:#e74c3c' : 'color:#f39c12';
            let resultText = data.is_terminal ? (data.result === 'WIN_X' ? 'X venceu!' : data.result === 'WIN_O' ? 'O venceu!' : 'Empate!') : '';
            const moveName = data.move !== null ? ['TL','TC','TR','ML','MC','MR','BL','BC','BR'][data.move] : 'Raiz';

            let badges = '';
            if (data.pruned_children_count > 0) badges += `<span class="badge badge-pruned">${{data.pruned_children_count}} podados</span>`;
            if (data.tt_hit) badges += `<span class="badge badge-tt">TT Hit</span>`;
            if (data.is_symmetric_duplicate) badges += '<span class="badge badge-symmetry">Simetria</span>';
            if (data.is_null_window_search) badges += '<span class="badge badge-null">Null-Window</span>';
            if (data.was_re_searched) badges += '<span class="badge badge-research">Re-Search</span>';

            return `<div><strong>Profundidade:</strong> ${{d.depth}} ${{badges}}</div>
                <div><strong>Jogador:</strong> ${{data.player}} (${{data.is_max ? 'MAX' : 'MIN'}})</div>
                <div><strong>Movimento:</strong> ${{moveName}}</div>
                <div style="${{scoreStyle}}"><strong>Score:</strong> ${{data.score}}</div>
                ${{resultText ? '<div><strong>Resultado:</strong> ' + resultText + '</div>' : ''}}
                <pre style="margin-top:8px">${{boardToString(data.board)}}</pre>`;
        }}

        const paths = svg.selectAll('path').data(root.descendants().filter(d => d.depth > 0)).enter().append('path')
            .attr('d', arc).attr('fill', d => getColor(d)).attr('stroke', '#1a1a2e').attr('stroke-width', 0.5)
            .style('cursor', 'pointer').style('opacity', 0.85)
            .on('mouseover', function(e, d) {{
                d3.select(this).style('opacity', 1);
                tooltip.html(getTooltipContent(d))
                .style('opacity', 1).style('left', (e.pageX + 15) + 'px').style('top', (e.pageY - 10) + 'px');
            }})
            .on('mouseout', function() {{ d3.select(this).style('opacity', 0.85); tooltip.style('opacity', 0); }})
            .on('click', clicked);

        svg.append('circle').attr('r', root.y1 - root.y0).attr('fill', '#1a1a2e').attr('stroke', '#3498db')
            .attr('stroke-width', 2).style('cursor', 'pointer').on('click', () => clicked(null, root));

        function clicked(e, p) {{
            if (!p) p = root;
            document.getElementById('center-depth').textContent = p.depth;
            const ancestors = p.ancestors().reverse();
            document.getElementById('breadcrumb').textContent = ancestors.map((d, i) =>
                i === 0 ? 'Raiz' : (['TL','TC','TR','ML','MC','MR','BL','BC','BR'][d.data.move] || '?')).join(' > ');

            root.each(d => {{
                d.target = {{
                    x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
                    x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
                    y0: Math.max(0, d.y0 - p.y0),
                    y1: Math.max(0, d.y1 - p.y0)
                }};
            }});

            const t = svg.transition().duration(750);
            paths.transition(t).tween('data', d => {{ const i = d3.interpolate(d.current || d, d.target); return t => d.current = i(t); }})
                .attrTween('d', d => () => arc(d.current));
        }}

        root.each(d => d.current = d);
    </script>
</body>
</html>'''

    def _generate_treemap_html(self, tree_data: Dict, stats: Dict) -> str:
        """Generates HTML for treemap visualization with algorithm-specific styling."""
        tree_json = json.dumps(tree_data)
        ai_symbol = self.ai_symbol
        opponent = 'O' if ai_symbol == 'X' else 'X'
        algorithm = self.algorithm
        stats_html = self._get_algorithm_stats_html(stats)
        legend_html = self._get_algorithm_legend_html()

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Arvore {algorithm} - Treemap</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
        }}
        .header {{
            padding: 20px;
            text-align: center;
            background: rgba(0,0,0,0.3);
        }}
        .header h1 {{ font-size: 1.8em; margin-bottom: 10px; }}
        .algorithm-badge {{
            display: inline-block;
            padding: 5px 15px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            border-radius: 20px;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 15px; flex-wrap: wrap; }}
        .stat {{ text-align: center; min-width: 80px; }}
        .stat-value {{ font-size: 1.3em; font-weight: bold; color: #3498db; }}
        .stat-label {{ font-size: 0.8em; color: #95a5a6; }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            font-size: 0.8em;
            flex-wrap: wrap;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 15px; height: 15px; border-radius: 3px; }}
        .breadcrumb {{
            text-align: center;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            font-size: 0.9em;
        }}
        .breadcrumb span {{ cursor: pointer; color: #3498db; }}
        .breadcrumb span:hover {{ text-decoration: underline; }}
        #treemap-container {{
            width: 100%;
            height: calc(100vh - 280px);
            padding: 10px;
            position: relative;
        }}
        .cell {{
            position: absolute;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
            cursor: pointer;
            transition: border-color 0.2s;
        }}
        .cell:hover {{ border-color: white; z-index: 10; }}
        .cell-label {{
            padding: 4px;
            font-size: 10px;
            color: white;
            text-shadow: 0 0 3px black;
        }}
        .tooltip {{
            position: absolute;
            background: #1a1a2e;
            border: 1px solid #3498db;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            z-index: 1000;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 5px;
        }}
        .badge-pruned {{ background: #e74c3c; }}
        .badge-tt {{ background: #f1c40f; color: #000; }}
        .badge-symmetry {{ background: #9b59b6; }}
        .badge-null {{ background: #e67e22; }}
        .badge-research {{ background: #3498db; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="algorithm-badge">{algorithm}</div>
        <h1>Arvore de Busca - Treemap</h1>
        <p>Tamanho = numero de sub-nos. Clique para navegar.</p>
        <div class="stats">
            {stats_html}
        </div>
    </div>
    <div class="legend">
        {legend_html}
    </div>
    <div class="breadcrumb" id="breadcrumb"><span onclick="zoomTo(root)">Raiz</span></div>
    <div id="treemap-container"></div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const treeData = {tree_json};
        const aiSymbol = '{ai_symbol}';
        const container = document.getElementById('treemap-container');
        const width = container.clientWidth;
        const height = container.clientHeight;
        const tooltip = d3.select('#tooltip');

        function transformForHierarchy(data) {{
            return {{ ...data, value: data.children && data.children.length > 0 ? undefined : 1,
                children: data.children ? data.children.map(transformForHierarchy) : undefined }};
        }}

        const root = d3.hierarchy(transformForHierarchy(treeData)).sum(d => d.value || 0).sort((a, b) => (b.value || 0) - (a.value || 0));
        const treemap = d3.treemap().size([width, height]).paddingOuter(3).paddingTop(19).paddingInner(1).round(true);
        treemap(root);

        function getColor(d) {{
            const data = d.data;
            if (data.tt_hit) return '#f1c40f';
            if (data.is_symmetric_duplicate) return '#8e44ad';
            if (data.is_null_window_search && !data.was_re_searched) return '#e67e22';
            if (data.was_re_searched) return '#2980b9';
            if (data.is_terminal) {{
                if (data.result === 'WIN_' + aiSymbol) return '#2ecc71';
                if (data.result === 'TIE') return '#f39c12';
                return '#e74c3c';
            }}
            return data.is_max ? '#3498db' : '#9b59b6';
        }}

        function boardToString(board) {{
            let str = '';
            for (let i = 0; i < 9; i++) {{ str += board[i] === ' ' ? '.' : board[i]; if (i % 3 === 2 && i < 8) str += '\\n'; }}
            return str;
        }}

        function getTooltipContent(d) {{
            const data = d.data;
            const scoreStyle = data.score > 0 ? 'color:#2ecc71' : data.score < 0 ? 'color:#e74c3c' : 'color:#f39c12';
            let resultText = data.is_terminal ? (data.result === 'WIN_X' ? 'X venceu!' : data.result === 'WIN_O' ? 'O venceu!' : 'Empate!') : '';
            const moveName = data.move !== null ? ['TL','TC','TR','ML','MC','MR','BL','BC','BR'][data.move] : 'Raiz';

            let badges = '';
            if (data.pruned_children_count > 0) badges += `<span class="badge badge-pruned">${{data.pruned_children_count}} podados</span>`;
            if (data.tt_hit) badges += `<span class="badge badge-tt">TT Hit</span>`;
            if (data.is_symmetric_duplicate) badges += '<span class="badge badge-symmetry">Simetria</span>';
            if (data.is_null_window_search) badges += '<span class="badge badge-null">Null-Window</span>';
            if (data.was_re_searched) badges += '<span class="badge badge-research">Re-Search</span>';

            return `<div><strong>Profundidade:</strong> ${{d.depth}} ${{badges}}</div>
                <div><strong>Jogador:</strong> ${{data.player}} (${{data.is_max ? 'MAX' : 'MIN'}})</div>
                <div><strong>Movimento:</strong> ${{moveName}}</div>
                <div style="${{scoreStyle}}"><strong>Score:</strong> ${{data.score}}</div>
                ${{resultText ? '<div><strong>Resultado:</strong> ' + resultText + '</div>' : ''}}
                <div><strong>Sub-nos:</strong> ${{d.value}}</div>
                <pre style="margin-top:8px">${{boardToString(data.board)}}</pre>`;
        }}

        let currentRoot = root;
        const nodeMap = new Map();
        root.descendants().forEach(d => nodeMap.set(d.data.board.join(''), d));

        function render(focus) {{
            container.innerHTML = '';
            const nodes = focus.descendants().filter(d => d.depth <= focus.depth + 2);

            nodes.forEach(d => {{
                const div = document.createElement('div');
                div.className = 'cell';
                const fx0 = focus.x0, fx1 = focus.x1, fy0 = focus.y0, fy1 = focus.y1;
                div.style.left = (d.x0 - fx0) / (fx1 - fx0) * width + 'px';
                div.style.top = (d.y0 - fy0) / (fy1 - fy0) * height + 'px';
                div.style.width = (d.x1 - d.x0) / (fx1 - fx0) * width + 'px';
                div.style.height = (d.y1 - d.y0) / (fy1 - fy0) * height + 'px';
                div.style.background = getColor(d);

                const cellW = (d.x1 - d.x0) / (fx1 - fx0) * width;
                const cellH = (d.y1 - d.y0) / (fy1 - fy0) * height;
                if (cellW > 30 && cellH > 20) {{
                    const label = document.createElement('div');
                    label.className = 'cell-label';
                    const moveName = d.data.move !== null ? ['TL','TC','TR','ML','MC','MR','BL','BC','BR'][d.data.move] : 'R';
                    label.textContent = moveName + ' (' + d.data.score + ')';
                    div.appendChild(label);
                }}

                div.addEventListener('click', (e) => {{ e.stopPropagation(); if (d.children) zoomTo(d); }});
                div.addEventListener('mouseover', (e) => {{
                    tooltip.html(getTooltipContent(d))
                    .style('opacity', 1).style('left', (e.pageX + 15) + 'px').style('top', (e.pageY - 10) + 'px');
                }});
                div.addEventListener('mouseout', () => tooltip.style('opacity', 0));
                container.appendChild(div);
            }});
        }}

        window.zoomTo = function(d) {{
            currentRoot = d;
            const ancestors = d.ancestors().reverse();
            const bc = ancestors.map((a, i) => {{
                const moveName = a.data.move !== null ? ['TL','TC','TR','ML','MC','MR','BL','BC','BR'][a.data.move] : 'Raiz';
                const key = a.data.board.join('');
                return `<span onclick="zoomTo(nodeMap.get('${{key}}'))">${{moveName}}</span>`;
            }}).join(' > ');
            document.getElementById('breadcrumb').innerHTML = bc;
            treemap(root);
            render(d);
        }};

        window.nodeMap = nodeMap;
        render(root);
    </script>
</body>
</html>'''
