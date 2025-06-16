from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from flask import Flask, render_template, request, session, Response
from flask_session import Session
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from collections import OrderedDict
import json


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Read the csv file
dataframe = pd.read_csv("card_transactions_new.csv")

# Count transactions per agency and filter
agency_counts = dataframe["AGENCY"].value_counts().reset_index()
agency_counts.columns = ["AGENCY", "TRANSACTION_COUNT"]


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def index():
    agencies = agency_counts["AGENCY"].tolist()
    amount_of_transactions = agency_counts["TRANSACTION_COUNT"].tolist()
    
    return render_template("index.html", agencies=agencies, amount_of_transactions=amount_of_transactions)


@app.route("/select_agency", methods=["POST"])
def select_agency():
    agencies = agency_counts["AGENCY"].tolist()
    amount_of_transactions = agency_counts["TRANSACTION_COUNT"].tolist()
    
    selected_agency = str(request.form.get('agency'))
    
    # df_agency.to_csv("card_transaction_anomaly.csv", index=False)
    features = ["TRANSACTION_AMOUNT", "TRANSACTION_TIMESTAMP"]
    dataframe_transaction_amount_timestamp = find_anomalies_iforest(selected_agency, features)
    plot_transaction_amount_timestamp = scatter_plot(dataframe_transaction_amount_timestamp, "TRANSACTION_DATE", "TRANSACTION_AMOUNT", "Time", "Transaction Amount", "Transaction Amount Over Time")
    
    benfords_law_plot = benfords_law(selected_agency)
    
    # features = ["TRANSACTION_AMOUNT", "DAYS_SINCE_LAST_TRANSACTION"]
    # dataframe_transaction_amount_days_since_last_transaction = find_anomalies_iforest(selected_agency, features)
    # plot_transaction_amount_days_since_last_transaction = scatter_plot(dataframe_transaction_amount_days_since_last_transaction, "DAYS_SINCE_LAST_TRANSACTION", "TRANSACTION_AMOUNT", "Days", "Transaction Amount", "Purchase frequency")


    # weekday = scatter_plot(df_agency, selected_agency, "WEEKDAY", "TRANSACTION_AMOUNT")
    # weekday = scatter_plot(df_agency, selected_agency, "TRANSACTION_DATE", "TRANSACTION_AMOUNT")
    

    return render_template("index.html", selected_agency=selected_agency, agencies=agencies, amount_of_transactions=amount_of_transactions, plot_transaction_amount_timestamp=plot_transaction_amount_timestamp, benfords_law_plot=benfords_law_plot)


@app.route("/get_row", methods=["POST"])
def get_row():
    data = request.get_json()
    
    # print(data)
    objectid = data.get("index") 
    row = dataframe[dataframe["OBJECTID"] == int(objectid)].iloc[0].to_dict()
    
    row["TRANSACTION_DATE"] = pd.to_datetime(row["TRANSACTION_DATE"]).strftime("%Y-%m-%d %I:%M")
    row["TRANSACTION_AMOUNT"] = f"${row['TRANSACTION_AMOUNT']:.2f}"
    
    # Removing non relevant keys
    for key in ["OBJECTID", "HOUR", "VENDOR_STATE_PROVINCE_ENC", "TRANSACTION_TIMESTAMP", "WEEKDAY"]:
        row.pop(key, None)

    # Renamin keys
    renamed = {
        "Vendor Name": row.pop("VENDOR_NAME"),
        "Agency": row.pop("AGENCY"),
        "Merchant Category": row.pop("MCC_DESCRIPTION"),
        "Transaction Amount": row.pop("TRANSACTION_AMOUNT"),
        "Transaction Date": row.pop("TRANSACTION_DATE"),
        "Vendor State": row.pop("VENDOR_STATE_PROVINCE"),
        "Days Since Last Transaction": row.pop("DAYS_SINCE_LAST_TRANSACTION"),
        "Transaction Report / Modification Delays": row.pop("MOD_DELAY_DAYS")
    }

    custom_order = [
        "Agency",
        "Transaction Amount",
        "Vendor Name",
        "Vendor State",
        "Merchant Category",
        "Transaction Date",
        "Transaction Report / Modification Delays",
        "Days Since Last Transaction"
    ]

    ordered_row = OrderedDict((key, renamed[key]) for key in custom_order)

    print(type(row))
    print(row)
    print(ordered_row)
    
    return Response(json.dumps(ordered_row), mimetype='application/json')


def benfords_law(agency_name):
    # Select specific agency
    df_agency = dataframe[dataframe["AGENCY"] == agency_name].copy()
    
    first_digits = (
        df_agency[df_agency['TRANSACTION_AMOUNT'] > 0]['TRANSACTION_AMOUNT']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str[0]
        .astype(int)
    )
    
    digit_counts = first_digits.value_counts(normalize=True).sort_index()

    # Expected Benford distribution
    benford_x = list(range(1, 10))
    benford_y = [np.log10(1 + 1/d) for d in benford_x]

    # Prepare plot
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=digit_counts.index.astype(str),
        y=digit_counts.values,
        name="Observed",
        marker_color='blue',
        opacity=0.7
    ))

    fig.add_trace(go.Scatter(
        x=[str(d) for d in benford_x],
        y=benford_y,
        mode='lines+markers',
        name="Benford's Law",
        line=dict(color='red')
    ))

    fig.update_layout(
        title=f"Benford's Law - {agency_name}",
        xaxis_title="First Digit",
        yaxis_title="Proportion",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99)
    )
    
    # Render as embeddable HTML
    plot_html = pio.to_html(fig, full_html=False)
    
    return plot_html


def scatter_plot(dataframe, x, y, xlabel, ylabel, title):
    fig = px.scatter(
        dataframe,
        x=x,
        y=y,
        color=dataframe["anomaly"].map({1: "Normal", -1: "Anomaly"}),
        color_discrete_map={"Normal": "blue", "Anomaly": "red"},
        title=title,
        custom_data=[dataframe["OBJECTID"]]
    )
    
    # labelling the axis
    fig.update_layout(
        xaxis_title=xlabel,
        yaxis_title=ylabel
    )
    
    # Changing the style of the title
    fig.update_layout(
        title={
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
    }
    )

    # Render as embeddable HTML
    plot_html = pio.to_html(fig, full_html=False)
    
    return plot_html

def find_anomalies_iforest(selected_agency, features):
    
    dataframe["TRANSACTION_TIMESTAMP"] = pd.to_datetime(dataframe["TRANSACTION_DATE"], errors="coerce").astype(int) // 10**9        
    
    # Select specific agency
    df_agency = dataframe[dataframe["AGENCY"] == selected_agency].copy()

    # Use only relevant features
    
    X_agency = df_agency[features]

    # Scale the features
    scaler = StandardScaler()
    X_agency_scaled = scaler.fit_transform(X_agency)

    # Fit Isolation Forest
    iso_forest = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    df_agency["anomaly"] = iso_forest.fit_predict(X_agency_scaled)
    
    return df_agency
