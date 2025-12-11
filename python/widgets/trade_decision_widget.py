"""
AppleTrader Pro - Trade Decision Widget
Displays the current trade decision from the decision engine
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QPushButton, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import Optional

from core.decision_engine import TradeDecision, DecisionAction


class TradeDecisionWidget(QWidget):
    """
    Trade Decision Display Widget

    Shows:
    - Current trade decision (ENTER/WAIT/SKIP)
    - Confidence score
    - Entry, SL, TP prices
    - Reasons for decision
    - One-click execute button
    """

    execute_trade = pyqtSignal(dict)  # Emits trade parameters when execute clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_decision: Optional[TradeDecision] = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # === HEADER ===
        header_layout = QHBoxLayout()

        title = QLabel("🎯 Trade Decision")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Last update time
        self.time_label = QLabel("--:--:--")
        self.time_label.setFont(QFont("Arial", 8))
        self.time_label.setStyleSheet("color: #94A3B8;")
        header_layout.addWidget(self.time_label)

        layout.addLayout(header_layout)

        # === DECISION FRAME ===
        self.decision_frame = QFrame()
        self.decision_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.decision_frame.setMinimumHeight(200)

        decision_layout = QVBoxLayout(self.decision_frame)
        decision_layout.setContentsMargins(10, 10, 10, 10)
        decision_layout.setSpacing(8)

        # Action label (ENTER/WAIT/SKIP)
        self.action_label = QLabel("SCANNING...")
        self.action_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        decision_layout.addWidget(self.action_label)

        # Symbol + Direction
        symbol_layout = QHBoxLayout()
        symbol_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.symbol_label = QLabel("--")
        self.symbol_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        symbol_layout.addWidget(self.symbol_label)

        self.direction_label = QLabel("")
        self.direction_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        symbol_layout.addWidget(self.direction_label)

        decision_layout.addLayout(symbol_layout)

        # Confidence bar
        confidence_layout = QHBoxLayout()
        confidence_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        conf_label = QLabel("Confidence:")
        conf_label.setFont(QFont("Arial", 9))
        confidence_layout.addWidget(conf_label)

        self.confidence_label = QLabel("--")
        self.confidence_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        confidence_layout.addWidget(self.confidence_label)

        decision_layout.addLayout(confidence_layout)

        # Trade parameters (Entry, SL, TP, R:R)
        params_layout = QHBoxLayout()
        params_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.entry_label = QLabel("Entry: --")
        self.entry_label.setFont(QFont("Courier", 9))
        params_layout.addWidget(self.entry_label)

        self.sl_label = QLabel("SL: --")
        self.sl_label.setFont(QFont("Courier", 9))
        params_layout.addWidget(self.sl_label)

        self.tp_label = QLabel("TP: --")
        self.tp_label.setFont(QFont("Courier", 9))
        params_layout.addWidget(self.tp_label)

        self.rr_label = QLabel("R:R --")
        self.rr_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
        params_layout.addWidget(self.rr_label)

        decision_layout.addLayout(params_layout)

        # Lot size
        self.lot_label = QLabel("Lot Size: --")
        self.lot_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        decision_layout.addWidget(self.lot_label)

        # Execute button (only shown for ENTER decisions)
        self.execute_btn = QPushButton("🚀 EXECUTE TRADE")
        self.execute_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.execute_btn.setMinimumHeight(40)
        self.execute_btn.clicked.connect(self.on_execute_clicked)
        self.execute_btn.setVisible(False)
        decision_layout.addWidget(self.execute_btn)

        layout.addWidget(self.decision_frame)

        # === REASONS ===
        reasons_group = QGroupBox("✓ Reasons")
        reasons_layout = QVBoxLayout()

        self.reasons_text = QTextEdit()
        self.reasons_text.setReadOnly(True)
        self.reasons_text.setMaximumHeight(80)
        self.reasons_text.setFont(QFont("Courier", 9))
        reasons_layout.addWidget(self.reasons_text)

        reasons_group.setLayout(reasons_layout)
        layout.addWidget(reasons_group)

        # === BLOCKERS (only shown if WAIT/SKIP) ===
        self.blockers_group = QGroupBox("⚠️ Blockers")
        blockers_layout = QVBoxLayout()

        self.blockers_text = QTextEdit()
        self.blockers_text.setReadOnly(True)
        self.blockers_text.setMaximumHeight(60)
        self.blockers_text.setFont(QFont("Courier", 9))
        blockers_layout.addWidget(self.blockers_text)

        self.blockers_group.setLayout(blockers_layout)
        self.blockers_group.setVisible(False)
        layout.addWidget(self.blockers_group)

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
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 3px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #10B981;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)

    def update_decision(self, decision: TradeDecision):
        """Update display with new decision"""
        self.current_decision = decision

        # Update time
        self.time_label.setText(decision.timestamp.strftime("%H:%M:%S"))

        # Update action and styling
        action = decision.action

        if action == DecisionAction.ENTER:
            self.action_label.setText("✅ ENTER TRADE")
            self.action_label.setStyleSheet("color: #10B981;")  # Green
            self.decision_frame.setStyleSheet("""
                QFrame {
                    background-color: #064E3B;
                    border: 3px solid #10B981;
                    border-radius: 8px;
                }
            """)
            self.execute_btn.setVisible(True)
            self.blockers_group.setVisible(False)

        elif action == DecisionAction.WAIT:
            self.action_label.setText("⏸️ WAIT")
            self.action_label.setStyleSheet("color: #F59E0B;")  # Orange
            self.decision_frame.setStyleSheet("""
                QFrame {
                    background-color: #78350F;
                    border: 3px solid #F59E0B;
                    border-radius: 8px;
                }
            """)
            self.execute_btn.setVisible(False)
            self.blockers_group.setVisible(True)

        else:  # SKIP
            self.action_label.setText("⛔ SKIP")
            self.action_label.setStyleSheet("color: #EF4444;")  # Red
            self.decision_frame.setStyleSheet("""
                QFrame {
                    background-color: #7F1D1D;
                    border: 3px solid #EF4444;
                    border-radius: 8px;
                }
            """)
            self.execute_btn.setVisible(False)
            self.blockers_group.setVisible(True)

        # Update symbol and direction
        self.symbol_label.setText(decision.symbol)

        if decision.direction == 'BUY':
            self.direction_label.setText("📈 BUY")
            self.direction_label.setStyleSheet("color: #10B981;")
        else:
            self.direction_label.setText("📉 SELL")
            self.direction_label.setStyleSheet("color: #EF4444;")

        # Update confidence
        confidence_pct = decision.confidence * 100
        self.confidence_label.setText(f"{confidence_pct:.0f}%")

        if confidence_pct >= 75:
            self.confidence_label.setStyleSheet("color: #10B981;")
        elif confidence_pct >= 60:
            self.confidence_label.setStyleSheet("color: #F59E0B;")
        else:
            self.confidence_label.setStyleSheet("color: #EF4444;")

        # Update trade parameters
        if decision.entry > 0:
            self.entry_label.setText(f"Entry: {decision.entry:.5f}")
            self.sl_label.setText(f"SL: {decision.stop_loss:.5f}")
            self.tp_label.setText(f"TP: {decision.take_profit:.5f}")
            self.rr_label.setText(f"R:R {decision.risk_reward:.1f}")
            self.lot_label.setText(f"Lot Size: {decision.lot_size:.2f}")

            # Style based on R:R
            if decision.risk_reward >= 2.5:
                self.rr_label.setStyleSheet("color: #10B981;")
            elif decision.risk_reward >= 2.0:
                self.rr_label.setStyleSheet("color: #3B82F6;")
            else:
                self.rr_label.setStyleSheet("color: #F59E0B;")
        else:
            self.entry_label.setText("Entry: --")
            self.sl_label.setText("SL: --")
            self.tp_label.setText("TP: --")
            self.rr_label.setText("R:R --")
            self.lot_label.setText("Lot Size: --")

        # Update reasons
        if decision.reasons:
            reasons_text = '\n'.join(f"✓ {reason}" for reason in decision.reasons)
            self.reasons_text.setPlainText(reasons_text)
        else:
            self.reasons_text.setPlainText("No analysis data")

        # Update blockers
        if decision.blockers:
            blockers_text = '\n'.join(f"⚠️ {blocker}" for blocker in decision.blockers)
            self.blockers_text.setPlainText(blockers_text)

    def on_execute_clicked(self):
        """Handle execute trade button click"""
        if not self.current_decision:
            return

        if self.current_decision.action != DecisionAction.ENTER:
            return

        # Emit trade parameters
        trade_params = {
            'symbol': self.current_decision.symbol,
            'direction': self.current_decision.direction,
            'entry': self.current_decision.entry,
            'stop_loss': self.current_decision.stop_loss,
            'take_profit': self.current_decision.take_profit,
            'lot_size': self.current_decision.lot_size
        }

        self.execute_trade.emit(trade_params)

    def clear_display(self):
        """Clear the display"""
        self.action_label.setText("NO OPPORTUNITIES")
        self.action_label.setStyleSheet("color: #6B7280;")
        self.symbol_label.setText("--")
        self.direction_label.setText("")
        self.confidence_label.setText("--")
        self.entry_label.setText("Entry: --")
        self.sl_label.setText("SL: --")
        self.tp_label.setText("TP: --")
        self.rr_label.setText("R:R --")
        self.lot_label.setText("Lot Size: --")
        self.reasons_text.setPlainText("Waiting for opportunities...")
        self.blockers_text.setPlainText("")
        self.execute_btn.setVisible(False)
        self.blockers_group.setVisible(False)
        self.decision_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
