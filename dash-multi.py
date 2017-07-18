import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from phone_data import *
import sqlite3
import datetime as dt
import random


# hello :)
# Written by Jake Nelson
# July 17 2017

def to_time(decimal):
    return str(int(decimal // 1)) + ':' + str(int((decimal % 1) * 60) )

conn = sqlite3.connect('phone.db')
frames = dict()
types = [ 'daily','weekly', 'monthly']
data, columns = daily_data(conn)
frames['daily'] = pd.DataFrame.from_records(data, columns=columns)
color='#F3F3F3'
data, columns = weekly_data(conn)
frames['weekly'] = pd.DataFrame.from_records(data, columns=columns)

data, columns = monthly_data(conn)
frames['monthly'] = pd.DataFrame.from_records(data, columns=columns)

s1 = ['avg_call_length','avg_after_call','aux_time_per_call', 'avg_avail_time', 'avg_hold_time']
s2 = ['avg_ring_time']
s3 = ['staffed_per_day']
s4 = ['held_calls', 'calls']
s5 = ['hold_ratio']

for df in frames:
    for stat in s1+s2+s3:
        temp = []
        for z in frames[df][stat]:
            temp.append('Time: ' + to_time(z))
        frames[df][stat + '_clock'] = pd.Series(temp,frames[df][stat].index)

#frames['weekly']['test_time'] = pd.Series(temp,frames['weekly']['avg_call_length'].index)



stats = ["hold_ratio", "calls", "avg_call_length"]
stats2 = ['calls', 'avg_call_length',
          'avg_after_call', 'avg_ring_time',
          'aux_time_per_call', 'avg_avail_time', 'staffed_per_day',
          'held_calls', 'hold_ratio', 'avg_hold_time']

team_color = 'B1E9FF'

app = dash.Dash()
app.css.append_css({"external_url": "https://www.w3schools.com/w3css/4/w3.css"})

app.layout = html.Div([html.Link(rel="icon", href="favicon.ico"), html.Div([
    html.Table([
        html.Tr([
            html.Td(
                html.Div([html.Label('Team Stat:'),
                          html.Div([dcc.Dropdown(
                              id='stat-filter',
                              options=[{'label': i.upper(), 'value': i} for i in stats2],
                              value=random.choice(stats2)),

                          ]),
                          html.Br(),
                          html.Label('Months to show:'),
                          html.Div(dcc.Slider(
                                  id='month-slider',
                                  min=1,
                                  max=6,
                                  marks = {str(i) : str(i) for i in range(1,7)},
                                  value = 3,
                              ), style={'width':'80%', 'margin' :'auto'})
                          ], style={'width': '10vw'})
            ),
            html.Td(
                [html.Div(dcc.Graph(id='graph4', animate=False), style={'width': '42vw', 'height': '45vh','backgroundColor' : team_color})]
            , style={ 'border-color':'black','border-width':'4px', 'border-style':'solid', 'border-radius':'10px', 'backgroundColor' : team_color}),
            html.Td(
                html.Div(dcc.Graph(id='graph1', animate=False), style={'width': '42vw', 'height': '45vh'})
            )
        ]),
        html.Tr([
            html.Td(
                html.Div([html.Label('Select Agent:'),
                          dcc.Dropdown(
                              id='agent-filter',
                              options=[{'label': i, 'value': i} for i in frames['daily'].name.unique()],
                              value='Patrick Savage'),
                          html.Label('Group By:'),
                          dcc.Dropdown(
                              id='date-radio',
                              options=[{'label': k.upper(), 'value': k} for k in types],
                              value='weekly'
                          ),
                            html.Label('Date Range:'),
                          dcc.Dropdown(
                              id='date-length',
                              options=[{'label': k.upper(), 'value': k} for k in [ '3 months', 'all time']],
                              value='3 months',
                              #labelStyle={'layout':'inline-block'}
                          )
                          ], style={'width': '10vw'})
            ),
            html.Td(
                html.Div(dcc.Graph(id='graph2', animate=False), style={'width': '42vw', 'height': '45vh','backgroundColor' : color})
            ),
            html.Td(
                html.Div(dcc.Graph(id='graph3', animate=False), style={'width': '42vw', 'height': '45vh','backgroundColor' : color}))
        ])
    ])

], style={'backgroundColor' : color, 'height': '95vh'})
])


app.title = 'ANet Phone Dashboard'

graphs = {"graph1": "Calls", "graph2": "Call Time", "graph3": "Holds"}


@app.callback(dash.dependencies.Output('graph4', 'figure'),
              [dash.dependencies.Input('stat-filter', 'value'),
               dash.dependencies.Input('month-slider', 'value')])
def update_multi_graph(stat, months):
    past_date = dt.datetime.today() - dt.timedelta(days=months * 30)
    filtered_df = frames['monthly'][frames['monthly'].start_date > past_date.strftime('%Y-%m-%d')]
    traces = []
    annotations = []
    for month in filtered_df.month.unique():
        temp_df = filtered_df[filtered_df.month == month]
        mname = dt.datetime.strptime(temp_df['start_date'].values[0],'%Y-%m')

        if stat in s1+s2+s3:
            traces.append(go.Bar(
                x=temp_df['name'],
                y=temp_df[stat],
                opacity=0.8,
                #marker='lines+markers+text',
                name=mname.strftime('%b %y'),
                text=temp_df[stat+'_clock']
            ))
        else:
            traces.append(go.Bar(
                x=temp_df['name'],
                y=temp_df[stat],
                opacity=0.8,
                # marker='lines+markers+text',
                name=mname.strftime('%b %y'),
            ))
        for d, c in temp_df[['name', stat]].values:
            annotations.append(
                dict(x=d, y=c, xref='x1', yref='y1', text=str(c),  yanchor='bottom',
                     showarrow=False))

    if stat in s1:
        layout = go.Layout(
            title="Team Stat: " + stat.upper(),
            yaxis={'title': 'Time (Minutes)'},
            xaxis={'tickangle': -30},
            legend={'x': 0, 'y': 1},
            plot_bgcolor=team_color,
            paper_bgcolor=team_color,
            barmode='group',
            # annotations = annotations
        )
    elif stat in s2:
        layout = go.Layout(
            title="Team Stat: " + stat.upper(),
            yaxis={'title': 'Time (Seconds)'},
            xaxis={'tickangle': -30},
            legend={'x': 0, 'y': 1},
            plot_bgcolor=team_color,
            paper_bgcolor=team_color,
            barmode='group',
            # annotations = annotations
        )
    elif stat in s3:
        layout = go.Layout(
            title="Team Stat: " + stat.upper(),
            yaxis={'title': 'Time (Hours)'},
            xaxis={'tickangle': -30},
            legend={'x': 0, 'y': 1},
            plot_bgcolor=team_color,
            paper_bgcolor=team_color,
            barmode='group',
            # annotations = annotations
        )

    elif stat in s4:
        layout = go.Layout(
            title="Team Stat: " + stat.upper(),
            yaxis={'title': 'Calls'},
            xaxis={'tickangle': -30},
            legend={'x': 0, 'y': 1},
            plot_bgcolor=team_color,
            paper_bgcolor=team_color,
            barmode='group',
            # annotations = annotations
        )
    elif stat in s5:
        layout = go.Layout(
            title="Team Stat: " + stat.upper(),
            yaxis={'title': 'Percent (%)'},
            xaxis={'tickangle': -30},
            legend={'x': 0, 'y': 1},
            plot_bgcolor=team_color,
            paper_bgcolor=team_color,
            barmode='group',
            # annotations = annotations
        )
    return {'data': traces, 'layout': layout}


def generate_callback_box(graph):
    @app.callback(
        dash.dependencies.Output(graph, 'figure'),
        [dash.dependencies.Input('agent-filter', 'value'),
         dash.dependencies.Input('date-radio', 'value'),
         dash.dependencies.Input('date-length', 'value')])
    def update_figure(dd, datekind, datelength):

        if datelength == '3 months':
            target_date = dt.date.today()
            target_date = dt.date(day=target_date.day,
                                  month = (target_date.month-4) % 12,
                                  year = target_date.year)
            target_date = target_date.strftime('%Y-%m-%d')
        else:
            target_date = '2016-01-01'
        filtered_df = frames[datekind][frames[datekind].name == dd]
        filtered_df=filtered_df[filtered_df.start_date > target_date]
        traces = []

        annotations = []

        yranges = {'daily': [0, 25], 'weekly': [0, 100], 'monthly': [0, 300]}

        if graph == "graph1":
            traces.append(go.Bar(
                x=filtered_df['start_date'],
                y=filtered_df['calls'],
                 opacity=0.8,
                name='Calls Taken',
            ))
            for d, c in filtered_df[['start_date', 'calls']].values:
                annotations.append(
                    dict(x=d, y=c, xref='x1', yref='y1', text=str(c), xanchor='center', yanchor='bottom',
                         showarrow=False))

            layout = go.Layout(
                title=graphs[graph],
                yaxis={'title': 'Calls Taken', 'range': yranges[datekind]},
                xaxis={ 'tickangle': -30, 'domain': [0, 1], 'autotick': True},
                legend={'x': 1, 'y': 1},
                plot_bgcolor=color,
                paper_bgcolor=color,
                hovermode='closest',
                annotations=annotations
            )
        elif graph == "graph2":
            for col in ['avg_call_length', 'avg_after_call', 'aux_time_per_call']:
                traces.append(go.Bar(
                    x=filtered_df['start_date'],
                    y=filtered_df[col],
                    opacity=0.8,
                    text = filtered_df[col+'_clock'],
                    name=col.upper()
                ))
            layout = go.Layout(
                title=graphs[graph],
                yaxis={'title': 'Avg Time Per Call (min)', 'range': [0, 30]},
                xaxis={'tickangle': -30},
                legend={'x': 0.8, 'y': 1},
                plot_bgcolor=color,
                paper_bgcolor=color,
                barmode='stack'
            )
        elif graph == "graph3":
            traces.append(go.Bar(
                x=filtered_df['start_date'],
                y=filtered_df['hold_ratio'],
                name='Hold Ratio',
            opacity=0.8,
                yaxis='y1'
            ))
            for d, c in filtered_df[['start_date', 'hold_ratio']].values:
                annotations.append(
                    dict(x=d, y=c, xref='x1', yref='y1', text=str(c) + '%', xanchor='center', yanchor='bottom',
                         showarrow=False))
            traces.append(go.Scatter(
                x=filtered_df['start_date'],
                y=filtered_df['avg_hold_time'],
                text = filtered_df['avg_hold_time_clock'],
                mode='markers+lines',
                textposition = 'above',
                textfont=dict(
                    family='sans serif',
                    size=18,
                    color='#ff7f0e'
                ),
                name='Hold Time',
                yaxis='y2'
            ))
            layout = go.Layout(
                title=graphs[graph],
                xaxis={'tickangle':-30},
                yaxis={'title': 'Ratio of Calls Held', 'range': [0, 60]},
                yaxis2={'title': 'Avg Hold Time (min)', 'range': [0, 18],
                        'overlaying': 'y', 'side': 'right'},
                legend={'x': 1.1, 'y': 1},
                plot_bgcolor=color,
                paper_bgcolor=color,
                annotations=annotations
            )
        return {
            'data': traces,
            'layout': layout
        }


for col in ["graph1", "graph2", "graph3"]:
    generate_callback_box(col)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
