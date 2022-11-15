from mesa.batchrunner import batch_run
from multiprocessing import freeze_support
import os
import model
from model import SocialInfluenceModel
import pandas as pd
import numpy as np

params = {"number_influencers": 1, "influence_chance": 0.4, "influence_check_frequency": 0.4, "reintegration_probability": 0.3, "resilience_chance": 0.3, "gain_hardened_chance": 0.5}
# 2592 dimensions
if __name__ == '__main__':
    #freeze_support()
    results = batch_run(SocialInfluenceModel,parameters=params,iterations=1,max_steps=500,
                        number_processes=None,data_collection_period=1,display_progress=True,)

    df = pd.DataFrame(results)
    #results_df = df.drop(['width', 'height', 'seed'], axis=1)
    #print(results_df.keys())

    # To export a csv of the results
    cwd = os.getcwd()
    path = cwd + "/test.csv"
    df.to_csv(path)