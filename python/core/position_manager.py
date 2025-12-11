"""
AppleTrader Pro - Position Manager
Manages open positions with trailing stops and partial profit taking

Features:
- ATR-based trailing stops
- Partial profit taking at R multiples (1R, 2R, 3R)
- Break-even stop after 1R reached
- Position size scaling (close partials)
"""

from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class PositionStatus(Enum):
    """Position statuses"""
    OPEN = "OPEN"
    PARTIAL_CLOSED = "PARTIAL_CLOSED"
    CLOSED = "CLOSED"


@dataclass
class Position:
    """Active trading position"""
    ticket: int
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    initial_lot_size: float
    current_lot_size: float
    unrealized_pnl: float

    # Position management
    entry_time: datetime
    status: PositionStatus = PositionStatus.OPEN
    highest_price: float = 0.0  # Track highest price for trailing (BUY)
    lowest_price: float = 999999.0  # Track lowest price for trailing (SELL)

    # R-multiples achieved
    r_achieved: float = 0.0
    partials_taken: List[float] = None  # List of R levels where partials were taken

    # Management flags
    breakeven_moved: bool = False
    trailing_active: bool = False

    def __post_init__(self):
        if self.partials_taken is None:
            self.partials_taken = []

        if self.highest_price == 0.0:
            self.highest_price = self.current_price

        if self.lowest_price == 999999.0:
            self.lowest_price = self.current_price


class PositionManager:
    """
    Manages open positions with advanced techniques

    Features:
    1. Break-even stop: Move SL to BE after 1R profit
    2. Trailing stop: Trail SL using ATR multiples
    3. Partial profits: Take 50% at 2R, 25% at 3R
    4. Position monitoring: Track all positions
    """

    def __init__(self):
        # Position management settings
        self.enable_breakeven = True
        self.breakeven_trigger_r = 1.0  # Move to BE after 1R
        self.breakeven_buffer_pips = 5  # Keep 5 pip buffer above BE

        self.enable_trailing = True
        self.trailing_trigger_r = 1.5  # Start trailing after 1.5R
        self.trailing_atr_multiple = 1.5  # Trail 1.5 ATR behind price

        self.enable_partials = True
        self.partial_1r_percent = 0  # Don't take partial at 1R
        self.partial_2r_percent = 50  # Take 50% at 2R
        self.partial_3r_percent = 25  # Take 25% of remaining at 3R

        # Active positions
        self.positions: Dict[int, Position] = {}  # ticket_id -> Position

        # Statistics
        self.total_partials_taken = 0
        self.total_breakevens_set = 0
        self.total_trails = 0

    def add_position(self, position_data: Dict) -> Position:
        """
        Add new position to manager

        Args:
            position_data: Dict with position info from MT5

        Returns:
            Position object
        """

        ticket = position_data.get('ticket', 0)

        position = Position(
            ticket=ticket,
            symbol=position_data['symbol'],
            direction=position_data['type'],
            entry_price=position_data['price_open'],
            current_price=position_data['price_current'],
            stop_loss=position_data['sl'],
            take_profit=position_data['tp'],
            initial_lot_size=position_data['volume'],
            current_lot_size=position_data['volume'],
            unrealized_pnl=position_data['profit'],
            entry_time=datetime.fromtimestamp(position_data['time'])
        )

        self.positions[ticket] = position

        print(f"[Position Manager] Added position: {ticket} {position.direction} {position.symbol}")

        return position

    def update_position(self, position_data: Dict):
        """Update existing position with new prices"""

        ticket = position_data.get('ticket', 0)

        if ticket not in self.positions:
            # Position not tracked yet - add it
            self.add_position(position_data)
            return

        position = self.positions[ticket]

        # Update prices
        position.current_price = position_data['price_current']
        position.unrealized_pnl = position_data['profit']
        position.current_lot_size = position_data['volume']

        # Update highest/lowest for trailing
        if position.direction == 'BUY':
            position.highest_price = max(position.highest_price, position.current_price)
        else:  # SELL
            position.lowest_price = min(position.lowest_price, position.current_price)

        # Calculate current R achieved
        position.r_achieved = self._calculate_r_achieved(position)

    def manage_position(self, position: Position, atr: float) -> List[Dict]:
        """
        Apply position management rules

        Args:
            position: Position to manage
            atr: Current ATR value for symbol

        Returns:
            List of commands to send to MT5 (modify SL, partial close, etc.)
        """

        commands = []

        # ========================================
        # 1. BREAK-EVEN STOP
        # ========================================
        if (self.enable_breakeven and
            not position.breakeven_moved and
            position.r_achieved >= self.breakeven_trigger_r):

            # Move SL to break-even + buffer
            pip_value = 0.0001  # For most pairs
            buffer = self.breakeven_buffer_pips * pip_value

            if position.direction == 'BUY':
                new_sl = position.entry_price + buffer
            else:  # SELL
                new_sl = position.entry_price - buffer

            commands.append({
                'action': 'MODIFY_SL',
                'ticket': position.ticket,
                'new_sl': new_sl,
                'reason': f'Break-even stop ({position.r_achieved:.1f}R achieved)'
            })

            position.breakeven_moved = True
            position.stop_loss = new_sl
            self.total_breakevens_set += 1

            print(f"[Position Manager] Break-even set: {position.ticket} at {new_sl:.5f}")

        # ========================================
        # 2. TRAILING STOP
        # ========================================
        if (self.enable_trailing and
            position.breakeven_moved and
            position.r_achieved >= self.trailing_trigger_r):

            # Calculate trailing stop based on ATR
            trailing_distance = atr * self.trailing_atr_multiple

            if position.direction == 'BUY':
                # Trail below highest price
                new_sl = position.highest_price - trailing_distance

                # Only move SL up, never down
                if new_sl > position.stop_loss:
                    commands.append({
                        'action': 'MODIFY_SL',
                        'ticket': position.ticket,
                        'new_sl': new_sl,
                        'reason': f'Trailing stop ({position.r_achieved:.1f}R, {trailing_distance*10000:.0f} pip trail)'
                    })

                    position.stop_loss = new_sl
                    position.trailing_active = True
                    self.total_trails += 1

            else:  # SELL
                # Trail above lowest price
                new_sl = position.lowest_price + trailing_distance

                # Only move SL down, never up
                if new_sl < position.stop_loss:
                    commands.append({
                        'action': 'MODIFY_SL',
                        'ticket': position.ticket,
                        'new_sl': new_sl,
                        'reason': f'Trailing stop ({position.r_achieved:.1f}R, {trailing_distance*10000:.0f} pip trail)'
                    })

                    position.stop_loss = new_sl
                    position.trailing_active = True
                    self.total_trails += 1

        # ========================================
        # 3. PARTIAL PROFIT TAKING
        # ========================================
        if self.enable_partials:

            # Check 2R partial
            if (position.r_achieved >= 2.0 and
                2.0 not in position.partials_taken and
                self.partial_2r_percent > 0):

                close_lots = position.current_lot_size * (self.partial_2r_percent / 100)
                close_lots = round(close_lots, 2)

                if close_lots >= 0.01:  # Minimum lot size
                    commands.append({
                        'action': 'PARTIAL_CLOSE',
                        'ticket': position.ticket,
                        'close_lots': close_lots,
                        'reason': f'Partial profit at 2R ({self.partial_2r_percent}%)'
                    })

                    position.partials_taken.append(2.0)
                    position.status = PositionStatus.PARTIAL_CLOSED
                    position.current_lot_size -= close_lots
                    self.total_partials_taken += 1

                    print(f"[Position Manager] Partial close: {position.ticket} - {close_lots} lots at 2R")

            # Check 3R partial
            if (position.r_achieved >= 3.0 and
                3.0 not in position.partials_taken and
                self.partial_3r_percent > 0):

                close_lots = position.current_lot_size * (self.partial_3r_percent / 100)
                close_lots = round(close_lots, 2)

                if close_lots >= 0.01:
                    commands.append({
                        'action': 'PARTIAL_CLOSE',
                        'ticket': position.ticket,
                        'close_lots': close_lots,
                        'reason': f'Partial profit at 3R ({self.partial_3r_percent}%)'
                    })

                    position.partials_taken.append(3.0)
                    position.current_lot_size -= close_lots
                    self.total_partials_taken += 1

                    print(f"[Position Manager] Partial close: {position.ticket} - {close_lots} lots at 3R")

        return commands

    def _calculate_r_achieved(self, position: Position) -> float:
        """Calculate how many R multiples have been achieved"""

        risk_distance = abs(position.entry_price - position.stop_loss)

        if risk_distance == 0:
            return 0.0

        if position.direction == 'BUY':
            profit_distance = position.current_price - position.entry_price
        else:  # SELL
            profit_distance = position.entry_price - position.current_price

        r_multiple = profit_distance / risk_distance

        return r_multiple

    def remove_position(self, ticket: int):
        """Remove closed position from manager"""
        if ticket in self.positions:
            del self.positions[ticket]
            print(f"[Position Manager] Removed closed position: {ticket}")

    def get_position(self, ticket: int) -> Optional[Position]:
        """Get position by ticket ID"""
        return self.positions.get(ticket)

    def get_all_positions(self) -> List[Position]:
        """Get all active positions"""
        return list(self.positions.values())

    def get_stats(self) -> Dict:
        """Get position management statistics"""
        return {
            'active_positions': len(self.positions),
            'total_breakevens_set': self.total_breakevens_set,
            'total_trails': self.total_trails,
            'total_partials_taken': self.total_partials_taken,
            'breakeven_enabled': self.enable_breakeven,
            'trailing_enabled': self.enable_trailing,
            'partials_enabled': self.enable_partials
        }


# Global instance
position_manager = PositionManager()
