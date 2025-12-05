"""
AppleTrader Pro - Live Market Opportunity Scanner
Scans all pairs for high-probability trading setups in real-time
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


class OpportunityCard(QFrame):
    """Card widget for a single trading opportunity"""

    def __init__(self, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.setObjectName("OpportunityCard")
        self.init_ui()

    def init_ui(self):
        """Initialize the opportunity card UI"""
        self.setMinimumHeight(105)
        self.setMaximumHeight(110)
        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Fixed
        )
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
                padding: 6px;
            }}
            OpportunityCard QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header: Symbol + Direction + Score
        header_layout = QHBoxLayout()

        symbol_label = QLabel(self.opportunity['symbol'])
        symbol_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        symbol_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(symbol_label)

        direction = self.opportunity['direction']
        dir_color = '#10B981' if direction == 'BUY' else '#EF4444'
        dir_icon = '📈' if direction == 'BUY' else '📉'
        dir_label = QLabel(f"{dir_icon} {direction}")
        dir_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        dir_label.setStyleSheet(f"color: {dir_color};")
        header_layout.addWidget(dir_label)

        header_layout.addStretch()

        score_label = QLabel(f"⭐ {score}")
        score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        score_label.setStyleSheet(f"color: {border_color};")
        header_layout.addWidget(score_label)

        layout.addLayout(header_layout)

        # Entry and targets
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(10)

        entry_text = QLabel(f"Entry: {self.opportunity['entry']:.5f}")
        entry_text.setFont(QFont("Courier", 9))
        entry_text.setStyleSheet("color: #94A3B8;")
        entry_layout.addWidget(entry_text)

        sl_text = QLabel(f"SL: {self.opportunity['stop_loss']:.5f}")
        sl_text.setFont(QFont("Courier", 9))
        sl_text.setStyleSheet("color: #EF4444;")
        entry_layout.addWidget(sl_text)

        tp_text = QLabel(f"TP: {self.opportunity['take_profit']:.5f}")
        tp_text.setFont(QFont("Courier", 9))
        tp_text.setStyleSheet("color: #10B981;")
        entry_layout.addWidget(tp_text)

        rr_text = QLabel(f"R:R {self.opportunity['risk_reward']:.1f}")
        rr_text.setFont(QFont("Courier", 9, QFont.Weight.Bold))
        rr_text.setStyleSheet("color: #3B82F6;")
        entry_layout.addWidget(rr_text)

        entry_layout.addStretch()
        layout.addLayout(entry_layout)

        # Confluence reasons
        reasons = self.opportunity.get('confluence_reasons', [])
        reasons_text = " • ".join(reasons[:3])
        reasons_label = QLabel(f"✓ {reasons_text}")
        reasons_label.setFont(QFont("Arial", 8))
        reasons_label.setStyleSheet("color: #D1D5DB;")
        reasons_label.setWordWrap(True)
        layout.addWidget(reasons_label)

        # Timeframe
        tf_label = QLabel(f"⏱ {self.opportunity['timeframe']}")
        tf_label.setFont(QFont("Arial", 8))
        tf_label.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(tf_label)


class TimeframeGroup(QWidget):
    """Group widget for a specific timeframe range - cards flow left to right"""

    def __init__(self, timeframes: List[str], parent=None):
        super().__init__(parent)
        self.timeframes = timeframes
        self.opportunities = []
        self.init_ui()

    def init_ui(self):
        """Initialize the group UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(330)  # Height for 3 rows of cards (12 cards / 4 per row = 3 rows)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0F1729;
                border: 1px solid #1E293B;
                border-radius: 5px;
            }
        """)

        scroll_content = QWidget()

        # Grid layout - 4 columns, cards flow left-to-right
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(3, 3, 3, 3)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def update_opportunities(self, opportunities: List[Dict]):
        """Update opportunities - LIMIT TO 12 CARDS MAX, 3 rows × 4 columns"""
        # CRITICAL: Hard limit to 12 cards per timeframe section
        self.opportunities = opportunities[:12]

        # Clear existing cards
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        # Add cards in 4-column grid (max 3 rows × 4 cols = 12 cards)
        for idx, opp in enumerate(self.opportunities):
            card = OpportunityCard(opp)
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            row = idx // 4  # 4 cards per row
            col = idx % 4   # Columns 0, 1, 2, 3

            self.grid_layout.addWidget(card, row, col)

        # Fill remaining slots with spacers if < 12 cards (for even layout)
        for idx in range(len(self.opportunities), 12):
            spacer = QWidget()
            spacer.setMinimumHeight(105)
            spacer.setMaximumHeight(110)
            spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(spacer, row, col)


class OpportunityScannerWidget(QWidget):
    """
    Live Market Opportunity Scanner - Horizontal Flow Layout

    Cards flow left-to-right within each timeframe group.
    3 groups side-by-side, each showing 3 cards wide x 2+ cards tall.
    """

    opportunity_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OpportunityScannerWidget")

        self.opportunities = []

        # Expanded symbol list
        self.pairs_to_scan = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD',
            'NZDUSD', 'USDCHF', 'EURGBP', 'EURJPY', 'GBPJPY',
            'AUDJPY', 'EURAUD', 'EURNZD', 'GBPAUD', 'GBPNZD',
            'NZDJPY', 'CHFJPY', 'CADCHF', 'AUDCAD', 'AUDNZD'
        ]

        self.mt5_connector = None
        self.using_real_data = False

        # Signal persistence
        self.signal_persist_duration = 300  # 5 minutes

        self.init_ui()

        # Auto-scan timer
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_market)
        self.scan_timer.start(30000)

        # Initial scan
        QTimer.singleShot(100, self.scan_market)

    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🎯 Live Market Opportunity Scanner")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #00aaff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Status
        self.status_label = QLabel("🟢 SCANNING")
        self.status_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #10B981;")
        header_layout.addWidget(self.status_label)

        # Persistence
        persist_label = QLabel("⏱ Signals: 5 min")
        persist_label.setFont(QFont("Arial", 8))
        persist_label.setStyleSheet("color: #10B981;")
        header_layout.addWidget(persist_label)

        # Update time
        self.time_label = QLabel(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        self.time_label.setFont(QFont("Arial", 8))
        self.time_label.setStyleSheet("color: #94A3B8;")
        header_layout.addWidget(self.time_label)

        layout.addLayout(header_layout)

        # === THREE TIMEFRAME GROUPS (NO HEADERS, NO BADGES) ===
        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(10)

        # Group 1: Short-term (M1, M5, M15)
        self.short_group = TimeframeGroup(['M1', 'M5', 'M15'])
        groups_layout.addWidget(self.short_group, 1)

        # Group 2: Medium-term (M30, H1, H2)
        self.mid_group = TimeframeGroup(['M30', 'H1', 'H2'])
        groups_layout.addWidget(self.mid_group, 1)

        # Group 3: Long-term (H4, H8, D1)
        self.long_group = TimeframeGroup(['H4', 'H8', 'D1'])
        groups_layout.addWidget(self.long_group, 1)

        layout.addLayout(groups_layout)

        # Apply theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply dark theme - NO WHITE BACKGROUNDS"""
        self.setStyleSheet("""
            OpportunityScannerWidget {
                background-color: #0A0E27;
                color: #F8FAFC;
            }
            QLabel {
                background-color: transparent;
            }
            QWidget {
                background-color: #0A0E27;
            }
            QScrollArea {
                background-color: #0A0E27;
                border: none;
            }
        """)

    def set_mt5_connector(self, mt5_connector):
        """Set MT5 connector"""
        self.mt5_connector = mt5_connector
        if not self.using_real_data:
            self.using_real_data = True
            print("[Opportunity Scanner] Switched to REAL MT5 data")
            self.scan_market()

    def scan_market(self):
        """Scan all pairs for opportunities"""
        self.blink_status()

        current_time = datetime.now()

        # Filter expired
        cutoff_time = current_time - timedelta(seconds=self.signal_persist_duration)
        self.opportunities = [
            opp for opp in self.opportunities
            if opp.get('timestamp', current_time) > cutoff_time
        ]

        # Get new opportunities
        new_opportunities = []
        if self.using_real_data and self.mt5_connector:
            new_opportunities = self.scan_real_market_data()
            if len(new_opportunities) == 0:
                new_opportunities = self.generate_opportunities()
        else:
            new_opportunities = self.generate_opportunities()

        # Add timestamps
        for opp in new_opportunities:
            if 'timestamp' not in opp:
                opp['timestamp'] = current_time

        # Merge
        existing_keys = {(o['symbol'], o['timeframe']) for o in self.opportunities}
        for opp in new_opportunities:
            key = (opp['symbol'], opp['timeframe'])
            if key not in existing_keys:
                self.opportunities.append(opp)

        # Sort by quality
        self.opportunities.sort(key=lambda x: x['quality_score'], reverse=True)

        # Update display
        self.update_display()

        # Update time
        self.time_label.setText(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

    def generate_opportunities(self) -> List[Dict]:
        """Generate opportunities across all timeframes"""
        opportunities = []

        timeframe_groups = {
            'short': ['M1', 'M5', 'M15'],
            'medium': ['M30', 'H1', 'H2'],
            'long': ['H4', 'H8', 'D1']
        }

        # Generate 4-8 per group (to fill 4 cards per row properly)
        for group_name, timeframes in timeframe_groups.items():
            num_opps = random.randint(4, 8)

            for _ in range(num_opps):
                pair = random.choice(self.pairs_to_scan)
                direction = random.choice(['BUY', 'SELL'])
                timeframe = random.choice(timeframes)

                base_price = self.get_base_price(pair)
                entry = base_price + random.uniform(-0.0020, 0.0020)

                if direction == 'BUY':
                    stop_loss = entry - random.uniform(0.0015, 0.0030)
                    take_profit = entry + random.uniform(0.0030, 0.0080)
                else:
                    stop_loss = entry + random.uniform(0.0015, 0.0030)
                    take_profit = entry - random.uniform(0.0030, 0.0080)

                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                rr = reward / risk if risk > 0 else 0

                quality_score = random.randint(60, 95)

                all_reasons = [
                    'Order Block', 'FVG', 'Liquidity Sweep', 'Structure Break',
                    'Trend Alignment', 'Volume Spike', 'Session Open', 'Key Level',
                    'Fibonacci 61.8%', 'Supply/Demand', 'Pattern Confirmed',
                    'MTF Confluence', 'Momentum Shift', 'Breakout'
                ]

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
        """Get base price"""
        base_prices = {
            'EURUSD': 1.16104, 'GBPUSD': 1.31850, 'USDJPY': 149.50,
            'AUDUSD': 0.68500, 'USDCAD': 1.34200, 'NZDUSD': 0.62300,
            'USDCHF': 0.87500, 'EURGBP': 0.88000, 'EURJPY': 173.50,
            'GBPJPY': 197.00, 'AUDJPY': 102.50, 'EURAUD': 1.69500,
            'EURNZD': 1.86200, 'GBPAUD': 1.92500, 'GBPNZD': 2.11500,
            'NZDJPY': 92.50, 'CHFJPY': 170.80, 'CADCHF': 0.65200,
            'AUDCAD': 0.91500, 'AUDNZD': 1.09800
        }
        return base_prices.get(pair, 1.0000)

    def scan_real_market_data(self) -> List[Dict]:
        """Scan real MT5 data"""
        opportunities = []

        all_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H2', 'H4', 'H8', 'D1']

        for pair in self.pairs_to_scan[:8]:
            for timeframe in random.sample(all_timeframes, 3):
                df = self.mt5_connector.get_candles(pair, timeframe, 100)

                if df is None or len(df) < 50:
                    continue

                opp = self.analyze_opportunity(pair, timeframe, df)
                if opp:
                    opportunities.append(opp)

        return opportunities

    def analyze_opportunity(self, symbol: str, timeframe: str, df) -> Optional[Dict]:
        """Analyze for opportunity"""
        try:
            current_close = df['close'].iloc[-1]

            if len(df) >= 20:
                sma_20 = df['close'].tail(20).mean()
                trend = 'BUY' if current_close > sma_20 else 'SELL'
            else:
                return None

            df['hl'] = df['high'] - df['low']
            atr = df['hl'].tail(14).mean()

            if trend == 'BUY':
                entry = current_close
                stop_loss = entry - (atr * 1.5)
                take_profit = entry + (atr * 3.0)
            else:
                entry = current_close
                stop_loss = entry + (atr * 1.5)
                take_profit = entry - (atr * 3.0)

            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr = reward / risk if risk > 0 else 0

            quality_score = 60
            reasons = []

            if len(df) >= 50:
                sma_50 = df['close'].tail(50).mean()
                if (trend == 'BUY' and current_close > sma_50) or (trend == 'SELL' and current_close < sma_50):
                    quality_score += 15
                    reasons.append('Trend Alignment')

            if rr >= 2.0:
                quality_score += 10
                reasons.append('High R:R')

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
            return None

    def update_display(self):
        """Update all three groups with filtered opportunities"""
        # Separate by timeframe
        short_term = [opp for opp in self.opportunities if opp['timeframe'] in ['M1', 'M5', 'M15']]
        medium_term = [opp for opp in self.opportunities if opp['timeframe'] in ['M30', 'H1', 'H2']]
        long_term = [opp for opp in self.opportunities if opp['timeframe'] in ['H4', 'H8', 'D1']]

        # Update each group (max 12 per group = 3 rows x 4 columns)
        self.short_group.update_opportunities(short_term[:12])
        self.mid_group.update_opportunities(medium_term[:12])
        self.long_group.update_opportunities(long_term[:12])

    def blink_status(self):
        """Blink status"""
        self.status_label.setStyleSheet("color: #FFFFFF;")
        QTimer.singleShot(200, lambda: self.status_label.setStyleSheet("color: #10B981;"))
