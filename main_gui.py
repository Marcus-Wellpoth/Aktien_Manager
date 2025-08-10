import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QComboBox, QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QDateEdit, QSizePolicy)
from PyQt6.QtCore import QDate, Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import datetime

from stock_data_manager import StockDataManager
from financial_tools import FinancialTools

class MplCanvas(FigureCanvas):
    """Matplotlib Canvas für die Einbettung in PyQt."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()

class StockAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aktienanalyse-Tool")
        self.setGeometry(100, 100, 1200, 800)

        self.db_manager = StockDataManager("stock_analysis.db")
        self.financial_tools = FinancialTools()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._create_top_panel()
        self._create_tabs()
        self._load_initial_data()

    def _create_top_panel(self):
        """Erstellt das obere Panel für CSV-Import und Symbol-Auswahl."""
        top_panel_layout = QHBoxLayout()

        # CSV Import
        csv_group_layout = QVBoxLayout()
        csv_group_layout.addWidget(QLabel("CSV-Datei mit Symbolen importieren (Symbol,CompanyName):"))
        self.csv_path_input = QLineEdit("stocks.csv")
        csv_group_layout.addWidget(self.csv_path_input)
        import_csv_button = QPushButton("CSV importieren & Daten holen")
        import_csv_button.clicked.connect(self._import_csv_and_fetch)
        csv_group_layout.addWidget(import_csv_button)
        top_panel_layout.addLayout(csv_group_layout)

        top_panel_layout.addStretch(1) # Abstandhalter

        # Symbol Auswahl
        symbol_selection_layout = QVBoxLayout()
        symbol_selection_layout.addWidget(QLabel("Aktie auswählen:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.currentIndexChanged.connect(self._on_symbol_selected)
        symbol_selection_layout.addWidget(self.symbol_combo)
        
        # Datumsbereich
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("Von:"))
        self.start_date_edit = QDateEdit(QDate.currentDate().addYears(-1))
        self.start_date_edit.setCalendarPopup(True)
        date_range_layout.addWidget(self.start_date_edit)
        date_range_layout.addWidget(QLabel("Bis:"))
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        date_range_layout.addWidget(self.end_date_edit)
        symbol_selection_layout.addLayout(date_range_layout)

        # Refresh Button
        refresh_data_button = QPushButton("Daten aktualisieren")
        refresh_data_button.clicked.connect(self._refresh_selected_stock_data)
        symbol_selection_layout.addWidget(refresh_data_button)


        top_panel_layout.addLayout(symbol_selection_layout)

        self.main_layout.addLayout(top_panel_layout)

    def _create_tabs(self):
        """Erstellt die Reiter für verschiedene Ansichten."""
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.tab_overview = QWidget()
        self.tabs.addTab(self.tab_overview, "Übersicht & Kurse")
        self._setup_overview_tab()

        self.tab_returns = QWidget()
        self.tabs.addTab(self.tab_returns, "Renditen")
        self._setup_returns_tab()

        self.tab_ma = QWidget()
        self.tabs.addTab(self.tab_ma, "Gleitender Durchschnitt")
        self._setup_ma_tab()

        self.tab_volatility = QWidget()
        self.tabs.addTab(self.tab_volatility, "Volatilität")
        self._setup_volatility_tab()
        
        self.tab_beta = QWidget()
        self.tabs.addTab(self.tab_beta, "Beta (Marktabhängigkeit)")
        self._setup_beta_tab()


    def _setup_overview_tab(self):
        layout = QVBoxLayout(self.tab_overview)
        self.overview_canvas = MplCanvas(self.tab_overview, width=10, height=6)
        layout.addWidget(self.overview_canvas)
        self.overview_text = QLabel("Kursdaten:")
        layout.addWidget(self.overview_text)

    def _setup_returns_tab(self):
        layout = QVBoxLayout(self.tab_returns)
        self.returns_canvas = MplCanvas(self.tab_returns, width=10, height=6)
        layout.addWidget(self.returns_canvas)
        self.returns_text = QLabel("Renditen:")
        layout.addWidget(self.returns_text)

    def _setup_ma_tab(self):
        layout = QVBoxLayout(self.tab_ma)
        ma_controls_layout = QHBoxLayout()
        ma_controls_layout.addWidget(QLabel("Fenster (Tage):"))
        self.ma_window_input = QLineEdit("20")
        self.ma_window_input.setFixedWidth(50)
        ma_controls_layout.addWidget(self.ma_window_input)
        self.ma_apply_button = QPushButton("Anwenden")
        self.ma_apply_button.clicked.connect(self._plot_ma)
        ma_controls_layout.addWidget(self.ma_apply_button)
        ma_controls_layout.addStretch(1)
        layout.addLayout(ma_controls_layout)

        self.ma_canvas = MplCanvas(self.tab_ma, width=10, height=6)
        layout.addWidget(self.ma_canvas)
        self.ma_text = QLabel("Gleitender Durchschnitt:")
        layout.addWidget(self.ma_text)

    def _setup_volatility_tab(self):
        layout = QVBoxLayout(self.tab_volatility)
        vol_controls_layout = QHBoxLayout()
        vol_controls_layout.addWidget(QLabel("Fenster (Tage):"))
        self.vol_window_input = QLineEdit("20")
        self.vol_window_input.setFixedWidth(50)
        vol_controls_layout.addWidget(self.vol_window_input)
        self.vol_apply_button = QPushButton("Anwenden")
        self.vol_apply_button.clicked.connect(self._plot_volatility)
        vol_controls_layout.addStretch(1)
        layout.addLayout(vol_controls_layout)

        self.vol_canvas = MplCanvas(self.tab_volatility, width=10, height=6)
        layout.addWidget(self.vol_canvas)
        self.vol_text = QLabel("Volatilität:")
        layout.addWidget(self.vol_text)

    def _setup_beta_tab(self):
        layout = QVBoxLayout(self.tab_beta)
        beta_controls_layout = QHBoxLayout()
        beta_controls_layout.addWidget(QLabel("Markt-Symbol (z.B. SPY):"))
        self.market_symbol_input = QLineEdit("SPY")
        self.market_symbol_input.setFixedWidth(100)
        beta_controls_layout.addWidget(self.market_symbol_input)
        beta_controls_layout.addWidget(QLabel("Fenster (Tage):"))
        self.beta_window_input = QLineEdit("60")
        self.beta_window_input.setFixedWidth(50)
        beta_controls_layout.addWidget(self.beta_window_input)
        self.beta_apply_button = QPushButton("Anwenden")
        self.beta_apply_button.clicked.connect(self._plot_beta)
        beta_controls_layout.addStretch(1)
        layout.addLayout(beta_controls_layout)

        self.beta_canvas = MplCanvas(self.tab_beta, width=10, height=6)
        layout.addWidget(self.beta_canvas)
        self.beta_text = QLabel("Beta-Wert:")
        layout.addWidget(self.beta_text)


    def _load_initial_data(self):
        """Lädt initial alle Symbole in die ComboBox."""
        symbols = self.db_manager.get_all_symbols()
        if not symbols:
            # Füge Standard-Symbole hinzu, wenn DB leer ist
            default_symbols = ["AAPL", "MSFT", "GOOGL"]
            for s in default_symbols:
                self.db_manager.add_stock(s)
            symbols = default_symbols # Aktualisiere die Liste
            # Optional: Initialdaten für Standard-Symbole holen
            # for s in symbols:
            #     self.db_manager.fetch_and_store_data(s, period="1y")

        self.symbol_combo.clear()
        self.symbol_combo.addItems(symbols)
        if symbols:
            self._on_symbol_selected(0) # Wähle das erste Symbol aus und zeige Daten

    def _import_csv_and_fetch(self):
        """Importiert Symbole aus CSV und holt Daten."""
        csv_file = self.csv_path_input.text()
        try:
            df_symbols = pd.read_csv(csv_file)
            imported_count = 0
            fetched_count = 0
            for index, row in df_symbols.iterrows():
                symbol = row['Symbol'].upper()
                company_name = row.get('CompanyName', '')
                if self.db_manager.add_stock(symbol, company_name):
                    imported_count += 1
                if self.db_manager.fetch_and_store_data(symbol, period="max"): # Holt max. verfügbare Daten
                    fetched_count += 1
            
            QMessageBox.information(self, "Import abgeschlossen",
                                    f"{imported_count} neue Symbole hinzugefügt.\n{fetched_count} Symbole aktualisiert/Daten geholt.")
            self._load_initial_data() # Symbole in ComboBox aktualisieren

        except FileNotFoundError:
            QMessageBox.warning(self, "Fehler", f"Datei '{csv_file}' nicht gefunden.")
        except KeyError:
            QMessageBox.warning(self, "Fehler", f"Die CSV-Datei muss Spalten 'Symbol' und optional 'CompanyName' enthalten.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    def _refresh_selected_stock_data(self):
        """Holt aktuelle Daten für das gerade ausgewählte Symbol."""
        selected_symbol = self.symbol_combo.currentText()
        if selected_symbol:
            # Holen der neuesten Daten (yfinance holt automatisch nur die fehlenden)
            if self.db_manager.fetch_and_store_data(selected_symbol, period="max"):
                QMessageBox.information(self, "Aktualisiert", f"Daten für {selected_symbol} wurden aktualisiert.")
                self._on_symbol_selected(self.symbol_combo.currentIndex()) # Ansichten neu laden
            else:
                QMessageBox.warning(self, "Fehler", f"Konnte Daten für {selected_symbol} nicht aktualisieren.")
        else:
            QMessageBox.information(self, "Info", "Kein Symbol ausgewählt.")


    def _get_current_stock_data(self):
        """Hilfsfunktion zum Abrufen der aktuellen Aktiendaten basierend auf Auswahl."""
        selected_symbol = self.symbol_combo.currentText()
        if not selected_symbol:
            return pd.DataFrame()

        start_date_q = self.start_date_edit.date()
        end_date_q = self.end_date_edit.date()

        start_date_str = start_date_q.toString("yyyy-MM-dd")
        end_date_str = end_date_q.toString("yyyy-MM-dd")

        data = self.db_manager.get_stock_data(selected_symbol, start_date_str, end_date_str)
        return data

    def _on_symbol_selected(self, index):
        """Wird aufgerufen, wenn ein neues Symbol in der ComboBox ausgewählt wird."""
        self.plot_all_tabs()

    def plot_all_tabs(self):
        """Aktualisiert alle Diagramme und Texte in den Tabs."""
        data = self._get_current_stock_data()
        if data.empty:
            self._clear_all_plots()
            self.overview_text.setText("Keine Daten verfügbar für das ausgewählte Symbol oder den Zeitraum.")
            self.returns_text.setText("Keine Daten verfügbar.")
            self.ma_text.setText("Keine Daten verfügbar.")
            self.vol_text.setText("Keine Daten verfügbar.")
            self.beta_text.setText("Keine Daten verfügbar.")
            return

        self._plot_overview(data)
        self._plot_returns(data)
        self._plot_ma(data) # Kann überschrieben werden, wenn MA-Button geklickt wird
        self._plot_volatility(data) # Kann überschrieben werden, wenn Vol-Button geklickt wird
        self._plot_beta(data) # Kann überschrieben werden, wenn Beta-Button geklickt wird


    def _clear_plot(self, canvas):
        """Löscht einen Plot."""
        canvas.axes.clear()
        canvas.draw()

    def _clear_all_plots(self):
        self._clear_plot(self.overview_canvas)
        self._clear_plot(self.returns_canvas)
        self._clear_plot(self.ma_canvas)
        self._clear_plot(self.vol_canvas)
        self._clear_plot(self.beta_canvas)


    def _plot_overview(self, data):
        self._clear_plot(self.overview_canvas)
        ax = self.overview_canvas.axes
        ax.plot(data.index, data['adj_close'], label='Schlusskurs', color='blue')
        ax.set_title(f"{self.symbol_combo.currentText()} - Schlusskurs")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Kurs")
        ax.legend()
        ax.grid(True)
        self.overview_canvas.draw()
        self.overview_text.setText(f"Aktueller Kurs: {data['adj_close'].iloc[-1]:.2f}\n"
                                   f"Datum: {data.index[-1].strftime('%Y-%m-%d')}\n"
                                   f"Anzahl Datenpunkte: {len(data)}")


    def _plot_returns(self, data):
        self._clear_plot(self.returns_canvas)
        ax = self.returns_canvas.axes

        # Sicherstellen, dass calculate_returns und calculate_cumulative_returns die Series erhalten
        # und die Ausgabe der calculate_returns Funktion in Dezimalwerten ist, nicht in Prozent.
        # Ich habe das in FinancialTools vorgeschlagen, falls du es dort nicht direkt *100 machst.
        # Hier ist es wichtig, dass 'data['adj_close']' übergeben wird.
        daily_returns = self.financial_tools.calculate_returns(data['adj_close'])
        cumulative_returns = self.financial_tools.calculate_cumulative_returns(data['adj_close'])

        if not daily_returns.empty:
            ax.plot(daily_returns.index, daily_returns, label='Tägliche Rendite', color='green', alpha=0.7)
            ax.set_title(f"{self.symbol_combo.currentText()} - Tägliche Renditen")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Rendite (%)") # Hier ist "%" wichtig
            ax.grid(True)
            self.returns_canvas.draw()

            # Jetzt die Fehlerbehebung für die Textausgabe
            avg_daily_return = daily_returns.mean()
            # Überprüfe, ob es ein gültiger Zahlenwert ist, bevor formatiert wird
            avg_daily_return_str = f"{avg_daily_return:.4f}" if pd.notna(avg_daily_return) else "N/A"

            last_cumulative_return = cumulative_returns.iloc[-1]
            last_cumulative_return_str = f"{last_cumulative_return:.4f}" if pd.notna(last_cumulative_return) else "N/A"


            self.returns_text.setText(f"Durchschn. tägl. Rendite: {avg_daily_return_str}\n"
                                     f"Kumulierte Rendite (Gesamt): {last_cumulative_return_str}")
        else:
            self._clear_plot(self.returns_canvas)
            self.returns_text.setText("Nicht genügend Daten für Renditeberechnung.")


    def _plot_ma(self, data):
        self._clear_plot(self.ma_canvas)
        ax = self.ma_canvas.axes
        try:
            window = int(self.ma_window_input.text())
        except ValueError:
            QMessageBox.warning(self, "Eingabefehler", "Gleitender Durchschnitt: Fenster muss eine Zahl sein.")
            return

        ma = self.financial_tools.calculate_moving_average(data, window=window)

        if not ma.empty:
            ax.plot(data.index, data['adj_close'], label='Schlusskurs', color='blue', alpha=0.7)
            ax.plot(ma.index, ma, label=f'MA {window} Tage', color='red')
            ax.set_title(f"{self.symbol_combo.currentText()} - Gleitender Durchschnitt ({window} Tage)")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Kurs")
            ax.legend()
            ax.grid(True)
            self.ma_canvas.draw()
            self.ma_text.setText(f"Gleitender Durchschnitt ({window} Tage) berechnet.")
        else:
            self._clear_plot(self.ma_canvas)
            self.ma_text.setText("Nicht genügend Daten für gleitenden Durchschnitt.")

    def _plot_volatility(self, data):
        self._clear_plot(self.vol_canvas)
        ax = self.vol_canvas.axes
        try:
            window = int(self.vol_window_input.text())
        except ValueError:
            QMessageBox.warning(self.tab_volatility, "Eingabefehler", "Volatilität: Fenster muss eine Zahl sein.")
            return

        volatility = self.financial_tools.calculate_volatility(data, window=window)

        if not volatility.empty:
            ax.plot(volatility.index, volatility, label=f'Volatilität {window} Tage (annualisiert)', color='purple')
            ax.set_title(f"{self.symbol_combo.currentText()} - Rollierende Volatilität ({window} Tage)")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Volatilität (annualisiert)")
            ax.grid(True)
            self.vol_canvas.draw()
            self.vol_text.setText(f"Rollierende Volatilität ({window} Tage) berechnet.")
        else:
            self._clear_plot(self.vol_canvas)
            self.vol_text.setText("Nicht genügend Daten für Volatilitätsberechnung.")


    def _plot_beta(self, data):
        self._clear_plot(self.beta_canvas)
        ax = self.beta_canvas.axes
        market_symbol = self.market_symbol_input.text().upper()
        try:
            window = int(self.beta_window_input.text())
        except ValueError:
            QMessageBox.warning(self.tab_beta, "Eingabefehler", "Beta: Fenster muss eine Zahl sein.")
            return
        
        if not market_symbol:
            QMessageBox.warning(self.tab_beta, "Eingabefehler", "Bitte geben Sie ein Markt-Symbol ein (z.B. SPY).")
            return

        # Zuerst das Markt-Symbol zur DB hinzufügen und Daten holen, falls nicht vorhanden
        if not market_symbol in self.db_manager.get_all_symbols():
            if not self.db_manager.add_stock(market_symbol):
                QMessageBox.warning(self.tab_beta, "Datenfehler", f"Ungültiges Markt-Symbol: {market_symbol}")
                self._clear_plot(self.beta_canvas)
                self.beta_text.setText("Ungültiges Markt-Symbol.")
                return
            if not self.db_manager.fetch_and_store_data(market_symbol, period="max"):
                QMessageBox.warning(self.tab_beta, "Datenfehler", f"Konnte Daten für Markt-Symbol {market_symbol} nicht holen.")
                self._clear_plot(self.beta_canvas)
                self.beta_text.setText("Keine Marktdaten verfügbar.")
                return

        start_date_q = self.start_date_edit.date()
        end_date_q = self.end_date_edit.date()
        start_date_str = start_date_q.toString("yyyy-MM-dd")
        end_date_str = end_date_q.toString("yyyy-MM-dd")

        market_data = self.db_manager.get_stock_data(market_symbol, start_date_str, end_date_str)

        if market_data.empty:
            QMessageBox.warning(self.tab_beta, "Datenfehler", f"Keine Daten für Markt-Symbol {market_symbol} im angegebenen Zeitraum.")
            self._clear_plot(self.beta_canvas)
            self.beta_text.setText("Keine Marktdaten für Beta-Berechnung.")
            return

        beta = self.financial_tools.calculate_beta(data, market_data, window=window)

        if not beta.empty:
            ax.plot(beta.index, beta, label=f'Beta vs {market_symbol} ({window} Tage)', color='orange')
            ax.set_title(f"{self.symbol_combo.currentText()} - Rollierendes Beta vs {market_symbol} ({window} Tage)")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Beta")
            ax.axhline(1, color='gray', linestyle='--', linewidth=0.8, label='Beta = 1')
            ax.legend()
            ax.grid(True)
            self.beta_canvas.draw()
            self.beta_text.setText(f"Rollierendes Beta ({window} Tage) vs {market_symbol} berechnet. Aktuelles Beta: {beta.iloc[-1]:.2f}")
        else:
            self._clear_plot(self.beta_canvas)
            self.beta_text.setText("Nicht genügend Daten für Beta-Berechnung. Stellen Sie sicher, dass sowohl Aktie als auch Markt ausreichend historische Daten haben.")


    def closeEvent(self, event):
        """Wird aufgerufen, wenn das Fenster geschlossen wird."""
        self.db_manager.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockAnalyzer()
    window.show()
    sys.exit(app.exec())