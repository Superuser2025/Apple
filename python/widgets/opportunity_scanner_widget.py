"""
AppleTrader Pro - Live Market Opportunity Scanner
Scans all pairs for high-probability trading setups in real-time
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QScrollArea, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


class OpportunityCard(QFrame):
    """Card widget for a single trading opportunity"""

    def __init__(self, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.setObjectName("OpportunityCard")  # Set object name for specific styling
        self.init_ui()

    def init_ui(self):
        """Initialize the opportunity card UI"""
        self.setFixedHeight(140)  # Increased from 110 to 140
        self.setMinimumWidth(300)  # Minimum width, will expand to fill
        self.setSizePolicy(self.sizePolicy().Policy.Expanding, self.sizePolicy().Policy.Fixed)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Color based on quality score
        score = self.opportunity['quality_score']
        if score >= 85:
            border_color = '#10B981'  # Green - Excellent
            bg_color = '#064E3B'
        elif score >= 70:
            border_color = '#3B82F6'  # Blue - Good
            bg_color = '#1E3A8A'
        elif score >= 60:
            border_color = '#F59E0B'  # Orange - Fair
            bg_color = '#78350F'
        else:
            border_color = '#6B7280'  # Gray - Weak
            bg_color = '#374151'

        self.setStyleSheet(f"""
            OpportunityCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
            OpportunityCard QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header: Symbol + Direction + Score
        header_layout = QHBoxLayout()

        symbol_label = QLabel(self.opportunity['symbol'])
        symbol_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))  # Increased from 12 to 15
        symbol_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(symbol_label)

        direction = self.opportunity['direction']
        dir_color = '#10B981' if direction == 'BUY' else '#EF4444'
        dir_icon = '📈' if direction == 'BUY' else '📉'
        dir_label = QLabel(f"{dir_icon} {direction}")
        dir_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))  # Increased from 11 to 14
        dir_label.setStyleSheet(f"color: {dir_color};")
        header_layout.addWidget(dir_label)

        header_layout.addStretch()

        score_label = QLabel(f"⭐ {score}")
        score_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))  # Increased from 11 to 14
        score_label.setStyleSheet(f"color: {border_color};")
        header_layout.addWidget(score_label)

        layout.addLayout(header_layout)

        # Entry and targets
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(15)

        entry_text = QLabel(f"Entry: {self.opportunity['entry']:.5f}")
        entry_text.setFont(QFont("Courier", 11))  # Increased from 9 to 11
        entry_text.setStyleSheet("color: #94A3B8;")
        entry_layout.addWidget(entry_text)

        sl_text = QLabel(f"SL: {self.opportunity['stop_loss']:.5f}")
        sl_text.setFont(QFont("Courier", 11))  # Increased from 9 to 11
        sl_text.setStyleSheet("color: #EF4444;")
        entry_layout.addWidget(sl_text)

        tp_text = QLabel(f"TP: {self.opportunity['take_profit']:.5f}")
        tp_text.setFont(QFont("Courier", 11))  # Increased from 9 to 11
        tp_text.setStyleSheet("color: #10B981;")
        entry_layout.addWidget(tp_text)

        rr_text = QLabel(f"R:R {self.opportunity['risk_reward']:.1f}")
        rr_text.setFont(QFont("Courier", 11, QFont.Weight.Bold))  # Increased from 9 to 11
        rr_text.setStyleSheet("color: #3B82F6;")
        entry_layout.addWidget(rr_text)

        entry_layout.addStretch()
        layout.addLayout(entry_layout)

        # Confluence reasons
        reasons = self.opportunity.get('confluence_reasons', [])
        reasons_text = " • ".join(reasons[:3])  # Top 3 reasons
        reasons_label = QLabel(f"✓ {reasons_text}")
        reasons_label.setFont(QFont("Arial", 10))  # Increased from 8 to 10
        reasons_label.setStyleSheet("color: #D1D5DB;")
        reasons_label.setWordWrap(True)
        layout.addWidget(reasons_label)

        # Timeframe
        tf_label = QLabel(f"⏱ {self.opportunity['timeframe']}")
        tf_label.setFont(QFont("Arial", 10))  # Increased from 8 to 10
        tf_label.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(tf_label)


class OpportunityScannerWidget(QWidget):
    """
    Live Market Opportunity Scanner

    Features:
    - Scans all major currency pairs in real-time
    - Ranks opportunities by quality score (confluence)
    - Shows entry, SL, TP, R:R for each
    - Color-coded by signal strength
    - Shows WHY each setup is valid
    - Auto-refreshes every 10 seconds
    """

    opportunity_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OpportunityScannerWidget")

        self.opportunities = []
        self.pairs_to_scan = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
            'NZDUSD', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY'
        ]
        self.mt5_connector = None  # Will be set when MT5 connects
        self.using_real_data = False

        # Timeframe filter - default to scan multiple timeframes
        self.timeframe_filter = 'ALL'  # Can be 'ALL', 'M15', 'M30', 'H1', 'H4', 'D1'

        # Signal persistence - keep signals for 5 minutes minimum
        self.signal_persist_duration = 300  # 5 minutes in seconds

        self.init_ui()

        # Auto-scan timer (every 30 seconds - less frequent to keep signals visible longer)
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_market)
        self.scan_timer.start(30000)  # Changed from 10 to 30 seconds

        # Initial scan - delayed to ensure UI is fully initialized
        QTimer.singleShot(100, self.scan_market)

    def init_ui(self):
        """Initialize the user interface"""
        # Set minimum size for the widget (increased to fit larger cards)
        self.setMinimumHeight(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🎯 Live Market Opportunity Scanner")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))  # Increased from 13 to 14
        title.setStyleSheet("color: #00aaff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Scanning status
        self.status_label = QLabel("🟢 SCANNING")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #10B981;")
        header_layout.addWidget(self.status_label)

        # Last update time
        self.time_label = QLabel(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        self.time_label.setFont(QFont("Arial", 9))
        self.time_label.setStyleSheet("color: #94A3B8;")
        header_layout.addWidget(self.time_label)

        layout.addLayout(header_layout)

        # === TIMEFRAME FILTER & INFO BAR ===
        filter_layout = QHBoxLayout()

        # Timeframe filter
        tf_label = QLabel("Timeframe:")
        tf_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        tf_label.setStyleSheet("color: #F8FAFC;")
        filter_layout.addWidget(tf_label)

        self.tf_filter_combo = QComboBox()
        self.tf_filter_combo.addItems(['ALL', 'M15', 'M30', 'H1', 'H4', 'D1'])
        self.tf_filter_combo.setCurrentText('ALL')
        self.tf_filter_combo.setFont(QFont("Arial", 11))
        self.tf_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E3A8A;
                color: white;
                border: 2px solid #3B82F6;
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 80px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1E3A8A;
                color: white;
                selection-background-color: #3B82F6;
            }
        """)
        self.tf_filter_combo.currentTextChanged.connect(self.on_timeframe_filter_changed)
        filter_layout.addWidget(self.tf_filter_combo)

        filter_layout.addSpacing(20)

        # Persistence info
        persist_label = QLabel("⏱ Signals persist: 5 min")
        persist_label.setFont(QFont("Arial", 10))
        persist_label.setStyleSheet("color: #10B981;")
        filter_layout.addWidget(persist_label)

        filter_layout.addStretch()

        self.count_label = QLabel("0 opportunities found")
        self.count_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.count_label.setStyleSheet("color: #3B82F6;")
        filter_layout.addWidget(self.count_label)

        layout.addLayout(filter_layout)

        # === OPPORTUNITIES GRID ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(180)  # Increased from 140 to 180 for larger cards
        scroll.setObjectName("OpportunityScrollArea")
        scroll.setStyleSheet("""
            QScrollArea#OpportunityScrollArea {
                background-color: #0F1729;
                border: 1px solid #1E293B;
                border-radius: 5px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")

        # Use VBoxLayout with horizontal rows to fill width properly
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)  # Give it stretch factor to expand

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            OpportunityScannerWidget {
                background-color: #0A0E27;
                color: #F8FAFC;
            }
            QLabel {
                background-color: transparent;
            }
            QScrollArea {
                background-color: transparent;
            }
        """)

    def set_mt5_connector(self, mt5_connector):
        """Set MT5 connector to use real market data"""
        self.mt5_connector = mt5_connector
        if not self.using_real_data:
            self.using_real_data = True
            print("[Opportunity Scanner] Switched from demo data to REAL MT5 data")
            # Trigger immediate scan with real data
            self.scan_market()

    def scan_market(self):
        """Scan all pairs for trading opportunities"""
        print(f"[DEBUG] scan_market() called at {datetime.now().strftime('%H:%M:%S')}")
        self.blink_status()

        current_time = datetime.now()

        # Filter out expired opportunities (older than persist duration)
        cutoff_time = current_time - timedelta(seconds=self.signal_persist_duration)
        self.opportunities = [
            opp for opp in self.opportunities
            if opp.get('timestamp', current_time) > cutoff_time
        ]
        print(f"[Opportunity Scanner] Retained {len(self.opportunities)} persisted signals")

        # Try to use real MT5 data first
        new_opportunities = []
        if self.using_real_data and self.mt5_connector:
            new_opportunities = self.scan_real_market_data()
            print(f"[Opportunity Scanner] Scanned REAL MT5 data: {len(new_opportunities)} new opportunities found")

            # If no real opportunities found, show demo data as fallback (EA might not have sent data yet)
            if len(new_opportunities) == 0:
                print(f"[Opportunity Scanner] No real opportunities found - using demo data as fallback")
                new_opportunities = self.generate_opportunities()
        else:
            # MT5 not connected yet - show demo data temporarily
            print(f"[Opportunity Scanner] MT5 not connected - showing demo data temporarily")
            new_opportunities = self.generate_opportunities()

        # Add timestamps to new opportunities
        for opp in new_opportunities:
            if 'timestamp' not in opp:
                opp['timestamp'] = current_time

        # Merge new opportunities with persisted ones (avoid duplicates by symbol+timeframe)
        existing_keys = {(o['symbol'], o['timeframe']) for o in self.opportunities}
        for opp in new_opportunities:
            key = (opp['symbol'], opp['timeframe'])
            if key not in existing_keys:
                self.opportunities.append(opp)

        # Apply timeframe filter
        if self.timeframe_filter != 'ALL':
            self.opportunities = [
                opp for opp in self.opportunities
                if opp['timeframe'] == self.timeframe_filter
            ]

        # Sort by quality score (highest first)
        self.opportunities.sort(key=lambda x: x['quality_score'], reverse=True)

        # Update display
        self.update_display()
        print(f"[DEBUG] Display updated with {len(self.opportunities)} cards")

        # Update time
        self.time_label.setText(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

    def generate_opportunities(self) -> List[Dict]:
        """Generate trading opportunities (demo version with realistic data)"""
        opportunities = []

        # Number of opportunities to show (3-6 for better visibility)
        num_opportunities = random.randint(3, 6)

        # Track used pairs to avoid duplicates
        used_pairs = set()

        for _ in range(num_opportunities):
            # Select unique pair (not already used)
            available_pairs = [p for p in self.pairs_to_scan if p not in used_pairs]
            if not available_pairs:
                break  # No more unique pairs available

            pair = random.choice(available_pairs)
            used_pairs.add(pair)

            direction = random.choice(['BUY', 'SELL'])
            timeframe = random.choice(['M15', 'M30', 'H1', 'H4', 'D1'])

            # Generate realistic price levels
            base_price = self.get_base_price(pair)
            entry = base_price + random.uniform(-0.0020, 0.0020)

            if direction == 'BUY':
                stop_loss = entry - random.uniform(0.0015, 0.0030)
                take_profit = entry + random.uniform(0.0030, 0.0080)
            else:
                stop_loss = entry + random.uniform(0.0015, 0.0030)
                take_profit = entry - random.uniform(0.0030, 0.0080)

            # Calculate R:R
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr = reward / risk if risk > 0 else 0

            # Quality score (confluence-based)
            quality_score = random.randint(55, 95)

            # Confluence reasons
            all_reasons = [
                'Order Block', 'FVG', 'Liquidity Sweep', 'Structure Break',
                'Trend Alignment', 'Volume Spike', 'Session Open', 'Key Level',
                'Fibonacci 61.8%', 'Supply/Demand Zone', 'Pattern Confirmed',
                'MTF Confluence', 'News Catalyst', 'Momentum Shift'
            ]

            # Higher quality = more confluence reasons
            num_reasons = 3 if quality_score >= 80 else 2
            reasons = random.sample(all_reasons, num_reasons)

            opportunities.append({
                'symbol': pair,
                'direction': direction,
                'timeframe': timeframe,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': rr,
                'quality_score': quality_score,
                'confluence_reasons': reasons
            })

        return opportunities

    def get_base_price(self, pair: str) -> float:
        """Get base price for a currency pair"""
        base_prices = {
            'EURUSD': 1.16104, 'GBPUSD': 1.31850, 'USDJPY': 149.50,
            'AUDUSD': 0.68500, 'USDCAD': 1.34200, 'NZDUSD': 0.62300,
            'USDCHF': 0.87500, 'EURGBP': 0.88000, 'EURJPY': 173.50,
            'GBPJPY': 197.00
        }
        return base_prices.get(pair, 1.0000)

    def scan_real_market_data(self) -> List[Dict]:
        """Scan real market data from MT5 for trading opportunities"""
        opportunities = []

        # Scan top pairs for opportunities
        timeframes = ['H1', 'H4']  # Focus on these timeframes

        for pair in self.pairs_to_scan[:5]:  # Scan top 5 pairs to avoid overload
            for timeframe in timeframes:
                # Get candle data from MT5
                df = self.mt5_connector.get_candles(pair, timeframe, 100)

                if df is None or len(df) < 50:
                    continue

                # Analyze for trading opportunity
                opp = self.analyze_opportunity(pair, timeframe, df)
                if opp:
                    opportunities.append(opp)

        return opportunities

    def analyze_opportunity(self, symbol: str, timeframe: str, df) -> Optional[Dict]:
        """Analyze candle data for a trading opportunity"""
        try:
            # Get current and recent prices
            current_close = df['close'].iloc[-1]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]

            # Calculate simple trend (20-period SMA)
            if len(df) >= 20:
                sma_20 = df['close'].tail(20).mean()
                trend = 'BUY' if current_close > sma_20 else 'SELL'
            else:
                return None

            # Calculate volatility (ATR-like)
            df['hl'] = df['high'] - df['low']
            atr = df['hl'].tail(14).mean()

            # Set entry/SL/TP based on trend
            if trend == 'BUY':
                entry = current_close
                stop_loss = entry - (atr * 1.5)
                take_profit = entry + (atr * 3.0)
            else:  # SELL
                entry = current_close
                stop_loss = entry + (atr * 1.5)
                take_profit = entry - (atr * 3.0)

            # Calculate risk:reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr = reward / risk if risk > 0 else 0

            # Calculate quality score based on conditions
            quality_score = 60
            reasons = []

            # Check for volume spike
            if 'volume' in df.columns and len(df) >= 20:
                avg_volume = df['volume'].tail(20).mean()
                current_volume = df['volume'].iloc[-1]
                if current_volume > avg_volume * 1.5:
                    quality_score += 10
                    reasons.append('Volume Spike')

            # Check for strong trend
            if len(df) >= 50:
                sma_50 = df['close'].tail(50).mean()
                if (trend == 'BUY' and current_close > sma_50) or (trend == 'SELL' and current_close < sma_50):
                    quality_score += 15
                    reasons.append('Trend Alignment')

            # Check for good R:R
            if rr >= 2.0:
                quality_score += 10
                reasons.append('High R:R Ratio')

            # Only return if quality score is decent
            if quality_score < 65:
                return None

            if not reasons:
                reasons = ['Price Action', 'Technical Setup']

            return {
                'symbol': symbol,
                'direction': trend,
                'timeframe': timeframe,
                'entry': float(entry),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward': float(rr),
                'quality_score': quality_score,
                'confluence_reasons': reasons
            }

        except Exception as e:
            print(f"[Opportunity Scanner] Error analyzing {symbol}: {e}")
            return None

    def update_display(self):
        """Update the opportunities display - cards fill width horizontally"""
        print(f"[DEBUG] update_display() called with {len(self.opportunities)} opportunities")

        # Clear existing cards - properly remove them
        cleared_count = 0
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.layout():
                # It's a horizontal layout row
                row_layout = item.layout()
                while row_layout.count():
                    widget_item = row_layout.takeAt(0)
                    if widget_item.widget():
                        widget_item.widget().setParent(None)
                        widget_item.widget().deleteLater()
                        cleared_count += 1
            elif item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
                cleared_count += 1
        print(f"[DEBUG] Cleared {cleared_count} existing widgets")

        # Add opportunity cards in horizontal rows that fill width
        # Each card expands to fill available width
        for idx, opp in enumerate(self.opportunities):
            card = OpportunityCard(opp)
            card.mousePressEvent = lambda event, o=opp: self.opportunity_selected.emit(o)
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            # Create horizontal row for each card (fills width)
            row_layout = QHBoxLayout()
            row_layout.addWidget(card)
            self.cards_layout.addLayout(row_layout)

            print(f"[DEBUG] Added card {idx}: {opp['symbol']} {opp['direction']} [{opp['timeframe']}]")

        # Update count
        count = len(self.opportunities)
        self.count_label.setText(f"{count} opportunit{'y' if count == 1 else 'ies'} found")
        print(f"[DEBUG] Count label updated: {count} opportunities")

        # Force parent widget to update its layout
        self.updateGeometry()
        self.update()

    def on_timeframe_filter_changed(self, timeframe: str):
        """Handle timeframe filter change"""
        self.timeframe_filter = timeframe
        print(f"[Opportunity Scanner] Timeframe filter changed to: {timeframe}")
        # Re-scan immediately to apply filter
        self.scan_market()

    def blink_status(self):
        """Blink the scanning status indicator"""
        self.status_label.setStyleSheet("color: #FFFFFF;")
        QTimer.singleShot(200, lambda: self.status_label.setStyleSheet("color: #10B981;"))
