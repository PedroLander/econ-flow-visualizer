from flask import Flask, render_template, jsonify, request
from src.parser import FIGAROParser
import plotly.graph_objects as go
import json
import os

app = Flask(__name__)
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
parser = FIGAROParser(data_dir)

def get_initial_data():
    """Get initial data for the visualization setup."""
    years = parser.get_available_years()
    initial_year = years[0]
    flows = parser.get_flow_data(initial_year)
    
    # Get unique NACE codes
    nace_codes = sorted(list(set(flow['source'] for flow in flows)))
    
    # Get regions from metadata
    regions = parser.get_available_regions()
    
    # Get value range
    value_range = parser.get_value_range(initial_year)
    
    return years, nace_codes, regions, value_range

@app.route('/')
def index():
    years, nace_codes, regions, value_range = get_initial_data()
    return render_template('index.html', 
                         years=years,
                         nace_codes=nace_codes,
                         geo_regions=regions,
                         min_value=value_range['min'],
                         max_value=value_range['max'])

@app.route('/get_sankey')
def get_sankey():
    years = parser.get_available_years()
    year = int(request.args.get('year', years[0]))
    min_value = float(request.args.get('min_value', 0))
    nace_level = int(request.args.get('nace_level', 1))
    selected_regions = request.args.getlist('regions[]')
    show_imports = request.args.get('show_imports', 'true') == 'true'
    show_exports = request.args.get('show_exports', 'true') == 'true'
    
    flows = parser.get_flow_data(
        year=year,
        min_value=min_value,
        nace_level=nace_level,
        regions=selected_regions if selected_regions else None,
        include_imports=show_imports,
        include_exports=show_exports
    )
    
    # Create lists of unique sources and targets
    nodes = list(set([flow['source'] for flow in flows] + [flow['target'] for flow in flows]))
    
    # Create node-index mapping
    node_indices = {node: idx for idx, node in enumerate(nodes)}
    
    # Create Sankey data structure
    sankey_trace = {
        'type': 'sankey',
        'node': {
            'label': nodes,
            'pad': 15,
            'thickness': 20,
            'color': ['#1f77b4' if node in ('Total Imports', 'Total Exports') 
                     else '#2ca02c' for node in nodes]
        },
        'link': {
            'source': [node_indices[flow['source']] for flow in flows],
            'target': [node_indices[flow['target']] for flow in flows],
            'value': [flow['value'] for flow in flows],
            'color': ['rgba(31, 119, 180, 0.4)' for _ in flows]
        },
        'valueformat': '.0f',
        'valuesuffix': '€'
    }
    
    layout = {
        'title': {
            'text': f"FIGARO Trade Flows - {year}"
        },
        'font': {
            'size': 10
        },
        'height': 800,
        'plot_bgcolor': 'rgba(255, 255, 255, 0.9)',
        'paper_bgcolor': 'rgba(255, 255, 255, 0.9)'
    }
    
    figure = {
        'data': [sankey_trace],
        'layout': layout
    }
    
    return jsonify(figure)

if __name__ == '__main__':
    app.run(debug=True)
