from library import *


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
app = Dash(__name__)
app.layout = create_dash_layout(edge_trace, node_trace, annotations)


# MCP
# TODO - integrate the interface with the MCP. When the user clicks on a node, 
# the app should call the MCP and get the privacy policy of that app,
# and display it in the node info section. The MCP should be able to handle the
# request and return the privacy policy in a readable format.
# ALTERNATIVE - STATIC PRIVACY POLICY PREVIOUSLY STORED


@app.callback(
    Output('node-info', 'children'),
    Input('network-graph', 'clickData')
)
def callback(clickData):
    return display_node_info(G, clickData, graph_info)

if __name__ == '__main__':
    app.run(debug=True)
