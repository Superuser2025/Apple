"""
AppleTrader Pro - Backtest Widget
Run backtests and display results
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QTextEdit, QGroupBox,
                            QProgressBar, QSpinBox, QDoubleSpinBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from backtesting.backtest_engine import backtest_engine, BacktestResults
from backtesting.strategy_adapter import strategy_quality_70, strategy_quality_75, strategy_quality_80


class BacktestThread(QThread):
    """Thread for running backtest without freezing UI"""

    finished = pyqtSignal(object)  # Emits BacktestResults
    progress = pyqtSignal(str)  # Emits progress messages

    def __init__(self, symbol, timeframe, data, strategy, starting_balance, risk_percent):
        super().__init__()
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = data
        self.strategy = strategy
        self.starting_balance = starting_balance
        self.risk_percent = risk_percent

    def run(self):
        """Run backtest in separate thread"""
        try:
            self.progress.emit("Loading historical data...")

            self.progress.emit(f"Running backtest on {len(self.data)} candles...")

            results = backtest_engine.run_backtest(
                symbol=self.symbol,
                timeframe=self.timeframe,
                data=self.data,
                strategy_func=self.strategy.evaluate,
                starting_balance=self.starting_balance,
                risk_percent=self.risk_percent
            )

            self.progress.emit("Backtest complete!")
            self.finished.emit(results)

        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.finished.emit(None)


class BacktestWidget(QWidget):
    """
    Backtest Widget

    Allows user to:
    - Select symbol and timeframe
    - Choose strategy parameters
    - Run backtest
    - View results
    """

    def __init__(self, mt5_connector=None, parent=None):
        super().__init__(parent)
        self.mt5_connector = mt5_connector
        self.current_results: Optional[BacktestResults] = None
        self.backtest_thread: Optional[BacktestThread] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("📊 Strategy Backtest")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # === PARAMETERS ===
        params_group = QGroupBox("Backtest Parameters")
        params_layout = QVBoxLayout()

        # Symbol
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbol:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'])
        symbol_layout.addWidget(self.symbol_combo)
        params_layout.addLayout(symbol_layout)

        # Timeframe
        tf_layout = QHBoxLayout()
        tf_layout.addWidget(QLabel("Timeframe:"))
        self.tf_combo = QComboBox()
        self.tf_combo.addItems(['H1', 'H4', 'D1'])
        self.tf_combo.setCurrentText('H4')
        tf_layout.addWidget(self.tf_combo)
        params_layout.addLayout(tf_layout)

        # Strategy quality threshold
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Min Quality Score:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(60, 90)
        self.quality_spin.setValue(70)
        self.quality_spin.setSuffix(" pts")
        quality_layout.addWidget(self.quality_spin)
        params_layout.addLayout(quality_layout)

        # Starting balance
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(QLabel("Starting Balance:"))
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(1000, 100000)
        self.balance_spin.setValue(10000)
        self.balance_spin.setPrefix("$")
        balance_layout.addWidget(self.balance_spin)
        params_layout.addLayout(balance_layout)

        # Risk per trade
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Risk Per Trade:"))
        self.risk_spin = QDoubleSpinBox()
        self.risk_spin.setRange(0.1, 5.0)
        self.risk_spin.setValue(0.5)
        self.risk_spin.setSingleStep(0.1)
        self.risk_spin.setSuffix("%")
        risk_layout.addWidget(self.risk_spin)
        params_layout.addLayout(risk_layout)

        # Candles to test
        candles_layout = QHBoxLayout()
        candles_layout.addWidget(QLabel("Candles to Test:"))
        self.candles_spin = QSpinBox()
        self.candles_spin.setRange(500, 10000)
        self.candles_spin.setValue(2000)
        self.candles_spin.setSuffix(" bars")
        candles_layout.addWidget(self.candles_spin)
        params_layout.addLayout(candles_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # === RUN BUTTON ===
        self.run_btn = QPushButton("🚀 RUN BACKTEST")
        self.run_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.on_run_backtest)
        layout.addWidget(self.run_btn)

        # === PROGRESS ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Arial", 9))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        # === RESULTS ===
        results_group = QGroupBox("📈 Backtest Results")
        results_layout = QVBoxLayout()

        # Summary metrics
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_layout = QVBoxLayout(summary_frame)

        self.results_summary = QLabel("Run a backtest to see results")
        self.results_summary.setFont(QFont("Courier", 10))
        self.results_summary.setWordWrap(True)
        summary_layout.addWidget(self.results_summary)

        results_layout.addWidget(summary_frame)

        # Detailed results
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier", 9))
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #00aaff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0d7377;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14b1b8;
            }
            QPushButton:pressed {
                background-color: #0a5a5d;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """)

    def on_run_backtest(self):
        """Handle run backtest button click"""
        if not self.mt5_connector:
            self.progress_label.setText("❌ MT5 not connected")
            return

        # Get parameters
        symbol = self.symbol_combo.currentText()
        timeframe = self.tf_combo.currentText()
        quality_threshold = self.quality_spin.value()
        starting_balance = self.balance_spin.value()
        risk_percent = self.risk_spin.value()
        candles_count = self.candles_spin.value()

        # Get historical data from MT5
        self.progress_label.setText(f"Loading {candles_count} candles of {symbol} {timeframe}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.run_btn.setEnabled(False)

        # Load data
        df = self.mt5_connector.get_candles(symbol, timeframe, candles_count)

        if df is None or len(df) < 500:
            self.progress_label.setText("❌ Failed to load historical data")
            self.progress_bar.setVisible(False)
            self.run_btn.setEnabled(True)
            return

        # Select strategy based on quality threshold
        if quality_threshold >= 80:
            strategy = strategy_quality_80
        elif quality_threshold >= 75:
            strategy = strategy_quality_75
        else:
            strategy = strategy_quality_70

        # Run backtest in thread
        self.backtest_thread = BacktestThread(
            symbol, timeframe, df, strategy,
            starting_balance, risk_percent
        )
        self.backtest_thread.progress.connect(self.on_backtest_progress)
        self.backtest_thread.finished.connect(self.on_backtest_finished)
        self.backtest_thread.start()

    def on_backtest_progress(self, message: str):
        """Handle backtest progress updates"""
        self.progress_label.setText(message)

    def on_backtest_finished(self, results: Optional[BacktestResults]):
        """Handle backtest completion"""
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)

        if results is None:
            self.progress_label.setText("❌ Backtest failed")
            return

        self.current_results = results
        self.display_results(results)
        self.progress_label.setText(f"✅ Backtest complete: {results.total_trades} trades")

    def display_results(self, results: BacktestResults):
        """Display backtest results"""

        # Summary metrics (color-coded)
        win_rate_color = "#10B981" if results.win_rate >= 50 else "#EF4444"
        pnl_color = "#10B981" if results.total_pnl > 0 else "#EF4444"
        r_color = "#10B981" if results.avg_r_multiple > 1.0 else "#EF4444"

        summary_html = f"""
        <div style="padding: 10px;">
            <p style="font-size: 14px; margin: 5px 0;">
                <b>Total Trades:</b> {results.total_trades}
                ({results.winning_trades}W / {results.losing_trades}L)
            </p>
            <p style="font-size: 14px; margin: 5px 0; color: {win_rate_color};">
                <b>Win Rate:</b> {results.win_rate:.1f}%
            </p>
            <p style="font-size: 14px; margin: 5px 0; color: {pnl_color};">
                <b>Total P&L:</b> ${results.total_pnl:,.2f} ({results.total_pips:,.0f} pips)
            </p>
            <p style="font-size: 14px; margin: 5px 0; color: {r_color};">
                <b>Avg R-multiple:</b> {results.avg_r_multiple:.2f}R
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <b>Profit Factor:</b> {results.profit_factor:.2f}
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <b>Max Drawdown:</b> {results.max_drawdown_pct:.1f}% (${results.max_drawdown_dollars:,.2f})
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <b>Sharpe Ratio:</b> {results.sharpe_ratio:.2f}
            </p>
        </div>
        """

        self.results_summary.setText(summary_html)
        self.results_summary.setTextFormat(Qt.TextFormat.RichText)

        # Detailed trade list
        trade_lines = []
        trade_lines.append(f"{'='*80}")
        trade_lines.append(f"Backtest Results: {results.symbol} {results.timeframe}")
        trade_lines.append(f"Period: {results.start_date} to {results.end_date}")
        trade_lines.append(f"Days Tested: {results.days_tested}")
        trade_lines.append(f"{'='*80}\n")

        trade_lines.append("TRADE HISTORY:")
        trade_lines.append(f"{'#':<5} {'Date':<12} {'Dir':<5} {'Entry':<10} {'Exit':<10} {'Pips':<8} {'R':<6} {'P&L':<10}")
        trade_lines.append(f"{'-'*80}")

        for idx, trade in enumerate(results.trades[:50], 1):  # Show first 50 trades
            outcome_symbol = "✓" if trade.profit_loss > 0 else "✗"
            trade_lines.append(
                f"{idx:<5} "
                f"{trade.entry_time.strftime('%Y-%m-%d'):<12} "
                f"{trade.direction:<5} "
                f"{trade.entry_price:.5f}  "
                f"{trade.exit_price:.5f}  "
                f"{trade.pips_result:>7.1f} "
                f"{trade.r_multiple:>5.2f} "
                f"{outcome_symbol} ${trade.profit_loss:>8.2f}"
            )

        if len(results.trades) > 50:
            trade_lines.append(f"\n... and {len(results.trades) - 50} more trades")

        self.results_text.setPlainText('\n'.join(trade_lines))


def set_mt5_connector(self, connector):
        """Set MT5 connector"""
        self.mt5_connector = connector
