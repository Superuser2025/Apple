"""
Enhanced AppleTrader Pro - Main Window with Institutional Features
Integrates the comprehensive institutional panel and enhanced chart system
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QSplitter, QStatusBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from gui.institutional_panel import InstitutionalPanel
from gui.chart_panel_matplotlib import ChartPanel  # USE ORIGINAL EXCELLENT CHART!
from gui.controls_panel import ControlsPanel

# Import existing widgets
from widgets.opportunity_scanner_widget import OpportunityScannerWidget
from widgets.price_action_commentary_widget import PriceActionCommentaryWidget
from widgets.correlation_heatmap_widget import CorrelationHeatmapWidget
from widgets.volatility_position_widget import VolatilityPositionWidget
from widgets.session_momentum_widget import SessionMomentumWidget
from widgets.order_flow_widget import InstitutionalOrderFlowWidget
from widgets.pattern_scorer_widget import PatternScorerWidget
from widgets.mtf_structure_widget import MTFStructureWidget
from widgets.news_impact_widget import NewsImpactWidget
from widgets.risk_reward_widget import RiskRewardWidget
from widgets.equity_curve_widget import EquityCurveWidget
from widgets.trade_journal_widget import TradeJournalWidget

from core.mt5_connector import MT5Connector


class EnhancedMainWindow(QMainWindow):
    """
    Enhanced Main Window with Institutional Trading Robot v3.0 features
    """

    def __init__(self):
        super().__init__()
        self.current_symbol = "EURUSD"
        self.current_timeframe = "H4"

        # Initialize MT5 connector
        self.mt5_connector = MT5Connector()
        self.mt5_connector.connection_status_changed.connect(self.on_mt5_connection_changed)
        self.mt5_connector.data_updated.connect(self.on_mt5_data_updated)
        self.mt5_connector.error_occurred.connect(self.on_mt5_error)

        self.init_ui()

        # Start data update timer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_all_data)
        self.data_timer.start(1000)

    def init_ui(self):
        """Initialize the enhanced user interface"""
        self.setWindowTitle("AppleTrader Pro - Institutional Trading Robot v3.0")
        self.setGeometry(50, 50, 1920, 1080)  # Full HD size for better visibility

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # === TOP TOOLBAR ===
        toolbar_layout = self.create_toolbar()
        main_layout.addLayout(toolbar_layout)

        # === OPPORTUNITY SCANNER ===
        self.scanner_widget = OpportunityScannerWidget()
        self.scanner_widget.setMinimumHeight(260)
        self.scanner_widget.setMaximumHeight(280)
        self.scanner_widget.set_mt5_connector(self.mt5_connector)
        main_layout.addWidget(self.scanner_widget)

        # === MAIN CONTENT (NEW 3-COLUMN LAYOUT) ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT COLUMN: Institutional Panel (NEW!)
        self.institutional_panel = InstitutionalPanel()
        self.institutional_panel.setMaximumWidth(450)  # More space - not squashed!
        self.institutional_panel.setMinimumWidth(400)

        # Connect institutional panel signals
        self.institutional_panel.filter_toggled.connect(self.on_filter_toggled)
        self.institutional_panel.mode_changed.connect(self.on_mode_changed)

        splitter.addWidget(self.institutional_panel)

        # CENTER COLUMN: Chart + Controls + Analysis Tabs (ORIGINAL LAYOUT!)
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)

        # RIGHT COLUMN: Performance Tabs
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set column widths (25% left, 45% center, 30% right) - More space for left panel!
        splitter.setSizes([450, 810, 540])

        main_layout.addWidget(splitter)

        # === STATUS BAR ===
        self.create_status_bar()

        # Apply dark theme
        self.apply_dark_theme()

    def create_toolbar(self) -> QHBoxLayout:
        """Create top toolbar"""
        layout = QHBoxLayout()

        # Title
        title = QLabel("📊 AppleTrader Pro - Institutional Trading Robot v3.0")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff00;")
        layout.addWidget(title)

        layout.addStretch()

        # Time display
        self.time_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.time_label.setFont(QFont("Arial", 10))
        self.time_label.setStyleSheet("color: #94A3B8;")
        layout.addWidget(self.time_label)

        layout.addSpacing(20)

        # Connection status
        self.connection_label = QLabel("🔴 MT5: Disconnected")
        self.connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_label.setStyleSheet(
            "color: #EF4444; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;"
        )
        layout.addWidget(self.connection_label)

        return layout

    def create_center_panel(self) -> QWidget:
        """Create center panel with ORIGINAL excellent chart + controls + analysis tabs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # === ORIGINAL EXCELLENT CHART (TradingView-style with zones!) ===
        self.chart_panel = ChartPanel()  # The original excellent implementation!
        self.chart_panel.timeframe_changed.connect(self.on_timeframe_changed)
        layout.addWidget(self.chart_panel, 3)  # 60% height

        # === CONTROLS PANEL ===
        self.controls_panel = ControlsPanel()
        self.controls_panel.order_requested.connect(self.on_order_requested)
        self.controls_panel.setting_changed.connect(self.on_setting_changed)
        layout.addWidget(self.controls_panel, 1)  # 20% height

        # === ANALYSIS TABS ===
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: PRICE ACTION COMMENTARY
        commentary_tab = QWidget()
        commentary_layout = QVBoxLayout(commentary_tab)
        self.commentary_widget = PriceActionCommentaryWidget()
        commentary_layout.addWidget(self.commentary_widget)
        tabs.addTab(commentary_tab, "📊 Price Action")

        # Tab 2: Momentum
        momentum_tab = QWidget()
        momentum_layout = QVBoxLayout(momentum_tab)
        self.momentum_widget = SessionMomentumWidget()
        momentum_layout.addWidget(self.momentum_widget)
        tabs.addTab(momentum_tab, "⚡ Momentum")

        # Tab 3: Correlation
        correlation_tab = QWidget()
        correlation_layout = QVBoxLayout(correlation_tab)
        self.correlation_widget = CorrelationHeatmapWidget()
        correlation_layout.addWidget(self.correlation_widget)
        tabs.addTab(correlation_tab, "🔥 Correlation")

        # Tab 4: Structure
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        self.structure_widget = MTFStructureWidget()
        structure_layout.addWidget(self.structure_widget)
        tabs.addTab(structure_tab, "📊 Structure")

        # Tab 5: Order Flow
        orderflow_tab = QWidget()
        orderflow_layout = QVBoxLayout(orderflow_tab)
        self.orderflow_widget = InstitutionalOrderFlowWidget()
        orderflow_layout.addWidget(self.orderflow_widget)
        tabs.addTab(orderflow_tab, "💼 Order Flow")

        # Tab 6: News
        news_tab = QWidget()
        news_layout = QVBoxLayout(news_tab)
        self.news_widget = NewsImpactWidget()
        news_layout.addWidget(self.news_widget)
        tabs.addTab(news_tab, "📰 News")

        layout.addWidget(tabs, 1)  # 20% height

        return widget

    def create_right_panel(self) -> QWidget:
        """Create right panel with performance tabs"""
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Position Sizing
        sizing_tab = QWidget()
        sizing_layout = QVBoxLayout(sizing_tab)
        self.position_widget = VolatilityPositionWidget()
        sizing_layout.addWidget(self.position_widget)
        tabs.addTab(sizing_tab, "🎯 Position Size")

        # Tab 2: Risk-Reward
        rr_tab = QWidget()
        rr_layout = QVBoxLayout(rr_tab)
        self.rr_widget = RiskRewardWidget()
        rr_layout.addWidget(self.rr_widget)
        tabs.addTab(rr_tab, "🎯 Risk-Reward")

        # Tab 3: Pattern Scorer
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout(pattern_tab)
        self.pattern_widget = PatternScorerWidget()
        pattern_layout.addWidget(self.pattern_widget)
        tabs.addTab(pattern_tab, "⭐ Quality")

        # Tab 4: Equity Curve
        equity_tab = QWidget()
        equity_layout = QVBoxLayout(equity_tab)
        self.equity_widget = EquityCurveWidget()
        equity_layout.addWidget(self.equity_widget)
        tabs.addTab(equity_tab, "📊 Equity")

        # Tab 5: Trade Journal
        journal_tab = QWidget()
        journal_layout = QVBoxLayout(journal_tab)
        self.journal_widget = TradeJournalWidget()
        journal_layout.addWidget(self.journal_widget)
        tabs.addTab(journal_tab, "📝 Journal")

        return tabs

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.addPermanentWidget(
            QLabel(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        )

    def on_symbol_changed(self, symbol: str):
        """Handle symbol change"""
        self.current_symbol = symbol
        self.status_label.setText(f"Symbol changed to: {symbol}")

        # Update all widgets with new symbol
        if hasattr(self, 'orderflow_widget'):
            self.orderflow_widget.set_symbol(symbol)

        self.update_all_data()

    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change"""
        self.current_timeframe = timeframe
        self.status_label.setText(f"Timeframe changed to: {timeframe}")
        self.update_all_data()

    def on_filter_toggled(self, filter_name: str, enabled: bool):
        """Handle filter toggle from institutional panel"""
        self.status_label.setText(f"Filter {filter_name}: {'Enabled' if enabled else 'Disabled'}")
        print(f"[Main Window] Filter {filter_name} {'enabled' if enabled else 'disabled'}")

        # Apply filter logic here
        # For now, just log it

    def on_mode_changed(self, mode: str):
        """Handle mode change (AUTO/MANUAL)"""
        self.status_label.setText(f"Trading mode: {mode}")
        print(f"[Main Window] Trading mode changed to {mode}")

    def on_order_requested(self, order_type: str):
        """Handle quick order button click from controls panel"""
        print(f"[Main Window] {order_type} order requested")
        self.status_label.setText(f"{order_type} order requested - sending to MT5...")

        # Send order command to MT5 via command manager
        from core.command_manager import command_manager
        try:
            command_manager.send_order(
                order_type=order_type,
                symbol=self.current_symbol,
                lot_size=0.01  # Default volume
            )
            self.status_label.setText(f"✓ {order_type} order sent to MT5 EA")
            print(f"[Main Window] {order_type} order command sent successfully")
        except Exception as e:
            self.status_label.setText(f"✗ Failed to send {order_type} order: {e}")
            print(f"[Main Window] Error sending order: {e}")

    def on_setting_changed(self, setting_name: str, value):
        """Handle setting change from controls panel"""
        print(f"[Main Window] Setting changed: {setting_name} = {value}")
        self.status_label.setText(f"Setting updated: {setting_name}")

        # Handle update speed changes
        if setting_name == 'update_speed':
            # Map speed to milliseconds
            speed_intervals = {
                'SLOW': 5000,      # 5 seconds
                'NORMAL': 2000,    # 2 seconds
                'FAST': 1000,      # 1 second
                'REALTIME': 500    # 0.5 seconds
            }

            interval = speed_intervals.get(value, 1000)

            # Update chart refresh timer
            if hasattr(self, 'chart_panel') and hasattr(self.chart_panel, 'update_timer'):
                self.chart_panel.update_timer.stop()
                self.chart_panel.update_timer.setInterval(interval)
                self.chart_panel.update_timer.start()
                print(f"[Main Window] Chart refresh rate changed to {interval}ms ({value})")
                self.status_label.setText(f"Chart refresh: {interval/1000}s")

                # Force immediate chart reload
                if hasattr(self.chart_panel, 'load_historical_data'):
                    success = self.chart_panel.load_historical_data()
                    if success and hasattr(self.chart_panel, 'plot_candlesticks'):
                        self.chart_panel.plot_candlesticks()
                    print(f"[Main Window] Chart reloaded immediately")

            # Update main window timer
            if hasattr(self, 'data_timer'):
                self.data_timer.stop()
                self.data_timer.setInterval(interval)
                self.data_timer.start()
                print(f"[Main Window] Data update rate changed to {interval}ms ({value})")

        # Handle filter changes
        elif setting_name in ['use_fvg_filter', 'use_ob_filter', 'use_liquidity_filter']:
            if hasattr(self, 'scanner_widget'):
                # Trigger a rescan with new filters
                self.scanner_widget.scan_market()

    def update_all_data(self):
        """Update all widgets with latest data"""
        # Update time display
        if hasattr(self, 'time_label'):
            self.time_label.setText(datetime.now().strftime("%H:%M:%S"))

        # Update institutional panel with sample data
        if hasattr(self, 'institutional_panel'):
            self.institutional_panel.update_market_status("Trending market - High volume detected")
            self.institutional_panel.update_context("LONDON", "H4/H1", "BULLISH", "HH forming")
            self.institutional_panel.update_risk_metrics(2.0, 5.2, 68.0)
            self.institutional_panel.update_performance(2.3, 8.7, 15.2)

        # Update status bar
        self.status_bar.showMessage(f"Updated: {datetime.now().strftime('%H:%M:%S')}", 2000)

    def on_mt5_connection_changed(self, connected: bool):
        """Handle MT5 connection status change"""
        if connected:
            self.connection_label.setText("🟢 MT5: Connected")
            self.connection_label.setStyleSheet(
                "color: #10B981; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;"
            )
            self.status_label.setText("MT5 connection established")
        else:
            self.connection_label.setText("🔴 MT5: Disconnected")
            self.connection_label.setStyleSheet(
                "color: #EF4444; background-color: #1E293B; padding: 5px 10px; border-radius: 5px;"
            )
            self.status_label.setText("MT5 connection lost")

    def on_mt5_data_updated(self, data: dict):
        """Handle new data from MT5"""
        if 'symbol' in data:
            self.current_symbol = data['symbol']
        if 'timeframe' in data:
            self.current_timeframe = data['timeframe']

        self.status_label.setText(f"MT5 data received: {self.current_symbol} {self.current_timeframe}")

    def on_mt5_error(self, error_message: str):
        """Handle MT5 error"""
        self.status_label.setText(f"MT5 Error: {error_message}")
        print(f"[MT5 ERROR] {error_message}")

    def apply_dark_theme(self):
        """Apply dark theme to main window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #444;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #444;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def closeEvent(self, event):
        """Handle window close event"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit AppleTrader Pro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
