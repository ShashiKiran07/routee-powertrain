import logging
from abc import ABC, abstractmethod

import onnx
import pandas as pd

from nrel.routee.powertrain.core.metadata import Metadata
from nrel.routee.powertrain.core.model import Model
from nrel.routee.powertrain.core.model_config import ModelConfig
from nrel.routee.powertrain.trainers.utils import test_train_split
from nrel.routee.powertrain.validation.errors import compute_errors

ENERGY_RATE_NAME = "energy_rate"


log = logging.getLogger(__name__)


class Trainer(ABC):
    def train(self, data: pd.DataFrame, config: ModelConfig) -> Model:
        """
        A wrapper for inner train that does some pre and post processing.
        """
        distance_name = config.feature_pack.distance.name

        for energy_target in config.feature_pack.energy:
            energy_rate_name = f"{energy_target.name}_rate"
            data[energy_rate_name] = data[energy_target.name] / data[distance_name]

            filtered_data = data[
                (data[energy_rate_name] > energy_target.feature_range.lower)
                & (data[energy_rate_name] < energy_target.feature_range.upper)
            ]
            filtered_rows = len(data) - len(filtered_data)
            log.info(
                f"filtered out {filtered_rows} rows with energy rates outside "
                f"of the limits of {energy_target.feature_range.lower} "
                f"and {energy_target.feature_range.upper} "
                f"for energy target {energy_target.name}"
            )

        train, test = test_train_split(
            filtered_data, test_size=config.test_size, seed=config.random_seed
        )
        features = train[config.feature_pack.feature_name_list]
        if features.isnull().values.any():
            raise ValueError("Features contain null values")

        target = train[config.feature_pack.energy_rate_name_list]
        if target.isnull().values.any():
            raise ValueError(
                "Target contains null values. Try decreasing the energy rate high limit"
            )

        onnx_model = self.inner_train(features=features, target=target, config=config)

        metadata = Metadata(config=config)

        vehicle_model = Model.build(onnx_model, metadata)

        model_errors = compute_errors(test, vehicle_model)

        model_with_errors = vehicle_model.set_errors(model_errors)

        return model_with_errors

    @abstractmethod
    def inner_train(
        self, features: pd.DataFrame, target: pd.DataFrame, config: ModelConfig
    ) -> onnx.ModelProto:
        """
        Builds an ONNX model from the given data and config
        """
        pass
