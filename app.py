from library import *
import json
import dash
from datetime import datetime
from dash import html, dcc, Output, Input, State

# CLICK HISTORY TRACKING
# Store to track user's click history for navigation
click_history = []

# DATA
url = 'https://ifttt.com/explore/top-applets-on-ifttt'
ids = get_applets_number(url)
ids = get_id_number(ids)
filelist = os.listdir('./data/applets')

count_ok, count_error = 0, 0
for id_ in tqdm(ids):
    if id_+'.json' not in filelist:
        try:
            applet = fetch_applet_info(id_)
            with open('./data/applets/{}.json'.format(id_), 'w') as f:
                json.dump(applet, f, indent=4) #pretty print
                count_ok += 1
        except:
            count_error += 1
    else: count_ok += 1 #print('Already scraped')
print('Scraped {} applets, {} errors'.format(count_ok, count_error))


# GRAPH
current_dir = os.getcwd()
subfolder_path = os.path.join(current_dir, './data/applets') #'/Users/pieror/Library/CloudStorage/OneDrive-Chalmers/research_chalmers/research/7_KG/data/IFTTT/applications/applets_23/applets_top30_2023')
json_files = [os.path.join(root, file) for root, _, files in os.walk(subfolder_path) for file in files if file.endswith('.json')]
app_categories = open_json(os.path.join(current_dir, './data/categories_services_2025.json'))

app_list = []
for file in json_files:
    app = open_json(file)
    dict_app = extract_features(app)
    sanity_check(dict_app, file)
    app_list.append(dict_app)

G = create_graph(app_list, app_categories)
pos = nx.spring_layout(G, k=2, seed=42)
graph_info = network_metrics(G)
export_graph_to_json(G, pos)
#draw_graph(G)

edge_trace, annotations = create_edges_and_annotations(G, pos)
node_trace = create_node_trace(G, pos)

# DASH WEB APPLICATION
"""
WHAT IS DASH?
Dash is a Python framework for building analytical web applications without requiring JavaScript.

ARCHITECTURE:
- Built on top of Flask (Python web framework)
- Uses Plotly.js for interactive visualizations
- Leverages React.js for component rendering
- Provides Python API for HTML/CSS components

HOW DASH WORKS:
1. Layout: Define the structure using HTML components (div, h1, graph, etc.)
2. Callbacks: Python functions that make the app interactive by connecting inputs to outputs
3. Components: Pre-built UI elements like graphs, dropdowns, sliders, tables
4. Server: Runs on Flask server, can be deployed to production

KEY BENEFITS:
- Pure Python (no HTML/CSS/JavaScript knowledge required)
- Reactive programming model
- Automatic updates when data changes
- Built-in support for interactive plots via Plotly

DASH INTERFACE COMPONENTS:
1. NETWORK GRAPH (Interactive Plotly visualization):
   - Shows relationships between IFTTT services and applets
   - Click on nodes to see detailed information
   - Hover over nodes to see service names

2. NODE INFORMATION PANEL:
   - Displays details when you click on a node
   - Shows applet descriptions, URLs, and metadata
   - Updates dynamically based on user interactions

WHAT EACH NODE REPRESENTS:
- NODES = IFTTT Services (e.g., Gmail, Spotify, Weather, Twitter)
- NODE COLORS = Different service categories (Social, Productivity, Smart Home, etc.)
- NODE SIZE = Number of applets using that service (larger = more popular)
- EDGES = Connections showing trigger → action relationships
- EDGE DIRECTION = Arrow from trigger service to action service

EXAMPLE INTERPRETATION:
- Node "Gmail" → Node "Google Drive" means: 
  "When something happens in Gmail (trigger), do something in Google Drive (action)"
- Node size indicates popularity: Larger Gmail node = more applets use Gmail
- Node color groups similar services: All Google services might share the same color

INTERACTIVE FEATURES:
- Click any node to see all applets that use that service
- Hover to see service name and connection count
- Pan and zoom to explore different parts of the network
- Node information panel shows real IFTTT applet details
- ADVANCED CLICK ANALYTICS: Comprehensive tracking system
  * 📊 Detailed tracking: Timestamp, IP address, system info
  * 🖥️ Server monitoring: CPU, RAM, disk usage in real-time
  * 📍 Click coordinates: Exact position on the graph
  * 🔢 Session tracking: Click numbers and session statistics
  * 🐍 Environment info: Python version, OS details
  * 📈 Performance metrics: System resource usage per click
  * 🗑️ Clear history: Reset all tracking data
  * 📱 Responsive cards: Color-coded status indicators
- AI-POWERED USER ANALYTICS DASHBOARD:
  * 🎯 Behavior pattern analysis: Fast Explorer, Steady Browser, Careful Researcher
  * 📊 Statistical visualizations: Bar charts, pie charts, radar plots, timelines
  * 🔮 Preference prediction: Identify preferred service categories
  * 💡 Smart recommendations: Personalized suggestions based on usage
  * 📈 Usage metrics: Exploration vs focus scores, engagement levels
  * 🎭 User profiling: Multi-dimensional behavior analysis
  * 📂 Category analysis: Service type preferences with percentages
  * ⏰ Time-based insights: Session duration, click intervals
"""

# Initialize Dash app
app = Dash(__name__)

# Define the app layout (HTML structure)
# The layout defines what the user sees - it's the visual structure of your app
# Common components:
# - dcc.Graph(): Interactive Plotly charts/graphs
# - html.Div(): Container elements (like HTML <div>)
# - html.H1(), html.P(): Text elements
# - dcc.Dropdown(), dcc.Slider(): Input controls
app.layout = create_dash_layout(edge_trace, node_trace, annotations)


# MCP
# TODO - integrate the interface with the MCP. When the user clicks on a node, 
# the app should call the MCP and get the privacy policy of that app,
# and display it in the node info section. The MCP should be able to handle the
# request and return the privacy policy in a readable format.
# ALTERNATIVE - STATIC PRIVACY POLICY PREVIOUSLY STORED


# DASH CALLBACKS
# Callbacks are Python functions that are automatically called by Dash
# whenever an input component's property changes. They make the app interactive.

# Callback for tab navigation between graph and analytics views
@app.callback(
    [
        Output('main-content', 'children'),
        Output('graph-tab-btn', 'style'),
        Output('analytics-tab-btn', 'style'),
        Output('current-view', 'children')
    ],
    [
        Input('graph-tab-btn', 'n_clicks'),
        Input('analytics-tab-btn', 'n_clicks')
    ],
    [
        State('click-history-store', 'children'),
        State('current-view', 'children')
    ]
)
def switch_views(graph_clicks, analytics_clicks, click_history, current_view):
    """Switch between graph view and analytics dashboard"""
    ctx = dash.callback_context
    
    # Default styles for buttons
    graph_style = {"padding": "10px 20px", "margin": "5px", "backgroundColor": "#6c757d", 
                   "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"}
    analytics_style = {"padding": "10px 20px", "margin": "5px", "backgroundColor": "#6c757d", 
                       "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"}
    
    # Determine which button was clicked
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'analytics-tab-btn':
            # Show analytics view
            analytics_style["backgroundColor"] = "#007bff"
            return create_analytics_page(click_history, G, graph_info), graph_style, analytics_style, 'analytics'
        else:
            # Show graph view (default)
            graph_style["backgroundColor"] = "#007bff"
            return create_graph_view(), graph_style, analytics_style, 'graph'
    
    # Default to graph view
    graph_style["backgroundColor"] = "#007bff"
    return create_graph_view(), graph_style, analytics_style, 'graph'

def create_graph_view():
    """Create the graph view content"""
    # Access global variables
    global edge_trace, node_trace, annotations
    
    return html.Div([
        # Main content area with graph and click history
        html.Div([
            # Network graph (left side)
            html.Div([
                dcc.Graph(
                    id='network-graph',
                    figure={
                        'data': edge_trace + [node_trace],
                        'layout': go.Layout(
                            clickmode='event+select',
                            showlegend=False,
                            margin=dict(l=20, r=20, t=20, b=20),
                            hovermode='closest',
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            annotations=annotations
                        )
                    },
                    style={"height": "600px"}
                ),
            ], style={"width": "60%", "display": "inline-block", "verticalAlign": "top"}),
            
            # Detailed click history panel (right side)
            html.Div([
                html.H3("📊 Click Analytics", style={"textAlign": "center", "margin": "10px 0", "color": "#333"}),
                html.Div([
                    html.Button("🗑️ Clear History", id="clear-history-btn", 
                              style={"width": "100%", "marginBottom": "15px", 
                                   "backgroundColor": "#dc3545", "color": "white", 
                                   "border": "none", "padding": "10px", "cursor": "pointer",
                                   "borderRadius": "5px", "fontSize": "14px", "fontWeight": "bold"}),
                    html.Div(id="click-history-list", 
                           style={"maxHeight": "520px", "overflowY": "auto", 
                                "border": "1px solid #dee2e6", "padding": "10px", 
                                "backgroundColor": "#f8f9fa", "borderRadius": "5px"})
                ])
            ], style={"width": "38%", "display": "inline-block", "verticalAlign": "top", 
                     "marginLeft": "2%", "padding": "10px"})
            
        ], style={"display": "flex", "width": "100%"}),
        
        # Node information panel (bottom)
        html.Div(id='node-info', style={"padding": "20px", "fontSize": "16px", 
                                       "border": "1px solid #ddd", "marginTop": "20px",
                                       "backgroundColor": "#f5f5f5"})
    ])

# Main callback to handle node clicks and update both node info and click history
@app.callback(
    [
        # Output: What gets updated when the callback is triggered
        Output('node-info', 'children'),  # Updates the node information panel
        Output('click-history-store', 'children'),  # Updates the hidden click history store
        Output('click-history-list', 'children')  # Updates the visible click history list
    ],
    [
        # Input: What triggers the callback
        Input('network-graph', 'clickData'),  # Triggered when user clicks on graph
        Input('clear-history-btn', 'n_clicks')  # Triggered when clear history button is clicked
    ],
    [
        # State: Current values that don't trigger the callback but are needed
        State('click-history-store', 'children'),  # Current click history data
        State('current-view', 'children')  # Current view state
    ]
)
def update_interface(clickData, clear_clicks, current_history, current_view):
    """
    This callback function handles:
    1. Node clicks in the network graph
    2. Click history tracking and display
    3. Clear history button functionality
    
    Args:
        clickData: Plotly click event data containing information about the clicked node
        clear_clicks: Number of times the clear history button has been clicked
        current_history: Current click history stored as JSON string
        current_view: Current view state (graph or analytics)
        
    Returns:
        Tuple of (node_info_html, updated_history_json, history_display_html)
    """
    # Get callback context to determine what triggered the callback
    ctx = dash.callback_context
    
    # If clear history button was clicked
    if ctx.triggered and 'clear-history-btn' in ctx.triggered[0]['prop_id']:
        empty_history = json.dumps([])
        return (
            html.P("Click history cleared. Click on a node to start tracking again.", 
                  style={"textAlign": "center", "color": "#666", "fontStyle": "italic"}),
            empty_history,
            render_click_history(empty_history)
        )
    
    # Handle node clicks (only if in graph view)
    if clickData and current_view == 'graph':
        # Update click history
        updated_history = update_click_history(current_history, clickData)
        
        # Get node information
        node_info = display_node_info(G, clickData, graph_info)
        
        # Render updated history
        history_display = render_click_history(updated_history)
        
        return node_info, updated_history, history_display
    
    # Default state (no clicks yet)
    default_history = current_history or json.dumps([])
    return (
        display_node_info(G, None, graph_info),  # Show default info
        default_history,
        render_click_history(default_history)
    )

# Flask server instance
# Dash runs on top of Flask web framework
# This server object can be used for deployment (e.g., with Gunicorn)
server = app.server

if __name__ == '__main__':
    # Run the Dash application in debug mode
    # debug=True enables:
    # - Hot reloading: Auto-restart when code changes
    # - Better error messages
    # - Development tools
    # Access the app at: http://127.0.0.1:8050/
    app.run(debug=True)
