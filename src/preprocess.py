import pandas as pd
import numpy as np
import ast
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

def load_movie_data() -> pd.DataFrame:
    '''
    Load data from CSV files and merge them.

    Returns:
        pd.DataFrame: Merged DataFrame containing movie information.
    '''
    try:
        cred = pd.read_csv('data/tmdb_5000_credits.csv')
        mov = pd.read_csv('data/tmdb_5000_movies.csv')
        merged_df = mov.merge(cred, left_on='id', right_on='movie_id')
        merged_df.drop(['id','title_y'], axis=1, inplace=True)
        
        return merged_df
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return pd.DataFrame()
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

# Load the data
merged_df = load_movie_data()

def preprocess_and_feature_extraction(merged_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Preprocess the movie dataset and extract relevant features.

    Args:
        merged_df (pd.DataFrame): Input DataFrame containing movie information.

    Returns:
        pd.DataFrame: Preprocessed DataFrame with extracted features.
    '''
    # Change datatype of release date and rename columns
    merged_df['release_date'] = pd.to_datetime(merged_df['release_date'], errors='coerce')
    merged_df.rename(columns={'title_x': 'title'}, inplace=True)

    # Feature extraction
    if 'genres' in merged_df.columns:
        merged_df['genre_names'] = merged_df['genres'].apply(lambda x: [genre['name'] for genre in json.loads(x)] if isinstance(x, str) and x != '[]' else [])
    if 'crew' in merged_df.columns:
        merged_df['crew'] = merged_df['crew'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        merged_df['director'] = merged_df['crew'].apply(lambda x: next((i['name'] for i in x if i['job'] == 'Director'), np.nan))
    merged_df['year'] = merged_df['release_date'].dt.year.astype('Int64')
    if 'cast' in merged_df.columns:
        merged_df['cast'] = merged_df['cast'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        merged_df['cast_names'] = merged_df['cast'].apply(lambda x: [actor['name'] for actor in x] if isinstance(x, list) else [])
    if 'keywords' in merged_df.columns:
        merged_df['keywords'] = merged_df['keywords'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        merged_df['keyword_names'] = merged_df['keywords'].apply(lambda x: [keyword['name'] for keyword in x])
    if 'production_companies' in merged_df.columns:
        merged_df['production_companies'] = merged_df['production_companies'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        merged_df['production_company_names'] = merged_df['production_companies'].apply(lambda x: [company['name'] for company in x] if isinstance(x, list) else [])
    if 'spoken_languages' in merged_df.columns:
        merged_df['spoken_languages'] = merged_df['spoken_languages'].apply(json.loads)
        merged_df['language'] = merged_df['spoken_languages'].apply(lambda x: [lang['name'] for lang in x])
    
    return merged_df

processed_df = preprocess_and_feature_extraction(merged_df)

def handling_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Handle missing values in the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame with missing values.

    Returns:
        pd.DataFrame: DataFrame with missing values handled.
    '''
    df['has_homepage'] = df['homepage'].notnull().astype(int)
    df['has_tagline'] = df['tagline'].notnull().astype(int)
    df.drop(['homepage', 'tagline'], axis=1, inplace=True)

    df['overview'].fillna(' ', inplace=True)
    default_date = pd.to_datetime('1900-01-01')  # A default date to replace missing release_date values
    df['release_date'] = df['release_date'].fillna(default_date)
    df['runtime'].fillna(df['runtime'].mean(), inplace=True)
    
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    mean_year = round(df['year'].mean())
    df['year'].fillna(mean_year, inplace=True)
    
    df['director'].fillna('Not Available', inplace=True)
    
    return df

handled_df = handling_missing_values(processed_df)

def preprocess_text(text):
    '''
    Preprocesses text data by lowercasing and removing special characters and digits.

    Args:
        text (str): Text data to be preprocessed.

    Returns:
        str: Preprocessed text.
    '''
    # Lowercasing
    text = text.lower()
    # Removing special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

def tokenize_and_lemmatize(text):
    '''
    Tokenizes and lemmatizes text data.

    Args:
        text (str): Text data to be tokenized and lemmatized.

    Returns:
        list: List of tokens after tokenization and lemmatization.
    '''
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    
    return tokens

features_to_preprocess = ['director', 'genre_names', 'cast_names', 'keyword_names', 'language', 'overview']

for feature in features_to_preprocess:
    if feature in handled_df.columns:
        handled_df[feature] = handled_df[feature].astype(str).apply(preprocess_text)
        handled_df[feature] = handled_df[feature].apply(tokenize_and_lemmatize)


# Accessing the resulting DataFrames
merged_df = load_movie_data()
processed_df = preprocess_and_feature_extraction(merged_df)
handled_df = handling_missing_values(processed_df)
