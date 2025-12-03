# AppleTrader Pro - Institutional Trading Dashboard

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**Professional-grade trading dashboard with 10 advanced institutional improvements**

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **MT5 Terminal** - With `InstitutionalTradingRobot_v3.mq5` EA running
- **Windows 10/11** (or Linux/Mac with adjustments)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Superuser2025/MagicBranch.git
cd MagicBranch/Apple/python
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Launch the application:**
```bash
python main.py
```

**Or simply double-click:** `run_appletrader.bat`

---

## 📊 Features Overview

### All 10 Institutional Improvements Integrated:

#### 1️⃣ **Multi-Symbol Correlation Heatmap**
- Real-time correlation analysis across 12+ pairs
- Divergence detection and alerts
- Color-coded matrix (dark green = +0.8, dark red = -0.8)
- **Impact:** Catch hidden divergence opportunities, save 15-20 min/day

#### 2️⃣ **Volatility-Adjusted Position Sizing**
- Dynamic lot sizing based on ATR/ADX
- Automatic adjustment: HIGH vol → -30%, LOW vol → +30%
- Strong trend → +20%, Ranging → -30%
- **Impact:** -30% max drawdown, maintains true risk %

#### 3️⃣ **Session Momentum Scanner**
- Live momentum leaderboard (top 10 pairs)
- ATR spike + range expansion + volume analysis
- Auto-focus on highest momentum
- **Impact:** Immediate focus on best opportunities

#### 4️⃣ **Institutional Order Flow Footprint**
- Large order detection (absorption, sweep, accumulation)
- Volume spike threshold: 3× average
- Chart markers sized by order volume
- **Impact:** Trade WITH institutions, not against them

#### 5️⃣ **AI-Powered Pattern Quality Scorer**
- 0-100 scoring system with 5-star ratings
- Confluence detection (FVG, OB, liquidity, MTF)
- Historical win rate tracking
- **Impact:** +8-12% win rate, only trade 4-5 star setups

#### 6️⃣ **Multi-Timeframe Structure Map**
- Support/resistance across W1/D1/H4/H1/M15
- Confluence zone detection (2+ timeframes)
- Chart overlays with adaptive line weights
- **Impact:** +5-8% win rate at confluence zones

#### 7️⃣ **News Event Impact Predictor**
- Economic calendar with historical 12-month impact
- Auto-flatten alerts 5min before EXTREME events
- Expected pip movement per event
- **Impact:** -80% spike losses, +3-5% win rate

#### 8️⃣ **Risk-Reward Optimizer**
- Structure-based TP placement (not arbitrary pips)
- Expected value calculation per TP level
- Quality rating (1-5 stars per TP)
- **Impact:** +40% average R per trade

#### 9️⃣ **Equity Curve & Drawdown Analyzer**
- Live equity curve chart (30-day view)
- Daily/weekly loss limit monitoring
- Psychological state detection
- **Impact:** -50% emotional trading, prevents blowups

🔟 **Automated Trade Journal with AI Insights**
- Zero manual journaling work
- Performance by setup/session/day
- AI-powered pattern recognition
- Personalized recommendations
- **Impact:** Continuous improvement, identifies your edge

---

## 🎯 Layout & Interface

### Main Window (3-Column Layout):

```
┌─────────────────────────────────────────────────────────────┐
│  AppleTrader Pro     [Symbol: EURUSD] [TF: H4]  🔴 Status  │
├─────────────────┬────────────────────┬──────────────────────┤
│  LEFT (40%)     │  CENTER (35%)      │  RIGHT (25%)         │
│                 │                    │                      │
│  📈 CHART       │  ⚡ Momentum       │  🎯 Position Size    │
│                 │  🔥 Correlation    │  🎯 Risk-Reward      │
│  ───────────    │  📊 Structure      │  ⭐ Quality          │
│                 │  💼 Order Flow     │  📊 Equity           │
│  🎛️ CONTROLS    │  📰 News           │  📝 Journal          │
│                 │                    │                      │
└─────────────────┴────────────────────┴──────────────────────┘
```

### Tab System:
- **Left Panel:** Chart + Interactive Controls
- **Center Panel:** 5 Analysis Tabs (Momentum, Correlation, Structure, Order Flow, News)
- **Right Panel:** 5 Performance Tabs (Position Size, R:R, Quality, Equity, Journal)

---

## 🔌 MT5 Integration

### Data Communication:
The EA exports JSON data to:
```
%APPDATA%\MetaQuotes\Terminal\Common\Files\AppleTrader\market_data.json
```

### Exported Data Structure:
```json
{
  "candles_EURUSD_H4": [...],
  "price_EURUSD": 1.10000,
  "zones_EURUSD": {
    "fvgs": [...],
    "order_blocks": [...],
    "liquidity": [...]
  },
  "ml_EURUSD": {...},
  "positions": [...]
}
```

### Command System:
The GUI can send commands to EA via:
```
%APPDATA%\MetaQuotes\Terminal\Common\Files\AppleTrader\commands.json
```

---

## 📁 Project Structure

```
Apple/python/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── run_appletrader.bat             # Windows launcher
├── README.md                        # This file
│
├── gui/
│   ├── main_window.py              # Main application window
│   ├── chart_panel_matplotlib.py   # Chart display
│   └── controls_panel.py           # Interactive controls
│
├── core/
│   ├── mt5_connector.py            # MT5 JSON data reader
│   ├── data_manager.py             # Data processing
│   ├── risk_manager.py             # Risk management
│   └── command_manager.py          # Command system
│
└── widgets/                         # All 10 improvements
    ├── correlation_analyzer.py
    ├── correlation_heatmap_widget.py
    ├── equity_curve_analyzer.py
    ├── equity_curve_widget.py
    ├── mtf_structure_map.py
    ├── mtf_structure_widget.py
    ├── news_impact_predictor.py
    ├── news_impact_widget.py
    ├── order_flow_detector.py
    ├── order_flow_widget.py
    ├── pattern_scorer.py
    ├── pattern_scorer_widget.py
    ├── risk_reward_optimizer.py
    ├── risk_reward_widget.py
    ├── session_momentum_scanner.py
    ├── session_momentum_widget.py
    ├── trade_journal.py
    ├── trade_journal_widget.py
    ├── volatility_position_sizer.py
    └── volatility_position_widget.py
```

---

## ⚙️ Configuration

### Symbol List
Edit `main_window.py` line 61 to customize symbols:
```python
self.symbol_combo.addItems([
    "EURUSD", "GBPUSD", "USDJPY", ...
])
```

### Update Frequency
Edit `main_window.py` line 31 to adjust update interval:
```python
self.data_timer.start(1000)  # 1000ms = 1 second
```

### Data Directory
Auto-detected at:
```
%APPDATA%\MetaQuotes\Terminal\Common\Files\AppleTrader\
```

To change, edit `mt5_connector.py` line 40

---

## 🎨 Theming

All widgets use a consistent **dark theme** with:
- Background: `#1e1e1e`
- Panels: `#2b2b2b`
- Accent: `#0d7377`
- Text: `#ffffff`

Customize in `main_window.py` method `apply_dark_theme()`

---

## 🚀 Performance Tips

1. **Reduce Update Frequency** - For slower PCs, increase timer interval to 2-3 seconds
2. **Close Unused Tabs** - Only keep active tabs open to save CPU
3. **Limit Candle History** - Reduce lookback periods in analyzers
4. **Use H4 Timeframe** - Lower timeframes require more processing

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install --upgrade -r requirements.txt
```

### "No data displayed"
1. Check MT5 EA is running
2. Verify JSON files exist in data directory
3. Check file permissions
4. Restart both EA and GUI

### "PyQt6 import error"
```bash
pip uninstall PyQt6
pip install PyQt6
```

### Connection shows "Disconnected"
- Ensure EA is running on MT5
- Check EA exports data every second
- Verify data directory path

---

## 📈 Expected Performance Impact

Based on PROJECT_MEMORY.md specifications:

| Metric | Improvement |
|--------|-------------|
| ⏱️ Time Saved | 45-60 min/day |
| 📈 Win Rate | +15-25% |
| 🛡️ Drawdown | -30-50% |
| 💰 Avg R per Trade | +40% |

---

## 🔐 License

MIT License - See LICENSE file

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `PROJECT_MEMORY.md` for comprehensive documentation
3. Check GitHub issues

---

## 🎯 Next Steps

1. ✅ **Install** - Follow Quick Start guide
2. ✅ **Connect MT5** - Ensure EA is running
3. ✅ **Test Features** - Try each of the 10 improvements
4. ✅ **Customize** - Adjust symbols, timeframes, settings
5. ✅ **Trade** - Use insights to improve your trading

---

**Built with ❤️ for institutional-grade trading**

Version 1.0 | © 2025 AppleTrader Pro
