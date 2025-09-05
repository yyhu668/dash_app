# IFTTT Data Transparency Knowledge Graph

https://ifttt-knowledge-graph.onrender.com/

## Introduction
IFTTT (If This Then That) connects various online services through applets that automate tasks across platforms. This project visualizes these connections as a knowledge graph, aiming to reveal hidden data flows, service interactions, and privacy implications inherent in digital automation networks.

## System Architecture
The system employs a layered design comprising scraping, processing, visualization, and analytics components. IFTTT applets are harvested using a GraphQL-based approach, then transformed into a directed graph representing services and their interactions. The dashboard is built with Dash and Plotly, enabling dynamic and interactive visualization of the knowledge graph.

## Visualization & User Experience
Nodes in the graph are color-coded by service category and sized according to their popularity. Directed edges illustrate the flow of data and automation triggers. Users can interactively click nodes to view detailed information and summaries of privacy policies. The system also tracks user interactions, including timestamps, clicks, and performance metrics, to enhance the experience and gather usage insights.

## Advanced Analytics
The platform includes behavioral classification of users into Fast Explorers, Steady Browsers, and Careful Researchers based on their interaction patterns. Metrics such as Exploration Score and Focus Score quantify navigation behavior. Radar charts visualize these metrics, while predictive recommendations suggest relevant applets and services. Statistical charts including bar charts, pie charts, and timelines provide additional insights into usage and trends.

### Interface
#### Visualise your IFTTT applications
In this dashboard the applications showed are taken from [IFTTT Top Applets 2025](https://ifttt.com/explore/top-applets-on-ifttt)
You can visualise an applciation by clicking to a node. Each node represents a service where IFTTT is connected to run the application.
The common application structure is IF THIS THEN THAT:
1) IF enter in the room THEN turn on the lights
2) IF like new video on Youtube THEN add on Spotify playlist (IFTTT App)[https://ifttt.com/applets/pc6CeRjs-add-songs-from-videos-you-like-to-a-spotify-playlist]
3) IF 7am THEN send me weather forecasting (IFTTT App)[https://ifttt.com/applets/YY9Mqgw5-get-the-weather-forecast-every-day-at-7-00-am]

#### Privacy Policy
In IFTTT, while running an application, it is assumed that the user is subscribed to the services connected.
Thus, when clicking a node, it is possible to visualise a summary of the privacy policy of that node.

## Applications
This platform serves multiple use cases: researchers can analyze the digital automation ecosystem and privacy risks; businesses can leverage market intelligence and integration opportunities; educators can teach visualization and analytics concepts through interactive exploration of real-world data flows.

## Future Directions
Planned extensions include integrating the MCP framework for privacy auditing, expanding scraping to cover more applets, enabling cross-platform interoperability with services like Zapier and Power Automate, conducting longitudinal studies of automation trends, and incorporating large language models to support natural language queries over the knowledge graph.
