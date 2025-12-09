"""
Filter Manager - Controls which opportunities pass institutional filters
"""

class FilterManager:
    """Manages filter state and applies filters to trading opportunities"""

    def __init__(self):
        # Institutional Filters
        self.volume_filter = True
        self.spread_filter = True
        self.strong_price_model = True
        self.multi_timeframe = True
        self.volatility_filter = True
        self.sentiment_filter = True
        self.correlation_filter = True
        self.volatility_adaptation = True
        self.dynamic_risk = True
        self.pattern_decay = True

        # Smart Money Concepts
        self.liquidity_sweep = True
        self.retail_trap_detection = True
        self.order_block_invalidation = True
        self.market_structure = True

        # Machine Learning
        self.pattern_tracking = True
        self.parameter_adaptation = True
        self.regime_strategy = True

    def set_filter(self, filter_name: str, enabled: bool):
        """Enable/disable a specific filter"""
        # Normalize filter name to attribute name
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")

        if hasattr(self, attr_name):
            setattr(self, attr_name, enabled)
            print(f"[FilterManager] {filter_name} = {enabled}")
            return True
        else:
            print(f"[FilterManager] WARNING: Unknown filter '{filter_name}'")
            return False

    def get_filter(self, filter_name: str) -> bool:
        """Get current state of a filter"""
        attr_name = filter_name.lower().replace(" ", "_").replace("-", "_")
        return getattr(self, attr_name, True)  # Default to True if not found

    def filter_opportunity(self, opportunity: dict) -> bool:
        """
        Apply all enabled filters to an opportunity.
        Returns True if opportunity passes all filters, False otherwise.
        """
        # If all filters disabled, show everything
        if not any([self.volume_filter, self.spread_filter, self.strong_price_model,
                   self.multi_timeframe, self.volatility_filter, self.sentiment_filter,
                   self.correlation_filter, self.volatility_adaptation, self.dynamic_risk,
                   self.pattern_decay, self.liquidity_sweep, self.retail_trap_detection,
                   self.order_block_invalidation, self.market_structure, self.pattern_tracking,
                   self.parameter_adaptation, self.regime_strategy]):
            return True

        # VOLUME FILTER - Check if volume is adequate
        if self.volume_filter:
            volume = opportunity.get('volume', 0)
            if volume < 100:  # Minimum volume threshold
                return False

        # SPREAD FILTER - Check if spread is reasonable
        if self.spread_filter:
            spread = opportunity.get('spread', 0)
            if spread > 20:  # Maximum spread in pips
                return False

        # STRONG PRICE MODEL - Check pattern strength
        if self.strong_price_model:
            strength = opportunity.get('pattern_strength', 0)
            if strength < 5:  # Minimum strength threshold
                return False

        # MULTI-TIMEFRAME - Check MTF confirmation
        if self.multi_timeframe:
            mtf_confirmed = opportunity.get('mtf_confirmed', False)
            if not mtf_confirmed:
                return False

        # VOLATILITY FILTER - Check volatility range
        if self.volatility_filter:
            volatility = opportunity.get('volatility', 0)
            if volatility < 0.3 or volatility > 3.0:  # Acceptable volatility range
                return False

        # SENTIMENT FILTER - Check market sentiment alignment
        if self.sentiment_filter:
            sentiment = opportunity.get('sentiment', 'neutral')
            direction = opportunity.get('direction', 'BUY')
            # Bullish sentiment for BUY, bearish for SELL
            if direction == 'BUY' and sentiment == 'bearish':
                return False
            if direction == 'SELL' and sentiment == 'bullish':
                return False

        # CORRELATION FILTER - Check correlation with other pairs
        if self.correlation_filter:
            correlation_score = opportunity.get('correlation_score', 0.5)
            if correlation_score < 0.3:  # Minimum correlation threshold
                return False

        # LIQUIDITY SWEEP - Check for liquidity events
        if self.liquidity_sweep:
            has_liquidity_sweep = opportunity.get('liquidity_sweep', False)
            # Only show opportunities WITH liquidity sweeps when this is enabled
            if self.liquidity_sweep and not has_liquidity_sweep:
                return False

        # RETAIL TRAP DETECTION - Filter out retail traps
        if self.retail_trap_detection:
            is_retail_trap = opportunity.get('is_retail_trap', False)
            if is_retail_trap:  # Reject retail traps
                return False

        # ORDER BLOCK INVALIDATION - Check order block validity
        if self.order_block_invalidation:
            ob_valid = opportunity.get('order_block_valid', True)
            if not ob_valid:
                return False

        # MARKET STRUCTURE - Check market structure alignment
        if self.market_structure:
            structure_aligned = opportunity.get('structure_aligned', False)
            if not structure_aligned:
                return False

        # PATTERN TRACKING - Check pattern reliability
        if self.pattern_tracking:
            pattern_reliability = opportunity.get('pattern_reliability', 0)
            if pattern_reliability < 60:  # Minimum 60% reliability
                return False

        # PARAMETER ADAPTATION - Check if parameters are optimized
        if self.parameter_adaptation:
            parameters_optimized = opportunity.get('parameters_optimized', True)
            if not parameters_optimized:
                return False

        # REGIME STRATEGY - Check if strategy matches current regime
        if self.regime_strategy:
            regime_match = opportunity.get('regime_match', True)
            if not regime_match:
                return False

        # Passed all enabled filters
        return True

    def get_active_filters(self) -> list:
        """Get list of currently active filter names"""
        active = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                if isinstance(getattr(self, attr_name), bool) and getattr(self, attr_name):
                    # Convert attr name back to display name
                    display_name = attr_name.replace('_', ' ').title()
                    active.append(display_name)
        return active


# Global singleton instance
filter_manager = FilterManager()
