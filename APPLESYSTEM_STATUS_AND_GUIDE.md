# AppleTrader Pro - System Status & User Guide

**Last Updated:** 2025-12-04
**Session:** claude/fix-branch-conflicts-01XGD6duwT9xwsZuBh9PxQG9

---

## ✅ ISSUES FIXED IN THIS SESSION

### 1. **Opportunity Scanner - FIXED**

**Problems:**
- Signals disappeared in seconds (despite being D1/H1/H4 timeframes)
- No timeframe filter available
- Cards didn't fill width - huge gaps
- Duplicate symbols showing

**Solutions:**
- ✅ **Signals now persist for 5 minutes minimum** (configurable)
- ✅ **Timeframe filter dropdown added** (ALL, M15, M30, H1, H4, D1)
- ✅ **Cards now fill full width** - no more wasted space
- ✅ **No duplicate symbols** - each symbol appears once per scan
- ✅ **Scan interval: 30 seconds** (was 10s - gives signals time to be visible)

**How It Works:**
- Scanner tracks signal timestamps
- Signals persist for `signal_persist_duration` (300s default)
- New scans merge with persisted signals (no duplicates by symbol+timeframe)
- Timeframe filter applied in real-time

---

### 2. **Chart Commentary - FIXED**

**Problems:**
- No symbol information shown
- No timeframe information shown
- Always showed EURUSD regardless of selected pair
- Signals worthless without context

**Solutions:**
- ✅ **ALL commentary now shows SYMBOL + TIMEFRAME**
  - Header: "📊 EURUSD | H4"
  - System messages: "✅ EURUSD H4: Optimal timeframe..."
  - Pattern detection: "Patterns detected: 2 active [H4]"
- ✅ **Updates dynamically when you change symbol/timeframe**
- ✅ **Uses `self.current_symbol` and `self.current_timeframe` throughout**

**Every trading signal now has proper context!**

---

### 3. **Font Sizes - FIXED**

**Problems:**
- Left panel text tiny and unreadable
- Opportunity cards text too small
- Risk Management section illegible

**Solutions:**
- ✅ **Left panel fonts increased 40-44%**
  - All 9px → 13px
  - All 10px → 14px
  - All 12px → 16px
  - GroupBox titles → 15px
- ✅ **Opportunity cards fonts increased 22-27%**
  - Symbol: 12pt → 15pt
  - Direction/Score: 11pt → 14pt
  - Entry/SL/TP: 9pt → 11pt
- ✅ **All buttons enlarged** (MODE: 55px, BUY/SELL: 50px, etc.)

---

## ⚠️ KNOWN LIMITATIONS & WHAT NEEDS WORK

### 1. **Left-Hand Filters - NOT CONNECTED YET**

**Current Status:**
The 10 institutional filters, Smart Money Concepts, and ML settings in the left panel are **UI only** at this stage. They emit signals when toggled, but:

- ❌ **Not connected to EA logic** - EA needs to receive and process these signals
- ❌ **No selective timeframe application** - Would need EA-side implementation
- ❌ **Turning ON/OFF doesn't affect trading** - Visual state only

**Why:**
These filters need to be integrated with the MT5 EA (`InstitutionalTradingRobot_v3.mq5`). The Python GUI sends signals via `filter_toggled.emit(name, enabled)` but the EA must listen and apply the filters.

**What's Needed:**
1. EA must receive filter state from Python (via file/socket/pipe)
2. EA must apply filters conditionally based on state
3. EA must implement per-timeframe filter application

**Your Filters:**
- Volume Filter
- Spread Filter
- Strong Price Model
- Multi-Timeframe
- Volatility Filter
- Sentiment Filter
- Correlation Filter
- Volatility Adaptation
- Dynamic Risk
- Pattern Decay
- Liquidity Sweep
- Retail Trap Detection
- Order Block Invalidation
- Market Structure

---

### 2. **Risk Management - NEEDS ENHANCEMENT**

**Current Status:**
Basic Risk% spinbox (0.1-5.0%) exists but is "flaky" because:

- ❌ **No lot size calculator** visible
- ❌ **No profit-taking criteria** shown
- ❌ **No max trades per day/week**
- ❌ **No trailing stop settings**

**What I Found in EA (need to implement):**
Looking at `InstitutionalTradingRobot_v3.mq5`, you have:
- Lot size calculation based on risk %
- Max spread checks
- Daily/weekly loss limits
- Trailing stop logic
- Partial profit taking

**What Should Be Added to GUI:**
```
⚠️ RISK MANAGEMENT
├── Risk %: [1.0] (0.1-5.0)
├── Max Lots: [0.1] (or "Auto")
├── Max Trades/Day: [3]
├── Max Daily Loss: [5%]
├── Trailing Stop: [ON/OFF]
│   ├── Start (pips): [20]
│   └── Step (pips): [5]
├── Partial TP: [ON/OFF]
│   ├── TP1 @ [50%] take [30%]
│   └── TP2 @ [100%] take [100%]
└── Current Exposure: [display]
```

**I'll implement this if you confirm these are the settings you want exposed.**

---

### 3. **Chart Visualization - TOO MINIMALISTIC**

**Current Status:**
Chart shows:
- ✅ Candlesticks
- ✅ FVG zones (cyan/magenta rectangles)
- ✅ Order Blocks (orange/yellow rectangles)
- ✅ Liquidity zones (red/green horizontal lines)
- ✅ Candlestick patterns with timeframe labels
- ✅ Active Patterns panel (top-left)
- ✅ Price action commentary (middle-right)
- ✅ System status messages (top)

**What's MISSING (compared to MT5 EA):**
- ❌ **Support/Resistance levels** - horizontal lines at key levels
- ❌ **Pivot points** (Daily/Weekly/Monthly)
- ❌ **EMA/SMA lines** (if used in your strategy)
- ❌ **Volume profile** (if applicable)
- ❌ **Session open/close markers** (London, NY, Tokyo)
- ❌ **High/Low markers** for previous day/week
- ❌ **Fibonacci retracement levels**

**What I Can Add:**
I can implement all of the above. The MT5 EA screenshot showed more levels/lines. Tell me which ones are critical and I'll add them.

**Common additions:**
- Daily high/low horizontal lines
- Previous day close
- Weekly pivots
- 20/50/200 EMA lines
- Key psychological levels (round numbers)

---

### 4. **Right-Hand Panels - HOW TO USE**

**Current Layout:**
The right-hand side has **analysis tabs**:

1. **📊 Market Analysis Tab**
   - Price action commentary widget
   - Session momentum widget
   - Pattern scorer widget

2. **📈 Opportunities Tab**
   - Multi-timeframe structure widget
   - Institutional order flow widget
   - Volatility position widget

3. **🔔 News & Events Tab**
   - News impact widget
   - Shows upcoming economic events
   - Impact levels (High/Medium/Low)

4. **📝 Journal Tab**
   - Trade journal widget
   - Log your trades manually
   - Review past performance

5. **📊 Performance Tab**
   - Equity curve widget
   - Risk/reward widget
   - Win rate statistics

**How It Works:**
- These widgets pull data from `data_manager`
- `data_manager` reads the JSON files written by MT5 EA
- If EA isn't writing data → widgets show placeholder/demo data

**If you see stale data:**
- Check if EA is running and writing to JSON files
- Check `data_manager.get_latest_price()`, `data_manager.get_zones()`, etc.
- Widgets refresh every 1-2 seconds

**Your control:**
- You can switch between tabs to view different aspects
- Most widgets are read-only displays
- Some widgets (like Journal) allow manual input

---

## 🎯 WHAT NEEDS YOUR DECISION

### 1. **Risk Management Section**
Do you want me to add all the settings I listed above? (Max lots, trailing stop, partial TP, etc.)

### 2. **Chart Levels**
Which levels do you want on the chart?
- [ ] Support/Resistance lines
- [ ] Pivot points (Daily/Weekly)
- [ ] Previous day High/Low/Close
- [ ] EMA lines (which periods?)
- [ ] Session markers (London/NY open/close)
- [ ] Fibonacci levels
- [ ] Key psychological levels (round numbers)

### 3. **Left-Hand Filters**
Do you want me to:
- Create a communication bridge between Python GUI and MT5 EA?
- Or should filters only apply to visual display (hide zones, patterns, etc.)?

### 4. **Scanner Persistence Duration**
Is 5 minutes good, or do you want:
- [ ] 5 minutes (current)
- [ ] 10 minutes
- [ ] 30 minutes
- [ ] Configurable in UI

---

## 📖 HOW TO USE THE SYSTEM

### Starting the Application

```bash
python python/main_enhanced.py
```

### Workflow

1. **Start MT5 EA** first (it writes data to JSON files)
2. **Start Python GUI** second (it reads from those files)
3. **Select symbol/timeframe** in chart toolbar
4. **Watch opportunity scanner** for high-probability setups
5. **Use timeframe filter** to focus on specific timeframes
6. **Check chart commentary** for current pair analysis
7. **Review right-hand panels** for detailed analysis

### Opportunity Scanner

- **Green cards (⭐ 85+):** Excellent setups, high confluence
- **Blue cards (⭐ 70-84):** Good setups, decent confluence
- **Orange cards (⭐ 60-69):** Fair setups, lower confluence
- **Timeframe filter:** Focus on specific timeframe (M15, H1, H4, etc.)
- **Signals persist 5 minutes:** Won't disappear immediately

### Chart

- **Cyan/Magenta rectangles:** FVG zones (Fair Value Gaps)
- **Yellow/Orange rectangles:** Order Blocks
- **Red/Green horizontal lines:** Liquidity zones
- **Pattern labels:** Show pattern type + timeframe (e.g., "HAMMER [H4]")
- **Active Patterns panel (top-left):** Currently detected patterns
- **Commentary boxes (right):** Trend, momentum, pattern analysis
- **System messages (top):** Timeframe recommendations, volatility alerts

### Left Panel

- **Trading Mode:** AUTO = EA trades, MANUAL = indicators only
- **Quick Orders:** Place manual BUY/SELL (if implemented in EA)
- **Risk%:** Set per-trade risk (needs EA integration)
- **Filters:** Toggle institutional filters (UI state, needs EA connection)
- **Visuals:** Toggle chart elements (patterns, zones, commentary)

---

## 🐛 TROUBLESHOOTING

### Signals Disappear Too Fast
- ✅ **FIXED** - Now persist 5 minutes

### Can't See Chart Details
- ✅ **FIXED** - Commentary shows symbol + timeframe
- ⚠️ Still missing support/resistance levels (tell me what to add)

### Text Too Small
- ✅ **FIXED** - All fonts increased 22-44%

### Cards Don't Fill Width
- ✅ **FIXED** - Cards now expand to fill available width

### Filters Don't Work
- ⚠️ **KNOWN ISSUE** - Not connected to EA yet
- They toggle state in UI but EA doesn't receive/apply them

### Right Panels Show Old Data
- Check if MT5 EA is running
- Check if JSON files are being updated
- EA must write: `latest_price.json`, `zones.json`, etc.

---

## 📝 SUMMARY

**FIXED:**
- ✅ Opportunity scanner fills width
- ✅ Timeframe filter added
- ✅ Signals persist 5 minutes
- ✅ No duplicate symbols
- ✅ Symbol + timeframe in ALL commentary
- ✅ Font sizes increased everywhere

**STILL NEEDS WORK:**
- ⚠️ Left-hand filters need EA integration
- ⚠️ Risk Management section needs expansion
- ⚠️ Chart needs support/resistance levels
- ⚠️ Documentation for right-hand panels (added above)

**TELL ME:**
1. What levels to add to chart
2. What Risk Management settings you want
3. Whether to connect filters to EA or just visual

---

**Your feedback is critical - tell me what's most important and I'll prioritize accordingly.**
