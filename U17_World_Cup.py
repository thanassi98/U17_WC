import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

# Cargar los datos
df = pd.read_excel("data/u17_world_cup_full_sofascore.xlsx")

# Preparar los datos
df['total_goals'] = df['homeScore.display'] + df['awayScore.display']
df['match_label'] = df['homeTeam.name'] + ' vs ' + df['awayTeam.name']

# Calcular estadísticas por equipo
def get_team_stats():
    home_stats = df.groupby('homeTeam.name').agg({
        'homeScore.display': 'sum',
        'awayScore.display': 'sum',
        'winnerCode': lambda x: (x == 1).sum(),
        'id': 'count',
        'homeRedCards': 'sum'
    }).rename(columns={
        'homeScore.display': 'goals_for',
        'awayScore.display': 'goals_against',
        'winnerCode': 'wins',
        'id': 'matches',
        'homeRedCards': 'red_cards'
    })
    
    away_stats = df.groupby('awayTeam.name').agg({
        'awayScore.display': 'sum',
        'homeScore.display': 'sum',
        'winnerCode': lambda x: (x == 2).sum(),
        'id': 'count',
        'awayRedCards': 'sum'
    }).rename(columns={
        'awayScore.display': 'goals_for',
        'homeScore.display': 'goals_against',
        'winnerCode': 'wins',
        'id': 'matches',
        'awayRedCards': 'red_cards'
    })
    
    # Combinar estadísticas
    all_teams = list(set(df['homeTeam.name'].unique().tolist() + df['awayTeam.name'].unique().tolist()))
    team_stats = []
    
    for team in all_teams:
        home_data = home_stats.loc[team] if team in home_stats.index else pd.Series({'goals_for': 0, 'goals_against': 0, 'wins': 0, 'matches': 0, 'red_cards': 0})
        away_data = away_stats.loc[team] if team in away_stats.index else pd.Series({'goals_for': 0, 'goals_against': 0, 'wins': 0, 'matches': 0, 'red_cards': 0})
        
        # Calcular empates
        home_draws = df[(df['homeTeam.name'] == team) & (df['winnerCode'] == 3)].shape[0]
        away_draws = df[(df['awayTeam.name'] == team) & (df['winnerCode'] == 3)].shape[0]
        
        # Calcular derrotas
        home_losses = df[(df['homeTeam.name'] == team) & (df['winnerCode'] == 2)].shape[0]
        away_losses = df[(df['awayTeam.name'] == team) & (df['winnerCode'] == 1)].shape[0]
        
        team_stats.append({
            'Equipo': team,
            'PJ': int(home_data['matches'] + away_data['matches']),
            'PG': int(home_data['wins'] + away_data['wins']),
            'PE': int(home_draws + away_draws),
            'PP': int(home_losses + away_losses),
            'GF': int(home_data['goals_for'] + away_data['goals_for']),
            'GC': int(home_data['goals_against'] + away_data['goals_against']),
            'DG': int((home_data['goals_for'] + away_data['goals_for']) - (home_data['goals_against'] + away_data['goals_against'])),
            'Pts': int((home_data['wins'] + away_data['wins']) * 3 + (home_draws + away_draws)),
            'Tarjetas Rojas': int(home_data['red_cards'] + away_data['red_cards'])
        })
    
    return pd.DataFrame(team_stats).sort_values('Pts', ascending=False)

team_stats_df = get_team_stats()

# Inicializar la app con Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Layout de la aplicación
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("⚽ Dashboard Mundial Sub-17", className="text-center mb-4 mt-3"),
            html.Hr()
        ])
    ]),
    
    dcc.Tabs(id='tabs', value='tab-overview', children=[
        dcc.Tab(label='📊 Vista General', value='tab-overview'),
        dcc.Tab(label='🏆 Tabla de Posiciones', value='tab-standings'),
        dcc.Tab(label='📈 Estadísticas', value='tab-stats'),
        dcc.Tab(label='🔍 Análisis Detallado', value='tab-detailed'),
        dcc.Tab(label='🔥 Heatmaps', value='tab-heatmaps'),
        dcc.Tab(label='📝 Todos los Partidos', value='tab-matches')
    ]),
    
    html.Div(id='tab-content', className="mt-4")
], fluid=True)

@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'tab-overview':
        # Estadísticas generales
        total_matches = len(df)
        total_goals = df['total_goals'].sum()
        avg_goals = df['total_goals'].mean()
        total_red_cards = df['homeRedCards'].sum() + df['awayRedCards'].sum()
        
        # Gráficos de resumen
        fig_goals_dist = px.histogram(df, x='total_goals', nbins=10,
                                     title='Distribución de Goles por Partido',
                                     labels={'total_goals': 'Total de Goles', 'count': 'Cantidad de Partidos'})
        
        fig_round_goals = df.groupby('roundInfo.name')['total_goals'].mean().reset_index()
        fig_round_goals_chart = px.bar(fig_round_goals, x='roundInfo.name', y='total_goals',
                                      title='Promedio de Goles por Ronda',
                                      labels={'total_goals': 'Promedio de Goles', 'roundInfo.name': 'Ronda'})
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total de Partidos", className="card-title"),
                            html.H2(f"{total_matches}", className="text-primary")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Total de Goles", className="card-title"),
                            html.H2(f"{int(total_goals)}", className="text-success")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Promedio de Goles/Partido", className="card-title"),
                            html.H2(f"{avg_goals:.2f}", className="text-info")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Tarjetas Rojas", className="card-title"),
                            html.H2(f"{int(total_red_cards)}", className="text-danger")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_goals_dist)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=fig_round_goals_chart)
                ], width=6)
            ])
        ])
    
    elif tab == 'tab-standings':
        # Tabla de posiciones
        fig_standings = go.Figure(data=[go.Bar(
            x=team_stats_df.head(15)['Equipo'],
            y=team_stats_df.head(15)['Pts'],
            text=team_stats_df.head(15)['Pts'],
            textposition='outside',
            marker_color='lightblue'
        )])
        fig_standings.update_layout(title='Top 15 Equipos por Puntos',
                                   xaxis_title='Equipo',
                                   yaxis_title='Puntos',
                                   height=500)
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Tabla de Posiciones Completa"),
                    dash_table.DataTable(
                        data=team_stats_df.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in team_stats_df.columns],
                        style_cell={'textAlign': 'center'},
                        style_data_conditional=[
                            {
                                'if': {'row_index': 0},
                                'backgroundColor': 'gold',
                                'color': 'black',
                            },
                            {
                                'if': {'row_index': 1},
                                'backgroundColor': 'silver',
                                'color': 'black',
                            },
                            {
                                'if': {'row_index': 2},
                                'backgroundColor': '#CD7F32',
                                'color': 'white',
                            }
                        ],
                        page_size=20
                    )
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_standings)
                ], width=12)
            ])
        ])
    
    elif tab == 'tab-stats':
        # Mejores goleadores (equipos)
        top_scorers = team_stats_df.nlargest(10, 'GF')[['Equipo', 'GF', 'GC', 'DG']]
        
        fig_scorers = px.bar(top_scorers, x='Equipo', y=['GF', 'GC'],
                            title='Top 10 Equipos Goleadores',
                            labels={'value': 'Goles', 'variable': 'Tipo'},
                            barmode='group')
        
        # Efectividad (puntos por partido)
        team_stats_df['Efectividad'] = team_stats_df['Pts'] / team_stats_df['PJ']
        top_effective = team_stats_df.nlargest(10, 'Efectividad')[['Equipo', 'Efectividad', 'PJ']]
        
        fig_effectiveness = px.scatter(top_effective, x='PJ', y='Efectividad', size='Efectividad',
                                     text='Equipo', title='Efectividad (Puntos por Partido)',
                                     labels={'PJ': 'Partidos Jugados', 'Efectividad': 'Puntos por Partido'})
        fig_effectiveness.update_traces(textposition='top center')
        
        # Partidos con más goles
        top_goals_matches = df.nlargest(10, 'total_goals')[['match_label', 'total_goals', 'homeScore.display', 'awayScore.display']]
        
        fig_top_matches = px.bar(top_goals_matches, x='match_label', y='total_goals',
                                title='Partidos con Más Goles',
                                labels={'total_goals': 'Total de Goles', 'match_label': 'Partido'})
        fig_top_matches.update_xaxes(tickangle=-45)
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_scorers)
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=fig_effectiveness)
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_top_matches)
                ], width=12)
            ])
        ])
    
    elif tab == 'tab-detailed':
        # Análisis por ronda
        rounds_analysis = df.groupby('roundInfo.name').agg({
            'total_goals': 'sum',
            'id': 'count',
            'homeRedCards': 'sum',
            'awayRedCards': 'sum'
        }).reset_index()
        rounds_analysis['total_red_cards'] = rounds_analysis['homeRedCards'] + rounds_analysis['awayRedCards']
        rounds_analysis['goals_per_match'] = rounds_analysis['total_goals'] / rounds_analysis['id']
        
        # Gráfico de análisis por ronda
        fig_rounds = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Goles por Ronda', 'Partidos por Ronda', 
                          'Tarjetas Rojas por Ronda', 'Promedio Goles/Partido por Ronda')
        )
        
        fig_rounds.add_trace(
            go.Bar(x=rounds_analysis['roundInfo.name'], y=rounds_analysis['total_goals'], name='Goles'),
            row=1, col=1
        )
        
        fig_rounds.add_trace(
            go.Bar(x=rounds_analysis['roundInfo.name'], y=rounds_analysis['id'], name='Partidos'),
            row=1, col=2
        )
        
        fig_rounds.add_trace(
            go.Bar(x=rounds_analysis['roundInfo.name'], y=rounds_analysis['total_red_cards'], name='T. Rojas'),
            row=2, col=1
        )
        
        fig_rounds.add_trace(
            go.Scatter(x=rounds_analysis['roundInfo.name'], y=rounds_analysis['goals_per_match'], 
                      mode='lines+markers', name='Promedio'),
            row=2, col=2
        )
        
        fig_rounds.update_layout(height=700, showlegend=False, title_text="Análisis Detallado por Ronda")
        
        # Distribución de resultados
        results = []
        for _, row in df.iterrows():
            if row['winnerCode'] == 1:
                results.append('Victoria Local')
            elif row['winnerCode'] == 2:
                results.append('Victoria Visitante')
            else:
                results.append('Empate')
        
        results_df = pd.DataFrame({'Resultado': results})
        fig_results = px.pie(results_df, names='Resultado', title='Distribución de Resultados')
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_rounds)
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig_results)
                ], width=6),
                dbc.Col([
                    html.H4("Estadísticas Adicionales"),
                    html.Hr(),
                    html.P(f"🏟️ Partidos con penales: {df['homeScore.penalties'].notna().sum() + df['awayScore.penalties'].notna().sum()}"),
                    html.P(f"⏱️ Tiempo de descuento promedio (1er tiempo): {df['time.injuryTime1'].mean():.1f} min"),
                    html.P(f"⏱️ Tiempo de descuento promedio (2do tiempo): {df['time.injuryTime2'].mean():.1f} min"),
                    html.P(f"📊 Goles en primer tiempo: {df['homeScore.period1'].sum() + df['awayScore.period1'].sum():.0f}"),
                    html.P(f"📊 Goles en segundo tiempo: {df['homeScore.period2'].sum() + df['awayScore.period2'].sum():.0f}"),
                    html.Hr(),
                    html.H5("Datos Curiosos:"),
                    html.P(f"🎯 Mayor goleada: {df.loc[df['total_goals'].idxmax(), 'match_label']} ({df['total_goals'].max()} goles)"),
                    html.P(f"🔴 Equipo con más tarjetas rojas: {team_stats_df.loc[team_stats_df['Tarjetas Rojas'].idxmax(), 'Equipo']} ({team_stats_df['Tarjetas Rojas'].max():.0f} tarjetas)")
                ], width=6)
            ])
        ])
    
    elif tab == 'tab-heatmaps':
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🔥 Análisis con Heatmaps", className="mb-4"),
                    html.Hr()
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Selecciona el tipo de Heatmap:", className="fw-bold"),
                    dcc.Dropdown(
                        id='heatmap-dropdown',
                        options=[
                            {'label': '⚔️ Enfrentamientos Directos (Head to Head)', 'value': 'h2h'},
                            {'label': '📈 Rendimiento por Ronda', 'value': 'rounds'},
                            {'label': '⏱️ Distribución de Goles por Período', 'value': 'goals_period'},
                            {'label': '📊 Matriz de Correlación', 'value': 'correlation'},
                            {'label': '🏠 Local vs Visitante', 'value': 'home_away'},
                            {'label': '🎯 Efectividad Goleadora', 'value': 'goals_efficiency'}
                        ],
                        value='h2h',
                        clearable=False,
                        style={'marginBottom': '20px'}
                    )
                ], width=6),
                dbc.Col([
                    html.Div(id='heatmap-description', className="alert alert-info")
                ], width=6)
            ]),
            
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-heatmap",
                        type="default",
                        children=html.Div(id='heatmap-content')
                    )
                ], width=12)
            ])
        ])
    
    elif tab == 'tab-matches':
        # Todos los partidos con filtros
        matches_display = df[['homeTeam.name', 'homeScore.display', 'awayScore.display', 
                             'awayTeam.name', 'roundInfo.name', 'status.description']].copy()
        matches_display.columns = ['Local', 'Goles Local', 'Goles Visitante', 'Visitante', 'Ronda', 'Estado']
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Todos los Partidos del Torneo"),
                    html.Hr(),
                    dash_table.DataTable(
                        data=matches_display.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in matches_display.columns],
                        filter_action="native",
                        sort_action="native",
                        page_size=20,
                        style_cell={'textAlign': 'center'},
                        style_data_conditional=[
                            {
                                'if': {
                                    'filter_query': '{Goles Local} > {Goles Visitante}',
                                    'column_id': 'Local'
                                },
                                'backgroundColor': 'lightgreen',
                                'color': 'black',
                            },
                            {
                                'if': {
                                    'filter_query': '{Goles Visitante} > {Goles Local}',
                                    'column_id': 'Visitante'
                                },
                                'backgroundColor': 'lightgreen',
                                'color': 'black',
                            }
                        ]
                    )
                ], width=12)
            ])
        ])

@app.callback(
    [Output('heatmap-content', 'children'),
     Output('heatmap-description', 'children')],
    Input('heatmap-dropdown', 'value')
)
def update_heatmap(selected_heatmap):
    if selected_heatmap is None:
        return html.Div("Selecciona un heatmap del menú desplegable"), ""
    
    # Preparar datos comunes
    teams = sorted(list(set(df['homeTeam.name'].unique().tolist() + df['awayTeam.name'].unique().tolist())))
    
    if selected_heatmap == 'h2h':
        # Heatmap de enfrentamientos directos
        h2h_matrix = pd.DataFrame(index=teams, columns=teams, data=0)
        
        for _, match in df.iterrows():
            home = match['homeTeam.name']
            away = match['awayTeam.name']
            home_goals = match['homeScore.display']
            away_goals = match['awayScore.display']
            
            if home in h2h_matrix.index and away in h2h_matrix.columns:
                h2h_matrix.loc[home, away] = home_goals - away_goals
                h2h_matrix.loc[away, home] = away_goals - home_goals
        
        h2h_filtered = h2h_matrix.loc[(h2h_matrix != 0).any(axis=1), (h2h_matrix != 0).any(axis=0)]
        
        fig = go.Figure(data=go.Heatmap(
            z=h2h_filtered.values,
            x=h2h_filtered.columns,
            y=h2h_filtered.index,
            colorscale='RdBu_r',
            zmid=0,
            text=h2h_filtered.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Diferencia<br>de Goles")
        ))
        fig.update_layout(
            title='Enfrentamientos Directos (Diferencia de Goles)',
            xaxis_title='Equipo Visitante',
            yaxis_title='Equipo Local',
            height=700
        )
        
        description = "Muestra la diferencia de goles en cada enfrentamiento. Valores positivos (rojos) indican victoria del equipo de la fila, negativos (azules) victoria del equipo de la columna."
        
    elif selected_heatmap == 'rounds':
        # Heatmap de rendimiento por ronda
        round_performance = []
        for team in teams:
            team_rounds = {}
            
            home_matches = df[df['homeTeam.name'] == team]
            for _, match in home_matches.iterrows():
                round_name = match['roundInfo.name']
                if match['winnerCode'] == 1:
                    points = 3
                elif match['winnerCode'] == 3:
                    points = 1
                else:
                    points = 0
                team_rounds[round_name] = team_rounds.get(round_name, 0) + points
            
            away_matches = df[df['awayTeam.name'] == team]
            for _, match in away_matches.iterrows():
                round_name = match['roundInfo.name']
                if match['winnerCode'] == 2:
                    points = 3
                elif match['winnerCode'] == 3:
                    points = 1
                else:
                    points = 0
                team_rounds[round_name] = team_rounds.get(round_name, 0) + points
            
            if team_rounds:
                team_rounds['Team'] = team
                round_performance.append(team_rounds)
        
        if round_performance:
            round_df = pd.DataFrame(round_performance).set_index('Team').fillna(0)
            round_df = round_df.loc[round_df.sum(axis=1) > 0]
            round_df = round_df.loc[round_df.sum(axis=1).sort_values(ascending=False).index]
            round_df = round_df.head(20)
            
            fig = go.Figure(data=go.Heatmap(
                z=round_df.values,
                x=round_df.columns,
                y=round_df.index,
                colorscale='Viridis',
                text=round_df.values,
                texttemplate='%{text:.0f}',
                textfont={"size": 10},
                colorbar=dict(title="Puntos")
            ))
            fig.update_layout(
                title='Rendimiento por Ronda (Top 20 Equipos)',
                xaxis_title='Ronda',
                yaxis_title='Equipo',
                height=700
            )
        else:
            fig = go.Figure()
            
        description = "Visualiza los puntos obtenidos por cada equipo en cada ronda del torneo. Permite identificar qué equipos mantuvieron consistencia a lo largo del campeonato."
        
    elif selected_heatmap == 'goals_period':
        # Heatmap de goles por período
        goals_by_period = []
        for team in teams:
            team_goals = {
                'Team': team,
                'Goles 1T (Local)': df[df['homeTeam.name'] == team]['homeScore.period1'].sum(),
                'Goles 2T (Local)': df[df['homeTeam.name'] == team]['homeScore.period2'].sum(),
                'Goles 1T (Visitante)': df[df['awayTeam.name'] == team]['awayScore.period1'].sum(),
                'Goles 2T (Visitante)': df[df['awayTeam.name'] == team]['awayScore.period2'].sum()
            }
            team_goals['Total'] = sum([team_goals['Goles 1T (Local)'], team_goals['Goles 2T (Local)'], 
                                      team_goals['Goles 1T (Visitante)'], team_goals['Goles 2T (Visitante)']])
            goals_by_period.append(team_goals)
        
        goals_period_df = pd.DataFrame(goals_by_period).set_index('Team')
        goals_period_df = goals_period_df.loc[goals_period_df['Total'] > 0].sort_values('Total', ascending=False).head(20)
        goals_period_display = goals_period_df[['Goles 1T (Local)', 'Goles 2T (Local)', 
                                               'Goles 1T (Visitante)', 'Goles 2T (Visitante)']]
        
        fig = go.Figure(data=go.Heatmap(
            z=goals_period_display.values,
            x=goals_period_display.columns,
            y=goals_period_display.index,
            colorscale='YlOrRd',
            text=goals_period_display.values,
            texttemplate='%{text:.0f}',
            textfont={"size": 10},
            colorbar=dict(title="Goles")
        ))
        fig.update_layout(
            title='Distribución de Goles por Tiempo y Condición (Top 20 Equipos)',
            xaxis_title='Período y Condición',
            yaxis_title='Equipo',
            height=700
        )
        
        description = "Analiza cuándo y cómo marcan los equipos sus goles: primer tiempo vs segundo tiempo, como local vs visitante."
        
    elif selected_heatmap == 'correlation':
        # Matriz de correlación
        corr_data = []
        for team in teams:
            home_matches = df[df['homeTeam.name'] == team]
            away_matches = df[df['awayTeam.name'] == team]
            
            total_matches = len(home_matches) + len(away_matches)
            if total_matches > 0:
                goals_for = home_matches['homeScore.display'].sum() + away_matches['awayScore.display'].sum()
                goals_against = home_matches['awayScore.display'].sum() + away_matches['homeScore.display'].sum()
                wins = ((home_matches['winnerCode'] == 1).sum() + (away_matches['winnerCode'] == 2).sum())
                draws = ((home_matches['winnerCode'] == 3).sum() + (away_matches['winnerCode'] == 3).sum())
                red_cards = home_matches['homeRedCards'].sum() + away_matches['awayRedCards'].sum()
                
                corr_data.append({
                    'Partidos': total_matches,
                    'Goles a Favor': goals_for,
                    'Goles en Contra': goals_against,
                    'Victorias': wins,
                    'Empates': draws,
                    'Tarjetas Rojas': red_cards,
                    'Puntos': wins * 3 + draws
                })
        
        corr_df = pd.DataFrame(corr_data)
        correlation_matrix = corr_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu_r',
            zmid=0,
            text=correlation_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlación")
        ))
        fig.update_layout(
            title='Matriz de Correlación de Estadísticas',
            height=600
        )
        
        description = "Muestra la relación entre diferentes métricas del torneo. Valores cercanos a 1 indican correlación positiva, cercanos a -1 correlación negativa."
        
    elif selected_heatmap == 'home_away':
        # Local vs Visitante
        performance_matrix = []
        for team in teams:
            home_matches = df[df['homeTeam.name'] == team]
            away_matches = df[df['awayTeam.name'] == team]
            
            if len(home_matches) > 0 or len(away_matches) > 0:
                # Estadísticas como local
                home_wins = (home_matches['winnerCode'] == 1).sum()
                home_draws = (home_matches['winnerCode'] == 3).sum()
                home_losses = (home_matches['winnerCode'] == 2).sum()
                home_goals_for = home_matches['homeScore.display'].sum()
                home_goals_against = home_matches['awayScore.display'].sum()
                
                # Estadísticas como visitante
                away_wins = (away_matches['winnerCode'] == 2).sum()
                away_draws = (away_matches['winnerCode'] == 3).sum()
                away_losses = (away_matches['winnerCode'] == 1).sum()
                away_goals_for = away_matches['awayScore.display'].sum()
                away_goals_against = away_matches['homeScore.display'].sum()
                
                performance_matrix.append({
                    'Team': team,
                    'PG Local': home_wins,
                    'PE Local': home_draws,
                    'PP Local': home_losses,
                    'GF Local': home_goals_for,
                    'GC Local': home_goals_against,
                    'PG Visitante': away_wins,
                    'PE Visitante': away_draws,
                    'PP Visitante': away_losses,
                    'GF Visitante': away_goals_for,
                    'GC Visitante': away_goals_against,
                    'Total Pts': (home_wins + away_wins) * 3 + (home_draws + away_draws)
                })
        
        perf_df = pd.DataFrame(performance_matrix).set_index('Team')
        perf_df = perf_df.sort_values('Total Pts', ascending=False).head(20)
        perf_display = perf_df[['PG Local', 'PE Local', 'PP Local', 'GF Local', 
                               'PG Visitante', 'PE Visitante', 'PP Visitante', 'GF Visitante']]
        
        fig = go.Figure(data=go.Heatmap(
            z=perf_display.values,
            x=perf_display.columns,
            y=perf_display.index,
            colorscale='Plasma',
            text=perf_display.values,
            texttemplate='%{text:.0f}',
            textfont={"size": 10},
            colorbar=dict(title="Valor")
        ))
        fig.update_layout(
            title='Rendimiento Local vs Visitante (Top 20 Equipos)',
            xaxis_title='Métrica',
            yaxis_title='Equipo',
            height=700
        )
        
        description = "Compara el rendimiento de los equipos jugando como local versus visitante. Incluye partidos ganados, empatados, perdidos y goles."
        
    elif selected_heatmap == 'goals_efficiency':
        # Efectividad goleadora
        efficiency_data = []
        for team in teams:
            home_matches = df[df['homeTeam.name'] == team]
            away_matches = df[df['awayTeam.name'] == team]
            
            total_matches = len(home_matches) + len(away_matches)
            if total_matches > 0:
                goals_for = home_matches['homeScore.display'].sum() + away_matches['awayScore.display'].sum()
                goals_against = home_matches['awayScore.display'].sum() + away_matches['homeScore.display'].sum()
                goals_1h = home_matches['homeScore.period1'].sum() + away_matches['awayScore.period1'].sum()
                goals_2h = home_matches['homeScore.period2'].sum() + away_matches['awayScore.period2'].sum()
                wins = ((home_matches['winnerCode'] == 1).sum() + (away_matches['winnerCode'] == 2).sum())
                
                efficiency_data.append({
                    'Team': team,
                    'Promedio GF': round(goals_for / total_matches, 2),
                    'Promedio GC': round(goals_against / total_matches, 2),
                    'Ratio 1T/2T': round(goals_1h / (goals_2h + 0.01), 2),  # Evitar división por cero
                    '% Victorias': round((wins / total_matches) * 100, 1),
                    'Diferencia': goals_for - goals_against,
                    'Total Goles': goals_for
                })
        
        eff_df = pd.DataFrame(efficiency_data).set_index('Team')
        eff_df = eff_df.sort_values('Total Goles', ascending=False).head(25)
        eff_display = eff_df[['Promedio GF', 'Promedio GC', 'Ratio 1T/2T', '% Victorias', 'Diferencia']]
        
        fig = go.Figure(data=go.Heatmap(
            z=eff_display.values,
            x=eff_display.columns,
            y=eff_display.index,
            colorscale='Turbo',
            text=eff_display.values,
            texttemplate='%{text:.1f}',
            textfont={"size": 10},
            colorbar=dict(title="Valor")
        ))
        fig.update_layout(
            title='Efectividad Goleadora (Top 25 Equipos)',
            xaxis_title='Métrica de Efectividad',
            yaxis_title='Equipo',
            height=700
        )
        
        description = "Analiza la efectividad goleadora: promedios de goles, ratio entre tiempos, porcentaje de victorias y diferencia de goles."
    
    return dcc.Graph(figure=fig), description

if __name__ == '__main__':
    app.run(debug=True)