# ANOMALY DETECTION ON PURCHASE CARD TRANSACTIONS
### Description
With this app you can look up anomalies in card transactions of US agencies.


### Starting the App
```
pip install -r requirements.txt
```

```
python3.12 -m flask run
```

open http://127.0.0.1:5000 in browser

## Usage
### Selecting Agency
Select your desired agency in the select menu.

### Anomaly details
- Click on a datapoint in the graph to get more insights of the data.
- Compare Benford's Law with the observed data


## Project Structure
```
anomaly_detection_digitalisierung_banken/
│
├── static/                       
│   ├── styles.css                     # Stylesheet
│   └── anomaly_detection_icon.jpg     # Icon of the website
│
├── templeates/                       
│   ├── layout.html                    # Website template
│   └── index.html                     # All components of the website
│
├── card_transactions_new.csv          # The dataset
│
└── app.py                             # Main application
```