import pandas as pd
import numpy as np

class FinancialTools:
    @staticmethod
    def calculate_returns(prices_series, in_percent=True): 
        """Berechnet die täglichen Renditen."""
        if prices_series.empty:
            return pd.Series(dtype='float64')
        if isinstance(prices_series, pd.DataFrame):
            if 'adj_close' in prices_series.columns:
                prices_series = prices_series['adj_close']
            elif 'close' in prices_series.columns:
                prices_series = prices_series['close']
            else:
                return pd.Series(dtype='float64')
        
        returns = prices_series.pct_change().dropna()
        if in_percent:
            return returns * 100 # Für die Anzeige in Prozent
        return returns # Für interne Berechnungen (Dezimalwerte)

    @staticmethod
    def calculate_cumulative_returns(prices_series):
        """Berechnet die kumulativen Renditen."""
        if prices_series.empty:
            return pd.Series(dtype='float64')
        daily_returns_raw = FinancialTools.calculate_returns(prices_series, in_percent=False)
        if daily_returns_raw.empty:
            return pd.Series(dtype='float64')
        return (1 + daily_returns_raw).cumprod() - 1

    @staticmethod
    def calculate_moving_average(prices_series, window=20):
        """Berechnet den gleitenden Durchschnitt."""
        if prices_series.empty:
            return pd.Series(dtype='float64')
        if isinstance(prices_series, pd.DataFrame):
            if 'adj_close' in prices_series.columns:
                prices_series = prices_series['adj_close']
            elif 'close' in prices_series.columns:
                prices_series = prices_series['close']
            else:
                return pd.Series(dtype='float64')
        
        return prices_series.rolling(window=window).mean()


    @staticmethod
    def calculate_volatility(prices_series, window=20):
        """Berechnet die rollierende Volatilität (Standardabweichung der Renditen)."""
        if prices_series.empty:
            return pd.Series(dtype='float64')
        
        # HIER: Rufe calculate_returns mit in_percent=False auf, um Dezimalwerte zu bekommen
        daily_returns_for_vol = FinancialTools.calculate_returns(prices_series, in_percent=False)
        
        if daily_returns_for_vol.empty:
            return pd.Series(dtype='float64')

        # Annualisiere die Volatilität
        return daily_returns_for_vol.rolling(window=window).std() * np.sqrt(252)


    @staticmethod
    def calculate_beta(stock_prices, market_prices, window=60):
        """
        Berechnet das rollierende Beta eines Wertpapiers relativ zu einem Marktindex.
        stock_prices: Pandas Series der Aktie
        market_prices: Pandas Series des Marktindex
        """
        if stock_prices.empty or market_prices.empty:
            return pd.Series(dtype='float64')
        
        # Sicherstellen, dass es Series sind, falls doch DataFrames übergeben werden
        if isinstance(stock_prices, pd.DataFrame):
            if 'adj_close' in stock_prices.columns:
                stock_prices = stock_prices['adj_close']
            elif 'close' in stock_prices.columns:
                stock_prices = stock_prices['close']
            else:
                return pd.Series(dtype='float64')
        
        if isinstance(market_prices, pd.DataFrame):
            if 'adj_close' in market_prices.columns:
                market_prices = market_prices['adj_close']
            elif 'close' in market_prices.columns:
                market_prices = market_prices['close']
            else:
                return pd.Series(dtype='float64')

        # HIER: Rufe calculate_returns mit in_percent=False auf, um Dezimalwerte zu bekommen
        returns_stock = FinancialTools.calculate_returns(stock_prices, in_percent=False)
        returns_market = FinancialTools.calculate_returns(market_prices, in_percent=False)

        # Kombiniere die Renditen und richte sie an den Daten aus
        combined_returns = pd.concat([returns_stock.rename('stock'), returns_market.rename('market')], axis=1).dropna()

        if combined_returns.empty:
            return pd.Series(dtype='float64')

        # Berechne die rollierende Kovarianz und Varianz
        rolling_covariance = combined_returns['stock'].rolling(window=window).cov(combined_returns['market'])
        rolling_variance = combined_returns['market'].rolling(window=window).var()

        # Berechne Beta
        beta = rolling_covariance / rolling_variance
        return beta.dropna()

