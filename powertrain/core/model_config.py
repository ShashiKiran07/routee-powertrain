from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from powertrain.core.features import FeaturePack
from powertrain.core.powertrain_type import PowertrainType


@dataclass
class ModelConfig:
    # vehicle information
    vehicle_description: str
    powertrain_type: PowertrainType

    # model information
    feature_pack: FeaturePack
    energy_rate_low_limit: float = 0.0
    energy_rate_high_limit: float = np.inf
    feature_dtype: str = "float32"
    onnx_input_name: str = "input"
    test_size: float = 0.2
    random_seed: int = 42

    trip_column: str = "trip_id"

    def __post_init__(self):
        if self.energy_rate_low_limit >= self.energy_rate_high_limit:
            raise ValueError(
                "energy_rate_low_limit must be less than energy_rate_high_limit"
            )
        if isinstance(self.feature_pack, dict):
            self.feature_pack = FeaturePack.from_dict(self.feature_pack)

        if isinstance(self.powertrain_type, str):
            self.powertrain_type = PowertrainType.from_string(self.powertrain_type)

    @classmethod
    def from_dict(cls, d: dict) -> ModelConfig:
        d["powertrain_type"] = PowertrainType.from_string(d["powertrain_type"])
        d["feature_pack"] = FeaturePack.from_dict(d["feature_pack"])
        return cls(**d)

    def to_dict(self) -> dict:
        d = self.__dict__
        d["powertrain_type"] = self.powertrain_type.name
        d["feature_pack"] = self.feature_pack.to_dict()

        return d
