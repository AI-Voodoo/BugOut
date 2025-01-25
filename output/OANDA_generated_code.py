import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# Constants
API_TOKEN = "7d6aebe7f36f3c0218dcf114c699f376-5c24095f0da4f93f35a4f02830c8ee99"
ACCOUNT_ID = "101-002-14006337-001"
INSTRUMENT = "WTICO_USD"
OUTPUT_PATH = "output/"

def fetch_historical_data(api_token, account_id, instrument, count=100):
    client = oandapyV20.API(access_token=api_token)
    params = {
        "count": count,
        "granularity": "M1"
    }
    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    client.request(r)
    return r.response['candles']

def prepare_data(candles):
    data = []
    for candle in candles:
        data.append([candle['mid']['o'], candle['mid']['h'], candle['mid']['l'], candle['mid']['c'], candle['volume']])
    df = pd.DataFrame(data, columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    return df

def train_model(df):
    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = (df['Close'].shift(-1) > df['Close']).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    return model, X_test, y_test

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return accuracy

def save_outputs(model, df, accuracy):
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    df.to_csv(f"{OUTPUT_PATH}training_data.csv", index=False)
    joblib.dump(model, f"{OUTPUT_PATH}model.pkl")
    with open(f"{OUTPUT_PATH}model_accuracy.txt", "w") as f:
        f.write(f"Model Accuracy: {accuracy:.2f}")

def main():
    candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
    df = prepare_data(candles)
    model, X_test, y_test = train_model(df)
    accuracy = evaluate_model(model, X_test, y_test)
    save_outputs(model, df, accuracy)

if __name__ == "__main__":
    main()

import unittest

class TestOANDAAPI(unittest.TestCase):

    def test_fetch_historical_data(self):
        candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
        self.assertIsNotNone(candles, "Historical data should be fetched")

    def test_prepare_data(self):
        candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
        df = prepare_data(candles)
        self.assertIsNotNone(df, "Data should be prepared")
        self.assertGreater(len(df), 0, "Dataframe should not be empty")

    def test_train_model(self):
        candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
        df = prepare_data(candles)
        model, _, _ = train_model(df)
        self.assertIsNotNone(model, "Model should be trained")

    def test_evaluate_model(self):
        candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
        df = prepare_data(candles)
        model, X_test, y_test = train_model(df)
        accuracy = evaluate_model(model, X_test, y_test)
        self.assertGreater(accuracy, 0.5, "Model accuracy should be greater than 50%")

    def test_save_outputs(self):
        candles = fetch_historical_data(API_TOKEN, ACCOUNT_ID, INSTRUMENT)
        df = prepare_data(candles)
        model, X_test, y_test = train_model(df)
        accuracy = evaluate_model(model, X_test, y_test)
        save_outputs(model, df, accuracy)
        self.assertTrue(os.path.exists(f"{OUTPUT_PATH}training_data.csv"), "Training data should be saved")
        self.assertTrue(os.path.exists(f"{OUTPUT_PATH}model.pkl"), "Model should be saved")
        self.assertTrue(os.path.exists(f"{OUTPUT_PATH}model_accuracy.txt"), "Model accuracy should be saved")

if __name__ == "__main__":
    unittest.main()