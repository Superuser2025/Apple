# AppleTrader Pro - Project Status & Technical Specification

**Last Updated**: 2025-12-12
**Branch**: `claude/fix-session-loading-01CGoxWXcoW46gPedLV3H6CX`
**Previous Working Branch**: `QG9` (contains last known working opportunity scanner)

---

## 🎯 PROJECT OVERVIEW

AppleTrader Pro is a PyQt6-based trading dashboard that connects to MetaTrader 5 (MT5) via JSON data export. The system has two main components:

1. **MT5 Expert Advisor (EA)**: MQL5 code that exports market data to JSON files
2. **Python GUI**: PyQt6 dashboard that reads JSON and displays trading opportunities

---

## ✅ COMPLETED PHASES

### **INCREMENT 1: Core Trading Dashboard** ✅
**Status**: FULLY WORKING on QG9 branch

**What Works:**
- ✅ Multi-symbol opportunity scanner showing cards at top of UI
- ✅ Scanner displays opportunities from MULTIPLE symbols (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF, EURGBP, EURJPY, GBPJPY)
- ✅ Each opportunity card shows:
  - Symbol name
  - **Timeframe prominently displayed** (M5, M15, M30, H1, H4, D1)
  - Direction (LONG/SHORT)
  - Entry price
  - Stop Loss
  - Take Profit
  - Risk/Reward ratio
  - Confluence reasons
- ✅ OpportunityCard widget properly displays all information
- ✅ MT5 data import via JSON working
- ✅ Real-time updates from MT5 EA

**Critical Requirement**: Every opportunity MUST show what timeframe the signal applies to. This is non-negotiable.

**Key Files (Working State - QG9 branch):**
- `python/gui/enhanced_main_window.py` - Main window (but user runs via `main_enhanced.py`)
- `python/main_enhanced.py` - Entry point that user actually runs
- `python/widgets/opportunity_scanner_widget.py` - Scanner widget that displays opportunity cards
- `python/core/mt5_connector.py` - Reads JSON data from MT5
- `AppleTrader.mq5` - MT5 Expert Advisor that exports data

---

### **INCREMENT 2: Trade Decision Engine** ⚠️ IN PROGRESS
**Status**: PARTIALLY IMPLEMENTED, NEEDS TESTING

**Goal**: Add AI-powered trade decision engine that evaluates all opportunities and shows the BEST one in a separate "Decisions" tab on the right panel.

**What This Is:**
- Scanner cards at top = Browse multiple opportunities from multiple symbols
- Decision tab on right = AI's single best trade recommendation (ENTER/WAIT/SKIP)

**What Was Added:**

1. **Decision Tab in Right Panel** ✅
   - File: `python/gui/enhanced_main_window.py` (lines 213-232)
   - Adds "🎯 Decisions" tab to right panel
   - Contains TradeDecisionWidget

2. **Trade Decision Widget** ✅
   - File: `python/widgets/trade_decision_widget.py`
   - Displays AI's decision: ENTER (green), WAIT (yellow), or SKIP (red)
   - Shows confidence score, reasoning, risk/reward analysis

3. **Decision Engine** ✅
   - File: `python/core/decision_engine.py`
   - Evaluates opportunities using weighted scoring:
     - Pattern Recognition: 30%
     - Momentum: 20%
     - ML Prediction: 20%
     - Trend: 10%
     - Divergence: 10%
     - Volume: 10%
   - Returns ENTER/WAIT/SKIP with confidence score

4. **Signal Connection** ✅
   - File: `python/gui/enhanced_main_window.py` (line 85)
   - Connects scanner's `opportunities_updated` signal to decision engine
   - Handler method: `on_opportunities_updated()` (lines 710-734)

5. **MT5 EA Scanner Data Export** ✅ (CODE COMPLETE, UNTESTED)
   - File: `AppleTrader.mq5` (lines 697-738)
   - Exports candle data for scanner:
     - **10 pairs**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF, EURGBP, EURJPY, GBPJPY
     - **6 timeframes**: M5, M15, M30, H1, H4, D1
     - **200 candles** per pair/timeframe
     - **Total**: 60 data sources
   - JSON keys format: `candles_EURUSD_M5`, `candles_GBPUSD_H1`, etc.

6. **JSONExporter Enhancement** ✅
   - File: `AppleTrader/JSONExporter.mqh`
   - Added `BeginArrayObject()` method (lines 352-365)
   - Allows creating anonymous objects inside JSON arrays
   - Needed for exporting candle data as array of objects

**What's NOT Working Yet:**
- ❌ Scanner showing 0 opportunities (likely due to missing/incomplete MT5 data)
- ❌ EA scanner export code NOT TESTED (user needs to recompile)
- ❌ Decision tab may not be receiving opportunities if scanner is empty

**Why Scanner Broke:**
During INCREMENT 2 development, changes were made to `opportunity_scanner_widget.py` that broke the scanner. The real issue is likely:
1. Scanner filters too strict (quality score thresholds)
2. MT5 EA wasn't exporting scanner data (now fixed in code, but not compiled/tested)

---

## 📁 CRITICAL FILE STRUCTURE

### **Python Application**

```
python/
├── main_enhanced.py                    # ⭐ ENTRY POINT - User runs this
├── gui/
│   └── enhanced_main_window.py         # ⭐ Main window with Decision tab
├── widgets/
│   ├── opportunity_scanner_widget.py   # ⭐ Scanner cards (top of UI)
│   └── trade_decision_widget.py        # ⭐ Decision display (right panel)
├── core/
│   ├── decision_engine.py              # ⭐ AI decision logic
│   ├── mt5_connector.py                # ⭐ Reads JSON from MT5
│   ├── pattern_recognition.py          # Pattern analysis
│   ├── momentum_scanner.py             # Momentum calculations
│   └── risk_manager.py                 # Risk management
└── models/
    └── ml_predictor.py                 # ML predictions
```

### **MT5 Expert Advisor**

```
AppleTrader.mq5                         # ⭐ Main EA file
AppleTrader/
└── JSONExporter.mqh                    # ⭐ JSON export utility
```

**Export Path**: `%APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\Common\Files\AppleTrader\market_data.json`

---

## 🔧 TECHNICAL DETAILS

### **How MT5 → Python Data Flow Works**

1. **MT5 EA exports data** (every tick or timer interval):
   ```mql5
   OnTimer() → ExportMarketData() → Writes JSON to disk
   ```

2. **Python reads JSON** (polling or file watching):
   ```python
   MT5Connector.load_data() → Reads JSON → Parses into Python dicts/DataFrames
   ```

3. **Scanner analyzes data**:
   ```python
   OpportunityScannerWidget → Gets candles → Finds patterns → Creates opportunity cards
   ```

4. **Decision engine evaluates**:
   ```python
   opportunities_updated signal → DecisionEngine.scan_all_opportunities() → Best trade shown in Decision tab
   ```

### **OpportunityCard Data Format**

Each opportunity is a dict with these keys:

```python
{
    'symbol': 'EURUSD',
    'timeframe': 'H1',           # ⭐ MUST BE PROMINENTLY DISPLAYED
    'direction': 'LONG',          # or 'SHORT'
    'entry': 1.0850,
    'stop_loss': 1.0800,
    'take_profit': 1.0950,
    'risk_reward': 2.0,           # Also accepts 'rr' key (backward compat)
    'confidence': 85.5,           # 0-100
    'confluence_reasons': [       # Also accepts 'reasons' key (backward compat)
        'Strong support level',
        'Bullish engulfing pattern',
        'RSI oversold'
    ],
    'quality_score': 72.0         # Internal scoring
}
```

### **JSON Export Format (MT5)**

```json
{
  "timestamp": 1702345678,
  "symbol": "EURUSD",
  "timeframe": "H1",
  "candles_EURUSD_M5": [
    {
      "time": 1702340000,
      "open": 1.0850,
      "high": 1.0865,
      "low": 1.0845,
      "close": 1.0860,
      "volume": 1500
    },
    ...
  ],
  "candles_EURUSD_M15": [ ... ],
  "candles_GBPUSD_M5": [ ... ],
  ...
}
```

### **Scanner Data Requirements**

For scanner to work, MT5 must export:
- **Pairs**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF, EURGBP, EURJPY, GBPJPY
- **Timeframes**: M5, M15, M30, H1, H4, D1
- **History**: At least 200 candles per pair/timeframe
- **JSON keys**: Format `candles_{SYMBOL}_{TIMEFRAME}` (e.g., `candles_EURUSD_H1`)

### **MT5 Connector API**

```python
# MT5Connector key methods (python/core/mt5_connector.py)

mt5 = MT5Connector()
mt5.load_data()  # Reads JSON from disk

# Get candles for specific symbol/timeframe
df = mt5.get_candles('EURUSD', 'H1', count=200)
# Returns pandas DataFrame with columns: time, open, high, low, close, volume

# Get current price
price = mt5.get_current_price('EURUSD')
```

---

## 🚨 KNOWN ISSUES

### **Issue 1: Scanner Showing 0 Opportunities**
**Status**: Root cause identified, fix implemented but UNTESTED

**Symptoms:**
- Scanner widget displays "No opportunities found"
- Console shows "✗ EURUSD M5 returned None" for all pairs/timeframes

**Root Causes:**
1. MT5 EA wasn't exporting scanner data (only exported current chart symbol)
2. Scanner filters may be too strict (quality_score threshold)

**Fix Applied:**
- Added scanner data export to `AppleTrader.mq5` (lines 697-738)
- Exports all 10 pairs × 6 timeframes = 60 data sources
- **STATUS**: Code written but NOT compiled/tested by user

**Next Steps:**
1. User must recompile `AppleTrader.mq5` in MetaEditor
2. User must restart EA on MT5 chart
3. Test if scanner now shows opportunities

### **Issue 2: Decision Tab Not Visible (RESOLVED)**
**Status**: FIXED

This was resolved by copying `enhanced_main_window.py` to the 6CX branch and ensuring the Decision tab code is present.

### **Issue 3: Git Branch Confusion (RESOLVED)**
**Status**: FIXED

- QG9 branch: Contains working scanner but can't push (403 errors)
- 6CX branch: Can push but was missing latest code
- Solution: All work now on `claude/fix-session-loading-01CGoxWXcoW46gPedLV3H6CX`

### **Issue 4: KeyError 'risk_reward' (RESOLVED)**
**Status**: FIXED

OpportunityCard now accepts both 'risk_reward' and 'rr' keys for backward compatibility (lines 107-118).

---

## 📋 WHAT NEEDS TO HAPPEN NEXT

### **IMMEDIATE PRIORITY: Get Scanner Working**

**Step 1**: Compile and Test MT5 EA
```
1. Pull latest code from claude/fix-session-loading-01CGoxWXcoW46gPedLV3H6CX
2. Open MetaEditor (F4 in MT5)
3. Open AppleTrader.mq5
4. Compile (F7)
5. Should show 0 errors, 0 warnings
6. Remove old EA from chart
7. Drag newly compiled EA onto chart
8. Enable "Allow Algo Trading"
9. Wait for data export (check MT5 Experts log)
```

**Step 2**: Verify JSON Export
```
1. Navigate to: %APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\Common\Files\AppleTrader\
2. Open market_data.json
3. Verify keys exist: candles_EURUSD_M5, candles_EURUSD_M15, etc.
4. Verify each array has ~200 candle objects
5. Check file size (should be several MB with all data)
```

**Step 3**: Run Python App and Test Scanner
```
1. cd /home/user/Apple/python
2. python main_enhanced.py
3. Watch console for debug output
4. Check if opportunity cards appear at top
5. Verify each card shows SYMBOL • TIMEFRAME in header
6. Verify Decision tab on right panel
```

**Step 4**: If Scanner Still Shows 0 Opportunities
```python
# Edit python/widgets/opportunity_scanner_widget.py
# Find the quality score threshold (search for "quality_score")
# Lower it from 50 to 20 or 10 to allow more opportunities through

# Example (around line 280-290):
if quality_score >= 20:  # Lowered from 50
    opportunities.append(opportunity)
```

### **SECONDARY PRIORITY: Verify Decision Engine**

Once scanner is working and showing opportunities:

1. Verify Decision tab updates automatically when opportunities appear
2. Check console for: `[Decision Engine] Evaluating X opportunities`
3. Verify Decision tab shows ENTER/WAIT/SKIP with confidence score
4. Test with multiple opportunities to ensure best one is selected

---

## 🔍 DEBUGGING CHECKLIST

### **Scanner Not Working?**

1. **Check MT5 EA is running**
   - Look for "AppleTrader" in MT5 Experts tab
   - Should see green "Expert" indicator on chart

2. **Check JSON export**
   - MT5 Experts log should show: `[EXPORT] ✓ Market data successfully exported`
   - JSON file should exist and be recently modified
   - JSON file should contain `candles_SYMBOL_TIMEFRAME` keys

3. **Check Python console output**
   - Should see: `Loading data from market_data.json`
   - Should NOT see: `✗ EURUSD M5 returned None` for all pairs

4. **Check MT5Connector**
   ```python
   # Add debug to mt5_connector.py get_candles() method
   print(f"[DEBUG] Looking for key: {candles_key}")
   print(f"[DEBUG] Available keys: {list(self.last_data.keys())}")
   ```

5. **Check Scanner Thresholds**
   ```python
   # In opportunity_scanner_widget.py
   # Find: if quality_score >= 50:
   # Add: print(f"[DEBUG] Quality score: {quality_score} (threshold: 50)")
   ```

### **Decision Tab Not Updating?**

1. **Check signal connection**
   ```python
   # In enhanced_main_window.py, verify line 85:
   self.scanner_widget.opportunities_updated.connect(self.on_opportunities_updated)
   ```

2. **Check signal emission**
   ```python
   # In opportunity_scanner_widget.py, verify emission:
   self.opportunities_updated.emit(self.opportunities)
   ```

3. **Add debug to handler**
   ```python
   def on_opportunities_updated(self, opportunities: list):
       print(f"[DEBUG] Received {len(opportunities)} opportunities in handler")
       # ... rest of method
   ```

---

## 💡 ARCHITECTURAL NOTES

### **Design Principles**

1. **Separation of Concerns**:
   - Scanner = Browse ALL opportunities from ALL symbols/timeframes
   - Decision Tab = AI picks ONE best trade

2. **Data Flow**:
   - MT5 EA → JSON file → Python MT5Connector → Scanner → Decision Engine
   - Scanner emits signal → Decision Engine evaluates → Decision Widget displays

3. **Timeframe Visibility**:
   - EVERY opportunity MUST show timeframe prominently
   - Format: "SYMBOL • TIMEFRAME" in card header (bold, white text)
   - Never hide timeframe or put it in small text at bottom

4. **Backward Compatibility**:
   - OpportunityCard accepts both 'rr' and 'risk_reward'
   - OpportunityCard accepts both 'reasons' and 'confluence_reasons'
   - Allows gradual migration of opportunity-generating code

### **Code Quality Standards**

1. **Always read files before editing** (use Read tool first)
2. **Test incrementally** (don't break working functionality)
3. **Use proper git workflow** (commit often, clear messages)
4. **Add debug output** (helps diagnose issues quickly)
5. **Don't over-engineer** (simple solutions first)

---

## 📝 COMMIT HISTORY (This Session)

```
ae7eee4 - FIX: Add BeginArrayObject() method for anonymous objects in JSON arrays
94fb32a - ADD M5/M15/M30/H1/H4/D1 timeframes: Export data for scanner from M5 and upwards
4523991 - FIX MT5 EA: Export candle data for all 10 pairs × 2 timeframes
97a5d74 - RESTORE working opportunity scanner from QG9 branch
bbb79ad - FALLBACK: Use EURUSD data when other pairs unavailable
```

---

## 🎯 SUCCESS CRITERIA

The system is fully working when:

1. ✅ Scanner shows opportunity cards at top from MULTIPLE symbols
2. ✅ Each card displays SYMBOL • TIMEFRAME prominently in header
3. ✅ Each card shows entry, SL, TP, R:R, confluence reasons
4. ✅ Decision tab on right shows AI's best trade (ENTER/WAIT/SKIP)
5. ✅ Decision tab updates automatically when new opportunities arrive
6. ✅ MT5 EA exports data for all 10 pairs × 6 timeframes
7. ✅ No errors in MT5 Experts log
8. ✅ No errors in Python console
9. ✅ Real-time updates working

---

## 🚀 FUTURE ENHANCEMENTS (Not Started)

These are ideas for later, NOT current priorities:

- Risk management integration
- Position sizing calculator
- Trade journal / history
- Performance analytics
- Multiple EA support
- News calendar integration
- Economic indicator overlay
- Backtesting framework

**DO NOT attempt these until INCREMENT 2 is fully working.**

---

## 📞 KEY TAKEAWAYS FOR NEXT SESSION

1. **Last working state**: QG9 branch had working scanner
2. **Current goal**: Complete INCREMENT 2 (Decision Engine)
3. **Blocker**: Scanner showing 0 opportunities
4. **Fix ready**: MT5 EA code updated, needs recompile/test
5. **Critical rule**: NEVER hide or remove timeframe from opportunity cards
6. **User runs**: `python/main_enhanced.py` (not main.py)
7. **Data path**: MT5 → JSON → MT5Connector → Scanner → Decision Engine
8. **Test incrementally**: Don't break working functionality to add new features

---

## 📚 QUICK REFERENCE

### Run Application
```bash
cd /home/user/Apple/python
python main_enhanced.py
```

### Git Commands
```bash
git status
git pull origin claude/fix-session-loading-01CGoxWXcoW46gPedLV3H6CX
git add <file>
git commit -m "message"
git push -u origin claude/fix-session-loading-01CGoxWXcoW46gPedLV3H6CX
```

### MT5 JSON Path
```
%APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\Common\Files\AppleTrader\market_data.json
```

### Key File Paths
```
/home/user/Apple/AppleTrader.mq5                          # MT5 EA
/home/user/Apple/AppleTrader/JSONExporter.mqh             # JSON utility
/home/user/Apple/python/main_enhanced.py                  # Entry point
/home/user/Apple/python/gui/enhanced_main_window.py       # Main window
/home/user/Apple/python/widgets/opportunity_scanner_widget.py  # Scanner
/home/user/Apple/python/core/decision_engine.py           # Decision logic
/home/user/Apple/python/core/mt5_connector.py             # MT5 data reader
```

---

**END OF DOCUMENT**

*This document should provide complete context for continuing development in a new session.*
