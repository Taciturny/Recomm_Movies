import pandas as pd
from surprise import Dataset, Reader, SVDpp, accuracy
from surprise.model_selection import train_test_split
from typing import Optional
import mlflow
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry.model_version import ModelVersion
import optuna
from optuna.samplers import TPESampler
from prefect import task, Flow
from config import cf_config
# Set MLflow tracking URI
MLFLOW_TRACKING_URI = mlflow.set_tracking_uri("http://localhost:5000")

# Set other MLflow configurations
EXPERIMENT_NAME = cf_config['experiment_name']
HYO_EXPERIMENT_NAME = cf_config['hyperparameter_opt_experiment_name']
MODEL_NAME = cf_config['model_name']
mlflow.set_experiment(EXPERIMENT_NAME)
client = MlflowClient(MLFLOW_TRACKING_URI)


class MovieRecommendationFlow:
    @staticmethod
    @task
    def load_rating_data():
        try:
            data = pd.read_csv('data/ratings_small.csv')
            return data
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

    @staticmethod
    @task
    def start_mlflow_run():
        mlflow.start_run(run_name="SVD++")
        mlflow.set_tag("model", "SVDpp")
        return None

    @staticmethod
    @task
    def prepare_data(data):
        print("Data Shape Before Preparation:", data.shape) 
        reader = Reader(rating_scale=(1, 5))
        data_surprise = Dataset.load_from_df(data[['userId', 'movieId', 'rating']], reader)
        train_data, test_data = train_test_split(data_surprise, test_size=0.2, random_state=42)
        return train_data, test_data

    @staticmethod
    @task
    def train_svd_model(train_data):
        n_factors = 25
        n_epochs = 25
        lr_all = 0.007
        reg_all = 0.2
        svd_model = SVDpp(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all, reg_all=reg_all)
        svd_model.fit(train_data)
        return svd_model, n_factors, n_epochs, lr_all, reg_all

    @staticmethod
    @task
    def log_parameters_and_recommendations(svd_model, n_factors, n_epochs, lr_all, reg_all, test_data):  
        mlflow.log_param('n_factors', n_factors)
        mlflow.log_param('n_epochs', n_epochs)
        mlflow.log_param('lr_all', lr_all)
        mlflow.log_param('reg_all', reg_all)
        print("Parameters logged successfully.")

    @staticmethod
    @task
    def get_cf_recommendations(user_id, model, data, top_n=10):
        print("Data Shape in get_cf_recommendations:", data.shape)  
        print("Data Head in get_cf_recommendations:", data.head()) 
        user_movies = set(data[data['userId'] == user_id]['movieId'])
        all_items = set(data['movieId'])
        items_to_predict = list(all_items - user_movies)

        test_set = [(user_id, movie_id, 0) for movie_id in items_to_predict]
        predictions = model.test(test_set)

        top_predictions = sorted(predictions, key=lambda x: x.est, reverse=True)[:top_n]
        recommended_movies = [pred.iid for pred in top_predictions]

        RMSE = accuracy.rmse(top_predictions, verbose=False)
        MAE = accuracy.mae(top_predictions, verbose=False)

        mlflow.log_metric("RMSE", RMSE)
        mlflow.log_metric("MAE", MAE)

        return recommended_movies
    

    @staticmethod
    @task
    def run_optimization(num_trials: int, train_data, test_data) -> dict:
        mlflow.set_experiment(HYO_EXPERIMENT_NAME)

        def objective(trial):
            params = {
                'n_factors': trial.suggest_int('n_factors', 5, 100),
                'n_epochs': trial.suggest_int('n_epochs', 5, 50),
                'lr_all': trial.suggest_float('lr_all', 0.001, 0.1),
                'reg_all': trial.suggest_float('reg_all', 0.01, 1.0),
            }

            with mlflow.start_run(nested=True):
                mlflow.set_tag("model", "SVDpp")
                mlflow.log_params(params)

                svd_model = SVDpp(**params)
                svd_model.fit(train_data)

                test_set = [(user_id, movie_id, 0) for user_id, movie_id, _ in test_data]
                predictions = svd_model.test(test_set)

                rmse = accuracy.rmse(predictions, verbose=False)
                mlflow.log_metric("rmse", rmse)

                return rmse

        sampler = TPESampler(seed=42)
        study = optuna.create_study(direction="minimize", sampler=sampler)
        study.optimize(lambda trial: objective(trial), n_trials=num_trials)

        return study.best_params


    @staticmethod
    @task
    def register_and_set_stage_model(client):
        # Search for the best model runs
        best_model_runs = client.search_runs(
            experiment_ids=["1"],
            filter_string="tags.`run type` = 'best model'",
            order_by=["attributes.start_time DESC"],
            max_results=1,
        )
        if best_model_runs:
            # Get the most recent best model run id
            run_id = best_model_runs[0].info.run_id

            # Register the model
            model_name = 'movie_recomm'
            mv = mlflow.register_model(model_uri=f"runs:/{run_id}/models", name=model_name)
            version = mv.version

            # Get the production model's run id
            registered_model = client.search_registered_models(filter_string=f"name='{model_name}'")
            production_run_id = [
                model.run_id
                for model in registered_model[0].latest_versions
                if model.current_stage == 'Production'
            ]

            # Set the stage based on comparison with the production model
            if production_run_id:
                production_run = client.get_run(production_run_id[0])
                production_rmse = production_run.data.metrics['rmse']

                best_run = client.get_run(run_id)
                best_rmse = best_run.data.metrics['rmse']

                new_stage = "Production" if best_rmse > production_rmse else "Archived"
            else:
                new_stage = "Production"

            # Transition model version stage
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=new_stage,
                archive_existing_versions=False,
            )

            print(f'The version {version} of {model_name} model has been set to {new_stage}')
        else:
            print("No best model runs found!")


    @staticmethod
    @task
    def end_mlflow_run():
        mlflow.end_run()
        return None

    @Flow
    def main_flow():
        data_task = MovieRecommendationFlow.load_rating_data()
        mlflow_task = MovieRecommendationFlow.start_mlflow_run()
        train_task = MovieRecommendationFlow.prepare_data(data_task)
        train_data, test_data = train_task
        trained_model, n_factors, n_epochs, lr_all, reg_all = MovieRecommendationFlow.train_svd_model(train_data)
        log_task = MovieRecommendationFlow.log_parameters_and_recommendations(
            trained_model, n_factors, n_epochs, lr_all, reg_all, test_data
        )
        
        recommendations_task = MovieRecommendationFlow.get_cf_recommendations(user_id=1930, model=trained_model, data=data_task)
        best_params = MovieRecommendationFlow.run_optimization(num_trials=1, train_data=train_data, test_data=test_data)
        register_model_task = MovieRecommendationFlow.register_and_set_stage_model(client)
        
        end_mlflow_task = MovieRecommendationFlow.end_mlflow_run()
        return end_mlflow_task


if __name__ == '__main__':
    MovieRecommendationFlow.main_flow()
