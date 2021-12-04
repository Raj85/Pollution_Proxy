#import os
#import pathlib

import dash
from dash import dcc
from dash import html
import pandas as pd
from dash.dependencies import Input, Output, State
from urllib.request import urlopen
import json
import plotly.express as px
import plotly.graph_objects as go
import cufflinks as cf  # Connects plotly with pandas (for df.iplot)
cf.go_offline()
cf.set_config_file(offline=False, world_readable=True)


# ============================================================ Initialize app ============================================================
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],)
app.title = "Pollution Proxy"
server = app.server


# ============================================================ Load data ============================================================
#APP_PATH = str(pathlib.Path(__file__).parent.resolve())
#print("App location: ",APP_PATH)
#print("\n")

# Geojson
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    geojson = json.load(response)


# Geomapping data
df_lat_lon = pd.read_csv("us-county-boundaries.csv", delimiter=';')
#print("Lat-Lon Data Columns: ",df_lat_lon.columns)
#print("\n")

# GEOID is what this whole section is trying to do (except for zero filling the state code)
# Need to cast them as strings, as they are int64 types
df_lat_lon["COUNTYFP"] = df_lat_lon["COUNTYFP"].astype(str)
df_lat_lon["STATEFP"] = df_lat_lon["STATEFP"].astype(str)
df_lat_lon["COUNTYFP"] = df_lat_lon["COUNTYFP"].apply(lambda x: str(x).zfill(3))  # Fill county code first
df_lat_lon["STATEFP"] = df_lat_lon["STATEFP"].apply(lambda x: str(x).zfill(2))  # Then fill state code first
df_lat_lon["FIPS"] = df_lat_lon["STATEFP"] + df_lat_lon["COUNTYFP"]  # Combine to get true FIPS county code

lat_lon = df_lat_lon["Geo Point"].apply(lambda x: x.split(","))
df_lat_lon["Latitude"] = lat_lon.apply(lambda x: x[0])
df_lat_lon["Longitude"] = lat_lon.apply(lambda x: x[1])


# AQI data
df_full_data = pd.read_csv("finalprojectdata_metrics_from_2014.csv")
# print("AQI Data Columns: ",df_full_data.columns)
# print("\n")

df_full_data["FIPS"] = df_full_data["countyFIPS"].apply(lambda x: str(x).zfill(5))  # Fill just in case

minAQI = min(df_full_data["Median AQI"])
maxAQI = max(df_full_data["Median AQI"])


# Predicted data
df_2020_forecast = pd.read_csv("forecasting_2020.csv")
df_2020_forecast["FIPS"] = df_2020_forecast["countyFIPS"].apply(lambda x: str(x).zfill(5))  # Fill just in case
df_2020_forecast.rename(columns={"Median_AQI": "Median AQI"}, inplace=True)

df_2021_forecast = pd.read_csv("forecasting_2021.csv")
df_2021_forecast["FIPS"] = df_2021_forecast["countyFIPS"].apply(lambda x: str(x).zfill(5))  # Fill just in case
df_2021_forecast.rename(columns={"Median_AQI": "Median AQI"}, inplace=True)


# Combine dataframes -> THOUGH THIS MIGHT NOT BE NECESARY, IT'S A WAY TO LIMIT TO MEMORY REQUIREMENT PER CALLBACK SINCE THIS DATA IS LOADED IN TO MEMORY EACH TIME THAT HAPPENS
df_lat_lon_only = df_lat_lon[["FIPS", "NAME", "STATE_NAME", "Latitude", "Longitude"]]  # Also need name in one of these df's
df_medAQI_only = df_full_data[["FIPS", "Year", "Median AQI"]]
df_partial_data = df_full_data[["FIPS", "Year", "Median AQI", "goodday%", "unhealthyday%", "goodday%", "goodday%", "goodday%",]]

df_medAQI_only_2020 = df_2020_forecast[["FIPS", "Year", "Median AQI"]]  # Only use median AQI from 2020 (contains data for all years)
df_medAQI_only_2021 = df_2021_forecast[["FIPS", "Year", "Median AQI"]]  # Only use median AQI from 2021 (contains data for all years)


#df_combined = df_medAQI_only.join(df_lat_lon_only, on="FIPS")  # Join throws a ValueType error even though all data is of the same type (indices seem to be the same as well)... but merge seems to work
df_combined = df_medAQI_only.merge(df_lat_lon_only, on="FIPS")
df_combined_2020 = df_medAQI_only_2020.merge(df_lat_lon_only, on="FIPS")
df_combined_2021 = df_medAQI_only_2021.merge(df_lat_lon_only, on="FIPS")


# ============================================================ App layout ============================================================
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.H4(children="US Air Pollution by County"),
                html.P(
                    id="description",
                    children="Over the years, air quality has been closely monitored due to the effect it has       \
                              on human health and the environment. The COVID-19 pandemic has had a major impact on  \
                              human behaviors due to the policies put in place nationwide by policy makers and      \
                              health officials aiming to limit the amount of exposure that individuals have to the virus.",
                ),
            ],
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                ),
                                dcc.Slider(
                                    id="years-slider",
                                    min=2014,
                                    max=2021.8,  # Helps with display (2021 forecast gets squished)
                                    value=2014,  # Default value
                                    marks={
                                        2014: {"label": "2014", "style": {"color": "#45454D"}},
                                        2015: {"label": "2015", "style": {"color": "#45454D"}},
                                        2016: {"label": "2016", "style": {"color": "#45454D"}},
                                        2017: {"label": "2017", "style": {"color": "#45454D"}},
                                        2018: {"label": "2018", "style": {"color": "#45454D"}},
                                        2019: {"label": "2019", "style": {"color": "#45454D"}},
                                        2020: {"label": "2020", "style": {"color": "#45454D"}},
                                        2020.5: {"label": "2020 forecast", "style": {"color": "#45454D"}},
                                        2021: {"label": "2021", "style": {"color": "#45454D"}},
                                        2021.5: {"label": "2021 forecast", "style": {"color": "#45454D"}},
                                    },
                                    step=None  # Allows discrete fractical values
                                ),
                            ],
                        ),
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.P(
                                    "Heatmap of AQI based on a variety of different factors in {0}".format(
                                        2014  # Default value
                                    ),
                                    id="heatmap-title",
                                ),
                                dcc.Graph(
                                    id="county-choropleth",
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="graph-container",
                    children=[
                        html.P(id="chart-selector", children="Select chart:"),
                        dcc.Dropdown(
                            options=[
                                {
                                    "label": "Median AQI",
                                    "value": "median_aqi",
                                },
                                {
                                    "label": "Good Day %",
                                    "value": "good_day_perc",
                                },
                                {
                                    "label": "Unhealthy Day %",
                                    "value": "unhealthy_day_perc",
                                },
                                {
                                    "label": "Hazardous Day %",
                                    "value": "hazardous_day_perc",
                                },
                                {
                                    "label": "AQI due to Ozone %",
                                    "value": "ozone_perc",
                                },
                                {
                                    "label": "AQI due to NO2 %",
                                    "value": "no2_perc",
                                },
                                {
                                    "label": "AQI due to PM2.5 %",
                                    "value": "pm2p5_perc",
                                },
                                {
                                    "label": "AQI per Population",
                                    "value": "aqi_per_pop",
                                },
                            ],
                            value="median_aqi",  # Default value
                            id="chart-dropdown",
                        ),
                        dcc.Graph(
                            id="selected-data",
                            figure=dict(
                                data=[dict(x=0, y=0)],
                                layout=dict(
                                    paper_bgcolor="#45454D",
                                    plot_bgcolor="#F4F4F8",
                                    autofill=True,
                                    margin=dict(t=75, r=50, b=100, l=50),
                                ),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ============================================================ App callbacks ============================================================
@app.callback(
    Output("county-choropleth", "figure"),
    [Input("years-slider", "value")],
)
def display_map(year):

    # Filter the combined df by year
    if (year == 2020.5):
        actYear = 2020  # Actual year
        yearFilt = df_combined_2020.loc[df_combined_2020["Year"] == actYear]
    elif (year == 2021.5):
        actYear = 2021  # Actual year
        yearFilt = df_combined_2021.loc[df_combined_2021["Year"] == actYear]
    else:
        yearFilt = df_combined.loc[df_combined["Year"] == year]
    
    # TODO: Create custom hovers
    fig = px.choropleth(yearFilt, geojson=geojson, locations="FIPS", color="Median AQI",
                        color_continuous_scale="matter",
                        range_color=[minAQI, maxAQI],
                        scope="usa",
                        hover_data=["NAME", "STATE_NAME"],
                        labels={"NAME": "County", "STATE_NAME": "State", "Median AQI": "AQI"},
                        template="plotly_dark")
    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    #fig.update_traces(hovertemplate="County: %{}".format(yearFilt["NAME"]))  # Displays the entire Series...

    return fig


# Year slider
@app.callback(
    Output("heatmap-title", "children"), 
    [Input("years-slider", "value")]
)
def update_map_title(year):
    print("Year selected by slider: ",year)
    return "Heatmap of AQI based on a variety of different factors in {0}".format(year)


 # Barchart callback
@app.callback(
    Output("selected-data", "figure"),
    [
        Input("county-choropleth", "selectedData"),
        Input("chart-dropdown", "value"),
        Input("years-slider", "value"),
    ],
)
def display_selected_data(selectedData, chart_dropdown, year):

    if selectedData is None:
        return dict(
            data=[dict(x=0, y=0)],
            layout=dict(
                title="Click-drag on the map to select counties",
                paper_bgcolor="#0F0F0F",
                plot_bgcolor="#0F0F0F",
                font=dict(color="#A260BE"),
                margin=dict(t=75, r=50, b=100, l=75),
            ),
        )

    pts = selectedData["points"]
    fips = [pt["location"] for pt in pts]

    if (year == 2020.5):
        year = 2020  # Re-write correct year
        dfd = df_2020_forecast[df_2020_forecast["FIPS"].isin(fips)]
    elif (year == 2021.5):
        year = 2021  # Re-write correct year
        dfd = df_2021_forecast[df_2021_forecast["FIPS"].isin(fips)]
    else:
        dfd = df_full_data[df_full_data["FIPS"].isin(fips)]


    if chart_dropdown == "median_aqi":
        title = "Median AQI per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "Median AQI"
    elif chart_dropdown == "good_day_perc":
        title = "Good Day % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "goodday%"
    elif chart_dropdown == "unhealthy_day_perc":
        title = "Unhealthy Day % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "unhealthyday%"
    elif chart_dropdown == "hazardous_day_perc":
        title = "Hazardous Day % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "hazardousday%"
    elif chart_dropdown == "ozone_perc":
        title = "AQI Due to Ozone % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "ozoneday%"
    elif chart_dropdown == "no2_perc":
        title = "AQI Due to NO2 % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "NO2day%"
    elif chart_dropdown == "pm2p5_perc":
        title = "AQI Due to PM2.5 % per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "PM2.5day%"
    elif chart_dropdown == "aqi_per_pop":
        title = "AQI per Population per county, <b>" + str(year) + "</b>"    
        AGGREGATE_BY = "AQI_per_population"

    filteredData = dfd[dfd.Year == year]
    groupedData = filteredData.groupby("County")[AGGREGATE_BY].sum()
    groupedData = groupedData.sort_values()
    fig = groupedData.iplot(
            kind="bar", y=AGGREGATE_BY, title=title, asFigure=True
        )

    fig_layout = fig["layout"]
    fig_data = fig["data"]

    fig_data[0]["text"] = groupedData.values.tolist()
    fig_data[0]["marker"]["color"] = "#A260BE"
    fig_data[0]["marker"]["opacity"] = 1
    fig_data[0]["marker"]["line"]["width"] = 0
    fig_data[0]["textposition"] = "outside"
    fig_layout["paper_bgcolor"] = "#0F0F0F"
    fig_layout["plot_bgcolor"] = "#0F0F0F"
    fig_layout["font"]["color"] = "#A260BE"
    fig_layout["title"]["font"]["color"] = "#A260BE"
    fig_layout["xaxis"]["tickfont"]["color"] = "#A260BE"
    fig_layout["yaxis"]["tickfont"]["color"] = "#A260BE"
    fig_layout["xaxis"]["gridcolor"] = "#0F0F0F"  # Same as background to negate axis grid
    fig_layout["yaxis"]["gridcolor"] = "#6A6A6A"
    fig_layout["margin"]["t"] = 75
    fig_layout["margin"]["r"] = 50
    fig_layout["margin"]["b"] = 100
    fig_layout["margin"]["l"] = 50

    return fig


# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
