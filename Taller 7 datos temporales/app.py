import dash
from dash import dcc, html, Input, Output, callback_context
import pandas as pd
import plotly.express as px

# 1. Cargar los datos limpios
df = pd.read_csv('ML-Dataset_Clean.csv')
df['OrderDate'] = pd.to_datetime(df['OrderDate'])

app = dash.Dash(__name__)

# 2. Diseño de la Interfaz
app.layout = html.Div([
    html.H1("Dashboard de Ventas y Operaciones", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Selecciona el Año:"),
        dcc.Dropdown(
            id='year-filter',
            options=[{'label': i, 'value': i} for i in sorted(df['OrderDate'].dt.year.unique())],
            value=df['OrderDate'].dt.year.max(),
            clearable=False
        ),
        html.Button('Resetear Filtro de Categoría', id='reset-btn', n_clicks=0, style={'marginTop': '10px'})
    ], style={'width': '30%', 'margin': 'auto', 'padding': '20px', 'textAlign': 'center'}),

    html.Div([
        html.Div([
            dcc.Graph(id='heatmap-ciclico')
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='barras-trimestre')
        ], style={'width': '48%', 'display': 'inline-block'}),
    ]),

    html.Div([
        dcc.Graph(id='treemap-status')
    ], style={'marginTop': '20px'})
])

# 3. Lógica de Interactividad
@app.callback(
    [Output('heatmap-ciclico', 'figure'),
     Output('barras-trimestre', 'figure'),
     Output('treemap-status', 'figure')],
    [Input('year-filter', 'value'),
     Input('treemap-status', 'clickData'),
     Input('reset-btn', 'n_clicks')]
)
def update_graphs(selected_year, clickData, n_clicks):
    # Determinar qué disparó el callback
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Filtrar primero por año
    filtered_df = df[df['OrderDate'].dt.year == selected_year]
    
    # Lógica de filtrado por categoría desde el Treemap
    selected_category = None
    if trigger_id == 'treemap-status' and clickData:
        # Extraemos la categoría del clic. En Treemaps, el último nivel suele estar en 'label' o 'pointNumber'
        # Dependiendo de dónde se haga clic, buscamos la categoría
        if 'entry' in clickData['points'][0]:
            selected_category = clickData['points'][0]['label']
    
    # Si se presionó reset, limpiamos la selección
    if trigger_id == 'reset-btn':
        selected_category = None

    # --- GRÁFICO 1: Heatmap (No se afecta por categoría para mantener contexto general) ---
    df_heat = filtered_df.groupby(['OrderDayName', 'RegionName']).size().reset_index(name='Total')
    fig1 = px.density_heatmap(
        df_heat, x="RegionName", y="OrderDayName", z="Total",
        title=f"Densidad de Pedidos en {selected_year}",
        color_continuous_scale='Viridis'
    )

    # --- GRÁFICO 2: Barras por Trimestre (EL QUE SE ENFOCA) ---
    df_trim = filtered_df.copy()
    
    # Si hay una categoría seleccionada, filtramos el gráfico de barras
    title_barras = "Ventas Totales por Cuarto"
    if selected_category in df['CategoryName'].unique():
        df_trim = df_trim[df_trim['CategoryName'] == selected_category]
        title_barras = f"Ventas de {selected_category} por Cuarto"

    df_trim_grouped = df_trim.groupby(['OrderQuarter', 'CategoryName'])['PerUnitPrice'].sum().reset_index()
    
    fig2 = px.bar(
        df_trim_grouped, x="OrderQuarter", y="PerUnitPrice", color="CategoryName",
        title=title_barras,
        barmode="group"
    )

    # --- GRÁFICO 3: Treemap ---
    fig3 = px.treemap(
        filtered_df, path=['Status', 'CategoryName'], values='OrderItemQuantity',
        title="Distribución de Estatus y Categorías"
    )

    return fig1, fig2, fig3

if __name__ == '__main__':
    app.run(debug=True)