"""
AppleTrader Pro - ML Model Trainer
Trains XGBoost classifier to predict trade profitability

Process:
1. Load historical trades with features
2. Label trades as winners (1) or losers (0)
3. Train XGBoost model
4. Evaluate on test set
5. Save model for predictions
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime
import pickle
import os

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[ML] XGBoost not available - install with: pip install xgboost")

from ml.feature_engineering import feature_engineer, MLFeatures
from backtesting.backtest_engine import backtest_engine, BacktestTrade


class MLModelTrainer:
    """
    Trains ML models to predict trade profitability
    """

    def __init__(self):
        self.model = None
        self.feature_names = []
        self.model_metrics = {}

    def prepare_training_data(
        self,
        historical_trades: List[BacktestTrade],
        historical_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from backtest results

        Args:
            historical_trades: List of completed trades from backtest
            historical_data: Historical OHLCV data

        Returns:
            (X_features, y_labels)
        """

        print(f"[ML Trainer] Preparing training data from {len(historical_trades)} trades...")

        features_list = []
        labels = []

        for trade in historical_trades:
            try:
                # Find the candle index for this trade
                trade_time = trade.entry_time
                candle_idx = historical_data.index.get_loc(trade_time)

                # Calculate features at trade entry
                features = feature_engineer.calculate_features(historical_data, index=candle_idx)

                # Convert features to dict
                feature_dict = {
                    'ema_20': features.ema_20,
                    'ema_50': features.ema_50,
                    'ema_200': features.ema_200,
                    'ema_slope_20': features.ema_slope_20,
                    'ema_alignment': features.ema_alignment,
                    'macd': features.macd,
                    'macd_signal': features.macd_signal,
                    'macd_histogram': features.macd_histogram,
                    'adx': features.adx,
                    'rsi_14': features.rsi_14,
                    'rsi_slope': features.rsi_slope,
                    'stoch_k': features.stoch_k,
                    'stoch_d': features.stoch_d,
                    'cci': features.cci,
                    'williams_r': features.williams_r,
                    'momentum_10': features.momentum_10,
                    'atr_14': features.atr_14,
                    'atr_ratio': features.atr_ratio,
                    'bb_width': features.bb_width,
                    'bb_position': features.bb_position,
                    'volume_ratio': features.volume_ratio,
                    'volume_trend': features.volume_trend,
                    'obv_slope': features.obv_slope,
                    'candle_size': features.candle_size,
                    'upper_wick_ratio': features.upper_wick_ratio,
                    'lower_wick_ratio': features.lower_wick_ratio,
                    'body_ratio': features.body_ratio,
                    'is_engulfing': features.is_engulfing,
                    'is_pin_bar': features.is_pin_bar,
                    'is_inside_bar': features.is_inside_bar,
                    'distance_to_high_20': features.distance_to_high_20,
                    'distance_to_low_20': features.distance_to_low_20,
                    'swing_strength': features.swing_strength,
                    'trend_strength': features.trend_strength,
                }

                features_list.append(feature_dict)

                # Label: 1=winner, 0=loser
                label = 1 if trade.profit_loss > 0 else 0
                labels.append(label)

            except Exception as e:
                print(f"[ML Trainer] Error processing trade: {e}")
                continue

        X = pd.DataFrame(features_list)
        y = pd.Series(labels)

        print(f"[ML Trainer] Prepared {len(X)} training samples")
        print(f"[ML Trainer] Winners: {sum(labels)} ({sum(labels)/len(labels)*100:.1f}%)")

        return X, y

    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame = None,
        y_test: pd.Series = None
    ) -> Dict:
        """
        Train XGBoost classifier

        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features (optional)
            y_test: Test labels (optional)

        Returns:
            Dict with training metrics
        """

        if not XGBOOST_AVAILABLE:
            print("[ML Trainer] ❌ XGBoost not available")
            return {}

        print(f"[ML Trainer] Training XGBoost model...")

        # Store feature names
        self.feature_names = list(X_train.columns)

        # Train XGBoost
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )

        self.model.fit(X_train, y_train)

        # Evaluate on training set
        train_accuracy = self.model.score(X_train, y_train)
        train_proba = self.model.predict_proba(X_train)

        metrics = {
            'train_accuracy': train_accuracy,
            'train_samples': len(X_train),
            'feature_count': len(self.feature_names),
        }

        print(f"[ML Trainer] ✓ Training accuracy: {train_accuracy*100:.1f}%")

        # Evaluate on test set if provided
        if X_test is not None and y_test is not None:
            test_accuracy = self.model.score(X_test, y_test)
            test_proba = self.model.predict_proba(X_test)

            metrics['test_accuracy'] = test_accuracy
            metrics['test_samples'] = len(X_test)

            print(f"[ML Trainer] ✓ Test accuracy: {test_accuracy*100:.1f}%")

        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]

        print(f"\n[ML Trainer] Top 10 Features:")
        for feat, importance in top_features:
            print(f"  - {feat}: {importance:.4f}")

        metrics['feature_importance'] = feature_importance
        self.model_metrics = metrics

        return metrics

    def predict(self, features: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data

        Args:
            features: DataFrame with same features as training

        Returns:
            (predictions, probabilities)
        """

        if self.model is None:
            raise ValueError("Model not trained yet")

        # Ensure features are in correct order
        features = features[self.feature_names]

        predictions = self.model.predict(features)
        probabilities = self.model.predict_proba(features)

        return predictions, probabilities

    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'metrics': self.model_metrics,
            'trained_date': datetime.now().isoformat()
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"[ML Trainer] ✓ Model saved to: {filepath}")

    def load_model(self, filepath: str):
        """Load trained model from disk"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.model_metrics = model_data['metrics']

        print(f"[ML Trainer] ✓ Model loaded from: {filepath}")
        print(f"[ML Trainer] Trained: {model_data.get('trained_date', 'Unknown')}")
        print(f"[ML Trainer] Features: {len(self.feature_names)}")

    def train_from_backtest(
        self,
        symbol: str,
        timeframe: str,
        historical_data: pd.DataFrame,
        strategy_func,
        test_size: float = 0.2
    ) -> Dict:
        """
        Complete training pipeline from backtest

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            historical_data: Historical OHLCV data
            strategy_func: Strategy function for backtesting
            test_size: Fraction of data for testing

        Returns:
            Training metrics
        """

        print(f"\n[ML Trainer] === TRAINING PIPELINE ===")
        print(f"[ML Trainer] Symbol: {symbol}, Timeframe: {timeframe}")

        # Step 1: Run backtest to get trades
        print(f"\n[ML Trainer] Step 1: Running backtest...")
        results = backtest_engine.run_backtest(
            symbol=symbol,
            timeframe=timeframe,
            data=historical_data,
            strategy_func=strategy_func
        )

        if not results.trades or len(results.trades) < 50:
            print(f"[ML Trainer] ❌ Not enough trades for training ({len(results.trades)})")
            return {}

        # Step 2: Prepare training data
        print(f"\n[ML Trainer] Step 2: Preparing training data...")
        X, y = self.prepare_training_data(results.trades, historical_data)

        if len(X) < 50:
            print(f"[ML Trainer] ❌ Not enough samples ({len(X)})")
            return {}

        # Step 3: Split train/test
        split_idx = int(len(X) * (1 - test_size))
        X_train = X.iloc[:split_idx]
        y_train = y.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_test = y.iloc[split_idx:]

        print(f"[ML Trainer] Train: {len(X_train)}, Test: {len(X_test)}")

        # Step 4: Train model
        print(f"\n[ML Trainer] Step 3: Training model...")
        metrics = self.train_model(X_train, y_train, X_test, y_test)

        print(f"\n[ML Trainer] === TRAINING COMPLETE ===\n")

        return metrics


# Global instance
ml_trainer = MLModelTrainer()
