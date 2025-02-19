import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, no_update, ctx
import pandas as pd
import plotly.graph_objects as go
import math

# ============================
# First Chart: "Was Ross Actually F.I.N.E?"
# ============================

# Load data for first chart from Friends ICA 2.xlsx
file_path1 = "D:/NMIMS SOD/YEAR 3 NMIMS/data design/trial 4/Friends ICA 2.xlsx"
xls = pd.ExcelFile(file_path1)
dialogue_sentiments_df = xls.parse('Dialogue Sentiments')
sentence_types_df = xls.parse('Sentence Types')
modality_pauses_df = xls.parse('Modality & Pauses')

main_characters = ["Ross", "Rachel", "Joey", "Chandler", "Monica", "Phoebe", "Frank Jr."]

# Initialize global counters for first chart
filler_counts = {"Fine": 0, "Oh": 0, "Okay": 0}
progress = 0

def get_progress_bar(value):
    if value == 0:
        return html.Div()
    return html.Div(
        children=[html.Div(style={
            'width': f'{value}%', 
            'height': '5px', 
            'backgroundColor': '#FF9800', 
            'transition': 'width 0.5s'
        })],
        style={'width': '100%', 'backgroundColor': '#ddd', 'borderRadius': '5px', 'marginTop': '2px'}
    )

# ============================
# Second Chart: Sankey Diagram
# ============================

# Load data for second chart from Ross_Fight_Scenes_Updated_v4_Sorted.xlsx
file_path2 = "Ross_Fight_Scenes_Updated_v4_Sorted.xlsx"
df_sankey = pd.read_excel(file_path2)
df_sankey.dropna(subset=["Location", "Season", "Character_Fought_With"], inplace=True)

ordered_locations = [
    "Central Perk",
    "Joey's apartment",
    "Monica's apartment",
    "Ross's apartment",
    "Other",
    "A Restaurant",
    "Class of '91 reunion",
    "The theatre",
    "The breakfast buffet",
    "The hospital"
]

seasons_sankey = sorted(df_sankey["Season"].unique())
locations_sankey = sorted(
    df_sankey["Location"].unique(),
    key=lambda x: ordered_locations.index(x) if x in ordered_locations else 999
)
characters_sankey = sorted(df_sankey["Character_Fought_With"].unique())

# ============================
# Shared Helper Functions
# ============================
def normalize_location_id(loc):
    return loc.replace("’", "'").strip().lower()

def hex_to_rgba(hex_color, opacity):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{opacity})"

def darken_color(hex_color, factor):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))
    return f"#{r:02x}{g:02x}{b:02x}"

# New color palette for location nodes (for the Sankey diagram)
color_options = [
    "#00009E",  # Deep blue
    "#FFDC00",  # Yellow
    "#9A0006",  # Dark red
    "#A3DBFE",  # Light blue
    "#A5714F",  # Brownish
    "#6B9256",  # Olive green
    "#F0AE75",  # Peach
    "#593178"   # Dark purple
]

location_color_map = {
    normalize_location_id(loc): color_options[i % len(color_options)]
    for i, loc in enumerate(ordered_locations)
}

def build_sankey(filtered_df):
    # Aggregate flows for Season → Location
    df_sl = filtered_df.groupby(["Season", "Location"]).size().reset_index(name="value")
    # Aggregate flows for Location → Character
    df_lc = filtered_df.groupby(["Location", "Character_Fought_With"]).size().reset_index(name="value")
    
    season_nodes = sorted(filtered_df["Season"].unique())
    location_nodes = sorted(
        filtered_df["Location"].unique(),
        key=lambda x: ordered_locations.index(x) if x in ordered_locations else 999
    )
    character_nodes = sorted(filtered_df["Character_Fought_With"].unique())
    
    node_labels = season_nodes + location_nodes + character_nodes
    # Set season and character nodes to light grey.
    season_color = "#D3D3D3"       
    character_color = "#D3D3D3"      
    location_colors = [location_color_map.get(normalize_location_id(loc), "#888") for loc in location_nodes]
    node_colors = [season_color] * len(season_nodes) + location_colors + [character_color] * len(character_nodes)
    
    node_to_index = {label: i for i, label in enumerate(node_labels)}
    
    sl_source, sl_target, sl_value, sl_label, sl_link_color, sl_customdata = [], [], [], [], [], []
    for _, row in df_sl.iterrows():
        s = row["Season"]
        l = row["Location"]
        v = row["value"]
        sl_source.append(node_to_index[s])
        sl_target.append(node_to_index[l])
        sl_value.append(v)
        sl_label.append(f"{s} → {l}: {v}")
        base_color = location_color_map.get(normalize_location_id(l), "#888")
        sl_link_color.append(hex_to_rgba(base_color, 0.3))
        sl_customdata.append(base_color)
    
    lc_source, lc_target, lc_value, lc_label, lc_link_color, lc_customdata = [], [], [], [], [], []
    for _, row in df_lc.iterrows():
        l = row["Location"]
        c = row["Character_Fought_With"]
        v = row["value"]
        lc_source.append(node_to_index[l])
        lc_target.append(node_to_index[c])
        lc_value.append(v)
        lc_label.append(f"{l} → {c}: {v}")
        base_color = location_color_map.get(normalize_location_id(l), "#888")
        lc_link_color.append(hex_to_rgba(base_color, 0.3))
        lc_customdata.append(base_color)
    
    source = sl_source + lc_source
    target = sl_target + lc_target
    value  = sl_value + lc_value
    link_labels = sl_label + lc_label
    link_colors = sl_link_color + lc_link_color
    link_customdata = sl_customdata + lc_customdata
    
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
            hovertemplate="<extra></extra>",
            hoverlabel=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color="rgba(0,0,0,0)"))
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            label=link_labels,
            color=link_colors,
            customdata=link_customdata,
            hovertemplate="<extra></extra>",
            hoverlabel=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color="rgba(0,0,0,0)"))
        )
    )])
    fig.update_layout(title_text="", font_size=10, height=600, width=800)
    return fig

# ============================
# Combined App Layout
# ============================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div([
    # Logo in the top right corner
    html.Img(src="/assets/logo.jpg", style={'position': 'absolute', 'right': '40px', 'width': '150px'}),
    
    # First chart section (Line chart with progress bar)
    html.Div([
        html.H1("Part 2: Was Ross Actually F.I.N.E?", style={'text-align': 'center', 'margin-top': '150px', 'margin-bottom': '10px'}),
        dcc.Markdown(
            """
            Ross might insist he's fine, but his words tell a different story—as we discovered in Part 1.<br>
            And what about the other characters? Could their emotions be influencing Ross's behavior?<br>
            Let’s find out.
            """,
            dangerously_allow_html=True,
            style={"textAlign": "center", "fontSize": "16px", "lineHeight": "1.2", "margin": "20px"}
        ),
        html.Video(src="/assets/ross chaos.mp4", autoPlay=True, loop=True, muted=True,
                   style={'display': 'block', 'margin': 'auto', 'opacity': '0.5', 'width': '500px', 'height': '400px', 'margin-bottom': '10px'}),
        html.Div("*animation made in excel*", style={'text-align': 'center', 'font-size': 'x-small', 'margin-bottom': '20px'}),
        html.Hr(style={'width': '80%', 'margin': 'auto', 'border': '2px solid #ccc'}),
        html.H2("How Were the Others Feeling?", style={'text-align': 'center', 'margin-bottom': '10px', 'margin-top': '10px', 'fontFamily': 'Gabriel Weiss Friends'}),
        dcc.Dropdown(
            id='character-dropdown1',
            options=[{"label": char, "value": char} for char in main_characters],
            value="Ross",
            clearable=False,
            style={'font-size': '12px', 'width': '50%', 'margin': 'auto', 'margin-bottom': '20px'}
        ),
        # New text added after the first chart dropdown:
        html.P(
            "Notice how Ross’s straightforward speech (declarative) is punctuated by pauses that hint at turbulent emotional changes.",
            style={'textAlign': 'center', 'fontSize': '16px', 'margin-bottom': '20px'}
        ),
        dcc.Graph(id='combined-visualization1', style={'transition': 'opacity 0.3s'}),
        html.Div(id='filler-count-display1', style={'text-align': 'center', 'font-size': '20px', 'margin-top': '20px'}),
        html.Div(id='progress-bar-container1', children=get_progress_bar(progress)),
        html.P(id="instruction-text1", style={'text-align': 'center', 'margin-top': '10px'}),
        html.Hr(style={'width': '80%', 'margin': 'auto', 'border': '2px solid #ccc'})
    ], style={'margin-bottom': '50px'}),
    
    # Second chart section (Sankey Diagram)
    html.Div([
        html.Div([
            html.H1("Did Ross's Behavior Change Over Time?", style={"textAlign": "center"}),
            html.Div("*use the dropdowns to see with whom did ross argue the most*", 
                     style={"textAlign": "center", "fontStyle": "italic", "marginBottom": "20px"}),
            dcc.Dropdown(
                id="location-dropdown2",
                options=[{"label": loc, "value": loc} for loc in locations_sankey],
                value=None,
                multi=False,
                placeholder="Select Location",
                style={'width': '50%', 'margin': 'auto', 'margin-bottom': '20px'}
            ),
            dcc.Dropdown(
                id="character-dropdown2",
                options=[{"label": char, "value": char} for char in characters_sankey],
                value=None,
                multi=False,
                placeholder="Select Character",
                style={'width': '50%', 'margin': 'auto', 'margin-bottom': '20px'}
            ),
            html.Div(
                html.Button("Reset Filters", id="reset-button2", n_clicks=0),
                style={"textAlign": "center", "margin": "10px"}
            )
        ], style={"textAlign": "center"}),
        # Only the Sankey diagram graph is pushed to the right.
        html.Div(
            dcc.Graph(
                id="sankey-diagram2",
                config={"displayModeBar": False, "scrollZoom": False}
            ),
            style={"width": "60%", "marginLeft": "400px"}
        ),
        # New texts for the second chart added after the graph:
        html.P(
            "Who would have expected it? The dropdowns confirm Rachel is the one Ross ended up arguing with the most at almost all of the locations.",
            style={'textAlign': 'center', 'fontSize': '16px', 'margin-top': '20px'}
        ),
        html.H2(
            "The one with the usability",
            style={'textAlign': 'center', 'fontFamily': 'Gabriel Weiss Friends', 'margin-top': '30px', 'margin-bottom': '10px', 'fontSize': '40px'}
        ),
        html.P(
            "Visual mapping of the TV series enables us to study real-life behavior, providing a powerful tool for recruiters assessing interviews, husbands discerning if 'I'm fine' truly means fine, and designers structuring more user-friendly interviews by recognizing awkward speech patterns.",
            style={'textAlign': 'center', 'fontSize': '14px', 'margin-bottom': '20px', 'border': '2px solid #ccc', 'margin-bottom': '100px'}
        ),
        html.P(
            "The transcript was sourced from the site: https://www.livesinabox.com/friends/1002.shtml. | Dataset was taken from: https://www.kaggle.com/",
            style={'textAlign': 'center', 'fontSize': '14px', 'margin-bottom': '20px', 'margin-bottom': '100px', 'opacity': '0.5'}
        )
    ])
], style={"fontFamily": "Satoshi, sans-serif", "position": "relative"})

# ============================
# Callbacks for First Chart
# ============================
@app.callback(
    Output('combined-visualization1', 'figure'),
    Input('character-dropdown1', 'value')
)
def update_combined_chart(character):
    df_sentiments = dialogue_sentiments_df[dialogue_sentiments_df['person'] == character].reset_index()
    df_sentence_types = sentence_types_df[sentence_types_df['person'] == character].reset_index()
    df_modality = modality_pauses_df[modality_pauses_df['person'] == character].reset_index()

    df_sentiments = df_sentiments.iloc[:301]
    df_sentence_types = df_sentence_types.iloc[:301]
    df_modality = df_modality.iloc[:301]

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=df_sentence_types.index, y=df_sentence_types['declarative'], mode='lines',
                             line=dict(dash='dash', color='#00009E'), name='Declarative'))
    fig.add_trace(go.Scatter(x=df_sentence_types.index, y=df_sentence_types['interrogative'], mode='lines',
                             line=dict(dash='dot', color='#FFDC00'), name='Interrogative'))
    fig.add_trace(go.Scatter(x=df_sentence_types.index, y=df_sentence_types['exclamatory'], mode='lines',
                             line=dict(color='#9A0006'), name='Exclamatory'))
    
    for column, color in zip(['Forced positivity', 'Discomfort', 'Suppressed frustration'],
                              ['#FFF580', '#42A2D6', '#FF4238']):
        fig.add_trace(go.Scatter(
            x=df_sentiments.index,
            y=df_sentiments[column],
            mode='lines',
            fill='tozeroy',
            line=dict(width=0.5, color=color),
            name=column,
            hoverinfo='text',
            text=df_sentiments['dialogue'].fillna("No dialogue available")
        ))
    
    pause_indices = df_modality[df_modality['Pauses'] == 1].index
    fig.add_trace(go.Scatter(
        x=pause_indices,
        y=[0.5] * len(pause_indices),
        mode='markers',
        marker=dict(color='black', size=6, symbol='square'),
        name='Pauses'
    ))

    fig.update_layout(template='plotly_white', xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
    return fig

@app.callback(
    [Output("filler-count-display1", "children"),
     Output("progress-bar-container1", "children"),
     Output("instruction-text1", "children")],
    [Input("character-dropdown1", "value"),
     Input("combined-visualization1", "clickData")]
)
def update_filler_progress_instruction(character, clickData):
    global filler_counts, progress

    if ctx.triggered_id == "character-dropdown1":
        if character != "Ross":
            progress = 0
            filler_counts = {"Fine": 0, "Oh": 0, "Okay": 0}
            return "", get_progress_bar(0), "Switch to Ross to check his so not fine filler words."
        return (f"Filler Counts: Fine - {filler_counts['Fine']}, Oh - {filler_counts['Oh']}, "
                f"Okay - {filler_counts['Okay']}"), get_progress_bar(progress), "*Click on a dialogue to track filler words. The progress bar moves only when new fillers are detected.*"

    if clickData and "points" in clickData and "text" in clickData["points"][0]:
        clicked_dialogue = clickData["points"][0]["text"]
        filtered_df = dialogue_sentiments_df[
            (dialogue_sentiments_df['person'] == character) &
            (dialogue_sentiments_df['dialogue'] == clicked_dialogue)
        ]
        new_filler_detected = False
        if not filtered_df.empty:
            for filler in ["Fine", "Oh", "Okay"]:
                previous_count = filler_counts[filler]
                filler_counts[filler] += int(filtered_df[filler].fillna(0).sum())
                if filler_counts[filler] > previous_count:
                    new_filler_detected = True
        
        if new_filler_detected:
            progress = min(progress + 10, 100)
    count_display = f"Filler Counts: Fine - {filler_counts['Fine']}, Oh - {filler_counts['Oh']}, Okay - {filler_counts['Okay']}"
    return count_display, get_progress_bar(progress), "*Click on a dialogue to track filler words. The progress bar moves only when new fillers are detected.*"

# ============================
# Callbacks for Second Chart (Sankey)
# ============================
@app.callback(
    Output("sankey-diagram2", "figure"),
    [Input("location-dropdown2", "value"),
     Input("character-dropdown2", "value"),
     Input("sankey-diagram2", "hoverData")]
)
def update_sankey_chart(selected_location, selected_character, hoverData):
    filtered_df = df_sankey.copy()
    if selected_location:
        filtered_df = filtered_df[filtered_df["Location"] == selected_location]
    if selected_character:
        filtered_df = filtered_df[filtered_df["Character_Fought_With"] == selected_character]
    fig = build_sankey(filtered_df)
    
    if hoverData and "points" in hoverData and len(hoverData["points"]) > 0:
        point = hoverData["points"][0]
        if "source" in point:
            hovered_index = point.get("pointNumber")
            if (hovered_index is not None and isinstance(hovered_index, int) and 
                hovered_index < len(fig.data[0].link.color)):
                link_colors = list(fig.data[0].link.color)
                base_color = fig.data[0].link.customdata[hovered_index]
                link_colors[hovered_index] = hex_to_rgba(base_color, 0.8)
                fig.data[0].link.color = link_colors
        else:
            hovered_index = point.get("pointNumber")
            if (hovered_index is not None and isinstance(hovered_index, int) and 
                hovered_index < len(fig.data[0].node.color)):
                node_colors = list(fig.data[0].node.color)
                base_color = node_colors[hovered_index]
                dark_hex = darken_color(base_color, 0.8)
                node_colors[hovered_index] = hex_to_rgba(dark_hex, 0.8)
                fig.data[0].node.color = node_colors
    return fig

@app.callback(
    [Output("location-dropdown2", "value"),
     Output("character-dropdown2", "value")],
    Input("reset-button2", "n_clicks")
)
def reset_filters2(n_clicks):
    if n_clicks and n_clicks > 0:
        return None, None
    return no_update, no_update

# ============================
# Run the App
# ============================
if __name__ == '__main__':
    app.run_server(debug=True)
