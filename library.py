### REQUIREMENTS FOR SCRAPER
import requests
from bs4 import BeautifulSoup
import os
import json
from tqdm import tqdm
import urllib.parse

### REQUIREMENTS FOR GRAPH AND INTERFACE
import json
import networkx as nx
import matplotlib.pyplot as plt
import os
from dash import html, dcc, Output, Input, Dash
import plotly.graph_objects as go


### SCRAPER
def get_applets_number(url):
        #get the list of applets from ifttt top applets
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        #find the a class that contains applet-card-body
        applets = soup.find_all('a', class_='applet-card-body')
    
        #from the list of applets, get the href that contains the applet id
        applets_id = []
        for applet in applets:
            if "#" not in applet['href']:
                applets_id.append(applet['href'])
        
        return applets_id

def get_id_number(ids):
    id_number = []
    for id_ in ids:
        id_ = id_.split('/')[4]
        id_ = id_.split('-')[0]
        id_number.append(id_)
    return id_number

def fetch_applet_info(applet_id):
    #query = f'{{applet(id:"{applet_id}"){{id name trigger{{name ingredients{{normalized_name value_type}}}} applet_queries{{query{{name ingredients{{normalized_name}}}}}} actions{{name full_normalized_module_name action_fields{{normalized_module_name}}}} filter_code tags{{name}}}}}}'
    query = f'''
            {{
            applet(id: "{applet_id}") {{
                id
                name
                description
                installs_count
                friendly_id
                channels {{
                    name
                    module_name
                    short_name
                    brand_color
                }}
                trigger {{
                    name
                    description
                    module_name
                    full_normalized_module_name
                    ingredients {{
                            normalized_name
                            value_type
                            slug
                            note
                    }}
                }}
                applet_queries {{
                    query {{
                            name
                            ingredients {{
                                normalized_name
                            }}
                    }}
                }}
                actions {{
                    name
                    description
                    module_name
                    full_normalized_module_name
                    action_fields {{
                        normalized_module_name
                    }}
                }}
                }}
            }}
            '''
    query = f'''{{ applet(id: "{applet_id}") {{ id name description installs_count friendly_id channels {{ name module_name short_name brand_color }} trigger {{ name description module_name full_normalized_module_name ingredients {{ normalized_name value_type slug note }} }} applet_queries {{ query {{ name ingredients {{ normalized_name }} }} }} actions {{ name description module_name full_normalized_module_name action_fields {{ normalized_module_name }} }} }} }}'''

    

    url = "https://ifttt.com/api/v3/graph?query=" + urllib.parse.quote(query)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch {applet_id}: {response.status_code}")
        return None
    
#### SCRAPER EXAMPLE ####
# url = 'https://ifttt.com/explore/top-applets-on-ifttt'
# ids = get_applets_number(url)
# ids = get_id_number(ids)
# filelist = os.listdir('./applets')

# count_ok, count_error = 0, 0
# for url in tqdm(ids):
#     if url[url.find('applets/')+len('applets/'):]+'.json' not in filelist:
#         try:
#             applet = fetch_applet_info(url)
#             with open('./applets/{}.json'.format(url), 'w') as f:
#                 json.dump(applet, f, indent=4) #pretty print
#                 count_ok += 1
#         except:
#             count_error += 1
# print('Scraped {} applets, {} errors'.format(count_ok, count_error))


### KNOWLEDGE GRAPH
def open_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def sanity_check(data, file):
    required_keys = {
        'id_app',
        'link',
        'description',
        'name',
        'installation_count',
        #'services_name',
        'trigger',
        'action',
        'permissions_trigger',
        'permissions_action',
        'node_color',
        'trigger',
        'action'
    }

    invalid_keys = [k for k in required_keys if not data.get(k)]
    if invalid_keys:
        print(f"Empty or None values in file {file}: {invalid_keys}")

############################# DATA EXTRACTION
def extract_fine_grained(data):
    fine_grained_triggers = data['data']['applet']['trigger']['ingredients']
    fine_grained_trigger_endpoints = {}
    for fine_grained_trigger in fine_grained_triggers:
        name = fine_grained_trigger['slug'].lower()
        if name not in fine_grained_trigger_endpoints:
            fine_grained_trigger_endpoints[name] = []
        fine_grained_trigger_endpoints[name].append(fine_grained_trigger['normalized_name'].lower())
    fine_grained_action_endpoints = {}
    #fine_grained_actions = data['appletDetails']['normalized_applet']['stored_fields']
    fine_grained_actions = data['data']['applet']['actions'][0]['action_fields']
    for fine_grained_action in fine_grained_actions:
        name = fine_grained_action['normalized_module_name']
        if name not in fine_grained_action_endpoints:
            fine_grained_action_endpoints[name] = []
        endpoint = data['data']['applet']['trigger']['full_normalized_module_name'].lower() 
        fine_grained_action_endpoints[name].append(endpoint)
    return fine_grained_trigger_endpoints, fine_grained_action_endpoints    

def extract_features(json):
    id_app = json['data']['applet']['id']
    link = 'https://ifttt.com/applets/'+json['data']['applet']['friendly_id']
    description = json['data']['applet']['description']
    name = json['data']['applet']['name']
    installation_count = json['data']['applet']['installs_count']
    #services_name = [json['data']['applet']['channels'][0]['name'], json['data']['applet']['channels'][1]['name']]
    trigger = json['data']['applet']['channels'][0]['name']
    try:
        action = json['data']['applet']['channels'][1]['name']
    except:
        action = json['data']['applet']['channels'][0]['name']
    permissions_trigger = "/triggers/"+json['data']['applet']['trigger']['full_normalized_module_name'].lower()
    permissions_action = "/actions/"+json['data']['applet']['actions'][0]['full_normalized_module_name'].lower()
    node_color = '#'+json['data']['applet']['channels'][0]['brand_color']
    fine_grained_trigger = extract_fine_grained(json)[0]
    fine_grained_action = extract_fine_grained(json)[1]
    return {
        'id_app': id_app,
        'link': link,
        'description': description,
        'name': name,
        'installation_count': installation_count,
        #'services_name': services_name,
        'trigger': trigger,
        'action': action,
        'permissions_trigger': permissions_trigger,
        'permissions_action': permissions_action,
        'node_color': node_color,
        'fine_grained_trigger': fine_grained_trigger,
        'fine_grained_action': fine_grained_action
    }

def get_data_category(app_categories, node_permission):
    data_category = 'unknown'
    service = node_permission[node_permission.find('/', node_permission.find('/')+1):node_permission.find('.', node_permission.find('/', node_permission.find('/')+1))].replace('/', '').lower()
    for c, s in app_categories.items():
        s = [item.replace('_', '') for item in s]
        if service in s:
            data_category = c
    return data_category

def get_privacy_policy(service):
    if " " in service:
        service = service.split(" ")[0]
    file_path = f'./data/privacy_policy/{service}.txt'
    
    if not os.path.exists(file_path):
        return html.P("Privacy policy not available.")

    with open(file_path, 'r') as f:
        text = f.read()

    lines = text.splitlines()
    bullet_lines = []
    paragraph_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("•", "*", "-")):
            bullet_lines.append(stripped.lstrip("•*- ").strip())
        elif stripped:
            paragraph_lines.append(stripped)

    elements = []

    if paragraph_lines:
        for para in paragraph_lines:
            elements.append(html.P(para))

    if bullet_lines:
        elements.append(html.Ul([html.Li(bullet) for bullet in bullet_lines]))

    return html.Div(elements)

############################ GRAPH CREATION
def new_node(G, data, node, app_categories):
    if node in data['trigger']:
        G.add_node(node, 
                   id_app=[data['id_app']], 
                   url=[data['link']],
                   description=[data['description']],
                   installation_count=[str(abs(int(data['installation_count'])))],
                   color=data['node_color'],
                   trigger=[data['trigger']],
                   action=[data['action']],
                   permission =[data['permissions_trigger']],
                   fine_grained_trigger=[data['fine_grained_trigger']],
                   fine_grained_action=[data['fine_grained_action']],
                   data_category=[get_data_category(app_categories, data['permissions_trigger'])])      
    if node in data['action']:
        G.add_node(node, 
                   id_app=[data['id_app']], 
                   url=[data['link']],
                   description=[data['description']],
                   installation_count=[str(abs(int(data['installation_count'])))],
                   color=data['node_color'],
                   trigger=[data['trigger']],
                   action=[data['action']],
                   permission=[data['permissions_action']],
                   fine_grained_trigger=[data['fine_grained_trigger']],
                   fine_grained_action=[data['fine_grained_action']],
                   data_category=[get_data_category(app_categories, data['permissions_action'])])  
    return G

def update_node(G, data, node, app_categories):
    if node in data['trigger']:
        G.nodes[node]['id_app'].append(data['id_app'])
        G.nodes[node]['url'].append(data['link'])
        G.nodes[node]['description'].append(data['description'])
        G.nodes[node]['installation_count'].append(str(abs(int(data['installation_count']))))
        G.nodes[node]['color'] = data['node_color']
        G.nodes[node]['trigger'].append(data['trigger'])
        G.nodes[node]['action'].append(data['action'])
        G.nodes[node]['permission'].append(data['permissions_trigger'])
        G.nodes[node]['fine_grained_trigger'].append(data['fine_grained_trigger'])
        G.nodes[node]['fine_grained_action'].append(data['fine_grained_action'])
        G.nodes[node]['data_category'].append(get_data_category(app_categories, data['permissions_trigger']))
    if node in data['action']:
        G.nodes[node]['id_app'].append(data['id_app'])
        G.nodes[node]['url'].append(data['link'])
        G.nodes[node]['description'].append(data['description'])
        G.nodes[node]['installation_count'].append(str(abs(int(data['installation_count']))))
        G.nodes[node]['color'] = data['node_color']
        G.nodes[node]['trigger'].append(data['trigger'])
        G.nodes[node]['action'].append(data['action'])
        G.nodes[node]['permission'].append(data['permissions_action'])
        G.nodes[node]['fine_grained_trigger'].append(data['fine_grained_trigger'])
        G.nodes[node]['fine_grained_action'].append(data['fine_grained_action'])
        G.nodes[node]['data_category'].append(get_data_category(app_categories, data['permissions_action']))
    return G

def create_graph(app_list, app_categories):
    G = nx.DiGraph()
    for data in app_list:
        for node in [data['trigger'], data['action']]:
            if node not in G.nodes:
                G = new_node(G, data, node, app_categories)
            else:
                G = update_node(G, data, node, app_categories)
        #G.add_edge(data['trigger'], data['action'], label='trigger', id_app=data['id_app'])
        G.add_edge(data['trigger'], data['action'], id_app=data['id_app'])

    return G

############################ EXPORTING GRAPH
def export_graph_to_json(G, pos, filename="figma_data.json"):
    data = {
        "nodes": [],
        "edges": []
    }

    for node, attr in G.nodes(data=True):
        node_data = {
            "id_app": attr.get("id_app", []),
            "service": node,
            "position": {"x": pos[node][0], "y": pos[node][1]},
            "url": attr.get("url", []),
            "description": attr.get("description", []),
            "installation_count": attr.get("installation_count", []),
            "color": attr.get("color", "#000000"),
            "trigger": attr.get("trigger", []),
            "action": attr.get("action", []),
            "permission": attr.get("permission", [])
        }
        data["nodes"].append(node_data)

    for source, target, edge_attr in G.edges(data=True):
        data["edges"].append({
            "source": source,
            "target": target,
            "label": edge_attr.get("label", "")
        })

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def network_metrics(graph: nx.Graph) -> None:

    """
    this function print out some network metrics
    comment and uncomment print line are due to the fact that some of these metrics are strictly related
    to a directional or undirectional network (connections between nodes)
    """    

    #max_de = max(nx.degree_centrality(graph).items(), key=itemgetter(1))
    #max_clo = max(nx.closeness_centrality(graph).items(), key=itemgetter(1))
    #max_bet = max(nx.betweenness_centrality(graph, normalized=True, endpoints=False).items(), key=itemgetter(1))
    #print(f"the node with id {max_de[0]} has a degree centrality of {max_de[1]:.2f} which is the maximum of the Graph")
    #print(f"the node with id {max_clo[0]} has a closeness centrality of {max_clo[1]:.2f} which is the maximum of the Graph")
    #print(f"the node with id {max_bet[0]} has a betweenness centrality of {max_bet[1]:.2f} which is the maximum of the Graph")

    information = {}
    information['total_nodes'] = graph.number_of_nodes()
    information['total_edges'] = graph.number_of_edges()
    print('total_nodes', information['total_nodes'])
    print('total_edges', information['total_edges'])
    information['max_in_degree'] = sorted(dict(graph.in_degree()).items(), key=lambda kv: kv[1], reverse=True)[:1]
    information['max_out_degree'] = sorted(dict(graph.out_degree()).items(), key=lambda kv: kv[1], reverse=True)[:1]
    print('max_in_degree', information['max_in_degree'])
    print('max_out_degree', information['max_out_degree'])
    information['max_degree_centrality'] = sorted(dict(nx.degree_centrality(graph).items()), key=lambda kv: kv[1], reverse=True)[:1]
    information['max_closeness_centrality'] = sorted(dict(nx.closeness_centrality(graph).items()), key=lambda kv: kv[1], reverse=True)[:1]
    information['max_betweenness_centrality'] = sorted(dict(nx.betweenness_centrality(graph, normalized=True, endpoints=False).items()), key=lambda kv: kv[1], reverse=True)[:1]
    information['pagerank'] = sorted(dict(nx.pagerank(graph).items()), key=lambda kv: kv[1], reverse=True)[:10]
    return information

def draw_graph(G):
    plt.figure(figsize=(20, 15))
    pos = nx.spring_layout(G, k=2, seed=42)
    edge_labels = nx.get_edge_attributes(G, 'label')
    node_colors = [G.nodes[node].get('color', '#8cc251') for node in G.nodes()]
    nx.draw(
        G, pos, with_labels=True,
        node_color=node_colors,
        node_size=2000,
        font_size=10,
        arrows=True
    )
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    plt.show()

### INTERFACE
def create_edges_and_annotations(G, pos):
    edge_trace = []
    annotations = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        # Line trace for edge
        edge_trace.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            line=dict(width=1, color='gray'),
            mode='lines',
            hoverinfo='none'
        ))

        # Arrow shape
        annotations.append(dict(
            ax=x0, ay=y0,
            x=x1, y=y1,
            xref='x', yref='y',
            axref='x', ayref='y',
            showarrow=True,
            arrowhead=3,
            arrowsize=1,
            arrowwidth=1.5,
            opacity=0.7
        ))

        # Edge label
        label = G.edges[edge].get('label', '')
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        annotations.append(dict(
            x=mid_x, y=mid_y,
            text=label,
            showarrow=False,
            font=dict(size=10, color="red"),
            xanchor="center",
            yanchor="bottom"
        ))

    return edge_trace, annotations

def create_node_trace(G, pos):
    node_x, node_y, node_text, node_ids, node_colors = [], [], [], [], []

    for node, attrs in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_ids.append(node)
        node_colors.append(attrs.get('color', '#1f77b4'))

    return go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            size=20,
            color=node_colors,
            line=dict(width=2, color='black')
        ),
        customdata=node_ids
    )

def create_dash_layout(edge_trace, node_trace, annotations):
    return html.Div([
        # Navigation header
        html.Div([
            html.H2("IFTTT Graph: Trigger → Action", style={"textAlign": "center", "margin": "10px 0", "color": "#333"}),
            html.Div([
                html.Button("📊 Network Graph", id="graph-tab-btn", 
                          style={"padding": "10px 20px", "margin": "5px", "backgroundColor": "#007bff", 
                                "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"}),
                html.Button("📈 Analytics Dashboard", id="analytics-tab-btn", 
                          style={"padding": "10px 20px", "margin": "5px", "backgroundColor": "#6c757d", 
                                "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"})
            ], style={"textAlign": "center", "marginBottom": "20px"})
        ]),
        
        # Main content area (will be switched between graph and analytics)
        html.Div(id="main-content", children=[
            # Network Graph View (default)
            html.Div([
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
            ], id="graph-view")
        ]),
        
        # Hidden div to store click history data
        html.Div(id='click-history-store', style={'display': 'none'}),
        
        # Hidden div to store current view state
        html.Div(id='current-view', children='graph', style={'display': 'none'})
    ])

def display_node_info(G, clickData, graph_info):
    if clickData and 'customdata' in clickData['points'][0]:
        node = clickData['points'][0]['customdata']
        data = G.nodes[node]

        id_apps = data.get('id_app', [])
        urls = data.get('url', [])
        descriptions = data.get('description', [])
        installs = data.get('installation_count', [])
        triggers = data.get('trigger', [])
        actions = data.get('action', [])
        permissions = data.get('permission', [])
        fine_grained_triggers = data.get("fine_grained_trigger", {})
        fine_grained_actions = data.get("fine_grained_action", {})
        data_types = data.get("data_category", [])

        combined_info = []

        def format_field_list(fields):
            if not fields:
                return ""
            elif len(fields) == 1:
                return fields[0]
            else:
                return ", ".join(fields[:-1]) + f", and {fields[-1]}"

        for i, (app_id, link, desc, count, trigger, action, permission, fg_trigger, fg_action, data_type) in enumerate(zip(
            id_apps, urls, descriptions, installs, triggers, actions, permissions,
            fine_grained_triggers, fine_grained_actions, data_types
        )):

            trigger_fields = list(fg_trigger.keys())
            action_fields = list(fg_action.keys())
            trigger_fields_readable = [field.replace('_', ' ').capitalize() for field in trigger_fields]
            action_fields_readable = [field.replace('_', ' ').capitalize() for field in action_fields]

            if permission.count('/') > 2:
                permission = permission.split('/')[:3]
                permission = '/'.join(permission)

            # Build the sharing sentence
            if trigger_fields_readable or action_fields_readable:
                trigger_str = format_field_list(trigger_fields_readable)
                action_str = format_field_list(action_fields_readable)
                sharing_sentence = html.Span(["This app uses the '", html.Strong(trigger.title()), "' trigger, sharing ", trigger_str.lower(), ", which is used in the '", html.Strong(action.title()), "' action involving ", action_str.lower(), "."])
            else:
                sharing_sentence = "No fine-grained data available."


            combined_info.append(html.Div([
                html.P(f"Data Category: {data_type.replace('-', ' ').title()}"),
                html.P(f"Purpose: {desc}"),
                html.P(f"Usage: {count} users"),
                #html.P(f"Trigger: {trigger}"),
                #html.P(f"Action: {action}"),
                html.P(["Fine Grained Data Sharing: ", sharing_sentence]),
                #html.P(f"Endpoint: {permission}"),
                html.A("Original Applet Link", href=link, target="_blank"),
                #html.P(f"App ID: {app_id}"),
            ], style={"marginBottom": "15px", "borderBottom": "1px solid #ccc"}))

        applet_list = html.Div([
            html.P(f"{node} is involved in the following App(s):"),
            *[html.P([f"• {app_id} – ", html.A("check on IFTTT", href=f"https://ifttt.com/applets/{app_id}", target="_blank")]) for app_id in id_apps]
        ], style={"marginTop": "20px", "borderBottom": "1px solid #ccc"})

        privacy_policy = html.Div([
            html.P(html.B("Privacy Policy:")), 
            html.P(get_privacy_policy(node))
        ], style={"marginTop": "20px"})

        return [html.H4(f"Node: {node}")] + combined_info + [applet_list, privacy_policy]

    return html.Div([
        html.P("Click on a node to see its details, including the applets it is involved in and the data it shares."),
        html.P(f"The mostly involved trigger node is {graph_info['max_in_degree'][0][0]} with {graph_info['max_in_degree'][0][1]} connections."),
        html.P(f"The mostly involved action node is {graph_info['max_out_degree'][0][0]} with {graph_info['max_out_degree'][0][1]} connections.")
])

def update_click_history(click_history_json, clickData):
    """Update click history with detailed tracking information"""
    import json
    import socket
    import platform
    from datetime import datetime
    
    # Try to import psutil for system monitoring, fall back gracefully if not available
    try:
        import psutil
        PSUTIL_AVAILABLE = True
    except ImportError:
        PSUTIL_AVAILABLE = False
    
    # Parse existing history
    if click_history_json:
        click_history = json.loads(click_history_json)
    else:
        click_history = []
    
    # Add new click if valid
    if clickData and 'customdata' in clickData['points'][0]:
        node = clickData['points'][0]['customdata']
        
        # Collect detailed tracking information
        now = datetime.now()
        
        # Get system information
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "Unknown"
            local_ip = "127.0.0.1"
        
        # Get server/system status (if psutil is available)
        if PSUTIL_AVAILABLE:
            try:
                cpu_usage = round(psutil.cpu_percent(interval=0.1), 1)
                memory = psutil.virtual_memory()
                memory_usage = round(memory.percent, 1)
                if platform.system() == 'Windows':
                    disk_usage = round(psutil.disk_usage('C:\\').percent, 1)
                else:
                    disk_usage = round(psutil.disk_usage('/').percent, 1)
            except:
                cpu_usage = "N/A"
                memory_usage = "N/A"
                disk_usage = "N/A"
        else:
            cpu_usage = "N/A (psutil not available)"
            memory_usage = "N/A (psutil not available)"
            disk_usage = "N/A (psutil not available)"
        
        # Create detailed click record
        click_record = {
            "node": node,
            "timestamp": now.isoformat(),
            "time_display": now.strftime("%H:%M:%S"),
            "date_display": now.strftime("%Y-%m-%d"),
            "hostname": hostname,
            "local_ip": local_ip,
            "user_agent": platform.platform(),
            "system_info": {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "psutil_available": PSUTIL_AVAILABLE
            },
            "session_info": {
                "click_number": len(click_history) + 1,
                "browser_session": "Dash Local Server",
                "total_session_clicks": len(click_history) + 1
            },
            "coordinates": {
                "x": clickData['points'][0].get('x', 'N/A'),
                "y": clickData['points'][0].get('y', 'N/A')
            },
            "server_status": "Active" if PSUTIL_AVAILABLE else "Limited Monitoring"
        }
        
        # Add to history (limit to last 15 clicks for detailed tracking)
        click_history.append(click_record)
        if len(click_history) > 15:
            click_history = click_history[-15:]
    
    return json.dumps(click_history)

def render_click_history(click_history_json):
    """Render detailed click history as HTML components"""
    import json
    
    if not click_history_json:
        return html.P("No clicks yet. Click on a node to start detailed tracking!", 
                     style={"textAlign": "center", "color": "#666", "fontStyle": "italic"})
    
    click_history = json.loads(click_history_json)
    
    if not click_history:
        return html.P("No clicks yet. Click on a node to start detailed tracking!", 
                     style={"textAlign": "center", "color": "#666", "fontStyle": "italic"})
    
    history_items = []
    for i, item in enumerate(reversed(click_history)):  # Show most recent first
        
        # Get system status color coding
        cpu_color = "#28a745" if isinstance(item.get("system_info", {}).get("cpu_usage"), (int, float)) and item["system_info"]["cpu_usage"] < 70 else "#dc3545"
        memory_color = "#28a745" if isinstance(item.get("system_info", {}).get("memory_usage"), (int, float)) and item["system_info"]["memory_usage"] < 80 else "#dc3545"
        
        # Create detailed information card
        detail_card = html.Div([
            # Main click info
            html.Div([
                html.Span(f"{len(click_history)-i}. ", style={"fontWeight": "bold", "color": "#007bff", "fontSize": "16px"}),
                html.Span(item["node"], style={"fontWeight": "bold", "fontSize": "16px", "color": "#333"}),
                html.Span(f" • {item['time_display']}", style={"fontSize": "14px", "color": "#666", "marginLeft": "10px"})
            ], style={"marginBottom": "8px"}),
            
            # Detailed tracking information
            html.Div([
                html.Div([
                    html.Span("📅 ", style={"marginRight": "5px"}),
                    html.Span(f"Date: {item['date_display']}", style={"fontSize": "12px"})
                ], style={"marginBottom": "3px"}),
                
                html.Div([
                    html.Span("🌐 ", style={"marginRight": "5px"}),
                    html.Span(f"IP: {item.get('local_ip', 'N/A')}", style={"fontSize": "12px"}),
                    html.Span(f" | Host: {item.get('hostname', 'N/A')}", style={"fontSize": "12px", "marginLeft": "10px"})
                ], style={"marginBottom": "3px"}),
                
                html.Div([
                    html.Span("💻 ", style={"marginRight": "5px"}),
                    html.Span(f"OS: {item.get('system_info', {}).get('os', 'N/A')}", style={"fontSize": "12px"})
                ], style={"marginBottom": "3px"}),
                
                html.Div([
                    html.Span("📊 Server Status: ", style={"fontSize": "12px", "fontWeight": "bold"}),
                    html.Span(f"{item.get('server_status', 'Unknown')}", 
                             style={"fontSize": "12px", "color": "#28a745" if item.get('server_status') == 'Active' else "#ffc107", 
                                   "marginRight": "10px", "fontWeight": "bold"}),
                    html.Br(),
                    html.Span("  CPU: ", style={"fontSize": "11px", "marginLeft": "20px"}),
                    html.Span(f"{item.get('system_info', {}).get('cpu_usage', 'N/A')}" + ("%" if isinstance(item.get('system_info', {}).get('cpu_usage'), (int, float)) else ""), 
                             style={"fontSize": "11px", "color": cpu_color, "marginRight": "8px"}),
                    html.Span("RAM: ", style={"fontSize": "11px"}),
                    html.Span(f"{item.get('system_info', {}).get('memory_usage', 'N/A')}" + ("%" if isinstance(item.get('system_info', {}).get('memory_usage'), (int, float)) else ""), 
                             style={"fontSize": "11px", "color": memory_color, "marginRight": "8px"}),
                    html.Span("Disk: ", style={"fontSize": "11px"}),
                    html.Span(f"{item.get('system_info', {}).get('disk_usage', 'N/A')}" + ("%" if isinstance(item.get('system_info', {}).get('disk_usage'), (int, float)) else ""), 
                             style={"fontSize": "11px", "color": "#6c757d"})
                ], style={"marginBottom": "3px"}),
                
                html.Div([
                    html.Span("🐍 ", style={"marginRight": "5px"}),
                    html.Span(f"Python: {item.get('system_info', {}).get('python_version', 'N/A')}", style={"fontSize": "12px"}),
                    html.Span(f" | {item.get('system_info', {}).get('os', 'N/A')}", style={"fontSize": "12px", "marginLeft": "10px"})
                ], style={"marginBottom": "3px"}),
                
                html.Div([
                    html.Span("📍 ", style={"marginRight": "5px"}),
                    html.Span(f"Position: ({item.get('coordinates', {}).get('x', 'N/A'):.2f}, {item.get('coordinates', {}).get('y', 'N/A'):.2f})" 
                             if isinstance(item.get('coordinates', {}).get('x'), (int, float)) else "Position: N/A", 
                             style={"fontSize": "12px"}),
                    html.Span(f" | Click #{item.get('session_info', {}).get('click_number', i+1)}", 
                             style={"fontSize": "12px", "marginLeft": "10px", "color": "#6c757d"})
                ], style={"marginBottom": "5px"})
                
            ], style={"paddingLeft": "20px", "borderLeft": "3px solid #007bff", "marginLeft": "10px"})
            
        ], style={
            "padding": "12px", 
            "backgroundColor": "white" if i % 2 == 0 else "#f8f9fa", 
            "border": "1px solid #dee2e6", 
            "marginBottom": "5px", 
            "borderRadius": "5px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
        })
        
        history_items.append(detail_card)
    
    return html.Div([
        html.Div([
            html.H4("🕒 Detailed Click History", style={"margin": "0 0 10px 0", "color": "#333"}),
            html.P(f"Tracking {len(click_history)} recent interactions", 
                  style={"margin": "0 0 15px 0", "fontSize": "12px", "color": "#6c757d"})
        ]),
        html.Div(history_items, style={"maxHeight": "400px", "overflowY": "auto"})
    ])

def analyze_user_preferences(click_history_json, G):
    """Analyze user preferences based on click history"""
    import json
    from collections import Counter, defaultdict
    from datetime import datetime
    import statistics
    
    if not click_history_json:
        return None
    
    click_history = json.loads(click_history_json)
    if not click_history:
        return None
    
    # Extract click data
    clicked_nodes = [item['node'] for item in click_history]
    click_times = [datetime.fromisoformat(item['timestamp']) for item in click_history]
    
    # Basic statistics
    total_clicks = len(click_history)
    unique_nodes = len(set(clicked_nodes))
    most_clicked = Counter(clicked_nodes).most_common(5)
    
    # Time analysis
    if len(click_times) > 1:
        time_intervals = [(click_times[i] - click_times[i-1]).total_seconds() 
                         for i in range(1, len(click_times))]
        avg_interval = statistics.mean(time_intervals) if time_intervals else 0
        session_duration = (click_times[-1] - click_times[0]).total_seconds()
    else:
        avg_interval = 0
        session_duration = 0
    
    # Category analysis
    category_counts = defaultdict(int)
    service_connections = defaultdict(int)
    
    for node in clicked_nodes:
        if node in G.nodes:
            # Get category information
            category = G.nodes[node].get('category', 'Unknown')
            category_counts[category] += 1
            
            # Get connection count (popularity)
            connections = G.degree(node)
            service_connections[node] = connections
    
    # User behavior patterns
    exploration_score = unique_nodes / total_clicks if total_clicks > 0 else 0
    focus_score = 1 - exploration_score
    
    # Predict preferences
    preferred_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    preferred_services = [node for node, count in most_clicked[:3]]
    
    # Activity pattern
    if avg_interval < 5:
        activity_pattern = "Fast Explorer"
    elif avg_interval < 15:
        activity_pattern = "Steady Browser"
    else:
        activity_pattern = "Careful Researcher"
    
    return {
        'total_clicks': total_clicks,
        'unique_nodes': unique_nodes,
        'most_clicked': most_clicked,
        'preferred_categories': preferred_categories,
        'preferred_services': preferred_services,
        'exploration_score': exploration_score,
        'focus_score': focus_score,
        'avg_interval': avg_interval,
        'session_duration': session_duration,
        'activity_pattern': activity_pattern,
        'category_distribution': dict(category_counts),
        'service_connections': dict(service_connections)
    }

def create_analytics_page(click_history_json, G, graph_info):
    """Create comprehensive analytics page with plots and predictions"""
    import json
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime
    
    analysis = analyze_user_preferences(click_history_json, G)
    
    if not analysis:
        return html.Div([
            html.H2("📊 User Analytics Dashboard", style={"textAlign": "center", "margin": "20px 0"}),
            html.P("No click data available yet. Start exploring the network to see analytics!", 
                  style={"textAlign": "center", "fontSize": "18px", "color": "#666"})
        ])
    
    # Create visualizations
    
    # 1. Most Clicked Services Bar Chart
    if analysis['most_clicked']:
        services, counts = zip(*analysis['most_clicked'])
        fig_services = go.Figure(data=[
            go.Bar(x=list(services), y=list(counts), 
                  marker_color=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'])
        ])
        fig_services.update_layout(
            title="🎯 Most Clicked Services",
            xaxis_title="Services",
            yaxis_title="Number of Clicks",
            height=300
        )
    else:
        fig_services = go.Figure()
    
    # 2. Category Distribution Pie Chart
    if analysis['category_distribution']:
        categories = list(analysis['category_distribution'].keys())
        values = list(analysis['category_distribution'].values())
        
        fig_categories = go.Figure(data=[
            go.Pie(labels=categories, values=values, hole=0.3)
        ])
        fig_categories.update_layout(
            title="📂 Service Category Preferences",
            height=300
        )
    else:
        fig_categories = go.Figure()
    
    # 3. User Behavior Radar Chart
    behavior_metrics = {
        'Exploration': analysis['exploration_score'] * 100,
        'Focus': analysis['focus_score'] * 100,
        'Activity': min(100, (60 / max(analysis['avg_interval'], 1)) * 20),
        'Engagement': min(100, analysis['total_clicks'] * 5),
        'Diversity': min(100, analysis['unique_nodes'] * 10)
    }
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=list(behavior_metrics.values()),
        theta=list(behavior_metrics.keys()),
        fill='toself',
        name='User Profile'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        title="🎭 User Behavior Profile",
        height=300
    )
    
    # 4. Click Timeline
    if click_history_json:
        click_history = json.loads(click_history_json)
        times = [datetime.fromisoformat(item['timestamp']) for item in click_history]
        nodes = [item['node'] for item in click_history]
        
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=times,
            y=list(range(len(times))),
            mode='markers+lines',
            text=nodes,
            marker=dict(size=10, color='#45b7d1'),
            line=dict(color='#45b7d1', width=2)
        ))
        fig_timeline.update_layout(
            title="⏰ Click Timeline",
            xaxis_title="Time",
            yaxis_title="Click Sequence",
            height=300
        )
    else:
        fig_timeline = go.Figure()
    
    # Create layout
    return html.Div([
        # Header
        html.Div([
            html.H1("📊 User Analytics Dashboard", 
                   style={"textAlign": "center", "margin": "20px 0", "color": "#333"}),
            html.P(f"Analysis based on {analysis['total_clicks']} interactions with {analysis['unique_nodes']} unique services",
                   style={"textAlign": "center", "fontSize": "16px", "color": "#666", "marginBottom": "30px"})
        ]),
        
        # Key Metrics Cards
        html.Div([
            html.Div([
                html.H3("🎯 Behavior Pattern", style={"margin": "0 0 10px 0", "color": "#333"}),
                html.H2(analysis['activity_pattern'], style={"margin": "0", "color": "#007bff"}),
                html.P(f"Avg. interval: {analysis['avg_interval']:.1f}s", style={"margin": "5px 0 0 0", "color": "#666"})
            ], className="metric-card", style={
                "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px",
                "textAlign": "center", "border": "1px solid #dee2e6", "width": "22%", "display": "inline-block", "margin": "1%"
            }),
            
            html.Div([
                html.H3("🔍 Exploration Score", style={"margin": "0 0 10px 0", "color": "#333"}),
                html.H2(f"{analysis['exploration_score']:.1%}", style={"margin": "0", "color": "#28a745"}),
                html.P(f"{analysis['unique_nodes']}/{analysis['total_clicks']} unique", style={"margin": "5px 0 0 0", "color": "#666"})
            ], className="metric-card", style={
                "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px",
                "textAlign": "center", "border": "1px solid #dee2e6", "width": "22%", "display": "inline-block", "margin": "1%"
            }),
            
            html.Div([
                html.H3("⏱️ Session Duration", style={"margin": "0 0 10px 0", "color": "#333"}),
                html.H2(f"{analysis['session_duration']:.0f}s", style={"margin": "0", "color": "#ffc107"}),
                html.P("Total active time", style={"margin": "5px 0 0 0", "color": "#666"})
            ], className="metric-card", style={
                "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px",
                "textAlign": "center", "border": "1px solid #dee2e6", "width": "22%", "display": "inline-block", "margin": "1%"
            }),
            
            html.Div([
                html.H3("🎪 Focus Score", style={"margin": "0 0 10px 0", "color": "#333"}),
                html.H2(f"{analysis['focus_score']:.1%}", style={"margin": "0", "color": "#dc3545"}),
                html.P("Repeat interactions", style={"margin": "5px 0 0 0", "color": "#666"})
            ], className="metric-card", style={
                "backgroundColor": "#f8f9fa", "padding": "20px", "borderRadius": "10px",
                "textAlign": "center", "border": "1px solid #dee2e6", "width": "22%", "display": "inline-block", "margin": "1%"
            })
        ], style={"margin": "20px 0", "textAlign": "center"}),
        
        # Charts Row 1
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_services)
            ], style={"width": "48%", "display": "inline-block", "margin": "1%"}),
            
            html.Div([
                dcc.Graph(figure=fig_categories)
            ], style={"width": "48%", "display": "inline-block", "margin": "1%"})
        ]),
        
        # Charts Row 2
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_radar)
            ], style={"width": "48%", "display": "inline-block", "margin": "1%"}),
            
            html.Div([
                dcc.Graph(figure=fig_timeline)
            ], style={"width": "48%", "display": "inline-block", "margin": "1%"})
        ]),
        
        # Predictions and Recommendations
        html.Div([
            html.H2("🔮 Predictions & Recommendations", style={"textAlign": "center", "margin": "30px 0 20px 0"}),
            
            html.Div([
                # Preferred Categories
                html.Div([
                    html.H4("📂 Predicted Preferred Categories", style={"color": "#333"}),
                    html.Ul([
                        html.Li(f"{cat}: {count} clicks ({count/analysis['total_clicks']:.1%})", 
                               style={"margin": "5px 0", "fontSize": "14px"})
                        for cat, count in analysis['preferred_categories']
                    ])
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "margin": "1%", 
                         "padding": "20px", "backgroundColor": "#e8f4fd", "borderRadius": "10px"}),
                
                # Recommendations
                html.Div([
                    html.H4("💡 Smart Recommendations", style={"color": "#333"}),
                    html.Ul([
                        html.Li(f"You seem interested in {analysis['preferred_categories'][0][0] if analysis['preferred_categories'] else 'various'} services"),
                        html.Li(f"Your {analysis['activity_pattern'].lower()} style suggests exploring connected services"),
                        html.Li(f"Consider checking services similar to {analysis['preferred_services'][0] if analysis['preferred_services'] else 'your favorites'}"),
                        html.Li("Try exploring less popular nodes for hidden gems" if analysis['exploration_score'] > 0.7 else "Focus on fewer services for deeper insights")
                    ], style={"fontSize": "14px"})
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "margin": "1%", 
                         "padding": "20px", "backgroundColor": "#f0f8e8", "borderRadius": "10px"}),
                
                # Next Steps
                html.Div([
                    html.H4("🚀 Suggested Next Steps", style={"color": "#333"}),
                    html.Ul([
                        html.Li("Explore services with high connection counts"),
                        html.Li("Check privacy policies of your favorite services"),
                        html.Li("Look for automation opportunities between your preferred categories"),
                        html.Li("Try the MCP integration for detailed privacy analysis")
                    ], style={"fontSize": "14px"})
                ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "margin": "1%", 
                         "padding": "20px", "backgroundColor": "#fef3e8", "borderRadius": "10px"})
            ])
        ])
    ])

### GRAPH EXAMPLE
# current_dir = os.getcwd()
# subfolder_path = os.path.join(current_dir, '../data/IFTTT/applications/applets_25/applets') #'/Users/pieror/Library/CloudStorage/OneDrive-Chalmers/research_chalmers/research/7_KG/data/IFTTT/applications/applets_23/applets_top30_2023')
# json_files = [os.path.join(root, file) for root, _, files in os.walk(subfolder_path) for file in files if file.endswith('.json')]
# app_categories = open_json(os.path.join(current_dir, '../data/IFTTT/app_categories/categories_services_2025.json'))

# app_list = []
# for file in json_files:
#     app = open_json(file)
#     dict_app = extract_features(app)
#     sanity_check(dict_app, file)
#     app_list.append(dict_app)

# G = create_graph(app_list, app_categories)
# pos = nx.spring_layout(G, k=2, seed=42)
# graph_info = network_metrics(G)
# export_graph_to_json(G, pos)
# draw_graph(G)

# edge_trace, annotations = create_edges_and_annotations(G, pos)
# node_trace = create_node_trace(G, pos)
# app = dash.Dash(__name__)
# app.layout = create_dash_layout(edge_trace, node_trace, annotations)

# @app.callback(
#     Output('node-info', 'children'),
#     Input('network-graph', 'clickData')
# )
# def callback(clickData):
#     return display_node_info(G, clickData, graph_info)

# if __name__ == '__main__':
#     app.run(debug=True)
