from __future__ import annotations

# from abc import ABC, abstractmethod
from pathlib import Path
import joblib
import base64
import io
import json
import pandas as pd
from ngboost import NGBRegressor

from nrel.routee.powertrain.core.features import DataColumn, FeatureSet, TargetSet
from core.model_config import PredictMethod
from nrel.routee.powertrain.estimators.estimator_interface import Estimator



class NGBoostEstimator(Estimator):

    def __init__(self, ngboost) -> None:
        self.model = ngboost  

    @classmethod
    def from_file(cls, filepath: str | Path) -> Estimator:
        """
        Load an estimator from a file
        """
        filepath = Path(filepath)

        with filepath.open("rb") as f:
            loaded_dict = json.load(f)
        
        return cls.from_dict(loaded_dict)

    def to_file(self, filepath: str | Path):
        """
        Save an estimator to a file
        """
        filepath = Path(filepath)

        # with filepath.open("wb") as f:
        #     json.dump(self.to_dict(), f)

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f)


    @classmethod
    def from_dict(cls, in_dict: dict) -> 'NGBRegressor':

        """
        Load an estimator from a bytes object in memory
        """

        # model_base64 = in_dict.get("ngboost_model")
        model_base64 = in_dict
        # print
        if model_base64 is None:
            raise ValueError("Model file must contain ngboost model at key: 'ngboost_model'")
        byte_stream = io.BytesIO(base64.b64decode(model_base64))
        ngboost_model = joblib.load(byte_stream)
        return cls(ngboost_model)

    def to_dict(self) -> dict:
        """
        Serialize an estimator to a python dictionary
        """
        byte_stream = io.BytesIO()
        joblib.dump(self.model, byte_stream)
        byte_stream.seek(0)
        model_base64 = base64.b64encode(byte_stream.read()).decode('utf-8')
        # print((model_base64))

        out_dict = dict({"ngboost_model": model_base64})
        # print(out_dict)
        # out_dict = {'ngboost_model' :model_base64}
        # print(out_dict)
        return out_dict
        # return model_base64
        # raise('Value Error')

    def print_som():
        print("It's working")

    def predict(
        self,
        links_df: pd.DataFrame,
        feature_set: FeatureSet,
        distance: DataColumn,
        target_set: TargetSet,
        predict_method: PredictMethod = PredictMethod.RATE,
    ) -> pd.DataFrame:
        if len(target_set.targets) != 1:
            raise ValueError(
                "NGBoost only supports a single energy target. "
                "Please use a different estimator for multiple energy targets."
            )
        energy = target_set.targets[0]

        distance_col = distance.name
        if predict_method == PredictMethod.RATE:
            feature_name_list = feature_set.feature_name_list
        elif predict_method == PredictMethod.RAW:
            feature_name_list = feature_set.feature_name_list + [distance.name]
        else:
            raise ValueError(
                f"Predict method {predict_method} is not supported by NGBoostEstimator"
            )
        x = links_df[feature_name_list].values
        # print(x)

        energy_pred_series = self.model.predict(x.tolist())

        energy_df = pd.DataFrame(index=links_df.index)

        if predict_method == PredictMethod.RAW:
            energy_pred = energy_pred_series
        elif predict_method == PredictMethod.RATE:
            energy_pred = energy_pred_series * links_df[distance_col]
        else:
            raise ValueError(
                f"Predict method {predict_method} is not supported by NGBoostEstimator"
            )
        energy_df[energy.name] = energy_pred

        return energy_df

 