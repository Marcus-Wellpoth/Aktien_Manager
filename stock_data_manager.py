import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime

class StockDataManager:
    def __init__(self, db_name="stock_data.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect_db()
        self._create_tables()

    def _connect_db(self):
        """Stellt eine Verbindung zur SQLite-Datenbank her."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"Erfolgreich mit Datenbank '{self.db_name}' verbunden.")
        except sqlite3.Error as e:
            print(f"Fehler beim Verbinden mit der Datenbank: {e}")

    def _create_tables(self):
        """Erstellt die Tabellen für Aktiendaten, falls sie noch nicht existieren."""
        if not self.conn:
            print("Keine Datenbankverbindung vorhanden.")
            return

        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    company_name TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    adj_close REAL,
                    volume INTEGER,
                    FOREIGN KEY (symbol) REFERENCES stocks (symbol) ON DELETE CASCADE,
                    UNIQUE (symbol, date)
                )
            ''')
            self.conn.commit()
            print("Datenbanktabellen überprüft/erstellt.")
        except sqlite3.Error as e:
            print(f"Fehler beim Erstellen der Tabellen: {e}")

    def add_stock(self, symbol, company_name=""):
        """Fügt ein Aktiensymbol zur 'stocks'-Tabelle hinzu."""
        if not self.conn: return
        try:
            self.cursor.execute("INSERT OR IGNORE INTO stocks (symbol, company_name) VALUES (?, ?)", (symbol.upper(), company_name))
            self.conn.commit()
            print(f"Aktie '{symbol.upper()}' zur Datenbank hinzugefügt (falls neu).")
            return True
        except sqlite3.Error as e:
            print(f"Fehler beim Hinzufügen der Aktie {symbol}: {e}")
            return False

    def get_all_symbols(self):
        """Gibt eine Liste aller in der Datenbank gespeicherten Symbole zurück."""
        if not self.conn: return []
        self.cursor.execute("SELECT symbol FROM stocks")
        return [row[0] for row in self.cursor.fetchall()]

    def fetch_and_store_data(self, symbol, period="1y"):
        """
        Holt historische Kursdaten für ein Symbol und speichert sie in der Datenbank.
        period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        """
        symbol = symbol.upper()
        print(f"Hole Daten für {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y", auto_adjust=False)
            if hist.empty:
                print(f"Keine Daten für {symbol} gefunden oder ungültiges Symbol.")
                return False

            # Füge das Symbol hinzu, falls es noch nicht existiert (z.B. wenn es direkt per API geholt wird)
            self.add_stock(symbol, ticker.info.get('longName', ''))

            data_to_insert = []
            for date, row in hist.iterrows():
                # Formatiere Datum als YYYY-MM-DD
                date_str = date.strftime('%Y-%m-%d')
                data_to_insert.append((
                    symbol,
                    date_str,
                    row['Open'],
                    row['High'],
                    row['Low'],
                    row['Close'],
                    row['Adj Close'],
                    row['Volume']
                ))
            
            # Verwende INSERT OR IGNORE, um Duplikate zu vermeiden
            self.cursor.executemany("""
                INSERT OR IGNORE INTO daily_prices (symbol, date, open, high, low, close, adj_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            self.conn.commit()
            print(f"Daten für {symbol} erfolgreich gespeichert/aktualisiert.")
            return True
        except Exception as e:
            print(f"Fehler beim Holen/Speichern der Daten für {symbol}: {e}")
            return False

    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """
        Holt historische Kursdaten für ein Symbol aus der Datenbank als Pandas DataFrame.
        Optional: Filter nach Start- und Enddatum.
        """
        symbol = symbol.upper()
        query = "SELECT date, open, high, low, close, adj_close, volume FROM daily_prices WHERE symbol = ?"
        params = [symbol]

        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.append(start_date)
            params.append(end_date)
        elif start_date:
            query += " AND date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date ASC"

        try:
            df = pd.read_sql(query, self.conn, params=params, parse_dates=['date'], index_col='date')
            if df.empty:
                print(f"Keine Daten für {symbol} im angegebenen Zeitraum in der Datenbank gefunden.")
            return df
        except sqlite3.Error as e:
            print(f"Fehler beim Abrufen der Daten für {symbol} aus der Datenbank: {e}")
            return pd.DataFrame()

    def close(self):
        """Schließt die Datenbankverbindung."""
        if self.conn:
            self.conn.close()
            print("Datenbankverbindung geschlossen.")

# Beispielnutzung (kann später entfernt werden, wenn GUI fertig ist)
if __name__ == "__main__":
    manager = StockDataManager("my_stocks.db")

    # Symbole aus CSV hinzufügen (Beispiel)
    # Angenommen, du hast eine stocks.csv mit 'Symbol,CompanyName'
    # Beispiel-CSV-Inhalt:
    # Symbol,CompanyName
    # AAPL,Apple Inc.
    # MSFT,Microsoft Corp.
    # GOOGL,Alphabet Inc. (GOOGL)
    # AMZN,Amazon.com Inc.
    
    csv_file = "stocks.csv" # Erstelle diese Datei manuell für den Test

    try:
        df_symbols = pd.read_csv(csv_file)
        for index, row in df_symbols.iterrows():
            manager.add_stock(row['Symbol'], row.get('CompanyName', ''))
    except FileNotFoundError:
        print(f"'{csv_file}' nicht gefunden. Bitte erstellen Sie eine CSV-Datei mit 'Symbol,CompanyName'.")
    except KeyError:
        print(f"Fehler: '{csv_file}' muss Spalten 'Symbol' und optional 'CompanyName' enthalten.")


    symbols_to_fetch = manager.get_all_symbols()
    if not symbols_to_fetch:
        # Fallback: Wenn CSV leer ist oder nicht existiert, einige bekannte Symbole holen
        symbols_to_fetch = ["AAPL", "MSFT", "GOOGL"]
        for s in symbols_to_fetch:
            manager.add_stock(s)

    for symbol in symbols_to_fetch:
        manager.fetch_and_store_data(symbol, period="1y") # Holt Daten für 1 Jahr

    # Testen des Datenabrufs
    aapl_data = manager.get_stock_data("AAPL")
    if not aapl_data.empty:
        print("\nAAPL Daten (erste 5 Reihen):")
        print(aapl_data.head())
    
    msft_data = manager.get_stock_data("MSFT", start_date="2024-01-01")
    if not msft_data.empty:
        print("\nMSFT Daten seit 2024-01-01 (letzte 5 Reihen):")
        print(msft_data.tail())

    manager.close()