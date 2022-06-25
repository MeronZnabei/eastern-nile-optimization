# Script for open exploration/scenario discovery


import numpy as np
import os
import pandas as pd
import sys

from datetime import datetime


from ema_workbench import RealParameter, ScalarOutcome, Model, Policy, Scenario
from ema_workbench import MultiprocessingEvaluator, ema_logging

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from model.model_nile_scenario import ModelNileScenario


if __name__ == "__main__":
    ema_logging.log_to_stderr(ema_logging.INFO)

    output_directory = "../outputs/"
    nile_model = ModelNileScenario()

    lever_count = nile_model.overarching_policy.get_total_parameter_count()

    em_model = Model("NileProblem", function=nile_model)
    em_model.uncertainties = [
        RealParameter("yearly_demand_growth_rate", 0.01, 0.03),
        RealParameter("blue_nile_mean_coef", 0.75, 1.25),
        RealParameter("white_nile_mean_coef", 0.75, 1.25),
        RealParameter("atbara_mean_coef", 0.75, 1.25),
        RealParameter("blue_nile_dev_coef", 0.5, 1.5),
        RealParameter("white_nile_dev_coef", 0.5, 1.5),
        RealParameter("atbara_dev_coef", 0.5, 1.5)
    ]
    em_model.levers = [
        RealParameter("v" + str(i), 0, 1) for i in range(lever_count)
    ]

    # specify outcomes
    em_model.outcomes = [
        ScalarOutcome("egypt_irr", ScalarOutcome.MINIMIZE),
        ScalarOutcome("egypt_90", ScalarOutcome.MINIMIZE),
        ScalarOutcome("egypt_low_had", ScalarOutcome.MINIMIZE),
        ScalarOutcome("sudan_irr", ScalarOutcome.MINIMIZE),
        ScalarOutcome("sudan_90", ScalarOutcome.MINIMIZE),
        ScalarOutcome("ethiopia_hydro", ScalarOutcome.MAXIMIZE),
    ]

    fixed_uncertainties = {"white_nile_mean_coef": 1, "atbara_mean_coef": 1,
                           "blue_nile_dev_coef": 1, "white_nile_dev_coef": 1,
                           "atbara_dev_coef": 1}
    my_scenarios = [
        Scenario("Baseline", yearly_demand_growth_rate=0.02,
                 blue_nile_mean_coef=1, **fixed_uncertainties
                 ),
        Scenario("HighD_HighB", yearly_demand_growth_rate=0.03,
                 blue_nile_mean_coef=1.25, **fixed_uncertainties
                 ),
        Scenario("HighD_LowB", yearly_demand_growth_rate=0.03,
                 blue_nile_mean_coef=0.75, **fixed_uncertainties
                 ),
        Scenario("LowD_HighB", yearly_demand_growth_rate=0.01,
                 blue_nile_mean_coef=1.25, **fixed_uncertainties
                 ),
        Scenario("LowD_LowB", yearly_demand_growth_rate=0.01,
                 blue_nile_mean_coef=0.75, **fixed_uncertainties
                 ),
    ]
    policy_df = pd.read_csv(f"{output_directory}baseline_results.csv")
    my_policies = [
        Policy(
            f"Policy{i}",
            **(policy_df.iloc[i, 1:165].to_dict())
        ) for i in policy_df.index
    ]

    before = datetime.now()

    with MultiprocessingEvaluator(em_model) as evaluator:
        experiments, outcomes = evaluator.perform_experiments(
            my_scenarios,
            my_policies
        )

    after = datetime.now()

    with open(f"{output_directory}time_counter_resimulation.txt", "w") as f:
        f.write(
            f"It took {after-before} time to run re-simulation 5 scenarios {len(my_policies)} policies"
        )
    outcomes = pd.DataFrame.from_dict(outcomes)
    experiments.to_csv(f"{output_directory}experiments_resimulation.csv")
    outcomes.to_csv(f"{output_directory}outcomes_resimulation.csv")
