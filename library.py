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

### REQUIREMENTS FOR MCP
import asyncio
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from mcp_use import MCPAgent, MCPClient
from time import time



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
        html.H2("IFTTT Graph: Trigger → Action", style={"textAlign": "center"}),
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
        html.Div(id='node-info', style={"padding": "10px", "fontSize": "16px"}),
        
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

### MCP
async def mcp_main(service):
    await asyncio.sleep(5)  # wait for the LLM and MCP server to start
    load_dotenv()
    config = {"mcpServers": {"http": {"url": "http://localhost:8931/sse"}}}
    client = MCPClient.from_dict(config)

    llm = ChatOllama(model="llama3.1", temperature=0)
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    #service = 'IFTTT'
    query = f"""Please find the privacy policy page of {service},
                                and give me a summary of that privacy policy in a few sentences containing: 
                                - precise and well defined data types, 
                                - how data are collected, 
                                - the purpose of collection, 
                                - the security guarantees, 
                                - the usage of the data, 
                                - what's the control for the user on their data, 
                                - and what's the contact information for the user with the link to it,
                                Please give me just the final answer in a string format using "FINAL ANSWER" to start it, with bullets for each point I've asked."""

    #async for chunk in agent.astream(query):
    #    print('\nCHUNK MESSAGE:', chunk, end="", flush=True)

    result = await agent.run(query)
    
    print(f"\nResult: {result}")
    

### MCP EXAMPLE
"""
https://github.com/mcp-use/mcp-use/tree/1f1c1f7a33aaab1889c769e004fd9144047c09a3
conda activate mcp
npx @playwright/mcp@latest --port 8931 - https://github.com/microsoft/playwright-mcp (no installation needed).
ollama run llama3.1
python privacy_policies.py
"""
# if __name__ == "__main__":
#     service = 'Spotify'
#     start = time()
#     asyncio.run(mcp_main(service))
#     end = time()
#     print(f"Execution time: {end - start:.2f} seconds")