from flask import Flask, render_template, jsonify
from parser import FIGAROParser
import plotly.graph_objects as go
import json
import os

app = Flask(__name__)
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
parser = FIGAROParser(data_dir)

@app.route('/')
def index():
    years = parser.get_available_years()
    return render_template('index.html', years=years)

@app.route('/get_sankey/<year>')
def get_sankey(year):
    flows = parser.get_flow_data(int(year))
    
    # Create lists of unique sources and targets
    nodes = list(set([flow['source'] for flow in flows] + [flow['target'] for flow in flows]))
    
    # Create node-index mapping
    node_indices = {node: idx for idx, node in enumerate(nodes)}
    
    # Create Sankey data structure
    sankey_data = {
        'node': {
            'label': nodes,
            'pad': 15,
            'thickness': 20
        },
        'link': {
            'source': [node_indices[flow['source']] for flow in flows],
            'target': [node_indices[flow['target']] for flow in flows],
            'value': [flow['value'] for flow in flows]
        }
    }
    
    fig = go.Figure(data=[go.Sankey(
        valueformat = ".0f",
        valuesuffix = "€",
        **sankey_data
    )])
    
    fig.update_layout(title_text=f"FIGARO Trade Flows - {year}",
                     font_size=10,
                     height=800)
    
    return json.dumps(fig.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
