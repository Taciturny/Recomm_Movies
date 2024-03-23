import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.preprocess import load_movie_data, preprocess_and_feature_extraction, handling_missing_values
import mlflow
from mlflow.tracking import MlflowClient
from prefect import Flow, task
import optuna
from optuna.samplers import TPESampler

mlflow.set_tracking_uri("http://localhost:5000")
EXPERIMENT_NAME = 'cb_training'
mlflow.set_experiment(EXPERIMENT_NAME)
MODEL_NAME = 'CB_Movie_Recomm_Model'
HYO_EXPERIMENT_NAME = 'cb_tuning'
client = MlflowClient()


class MovieRecommendationSystem:
    @staticmethod
    @task
    def load_and_preprocess_data():
        merged_df = load_movie_data()
        processed_df = preprocess_and_feature_extraction(merged_df)
        processed_df = handling_missing_values(processed_df)
        return processed_df
    
    @staticmethod
    @task
    def preprocess_text_features(processed_df):
        processed_df['combined_features'] = processed_df[['cast_names', 'language', 'keyword_names', 'genre_names', 'director', 'overview']].apply(lambda x: ' '.join(map(str, x)), axis=1)
        return processed_df

    
    @staticmethod
    @task
    def create_tfidf_matrix(features):
        tfidf = TfidfVectorizer(stop_words='english')
        features_matrix = tfidf.fit_transform(features)
        return tfidf, features_matrix
    
    @staticmethod
    @task
    def calculate_cosine_similarity(features_matrix):
        return cosine_similarity(features_matrix, features_matrix)
    
    @staticmethod
    @task
    def get_content_based_recommendations(movie_id, cosine_sim, processed_df, top_n=10):
        indices = pd.Series(processed_df.index, index=processed_df['movie_id'])
        idx = indices[movie_id]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:top_n + 1]
        movie_indices = [i[0] for i in sim_scores]

        recommendations = processed_df.iloc[movie_indices]['title'].tolist()
        return recommendations
    
    @staticmethod
    @task
    def log_model_and_artifacts(tfidf_model, processed_df, cosine_sim):
        mlflow.sklearn.log_model(tfidf_model, "tfidf_model") 

        np.save("cosine_similarity.npy", cosine_sim)  
        mlflow.log_artifact("cosine_similarity.npy", "artifacts")
        return "Log and save complete"
    

    @staticmethod
    # @task
    def evaluate_cb(processed_df):
        # Select a random movie for evaluation
        random_movie_index = np.random.randint(0, len(processed_df))
        random_movie_id = processed_df.iloc[random_movie_index]['movie_id']

        # Create TF-IDF matrix
        tfidf, features_matrix = MovieRecommendationSystem.create_tfidf_matrix(processed_df['combined_features'])

        # Calculate cosine similarity matrix
        cosine_sim = MovieRecommendationSystem.calculate_cosine_similarity(features_matrix)

        # Get content-based recommendations for the random movie
        recommendations = MovieRecommendationSystem.get_content_based_recommendations(random_movie_id, cosine_sim, processed_df)

        # Evaluate and print the results
        print(f"Randomly selected movie: {processed_df.iloc[random_movie_index]['title']}")
        print(f"Content-based recommendations: {recommendations}")

        # Return the selected movie and recommendations
        return {
            'selected_movie': processed_df.iloc[random_movie_index]['title'],
            'recommendations': recommendations
        }

    @staticmethod
    # @task
    def run_optimization(num_trials: int) -> dict:
        mlflow.set_experiment(HYO_EXPERIMENT_NAME)

        def objective(trial):
            tfidf_max_features = trial.suggest_int('tfidf_max_features', 1000, 10000)
            stop_words = trial.suggest_categorical('stop_words', ['english', None])

            # Load and preprocess data
            processed_df = MovieRecommendationSystem.load_and_preprocess_data()

            # Preprocess text features
            processed_df = MovieRecommendationSystem.preprocess_text_features(processed_df)

            # Evaluate the model
            recommendations = MovieRecommendationSystem.evaluate_cb(processed_df)
            metric_value = len(recommendations)  # Just an examplec

            # Log hyperparameters and metric
            with mlflow.start_run(nested=True):
                mlflow.set_tag("model", "ContentBased")
                mlflow.log_params({'tfidf_max_features': tfidf_max_features, 'stop_words': stop_words})
                mlflow.log_metric("metric_value", metric_value)

            return metric_value

        sampler = TPESampler(seed=42)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(lambda trial: objective(trial), n_trials=num_trials)

        return study.best_params

    @staticmethod
    @task
    def end_mlflow_run():
        try:
            # Your existing code here
            mlflow.end_run()
        except Exception as e:
            print(f"An error occurred: {e}")
        return None
    

    @Flow
    def main_flow():
        MovieRecommendationSystem()
        load_data_task = MovieRecommendationSystem.load_and_preprocess_data()
        preprocess_task = MovieRecommendationSystem.preprocess_text_features(load_data_task)
        matrix_task = MovieRecommendationSystem.create_tfidf_matrix(preprocess_task)
        log_params_task = MovieRecommendationSystem.log_model_and_artifacts(matrix_task, preprocess_task, matrix_task)
        recommendations_task = MovieRecommendationSystem.get_content_based_recommendations(movie_id=19995, cosine_sim=log_params_task, processed_df=preprocess_task)
        ev_metrics = MovieRecommendationSystem.evaluate_cb(processed_df=preprocess_task)
        optimize_hyperparameters_task = MovieRecommendationSystem.run_optimization(num_trials=1)
        print(recommendations_task)
        print(ev_metrics['recommendations'])
        end_mlflow_task = MovieRecommendationSystem.end_mlflow_run()
        return end_mlflow_task

if __name__ == "__main__":
    MovieRecommendationSystem().main_flow()
