import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State
import time  # Simulate loading time
from crm_script_monthly import monthly_breakdown
from crm_script_weekly import weekly_breakdown
from salesforce_data import get_dataframe, get_data

# Function to load data
def load_data():
    results = get_data()
    df = get_dataframe(results)
    monthly_data = monthly_breakdown(df)
    weekly_data = weekly_breakdown(df)


    data = {
        **monthly_data,
        'weekly_breakdown': weekly_data
    }
    return data

# Initial Data Load
data = load_data()
monthly_df = data['monthly_breakdown']
monthly_df['month'] = monthly_df['month'].astype(str)


weekly_df = data['weekly_breakdown']
weekly_df['week'] = weekly_df['week'].astype(str)



metrics = {
    "Basic LTV": data['Basic LTV'],
    "Advanced LTV": data['Advanced LTV'],
    "Average Purchase Value": data['Average Purchase Value'],
    "Average Purchase Frequency": data['Average Purchase Frequency'],
    "Average Customer Lifespan (Months)": data['Average Customer LifeSpan(Months)']
}
metrics_df = pd.DataFrame(metrics.items(), columns=["Metric", "Value"])
metrics_df["Value"] = metrics_df["Value"].round(2).astype(str)

dropdown_options = [{"label": col.replace("_", " ").title(), "value": col} for col in monthly_df.columns if col != "month"]

# Dash app setup
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Customer Insights"

# Main Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    html.Div([
        dcc.Link('🏠 Home', href='/'),
        " | ",
        dcc.Link('📊 Monthly Report', href='/monthly'),
        " | ",
        # dcc.Link('📈 Compare Two Features', href='/dynamic'),
        # " | ",
        dcc.Link('📑 LTV and Key Metrics', href='/metrics'),
        " | ",
        dcc.Link('📆 Weekly Report', href='/weekly'),
        " | ",
        html.Button("🔄 Refresh Data", id="refresh-btn", n_clicks=0),
    ], style={'padding': '10px', 'fontSize': '20px'}),

    html.Div(id="refresh-status", style={"color": "blue", "fontSize": "18px", "marginTop": "10px"}),  # Loading Message
    
    html.Div(id='page-content')  # Page Content
])


def get_home_layout():
    return html.Div([
        # Main Container for Centering
        html.Div([
            # Welcome Header
            html.H2("Welcome to Jungle World Data Dashboard", className="text-center mt-4"),

            # Box for Description and Navigation Instructions
            html.Div([
                html.P("📊 Explore your data using the navigation bar above:"),
                html.Ul([
                    html.Li("Click WEEKLY for weekly metrics"),
                    html.Li("Click MONTHLY for monthly trends")
                ], style={"listStyleType": "none", "paddingLeft": "0"}),
                
                html.P("🔍 Data updates may take a few moments to process"),
            ], style={
                "padding": "20px",
                "backgroundColor": "#f9f9f9",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                "maxWidth": "600px",
                "margin": "0 auto",
                "fontSize": "16px"
            }),

            # Spacer
            html.Br(),

        

            
            # Final message with centered text
            html.P("Navigate using the links above to view your data.", style={"textAlign": "center", "fontSize": "16px", "fontWeight": "bold"})
        ], style={
            "textAlign": "center",  # Center everything in this div
            "padding": "20px",
            "fontSize": "16px"
        }),
    ])


def get_weekly_layout():
    global weekly_df  # Ensure we're using the latest refreshed data
    weekly_df['week'] = weekly_df['week'].astype(str)
    
    return html.Div([
        html.H1("📅 Weekly CRM Report"),
        
        html.H2("Weekly Breakdown Table"),
        dash_table.DataTable(
            columns=[{"name": col.replace("_", " ").title(), "id": col} for col in weekly_df.columns],
            data=weekly_df.round(2).astype(str).to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
        ),

        html.H2("Insights"),
        dcc.Graph(figure=px.line(
            weekly_df, x='week', y=['new_customers', 'returning_customers'],
            title="New vs Returning Customers Trend (Weekly)", markers=True
        )),

        # Optional: only if you have 'new_percentage' and 'returning_percentage'
        dcc.Graph(figure=px.line(
            weekly_df, x='week', y=['new_percentage', 'returning_percentage'],
            title="Customer Type Percentages (Weekly)", markers=True
        )) if 'new_percentage' in weekly_df.columns and 'returning_percentage' in weekly_df.columns else html.Div(),

        dcc.Graph(figure=px.bar(
            weekly_df, x='week',
            y=['total_revenue', 'new_customer_revenue', 'returning_customer_revenue'],
            title="Revenue Breakdown (Weekly)", barmode='group'
        )),

        dcc.Graph(figure=px.bar(
            weekly_df, x='week',
            y=['new_customer_revenue', 'returning_customer_revenue'],
            title="New vs Returning Revenue (Weekly)", barmode='group'
        )),
    ])


# Function to generate page layouts dynamically
def get_insights_layout():
    return html.Div([
        html.H1("Monthly CRM Report"),
        html.H2("Monthly Breakdown Table"),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in monthly_df.columns],
            data=monthly_df.round(2).astype(str).to_dict('records'),
            style_table={'overflowX': 'auto'}
        ),
        html.H2("Insights"),
        dcc.Graph(figure=px.line(monthly_df, x='month', y=['new_customers', 'returning_customers'],
                                 title="New vs Returning Customers Trend", markers=True)),
        dcc.Graph(figure=px.line(monthly_df, x='month', y=['new_percentage', 'returning_percentage'],
                                 title="New vs Returning Customers Percentage Trend", markers=True)),
        dcc.Graph(figure=px.bar(monthly_df, x='month', y=['total_revenue', 'new_customer_revenue', 'returning_customer_revenue'],
                                 title="Revenue Breakdown", barmode='group')),
        dcc.Graph(figure=px.bar(monthly_df, x='month', y=['new_customer_revenue', 'returning_customer_revenue'],
                                 title="New Customer Revenue vs Returning Customer Revenue", barmode='group')),
    ])



def get_metrics_layout():
    return html.Div([
        html.H1("Key Metrics"),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in metrics_df.columns],
            data=metrics_df.to_dict('records'),
            style_table={'overflowX': 'auto'}
        ),
    ])

# Combined Callback for Page Navigation & Refresh Button
@app.callback(
    [Output('page-content', 'children'),
     Output('refresh-status', 'children'),
     Output("refresh-btn", "children")],  # Updates button text
    [Input('url', 'pathname'), Input('refresh-btn', 'n_clicks')],
    prevent_initial_call=True
)
def update_page(pathname, n_clicks):
    """ Handles both page navigation and refresh button with a loading state """
    global data, monthly_df, metrics_df  

    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'refresh-btn.n_clicks':
        # Show "Refreshing..." Message
        return dash.no_update, "🕛 Refreshing data... Please wait.", "Refreshing..."

    if pathname == '/metrics':
        return get_metrics_layout(), "", "🔄 Refresh Data"
    elif pathname == '/weekly':
        return get_weekly_layout(), "", "🔄 Refresh Data"
    elif pathname == '/monthly':
        return get_insights_layout(), "", "🔄 Refresh Data"
    else:  # default to home
        return get_home_layout(), "", "🔄 Refresh Data"

# Callback to actually refresh data after some delay
@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('refresh-status', 'children', allow_duplicate=True),
     Output("refresh-btn", "children", allow_duplicate=True)],
    Input("refresh-btn", "n_clicks"),
    State('url', 'pathname'),
    prevent_initial_call=True
)
def refresh_dashboard(n_clicks, pathname):
    """ Simulates data reloading and updates the UI with a success message """
    global data, monthly_df, metrics_df  

    # Simulating a loading delay (Replace this with actual data fetch)
    time.sleep(3)

    # Reload data
    data = load_data()
    monthly_df = data['monthly_breakdown']
    monthly_df['month'] = monthly_df['month'].astype(str)

    weekly_df = data['weekly_breakdown']
    weekly_df['week'] = weekly_df['week'].astype(str)

    metrics = {
        "Basic LTV": data['Basic LTV'],
        "Advanced LTV": data['Advanced LTV'],
        "Average Purchase Value": data['Average Purchase Value'],
        "Average Purchase Frequency": data['Average Purchase Frequency'],
        "Average Customer Lifespan (Months)": data['Average Customer LifeSpan(Months)']
    }
    metrics_df = pd.DataFrame(metrics.items(), columns=["Metric", "Value"])
    metrics_df["Value"] = metrics_df["Value"].round(2).astype(str)

    if pathname == '/metrics':
        page_layout = get_metrics_layout()
    elif pathname == '/weekly':
        page_layout = get_weekly_layout()
    elif pathname=='monthly':
        page_layout = get_insights_layout()
    else:
        page_layout = get_home_layout()

    return page_layout, "✅ Data refreshed successfully!", "🔄 Refresh Data"



# Run the Dash app
if __name__ == '__main__':
    app.run(debug=True)
