#==================================THAT DASH CODE=======================================
#=======================================================================================

dash_app = dash.Dash(__name__, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/plotly/')

applicant_count_df = pd.read_excel('Applicant_Count.xlsx')
total_applicant_count = applicant_count_df['applicant_count'].iloc[0]

work_df = pd.read_excel('Work.xlsx')
education_df = pd.read_excel('Education.xlsx')
skills_df = pd.read_excel('Skills.xlsx')
time_df = pd.read_excel('Time.xlsx')

colors = {
    'primary': '#2b377c',
    'secondary': '#f2efe9',
    'tertiary': '#cbb27f',
    'background': 'rgba(0, 0, 0, 0)'
}

work_ex_fig = px.bar(
    work_df,
    x='experience_years',
    y='count',
    labels={'experience_years': 'Work Experience (years)', 'count': 'Count'},
    title='Work Experience Count Distribution'
)

work_ex_fig.update_traces(marker_color=colors['primary'], opacity=0.6)

work_ex_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    xaxis=dict(tickmode='linear', dtick=1),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

education_fig = px.pie(
    education_df,
    names=education_df.columns,
    values=education_df.iloc[0],
    title='Education Level Distribution'
)

education_fig.update_traces(marker=dict(colors=[colors['primary'], colors['tertiary'], colors['secondary']]), opacity=0.6)
education_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)
skills_df = skills_df.nlargest(15, 'frequency')
skills_fig = px.bar(
    skills_df,
    x='frequency',
    y='skill',
    orientation='h',
    labels={'frequency': 'Frequency', 'skill': 'Skills'},
    title='Top Skills Frequency Distribution',
    category_orders={'skill': skills_df['skill'].tolist()}
)
skills_fig.update_traces(marker_color=colors['tertiary'], opacity=0.6)
skills_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

time_df['time_stamp'] = pd.to_datetime(time_df['time_stamp']).dt.date
time_aggregated = time_df.groupby('time_stamp').size().reset_index(name='count')
time_aggregated = time_aggregated.sort_values('time_stamp')
time_fig = px.line(
    time_aggregated,
    x='time_stamp',
    y='count',
    labels={'time_stamp': 'Date', 'count': 'Submission Count'},
    title='Submission Time Distribution'
)
time_fig.update_traces(line_color=colors['primary'], opacity=0.6)
time_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    xaxis=dict(
        tickmode='array',
        tickvals=time_aggregated['time_stamp'],
        tickformat='%Y-%m-%d'
    ),
    yaxis=dict(
        tickmode='linear',
        dtick=1
    ),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

dash_app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Analytics Dashboard", className='text-center mb-4', style={'fontSize': '24px', 'color': colors['primary']}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.H2(f"Total Applicants: {total_applicant_count}", className='text-center', style={'fontSize': '18px', 'color': '#000000'}), width=12)
    ]),
    dbc.Row([
                dbc.Col(dcc.Graph(figure=work_ex_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'}),
        dbc.Col(dcc.Graph(figure=education_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'})
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=skills_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'}),
        dbc.Col(dcc.Graph(figure=time_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'})
    ])
], fluid=True)

#===========================================END DASH================================================
#===================================================================================================