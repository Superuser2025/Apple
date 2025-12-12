"""
AppleTrader Pro - Live Market Opportunity Scanner
Scans all pairs for high-probability trading setups in real-time
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import numpy as np


class OpportunityCard(QFrame):
    """Card widget for a single trading opportunity"""

    def __init__(self, opportunity: Dict, parent=None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.setObjectName("OpportunityCard")  # Set object name for specific styling
        self.init_ui()

    def init_ui(self):
        """Initialize the opportunity card UI"""
        self.setFixedHeight(110)
        self.setFixedWidth(280)  # Set fixed width for consistency
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
                padding: 8px;
            }}
            OpportunityCard QLabel {{
                background-color: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Header: Symbol + Direction + Score
        header_layout = QHBoxLayout()

        symbol_label = QLabel(self.opportunity['symbol'])
        symbol_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        symbol_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(symbol_label)

        direction = self.opportunity['direction']
        dir_color = '#10B981' if direction == 'BUY' else '#EF4444'
        dir_icon = '📈' if direction == 'BUY' else '📉'
        dir_label = QLabel(f"{dir_icon} {direction}")
        dir_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        dir_label.setStyleSheet(f"color: {dir_color};")
        header_layout.addWidget(dir_label)

        header_layout.addStretch()

        score_label = QLabel(f"⭐ {score}")
        score_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        score_label.setStyleSheet(f"color: {border_color};")
        header_layout.addWidget(score_label)

        layout.addLayout(header_layout)

        # Entry and targets
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(15)

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
        reasons_text = " • ".join(reasons[:3])  # Top 3 reasons
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

        self.init_ui()

        # Auto-scan timer (every 10 seconds)
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_market)
        self.scan_timer.start(10000)

        # Initial scan - delayed to ensure UI is fully initialized
        QTimer.singleShot(100, self.scan_market)

    def init_ui(self):
        """Initialize the user interface"""
        # Set minimum size for the widget
        self.setMinimumHeight(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🎯 Live Market Opportunity Scanner")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
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

        # === INFO BAR ===
        info_layout = QHBoxLayout()

        info_text = QLabel("Showing high-probability setups across all pairs • Ranked by quality • Auto-updated")
        info_text.setFont(QFont("Arial", 9))
        info_text.setStyleSheet("color: #6B7280;")
        info_layout.addWidget(info_text)

        info_layout.addStretch()

        self.count_label = QLabel("0 opportunities found")
        self.count_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.count_label.setStyleSheet("color: #3B82F6;")
        info_layout.addWidget(self.count_label)

        layout.addLayout(info_layout)

        # === OPPORTUNITIES GRID ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(140)  # Ensure minimum height for displaying cards
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

        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

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
        """Scan all pairs for trading opportunities using REAL MT5 data"""
        print(f"[Opportunity Scanner] Scanning at {datetime.now().strftime('%H:%M:%S')}")
        self.blink_status()

        # Only scan if MT5 is connected
        if self.using_real_data and self.mt5_connector:
            self.opportunities = self.scan_real_market_data()
            print(f"[Opportunity Scanner] ✓ Found {len(self.opportunities)} real opportunities")
        else:
            # MT5 not connected - show message
            print(f"[Opportunity Scanner] ⚠️ MT5 not connected - no opportunities")
            self.opportunities = []

        # Sort by quality score (highest first)
        self.opportunities.sort(key=lambda x: x['quality_score'], reverse=True)

        # Update display
        self.update_display()

        # Update time and status
        self.time_label.setText(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        if self.using_real_data:
            self.status_label.setText("🟢 LIVE DATA")
        else:
            self.status_label.setText("🔴 DISCONNECTED")

    def generate_opportunities(self) -> List[Dict]:
        """Generate trading opportunities (demo version with realistic data)"""
        opportunities = []

        # Number of opportunities to show (3-6 for better visibility)
        num_opportunities = random.randint(3, 6)

        for _ in range(num_opportunities):
            pair = random.choice(self.pairs_to_scan)
            direction = random.choice(['BUY', 'SELL'])
            timeframe = random.choice(['H1', 'H4', 'D1'])

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

        # Scan all pairs across timeframes
        timeframes = ['H1', 'H4']  # Focus on these timeframes

        for pair in self.pairs_to_scan:  # Scan all pairs
            for timeframe in timeframes:
                try:
                    # Get candle data from MT5
                    df = self.mt5_connector.get_candles(pair, timeframe, 200)

                    if df is None or len(df) < 100:
                        continue

                    # Analyze for trading opportunity
                    opp = self.analyze_opportunity(pair, timeframe, df)
                    if opp:
                        opportunities.append(opp)
                        print(f"[Opportunity Scanner] ✓ {pair} {timeframe}: Score {opp['quality_score']}")

                except Exception as e:
                    print(f"[Opportunity Scanner] Error scanning {pair} {timeframe}: {e}")
                    continue

        return opportunities

    def analyze_opportunity(self, symbol: str, timeframe: str, df) -> Optional[Dict]:
        """
        Analyze candle data for HIGH-QUALITY trading opportunities

        Uses confluence of:
        - Pattern detection (pin bars, engulfing, inside bars)
        - Trend alignment (EMA 20/50/200)
        - Momentum (RSI, Volume)
        - Structure (support/resistance)
        - ATR-based positioning
        """
        try:
            if len(df) < 100:
                return None

            # === CALCULATE INDICATORS ===
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            open_price = df['open'].values

            current_close = close[-1]
            current_high = high[-1]
            current_low = low[-1]
            current_open = open_price[-1]
            prev_close = close[-2]
            prev_open = open_price[-2]
            prev_high = high[-2]
            prev_low = low[-2]

            # Calculate EMAs
            ema_20 = pd.Series(close).ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = pd.Series(close).ewm(span=50, adjust=False).mean().iloc[-1]
            ema_200 = pd.Series(close).ewm(span=200, adjust=False).mean().iloc[-1] if len(close) >= 200 else ema_50

            # Calculate ATR for stop loss and take profit
            tr = []
            for i in range(1, len(df)):
                tr_value = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr.append(tr_value)
            atr = np.mean(tr[-14:]) if len(tr) >= 14 else (high[-1] - low[-1])

            # Calculate RSI
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

            # === DETECT PATTERNS ===
            pattern_detected = None
            pattern_direction = None
            quality_score = 50
            reasons = []

            # Bullish Engulfing
            if (current_close > current_open and  # Current candle is bullish
                prev_close < prev_open and  # Previous candle was bearish
                current_close > prev_open and  # Current close above prev open
                current_open < prev_close):  # Current open below prev close
                pattern_detected = "Bullish Engulfing"
                pattern_direction = "BUY"
                quality_score += 15
                reasons.append("Bullish Engulfing")

            # Bearish Engulfing
            elif (current_close < current_open and  # Current candle is bearish
                  prev_close > prev_open and  # Previous candle was bullish
                  current_close < prev_open and  # Current close below prev open
                  current_open > prev_close):  # Current open above prev close
                pattern_detected = "Bearish Engulfing"
                pattern_direction = "SELL"
                quality_score += 15
                reasons.append("Bearish Engulfing")

            # Bullish Pin Bar
            elif (current_close > current_open and  # Bullish candle
                  (current_low - min(current_open, current_close)) > 2 * abs(current_close - current_open) and  # Long lower wick
                  (current_high - max(current_open, current_close)) < 0.5 * abs(current_close - current_open)):  # Small upper wick
                pattern_detected = "Bullish Pin Bar"
                pattern_direction = "BUY"
                quality_score += 12
                reasons.append("Bullish Pin Bar")

            # Bearish Pin Bar
            elif (current_close < current_open and  # Bearish candle
                  (max(current_open, current_close) - current_high) < 0.5 * abs(current_close - current_open) and  # Small upper wick
                  (min(current_open, current_close) - current_low) > 2 * abs(current_close - current_open)):  # Long lower wick
                pattern_detected = "Bearish Pin Bar"
                pattern_direction = "SELL"
                quality_score += 12
                reasons.append("Bearish Pin Bar")

            # No pattern detected
            else:
                # Check for simple trend continuation
                if current_close > ema_20 and ema_20 > ema_50:
                    pattern_direction = "BUY"
                    pattern_detected = "Trend Continuation"
                    quality_score += 5
                elif current_close < ema_20 and ema_20 < ema_50:
                    pattern_direction = "SELL"
                    pattern_detected = "Trend Continuation"
                    quality_score += 5
                else:
                    return None  # No clear setup

            # === VALIDATE TREND ALIGNMENT ===
            if pattern_direction == "BUY":
                if current_close > ema_20 > ema_50 > ema_200:
                    quality_score += 20
                    reasons.append("Strong Uptrend")
                elif current_close > ema_20 > ema_50:
                    quality_score += 12
                    reasons.append("Uptrend Aligned")
                else:
                    quality_score -= 10  # Against trend

            elif pattern_direction == "SELL":
                if current_close < ema_20 < ema_50 < ema_200:
                    quality_score += 20
                    reasons.append("Strong Downtrend")
                elif current_close < ema_20 < ema_50:
                    quality_score += 12
                    reasons.append("Downtrend Aligned")
                else:
                    quality_score -= 10  # Against trend

            # === VALIDATE RSI ===
            if pattern_direction == "BUY" and 30 < current_rsi < 70:
                quality_score += 10
                reasons.append("RSI Favorable")
            elif pattern_direction == "SELL" and 30 < current_rsi < 70:
                quality_score += 10
                reasons.append("RSI Favorable")
            elif (pattern_direction == "BUY" and current_rsi < 30) or (pattern_direction == "SELL" and current_rsi > 70):
                quality_score += 8
                reasons.append("RSI Oversold/Overbought")

            # === CHECK VOLUME ===
            if 'volume' in df.columns or 'tick_volume' in df.columns:
                vol_col = 'volume' if 'volume' in df.columns else 'tick_volume'
                avg_volume = df[vol_col].tail(20).mean()
                current_volume = df[vol_col].iloc[-1]

                if current_volume > avg_volume * 1.8:
                    quality_score += 15
                    reasons.append("High Volume")
                elif current_volume > avg_volume * 1.3:
                    quality_score += 8
                    reasons.append("Above Avg Volume")

            # === CALCULATE ENTRY, SL, TP ===
            if pattern_direction == "BUY":
                entry = current_close
                stop_loss = current_low - (atr * 0.5)  # Below pattern low
                take_profit = entry + (atr * 2.5)  # 2.5 ATR target

            else:  # SELL
                entry = current_close
                stop_loss = current_high + (atr * 0.5)  # Above pattern high
                take_profit = entry - (atr * 2.5)  # 2.5 ATR target

            # Calculate risk:reward
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr = reward / risk if risk > 0 else 0

            # Bonus for good R:R
            if rr >= 2.5:
                quality_score += 8
                reasons.append(f"R:R {rr:.1f}")

            # === QUALITY THRESHOLD ===
            # Only return opportunities with score > 65
            if quality_score < 50:  # Lowered from 65 to 50 to see more opportunities
                return None

            # Ensure we have reasons
            if not reasons:
                reasons = [pattern_detected]

            return {
                'symbol': symbol,
                'direction': pattern_direction,
                'timeframe': timeframe,
                'entry': float(entry),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward': float(rr),
                'quality_score': min(100, quality_score),  # Cap at 100
                'confluence_reasons': reasons[:4]  # Top 4 reasons
            }

        except Exception as e:
            print(f"[Opportunity Scanner] Error analyzing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_display(self):
        """Update the opportunities grid display"""
        print(f"[DEBUG] update_display() called with {len(self.opportunities)} opportunities")

        # Clear existing cards - properly remove them
        cleared_count = 0
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
                cleared_count += 1
        print(f"[DEBUG] Cleared {cleared_count} existing widgets")

        # Add opportunity cards (3 per row for better visibility)
        for idx, opp in enumerate(self.opportunities):
            card = OpportunityCard(opp)
            card.mousePressEvent = lambda event, o=opp: self.opportunity_selected.emit(o)
            card.setCursor(Qt.CursorShape.PointingHandCursor)

            row = idx // 3
            col = idx % 3
            self.grid_layout.addWidget(card, row, col)
            print(f"[DEBUG] Added card {idx} at row={row}, col={col}: {opp['symbol']} {opp['direction']}")

        # Update count
        count = len(self.opportunities)
        self.count_label.setText(f"{count} opportunit{'y' if count == 1 else 'ies'} found")
        print(f"[DEBUG] Count label updated: {count} opportunities")

        # Force parent widget to update its layout
        self.updateGeometry()
        self.update()

    def blink_status(self):
        """Blink the scanning status indicator"""
        self.status_label.setStyleSheet("color: #FFFFFF;")
        QTimer.singleShot(200, lambda: self.status_label.setStyleSheet("color: #10B981;"))
