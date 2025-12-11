"""
AppleTrader Pro - Trade Decision Engine
Coordinates all analysis widgets to generate actionable trade signals

This is the BRAIN of the trading system - combines:
- Opportunity scanner (pattern quality)
- Session momentum (pair selection)
- Correlation analysis (divergence confirmation)
- News calendar (event filtering)
- Risk management (position sizing + limits)
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DecisionAction(Enum):
    """Trade decision actions"""
    ENTER = "ENTER"  # High confidence - take the trade
    WAIT = "WAIT"    # Moderate confidence - wait for better setup
    SKIP = "SKIP"    # Low confidence or blocked - skip this trade


@dataclass
class TradeDecision:
    """
    Complete trade decision with all context
    """
    action: DecisionAction
    symbol: str
    direction: str  # 'BUY' or 'SELL'

    # Trade parameters (only if action==ENTER)
    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    lot_size: float = 0.0
    risk_reward: float = 0.0

    # Decision context
    confidence: float = 0.0  # 0.0-1.0
    quality_score: int = 0  # 0-100
    reasons: List[str] = None  # Why this decision was made
    blockers: List[str] = None  # Why trade was blocked (if SKIP/WAIT)

    # Analysis breakdown
    pattern_score: int = 0
    momentum_rank: int = 0
    has_divergence: bool = False
    news_clear: bool = True
    risk_ok: bool = True

    timestamp: datetime = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.blockers is None:
            self.blockers = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DecisionEngine:
    """
    Central trading decision engine

    Evaluates opportunities systematically:
    1. Check momentum (must be in top 5 pairs)
    2. Validate pattern quality (must be >70 score)
    3. Confirm divergence (optional but adds confidence)
    4. Check news calendar (blocks if high-impact event coming)
    5. Validate risk limits (symbol, daily, weekly)
    6. Calculate confidence score
    7. Generate final decision: ENTER / WAIT / SKIP
    """

    def __init__(self):
        # Thresholds
        self.min_pattern_score = 70  # Minimum quality score to consider
        self.max_momentum_rank = 5   # Only trade top 5 momentum pairs
        self.min_confidence_to_enter = 0.75  # Need 75% confidence to enter
        self.news_lookahead_minutes = 5  # Block trades if news in 5min

        # Weights for confidence calculation (WITH ML)
        self.weights = {
            'pattern_score': 0.30,  # 30% - Pattern quality
            'momentum': 0.20,        # 20% - Momentum ranking
            'trend_alignment': 0.10, # 10% - Multi-timeframe alignment
            'divergence': 0.10,      # 10% - Correlation divergence
            'volume': 0.10,          # 10% - Volume confirmation
            'ml_prediction': 0.20,   # 20% - ML model prediction (NEW!)
        }

        # ML settings
        self.use_ml = False  # Enable when model is loaded
        self.ml_min_confidence = 0.65  # Minimum ML confidence

    def evaluate_opportunity(
        self,
        opportunity: Dict,
        momentum_rank: int = 999,
        has_divergence: bool = False,
        upcoming_news_minutes: int = 999,
        risk_manager = None,
        mt5_connector = None,
        ml_prediction = None  # NEW: ML prediction result
    ) -> TradeDecision:
        """
        Evaluate a single trading opportunity

        Args:
            opportunity: Opportunity dict from scanner
            momentum_rank: Rank of this symbol (1=highest momentum)
            has_divergence: Does this pair have correlation divergence?
            upcoming_news_minutes: Minutes until next high-impact news
            risk_manager: Risk manager instance for validation
            mt5_connector: MT5 connector (optional, for additional data)

        Returns:
            TradeDecision with action and full context
        """

        symbol = opportunity['symbol']
        direction = opportunity['direction']
        pattern_score = opportunity['quality_score']

        # Initialize decision
        decision = TradeDecision(
            action=DecisionAction.SKIP,
            symbol=symbol,
            direction=direction,
            quality_score=pattern_score,
            momentum_rank=momentum_rank,
            has_divergence=has_divergence
        )

        # ========================================
        # STEP 1: Check Pattern Quality (CRITICAL)
        # ========================================
        if pattern_score < self.min_pattern_score:
            decision.blockers.append(f"Pattern score too low ({pattern_score} < {self.min_pattern_score})")
            decision.confidence = pattern_score / 100.0
            return decision

        decision.reasons.append(f"Pattern: {pattern_score}/100")

        # ========================================
        # STEP 2: Check Momentum Rank (IMPORTANT)
        # ========================================
        if momentum_rank > self.max_momentum_rank:
            decision.blockers.append(f"Low momentum (rank #{momentum_rank} > {self.max_momentum_rank})")
            decision.action = DecisionAction.WAIT  # Not SKIP, might improve later
            decision.confidence = 0.50
            return decision

        decision.reasons.append(f"Momentum: Rank #{momentum_rank}")

        # ========================================
        # STEP 3: Check News Calendar (BLOCKER)
        # ========================================
        if upcoming_news_minutes < self.news_lookahead_minutes:
            decision.blockers.append(f"High-impact news in {upcoming_news_minutes}min")
            decision.action = DecisionAction.WAIT
            decision.news_clear = False
            decision.confidence = 0.40
            return decision

        decision.news_clear = True
        decision.reasons.append("News clear")

        # ========================================
        # STEP 4: Validate Risk Limits (CRITICAL)
        # ========================================
        if risk_manager:
            # Calculate position size
            entry = opportunity['entry']
            sl = opportunity['stop_loss']

            position_calc = risk_manager.calculate_position_size(symbol, entry, sl)
            lot_size = position_calc['lot_size']

            # Check symbol limit
            can_trade, limit_msg = risk_manager.check_symbol_limit(symbol, lot_size)
            if not can_trade:
                decision.blockers.append(f"Symbol limit: {limit_msg}")
                decision.action = DecisionAction.SKIP
                decision.risk_ok = False
                decision.confidence = 0.0
                return decision

            # Check daily limit
            daily_ok, daily_msg = risk_manager.check_daily_limit()
            if not daily_ok:
                decision.blockers.append(f"Daily limit: {daily_msg}")
                decision.action = DecisionAction.SKIP
                decision.risk_ok = False
                decision.confidence = 0.0
                return decision

            # Check weekly limit
            weekly_ok, weekly_msg = risk_manager.check_weekly_limit()
            if not weekly_ok:
                decision.blockers.append(f"Weekly limit: {weekly_msg}")
                decision.action = DecisionAction.SKIP
                decision.risk_ok = False
                decision.confidence = 0.0
                return decision

            decision.lot_size = lot_size
            decision.risk_ok = True
            decision.reasons.append(f"Risk: {lot_size:.2f} lots")

        # ========================================
        # STEP 5: Calculate Confidence Score
        # ========================================
        confidence_components = {}

        # Pattern score (0-100 → 0.0-1.0)
        confidence_components['pattern_score'] = pattern_score / 100.0

        # Momentum score (rank 1-5 → 1.0-0.6)
        if momentum_rank <= 5:
            momentum_score = 1.0 - ((momentum_rank - 1) * 0.1)
        else:
            momentum_score = 0.0
        confidence_components['momentum'] = momentum_score

        # Trend alignment (from pattern reasons)
        reasons_text = ' '.join(opportunity.get('confluence_reasons', []))
        if 'Strong Uptrend' in reasons_text or 'Strong Downtrend' in reasons_text:
            confidence_components['trend_alignment'] = 1.0
        elif 'Uptrend' in reasons_text or 'Downtrend' in reasons_text:
            confidence_components['trend_alignment'] = 0.7
        else:
            confidence_components['trend_alignment'] = 0.3

        # Divergence bonus
        confidence_components['divergence'] = 1.0 if has_divergence else 0.3
        if has_divergence:
            decision.reasons.append("Divergence confirmed")

        # Volume (from pattern reasons)
        if 'High Volume' in reasons_text:
            confidence_components['volume'] = 1.0
        elif 'Above Avg Volume' in reasons_text:
            confidence_components['volume'] = 0.7
        else:
            confidence_components['volume'] = 0.4

        # ========================================
        # ML PREDICTION (NEW!)
        # ========================================
        if ml_prediction and self.use_ml:
            ml_score = ml_prediction.probability_win

            # Only trust ML if confidence is high enough
            if ml_prediction.confidence >= self.ml_min_confidence:
                confidence_components['ml_prediction'] = ml_score
                decision.reasons.append(f"ML: {ml_prediction.signal} ({ml_prediction.probability_win*100:.0f}%)")
            else:
                # Low ML confidence - use neutral score
                confidence_components['ml_prediction'] = 0.5
        else:
            # No ML - use neutral score
            confidence_components['ml_prediction'] = 0.5

        # Weighted confidence score
        confidence = sum(
            confidence_components[key] * self.weights[key]
            for key in confidence_components
        )

        decision.confidence = confidence
        decision.pattern_score = pattern_score

        # ========================================
        # STEP 6: Final Decision
        # ========================================
        if confidence >= self.min_confidence_to_enter:
            # HIGH CONFIDENCE - ENTER TRADE
            decision.action = DecisionAction.ENTER
            decision.entry = opportunity['entry']
            decision.stop_loss = opportunity['stop_loss']
            decision.take_profit = opportunity['take_profit']
            decision.risk_reward = opportunity['risk_reward']

            decision.reasons.append(f"Confidence: {confidence*100:.0f}%")

        elif confidence >= 0.60:
            # MODERATE CONFIDENCE - WAIT FOR BETTER SETUP
            decision.action = DecisionAction.WAIT
            decision.blockers.append(f"Confidence below threshold ({confidence*100:.0f}% < {self.min_confidence_to_enter*100:.0f}%)")

        else:
            # LOW CONFIDENCE - SKIP
            decision.action = DecisionAction.SKIP
            decision.blockers.append(f"Low confidence ({confidence*100:.0f}%)")

        return decision

    def scan_all_opportunities(
        self,
        opportunities: List[Dict],
        momentum_scanner=None,
        correlation_analyzer=None,
        news_predictor=None,
        risk_manager=None,
        mt5_connector=None
    ) -> List[TradeDecision]:
        """
        Evaluate all opportunities and return ranked decisions

        Args:
            opportunities: List of opportunity dicts from scanner
            momentum_scanner: Momentum scanner instance
            correlation_analyzer: Correlation analyzer instance
            news_predictor: News impact predictor instance
            risk_manager: Risk manager instance
            mt5_connector: MT5 connector instance

        Returns:
            List of TradeDecision objects, sorted by confidence (highest first)
        """

        decisions = []

        # Get momentum leaderboard (if available)
        momentum_ranks = {}
        if momentum_scanner and hasattr(momentum_scanner, 'leaderboard'):
            for idx, momentum_data in enumerate(momentum_scanner.leaderboard, start=1):
                symbol = momentum_data.get('symbol')
                if symbol:
                    momentum_ranks[symbol] = idx

        # Check upcoming news (if available)
        upcoming_news_minutes = 999
        if news_predictor:
            try:
                next_event = news_predictor.get_next_event(minutes=10)
                if next_event:
                    # Calculate minutes until event
                    # For now, assume no immediate news
                    upcoming_news_minutes = 10
            except:
                pass

        # Evaluate each opportunity
        for opp in opportunities:
            symbol = opp['symbol']

            # Get momentum rank
            momentum_rank = momentum_ranks.get(symbol, 999)

            # Check divergence (if available)
            has_divergence = False
            if correlation_analyzer:
                try:
                    divergence = correlation_analyzer.check_divergence(symbol)
                    has_divergence = divergence is not None
                except:
                    pass

            # Evaluate opportunity
            decision = self.evaluate_opportunity(
                opportunity=opp,
                momentum_rank=momentum_rank,
                has_divergence=has_divergence,
                upcoming_news_minutes=upcoming_news_minutes,
                risk_manager=risk_manager,
                mt5_connector=mt5_connector
            )

            decisions.append(decision)

        # Sort by confidence (highest first)
        decisions.sort(key=lambda d: d.confidence, reverse=True)

        return decisions

    def get_best_decision(
        self,
        opportunities: List[Dict],
        **kwargs
    ) -> Optional[TradeDecision]:
        """
        Get the single best trading decision right now

        Returns:
            TradeDecision with action=ENTER if confident, else None
        """
        decisions = self.scan_all_opportunities(opportunities, **kwargs)

        # Return first ENTER decision
        for decision in decisions:
            if decision.action == DecisionAction.ENTER:
                return decision

        return None


# Global instance
decision_engine = DecisionEngine()
