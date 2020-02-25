import boto3
import json 
from datetime import datetime
import random 
import pandas as pd 
from recommender import Recommender
from helpers import fill_id, df_to_id_list, prep_data
from database_connection import c, connection
import warnings;
warnings.filterwarnings('ignore')


class PythonPredictor:
    def __init__(self, config={}):
        """Called once before the API becomes available. Setup for model serving such as downloading/initializing the model or downloading vocabulary can be done here. Required.

        Args:
            config: Dictionary passed from API configuration (if specified).
        """
         
        # When using s3 bucket to download the model
        # s3 = boto3.client("s3")
        # s3.download_file(config["bucket"], config["key"], "w2v_limitingfactor_v3.51.model")

        # Or import the model locally 


        self.model = Recommender('models/w2v_limitingfactor_v3.51.model')
        
        pass

    def predict(self, payload): # recieves userid, outputs recommendation_id
        """Called once per request. Runs preprocessing of the request payload, inference, and postprocessing of the inference output. Required.

        Args:
            payload: The parsed JSON request payload.

        Returns:
            Prediction or a batch of predictions.
        """

        # Get ratings data from DB
        
        userid = payload
        
        
        c.execute("SELECT * FROM test_ratings WHERE userid=%s;", (userid,))
        ratings_sql= c.fetchall()
        ratings = pd.DataFrame(ratings_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd_URI', 'Rating', 'userid'])
        ratings= ratings.dropna()
        

        # c.execute("SELECT * FROM test_watchlist WHERE userid=%s;", (userid,))
        # watchlist_sql= c.fetchall()
        # watchlist = pd.DataFrame(watchlist_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd_URI', 'userid'])
        # watchlist = watchlist.dropna()
        

        c.execute("SELECT * FROM test_watched WHERE userid=%s;", (userid,))
        watched_sql= c.fetchall()
        watched = pd.DataFrame(watched_sql, columns = ['Date', 'Name', 'Year', 'Letterboxd_URI', 'userid'])
        watched = watched.dropna()
        

        # c.execute("SELECT * FROM test_title_basics_small;")
        # title_basics_small_sql= c.fetchall()
        # id_book = pd.DataFrame(title_basics_small_sql, columns = ['tconst', 'primaryTitle', 'originalTitle', 'startYear'])
        # id_book = id_book.dropna()
        
        # prep user data # substitute watched for watchlist
        good_list, bad_list, hist_list, val_list, ratings_dict = prep_data(
                                    ratings, watched_df=watched, good_threshold=4, bad_threshold=3) 
        
        """ process the raw JSON into a list """ # if receiving JSON (not userid) 
        # payload_jsonified = json.dumps(payload)
        # movie_dict = json.loads(payload_jsonified)
        # movie_list = list(movie_dict.values())
        
        """ run prediction """
        
        predictions = self.model.predict(good_list, bad_list, hist_list, val_list, ratings_dict, n=20, harshness=1, rec_movies=True, scoring=True,)
        
        """ turn back into JSON """
        
        names = ['Title', 'Year', 'IMDB URL', 'Average Rating', 'Number of Votes', 'Similarity Score', 'IMDB ID']
        names_lists = {key:[] for key in names}
        
        for x in range(0, len(predictions[0])):
            for y in range(0, len(predictions)):
                names_lists[names[x]].append(predictions[y][x])
                
        results_dict = [dict(zip(names_lists,t)) for t in zip(*names_lists.values())]
        json_data = json.dumps(results_dict)
        

        """ commit to the database """

        recommendation_id = random.randint(1, 100000000)
        recommendation_json = json_data
        date = datetime.now()
        c.execute("INSERT INTO recommendations VALUES (%s, %s, %s, %s)", (userid, recommendation_id, recommendation_json, date))
        connection.commit()
        
        return recommendation_id