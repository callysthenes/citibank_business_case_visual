import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import base64
import plotly.graph_objs as go
from plotly.offline import iplot
from plotly.subplots import make_subplots

# Helper function to transform regular data to sankey format
# Returns data and layout as dictionary
def genSankey(df,cat_cols=[],value_cols='',title='Sankey Diagram'):
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#4B8BBE','#306998','#FFE873','#FFD43B','#646464']
    labelList = []
    colorNumList = []
    for catCol in cat_cols:
        labelListTemp =  list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp
        
    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))
    
    # define colors based on number of levels
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]]*colorNum
        
    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()
        
    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))
    
    # creating the sankey diagram
    data = dict(
        type='sankey',
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = labelList,
          color = colorList
        ),
        link = dict(
          source = sourceTargetDf['sourceID'],
          target = sourceTargetDf['targetID'],
          value = sourceTargetDf['count']
        )
      )
    
    layout =  dict(
        title = title,
        font = dict(
          size = 10
        )
    )
       
    fig = dict(data=[data], layout=layout)
    return fig



df = pd.read_csv ("madrid_transactions.csv", index_col=0)
countries = pd.read_csv ("country-and-continent-codes-list.csv")
df = df.merge(countries, left_on="customer_country", right_on="Two_Letter_Country_Code")

df.tx_date_proc = df.tx_date_proc.apply(pd.to_datetime)
df['Day'] = [d.date() for d in df['tx_date_proc']]
df['Time'] = [d.time() for d in df['tx_date_proc']]

country_code = pd.read_csv ("all.csv")

# Optional:
# change the country name to the first part of the name
df['Country_Name'] = df['Country_Name'].apply(lambda x: str(x).split(',')[0])

# Optional:
# change United Kingdom of Great Britain & Northern Ireland to United Kingdom
df['Country_Name'] = df['Country_Name'].apply(lambda x: 'United Kingdom' if x == 'United Kingdom of Great Britain & Northern Ireland' else x)

# Traslating to English all purchase categories
df['category'] = df['category'].apply(lambda x: 'Travel Agency' if x == 'Agencias de viajes' else x)
df['category'] = df['category'].apply(lambda x: 'Home and reforms' if x == 'Hogar y reformas' else x)
df['category'] = df['category'].apply(lambda x: 'Automotive' if x == 'Automoción' else x)


df3 = df.merge(country_code, left_on="customer_country", right_on="alpha-2").groupby(['customer_country', "alpha-3", "Country_Name"])['amount'].sum().reset_index(name ='Total_Expenditure')
df4 = df.merge(country_code, left_on="customer_country", right_on="alpha-2").groupby(['customer_country', "alpha-3", "Country_Name"])['amount'].count().reset_index(name ='Total_Transactions')
df5 = df.merge(country_code, left_on="customer_country", right_on="alpha-2").groupby(['customer_country', "alpha-3", "Country_Name"])['amount'].mean().reset_index(name ='Avg_Ticket')

df_new = df3.merge(df4, on=['customer_country', "alpha-3", "Country_Name"]).merge(df5, on=['customer_country', "alpha-3", "Country_Name"])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

colors = {
    'background': '#FFFFFF',
    'text': '#FFFFFF'
}


df7 = df.groupby(['category', 'customer_country'])['amount'].sum().reset_index(name ='Total_amount')

def range_slider(id, min, max, step, value, is_vertical=False):
  return dcc.RangeSlider(
            id = id,
            min=min,
            max=max,
            step = step,
            marks=None,
            value=value,
            tooltip={"placement": "bottom", "always_visible": True},
            vertical=is_vertical,
            verticalHeight=450,
          )

# Defining App Layout 

app.layout = html.Div(className='main',
style={'backgroundColor': colors['background']}, children=[
    html.H1('Citibank Credit Card Intelligence: Group A', style={'textAlign':'center', 'color': colors['text']}),
    dcc.Tabs([
      dcc.Tab(label='Credit Card KPIs', children=[
            html.Div([
              html.Div([
                html.Div([ 
                  html.Label('Top Countries', style={'color': colors['text']}),
                  dcc.Slider(
                      id='countries-slider',
                      min=1,
                      max=df3.shape[0],
                      marks=None,
                      value=10,
                      tooltip={"placement": "bottom", "always_visible": True},
                  ),
                ], style={'padding-top': '10px', 'padding-bottom': '3px'}
                ),
              ]),
          ], style = {'width':'95%','margin':'auto'}), # slider Div
          html.Div(
            className= 'row',
            children=[
            html.Div(
              className= 'three columns',
              children=[
                html.Label('Choose a metric:', style={'font-size': '20px', 'font-weight': 700, 'margin-top': '-10px', 'color': colors['text']}),
                dcc.Dropdown(
                  id='interest-variable',
                  options=[{'label':'Total Expenditure', 'value':'Total_Expenditure'},
                            {'label': 'Total Transactions', 'value':'Total_Transactions'},
                            {'label': 'Avg Ticket', 'value':'Avg_Ticket'},
                            ],
                  value='Total_Expenditure',
                  clearable=False,
                  #style={'padding-top': '8px'}
                ),
              ], style={'padding-left': '10px', 'height': '60px', 'center': 'true'}
            ),
            html.Div(
              className= 'three columns',
              children=[
                html.Div([
                  html.P(
                    'Total Expenditure', 
                    style={'font-size': '15px', 'font-weight': 700, 'margin-top': '-15px'}
                  ),
                  html.P(
                    id = 'card1',
                    style={'font-weight': 700, 'font-size': '20px', 'margin-top': '-15px'},
                  ),
              ], className='card3'),
            ]), # card1
            html.Div(
              className= 'three columns',
              children=[
                html.Div([
                  html.P(
                    'Total Transactions', 
                    style={'font-size': '15px', 'font-weight': 700, 'margin-top': '-15px'}
                  ),
                  html.P(
                    id = 'card2',
                    style={'font-weight': 700, 'font-size': '20px', 'margin-top': '-15px'}
                  ),
              ], className='card3'),
            ]), # card2
            html.Div(
              className= 'three columns',
              children=[
                html.Div([
                  html.P(
                    'Avg Ticket', 
                    style={'font-size': '15px', 'font-weight': 700, 'margin-top': '-15px'}
                  ),
                  html.P(
                    id = 'card3',
                    style={'font-weight': 700, 'font-size': '20px', 'margin-top': '-15px'}
                  ),
              ], className='card3'),
            ]), # card3
          ], style={'padding-top': '10px', 'padding-bottom': '20px', 'width':'95%','margin':'auto'}
          ), # row div for the drop and cards
          html.Div(
            className= 'row',
            children=[
            html.Div(
              className= 'three columns',
              children=[
                #html.Label('Space for Text', style={'font-size': '15px', 'font-weight': 700, 'margin-left': '10px'}),
                html.P(
                  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                  style={'width': '100%', 'height': 600, 'margin-left': '10px', 'margin-right': '0px', 'color': colors['text']},
                ),
              ]
            ),
            html.Div(
              className= 'nine columns',
              children=[
                dcc.Graph(
                  id='map-graph',
                ),
            ], style = {'margin-left': '3%', 'margin-bottom': '3%'},
            ),
          ], style = {'width':'95%','margin':'auto'}
          ), # row div for the map and text area

          html.Div(
            className= 'row',
            children=[
              html.Div(
                className= 'seven columns',
                children=[
                  dcc.Graph(
                    id='pareto-plot',
                  ),
                ], style={'margin-bottom': '3%', 'height':'500px', 'margin-left': '-25px'}
              ),
              html.Div(
                className= 'five columns',
                children=[
                  dcc.Graph(
                    id='violin-plot',
                  ),
                ]
              ),
          ], style = {'width':'90%','margin':'auto'}),      
      ]),
      dcc.Tab(label='Daily Purchase Habits', children=[
        html.Div([
          html.Div( className= 'row',
            children=[ 
              html.Label('Top Countries', style={'color': colors['text']}),
              dcc.Slider(
                  id='countries-slider4',
                  min=1,
                  max=df3.shape[0],
                  marks=None,
                  value=10,
                  tooltip={"placement": "bottom", "always_visible": True},
              ),
        ], style={'padding-top': '10px', 'padding-bottom': '3px'}),
      ], style = {'width':'95%','margin':'auto'}),

      html.Div(
        className= 'row',
        children=[                  
          html.Div(
            className='three columns',
            children=[
                html.Label('Choose a metric:', style={'font-size': '20px', 'font-weight': 700, 'margin-top': '-10px', 'color': colors['text']}),
                dcc.Dropdown(
                  id='dropdown-page2',
                  options=[{'label':'Total Expenditure', 'value':'Total_Expenditure'},
                            {'label': 'Total Transactions', 'value':'Total_Transactions'},
                            {'label': 'Avg Ticket', 'value':'Avg_Ticket'},
                            ],
                  value='Total_Expenditure',
                  clearable=False,
                  #style={'padding-top': '8px'}
                ),
                html.P(
                  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                  style={'width': '100%', 'height': 850, 'margin-left': '0px', 'margin-right': '-10px', 'margin-top': '8%', 'color': colors['text']},
                ),
          ],style={'padding-left': '10px', 'height': '60px', 'center': 'true', 'margin-bottom': '3%', 'padding-right': '0%', 'margin-top': '1%'}),
          html.Div(
            className='nine columns',
            children=[
                dcc.Graph(
                  id='point-plot',
                  style = {'margin-bottom': '3%', 'margin-top': '3%'}
                ),
                dcc.Graph(
                    id='heatmap-plot',
                    style = {'margin-bottom': '3%'}
                  #style={'width': '100%', 'height': 450, 'margin-left': '10px', 'margin-right': '0px'},
                ),
          ]),
        ], style = {'width':'95%','margin':'auto'}),
        html.Div(
            className= 'row',
            children=[
            html.Div(
                children=[
                    dcc.Graph(
                        id='animated-plot',
                    ),
            ], style = {'margin-bottom': '3%'}),
            html.Div(
                children=[
                    dcc.Graph(
                        id='sankey-plot',
                    ),
            ], style = {'margin-bottom': '3%'}),
        ], style = {'width':'95%','margin':'auto'}),
            
      ]), # tab 2
      dcc.Tab(label='Targeting Analysis', children=[
          html.Div(
            className="row",
            children=[
              #html.Label("Select Scatter"),
              dcc.Dropdown(
                  id='scatter-type',
                  options=[{'label':'Total Transactions vs Average Ticket', 'value':'plot1'},
                           {'label': 'Total Transactions vs Total Expenditure', 'value':'plot2'},
                           ],
                  placeholder="Select a scatter plot",
                value='plot1',
                clearable=False,
              ),
              html.Div(id = 'divv'),
        ], style={'width':'90%','margin-top':'2%', 'margin-left':'5%'}
        )
      ]),
      ###########
      # ,
    ]),
      
])

# Callbacks

# callback for the cards
@app.callback(Output('card1', 'children'),
              Input('countries-slider', 'value'))
def update_card1(slider):
  data = df_new.sort_values(by= 'Total_Expenditure', ascending=False).head(slider)
  total = data['Total_Expenditure'].sum()
  return '{0:,.0f}'.format(total)

@app.callback(Output('card2', 'children'),
              Input('countries-slider', 'value'))
def update_card2(slider):
  data = df_new.sort_values(by= 'Total_Transactions', ascending=False).head(slider)
  total = data['Total_Transactions'].sum()
  return '{0:,.0f}'.format(total)

@app.callback(Output('card3', 'children'),
              Input('countries-slider', 'value'))
def update_card3(slider):
  data = df_new.sort_values(by= 'Avg_Ticket', ascending=False).head(slider)
  total = data['Avg_Ticket'].mean()
  return '{0:,.0f}'.format(total)

# callback for the map
@app.callback(Output('map-graph', 'figure'),
              [Input('interest-variable', 'value'),
               Input('countries-slider', 'value')])             
def update_world_map(value = 'Total_Expenditure', slider = 10):
  data = df_new.sort_values(by= value, ascending=False).head(slider)
  fig = px.choropleth(data,
                    locations="alpha-3",
                    color=value, # lifeExp is a column of gapminder
                    hover_name="Country_Name", # column to add to hover information
                    color_continuous_scale=px.colors.sequential.Plasma_r[::-1],
                    title=f"{value} by Country of Origin",
                    width=1100,
                    height=600,
                    )
  return fig

@app.callback(Output('pareto-plot', 'figure'),
              [Input('interest-variable', 'value'),
              Input('countries-slider', 'value')])
def draw_pareto_plot(value, slider):
    if value == 'Avg_Ticket':
        value = 'Total_Expenditure'
    df = df_new
    df = df.sort_values(by=value, ascending=False).head(slider)
    df.sort_values(by=value, ascending=False, inplace=True)
    df['cumulative_sum'] = df[value].cumsum()
    df['cumulative_perc'] = 100*df.cumulative_sum/df[value].sum()
    #df.sort_values(by=value, ascending=False, inplace=True)
    trace_0 = go.Bar(
    x=df["Country_Name"],
    y=df[value],
    marker=dict(color=df[value], coloraxis="coloraxis"),
    text=df[value],
    textposition="outside",
    textfont=dict(color="black"),
    texttemplate='%{text:.3s}'
    )

    trace_1 = go.Scatter(
        x=df["Country_Name"],
        y=df["cumulative_perc"],
        mode="markers+lines"
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(trace_0)

    fig.add_trace(trace_1,secondary_y=True)

    fig.update_layout(
        title=f"Pareto Analysis: {value} by Country of Origin",
        showlegend=False,
        coloraxis_showscale=False,
        height=500,
    )

    # Set y-axes titles
    fig.update_yaxes(title_text=value, secondary_y=False),
    fig.update_yaxes(title_text=f"Cummulativee % {value}", secondary_y=True)

    return fig

@app.callback(Output('violin-plot', 'figure'),
              [Input('interest-variable', 'value'),
              Input('countries-slider', 'value')])
def draw_violin_plot(value, slider):
    if value == 'Total_Expenditure':
        df_country = df.groupby(['customer_country'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].sum().reset_index(name ='Total_amount')
    elif value == 'Total_Transactions':
        df_country = df.groupby(['customer_country'])['amount'].count().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].count().reset_index(name ='Total_amount')
    elif value == 'Avg_Ticket':
        df_country = df.groupby(['customer_country'])['amount'].mean().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].mean().reset_index(name ='Total_amount')
    
    df8 = df8[df8['customer_country'].isin(df_country['customer_country'].head(slider))]
    fig = px.violin(df8 , y='customer_country',x="Total_amount", color = 'customer_country', color_discrete_sequence=px.colors.sequential.Plasma_r, category_orders= {'customer_country': df_country['customer_country'].head(slider).tolist()})
    fig.update_traces(orientation='h', side='positive', width=2, points=False)
    fig.update_layout(title=f'Top {slider} Countries based on {value}: Total Expenses Distribution',xaxis_showgrid=False, xaxis_zeroline=False, yaxis_title=f'Top {slider} Countries based on Total Expenditure', xaxis_title='Total Expenses', yaxis = dict(tickmode='linear'), showlegend=False, width=600, height=500,violinmode='group')
    
    return fig

# 2nd tab

# point plot
@app.callback(Output('point-plot', 'figure'),
              [Input('dropdown-page2', 'value'),
                Input('countries-slider4', 'value')])

def draw_point_plot(value, slider):
    if value == 'Total_Expenditure':
        df_country = df.groupby(['customer_country'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df_category = df.groupby(['category'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df.groupby(['category', 'customer_country'])['amount'].sum().reset_index(name ='Total_amount')
        data = data[data['customer_country'].isin(df_country['customer_country'].head(slider))]

    elif value == 'Total_Transactions':
        df_country = df.groupby(['customer_country'])['amount'].count().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df_category = df.groupby(['category'])['amount'].count().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df.groupby(['category', 'customer_country'])['amount'].count().reset_index(name ='Total_amount')
        data = data[data['customer_country'].isin(df_country['customer_country'].head(slider))]
    
    elif value == 'Avg_Ticket':
        df_country = df.groupby(['customer_country'])['amount'].mean().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        df_category = df.groupby(['category'])['amount'].mean().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df.groupby(['category', 'customer_country'])['amount'].mean().reset_index(name ='Total_amount')
        data = data[data['customer_country'].isin(df_country['customer_country'].head(slider))]

    fig = px.scatter(data, x='customer_country', y='category',
                 color='Total_amount',size = data['Total_amount']**0.5, size_max=15,
                title=f"{value} per Category and Top {slider} Countries",
                labels={'customer_country':"Country" , 'category':"Category", 'Total_amount':f"{value}"},
                category_orders={
                    'category':df_category['category'].tolist(),
                    'customer_country':df_country['customer_country'].head(slider).tolist()},
                opacity=1)
    return fig

# heatmap plot
@app.callback(Output('heatmap-plot', 'figure'),
              [Input('dropdown-page2', 'value'),
                Input('countries-slider4', 'value')])

def draw_heatmap_plot(value, slider):
    if value == 'Total_Expenditure':
        df_country = df.groupby(['customer_country'])['amount'].sum().reset_index(name ='amount').sort_values(by=['amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].sum().reset_index(name ='amount')
    elif value == 'Total_Transactions':
        df_country = df.groupby(['customer_country'])['amount'].count().reset_index(name ='amount').sort_values(by=['amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].count().reset_index(name ='amount')
    else:
        df_country = df.groupby(['customer_country'])['amount'].mean().reset_index(name ='amount').sort_values(by=['amount'], ascending=False)
        df8 = df.groupby(['customer_country', 'hour'])['amount'].mean().reset_index(name ='amount')

    df8 = df8.loc[df8['customer_country'].isin(df_country['customer_country'].head(slider))]
    data = df8.pivot_table(columns='hour',index='customer_country',values='amount').reindex(df_country['customer_country'].head(slider))

    fig = px.imshow(data ,x=data.columns, y=data.index, title = f'{value} per hour and Top {slider} countries', labels={'x':'Hour', 'y':'Country', 'color':f'{value}'})
    return fig

# animated chart
@app.callback(Output('animated-plot', 'figure'),
              [Input('countries-slider4', 'value'),])

def update_bar_plot(slider= 10):
  df_country = df.groupby(['customer_country'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
  df8 = df.groupby(['customer_country', 'hour'])['amount'].sum().reset_index(name ='Total_amount')
  df9 = df.groupby(['customer_country', 'hour'])['amount'].count().reset_index(name ='Total_Transactions')
  # merge the two dataframes
  df10 = df8.merge(df9, on=['customer_country', 'hour'])

  df10 = df10[df10['customer_country'].isin(df_country['customer_country'].head(slider))]

  fig = px.scatter(df10.sort_values(by = ['hour'], ascending = True), x="Total_Transactions",y="Total_amount",
                  template = 'plotly_white',
                  title = f'Total Expenditure by Hour and Top {slider} countries',
                  text="customer_country",
                  color="customer_country", hover_name = 'customer_country',
                  hover_data = ['hour'],
                  animation_frame='hour',
                  height=600,
                  log_x=True, log_y=True,
                  
                  )

  return fig 

# sankey plot

@app.callback(Output('sankey-plot', 'figure'),
              [Input('dropdown-page2', 'value'),
                Input('countries-slider4', 'value')])

def draw_sankey(value, slider):
    if value == 'Total_Expenditure':
        df_country = df.groupby(['customer_country'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df[df['customer_country'].isin(df_country['customer_country'].head(slider))]
        df_category_datetime = data.groupby(['category', 'daytime'])['amount'].sum().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False).reset_index(drop=True)

    elif value == 'Total_Transactions':
        df_country = df.groupby(['customer_country'])['amount'].count().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df[df['customer_country'].isin(df_country['customer_country'].head(slider))]
        df_category_datetime = data.groupby(['category', 'daytime'])['amount'].count().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False).reset_index(drop=True)
        
    
    elif value == 'Avg_Ticket':
        df_country = df.groupby(['customer_country'])['amount'].mean().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False)
        data = df[df['customer_country'].isin(df_country['customer_country'].head(slider))]
        df_category_datetime = data.groupby(['category', 'daytime'])['amount'].mean().reset_index(name ='Total_amount').sort_values(by=['Total_amount'], ascending=False).reset_index(drop=True)
        
    all = genSankey(df_category_datetime,cat_cols=['category','daytime'],value_cols='Total_amount',title='Merchant Transactions')

    sankey = []
    df_category = df['category'].unique().tolist()
    for category in df_category:
        sankey.append(genSankey(df_category_datetime[df_category_datetime['category']==category],cat_cols=['category','daytime'],value_cols='Total_amount',title='Merchant Transactions'))

    buttons = []
    # appending all then the rest
    buttons.append(dict(
            args = [all],
            label = 'All',
            method = 'animate'
        ))

    for i in range(len(sankey)):
        buttons.append(
        dict(
            args = [sankey[i]],
            label = df_category[i],
            method = 'animate'
        ))

    updatemenus =[{'buttons': buttons}]


    # update layout with buttons, and show the figure
    sank = genSankey(df_category_datetime, cat_cols=['category','daytime'],value_cols='Total_amount',title='Merchant Transactions')
    fig = go.Figure(sank)
    fig.update_layout(updatemenus=updatemenus)
    #iplot(fig)
    
    return fig




# 3rd tab

@app.callback(Output('divv', 'children'),
              [Input('scatter-type', 'value')],
              #prevent_initial_call = True
              )
def update_scatter_plot(value):
  if value == 'plot1':
    return html.Div(className='main',
                children=[
                  html.Div(
                className="one columns",
                  children = [
                  html.Div([
                      range_slider('countries-slider2', 0, max(df_new['Avg_Ticket']) + 10, 10, [0, max(df_new['Avg_Ticket'])+10], is_vertical=True)
                      ], style={'margin-left':'50%', 'margin-bottom':'6%', 'margin-top': '90px', 'height':'500px'})
                  ], 
                  style={'hight': '600px'}
                ),
                html.Div(
                  className="eleven columns",
                  children = [
                    dcc.Graph(
                          id='scatter',
                    ),
                    html.Div([
                        range_slider('countries-slider3', 0, max(df_new['Total_Transactions']) + 10, 10, [0, 500])
                      ,], style={'margin-right':'5%', 'padding-bottom':'40px', 'margin-top':'2%'}
                    ),
                    html.P(
                      "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                    style={'width': '100%', 'height': 120, 'margin-bottom:':'3rem', 'color': colors['text']},
                    ),
                    html.P(
                    "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                    style={'width': '100%', 'height': 100, 'margin-bottom:':'3rem', 'color': colors['text']},
                    ),
                  ],
                  style={'margin-left':'0', 'margin-bottom':'3%', 'margin-top':'3%'}
                )
              ])

  elif value == 'plot2':
    return html.Div(
                className='main',
                children=[
                  html.Div(
                className="one columns",
                  children = [
                  html.Div([
                      range_slider('countries-slider2', 0, max(df_new['Total_Expenditure']) + 100, 100, [0, max(df_new['Total_Expenditure'])+ 100], is_vertical=True)
                      ], style={'margin-left':'50%', 'margin-bottom':'0%', 'margin-top': '90px', 'height':'500px'})
                  ], 
                  style={'hight': '600px'}
                ),
                html.Div(
                  className="eleven columns",
                  children = [
                    dcc.Graph(
                          id='scatter',
                    ),
                    html.Div([
                        range_slider('countries-slider3', 0, max(df_new['Total_Transactions']) + 10, 1, [0, max(df_new['Total_Transactions']) + 10])
                      ,], style={'margin-right':'5%', 'padding-bottom':'40px', 'margin-top':'2%'}
                    ),
                    html.P(
                      "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                    style={'width': '100%', 'height': 120, 'margin-bottom:':'3rem', 'color': colors['text']},
                    ),
                    html.P(
                    "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's \
                    standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make \
                      a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, \
                        remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages\
                          , and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
                    style={'width': '100%', 'height': 100, 'margin-bottom:':'3rem', 'color': colors['text']},
                    ),
                  ],
                  style={'margin-left':'0', 'margin-bottom':'3%', 'margin-top':'3%'}
                )
              ])



@app.callback(Output('scatter', 'figure'),
              [Input('scatter-type', 'value'),
              Input('countries-slider2', 'value'),
              Input('countries-slider3', 'value')],
              #prevent_initial_call = True
              )
def update_scatter_plot(value = 'plot1', slider1 = [0, 10], slider2 = [0, 10]):
  if value == 'plot1':
    data = df_new [(df_new['Total_Transactions'] >= slider2[0]) & (df_new['Total_Transactions'] <= slider2[1])
                    & (df_new['Avg_Ticket'] >= slider1[0]) & (df_new['Avg_Ticket'] <= slider1[1])]
    fig = px.scatter(data, 
                 x="Total_Transactions", 
                 y="Avg_Ticket",
                 template = 'plotly_white',
                 title = 'Total Transactions vs Average Ticket',
                 text="customer_country",
                 color="Country_Name", hover_name = 'Country_Name',
                 #hover_data = ['Country_Name'],
#                  log_x=True, log_y=True,
                 height=600,
                 range_x=[slider2[0], slider2[1]+1],
                 range_y=[slider1[0], slider1[1]+1],
                 color_continuous_scale=px.colors.sequential.Plasma)
    return fig
  elif value == 'plot2':

    conditions = [
    (df_new['Total_Expenditure'] >= 9400) & (df_new['Total_Transactions'] >= 6.5),
    (df_new['Total_Expenditure'] < 9400) & (df_new['Total_Transactions'] >= 6.5),
    (df_new['Total_Transactions'] < 6.5)
    ]

    # create a list of the values we want to assign for each condition
    values = ['Tier 3', 'Tier 2', 'Tier 1']
    df_new['Tier'] = np.select(conditions, values)

    data = df_new [(df_new['Total_Transactions'] >= slider2[0]) & (df_new['Total_Transactions'] <= slider2[1])
                    & (df_new['Total_Expenditure'] >= slider1[0]) & (df_new['Total_Expenditure'] <= slider1[1])]
    fig2 = px.scatter(data, x="Total_Transactions",y="Total_Expenditure",
                 template = 'plotly_white',
                 title = 'Total Transactions vs Total Expenditure',
                 text="customer_country",
                 color="Tier",
                  hover_name = 'Country_Name',
                 #hover_data = ['customer_country'],
                 height=600,
                 log_x=True, log_y=True,
                #  range_x=[slider2[0], slider2[1]+1],
                #  range_y=[slider1[0], slider1[1]+1],
                 color_continuous_scale=px.colors.sequential.Plasma)
    fig2.add_vline(x=82.25, line_width=1, line_dash="dash", line_color="red")
    fig2.add_vline(x=6.5, line_width=1, line_dash="dash", line_color="red")
    fig2.add_hline(y=9400, line_width=1, line_dash="dash", line_color="blue")
    fig2.add_hline(y=630, line_width=1, line_dash="dash", line_color="blue")
    return fig2


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)