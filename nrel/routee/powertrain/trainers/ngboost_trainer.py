from enum import Enum
import pandas as pd

from ngboost import NGBRegressor
from ngboost.distns import Exponential, Normal


from nrel.routee.powertrain.core.model_config import ModelConfig
from nrel.routee.powertrain.estimators.estimator_interface import Estimator
from nrel.routee.powertrain.estimators.ngboost_estimator import NGBoostEstimator
from nrel.routee.powertrain.trainers.trainer import Trainer


class NGBoostTrainer(Trainer):
    def __init__(
        self,
        # max_depth: int = 10,
        # min_samples_split: int = 10,
        n_estimators: int = 100,
        Dist=Normal,
        verbose: bool = True,
        verbose_eval: int = 20,
        # learning_rate: float = 0.01,
        random_state: int = 52,
        # cores: int = 4,
        # output_type=RandomForestTrainerOutput.ONNX,
    ):
        # self.max_depth = max_depth
        # self.min_samples_split = min_samples_split
        self.n_estimators = n_estimators
        self.Dist = Dist
        self.verbose = verbose
        self.verbose_eval = verbose_eval
        # self.learning_rate = learning_rate
        self.random_state = random_state
        # self.cores = cores
        # self.output_type = output_type

    def inner_train(
        self, features: pd.DataFrame, target: pd.DataFrame, config: ModelConfig
    ) -> Estimator:
        """
        Uses a ngboost model to predict the energy rate values
        """
        ng = NGBRegressor(
            n_estimators=self.n_estimators,
            Dist=self.Dist,
            verbose=self.verbose,
            verbose_eval=self.verbose_eval,
            random_state=self.random_state,
            # min_samples_split=self.min_samples_split,
            # n_jobs=self.cores,
        )
        X = features.values
        y = target.values

        if y.shape[1] == 1:
            y = y.ravel()

        ng.fit(X, y)
        estimator = NGBoostEstimator(ng)
        return estimator
