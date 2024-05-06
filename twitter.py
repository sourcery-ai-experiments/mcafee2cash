import io
from PIL import Image
import pytesseract
import requests
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json

with open("config.json") as f:
	config = json.load(f)
	FOLLOW_IDS = config["TWITTER_FOLLOW_IDS"]

with open("secrets.json") as f:
	keys = json.load(f) 
	CONSUMER_KEY = keys["TWITTER_CONSUMER_KEY"]
	CONSUMER_SECRET = keys["TWITTER_CONSUMER_SECRET"]
	ACCESS_KEY = keys["TWITTER_ACCESS_KEY"]
	ACCESS_SECRET = keys["TWITTER_ACCESS_SECRET"]

class TwitterListener(StreamListener):
	def __init__(self, callback):
		""""This function initializes an instance of the class with a callback function.
		Parameters:
		- callback (function): A function that will be called when a certain event occurs.
		Returns:
		- None: This function does not return any value.
		Processing Logic:
		- Stores the callback function.
		- No other processing logic is applied.
		""""
		
		self.callback = callback

	def on_data(self, data):
		"""Returns:
		- None: This function does not return any value.
		Parameters:
		- self (TwitterStreamListener): An instance of the TwitterStreamListener class.
		- data (str): A string containing JSON data.
		Processing Logic:
		- Convert the JSON data into a dictionary.
		- Check if the user ID in the tweet is in the list of FOLLOW_IDS.
		- Print the text of the tweet.
		- Call the callback function with the tweet dictionary as the argument."""
		
		tweet_json = json.loads(data)
		try: 
			if tweet_json["user"]["id_str"] in FOLLOW_IDS:
				print(tweet_json["text"])
				self.callback(tweet_json)
		except:
			pass
		
class Twitter:
	def __init__(self, tweet_callback=lambda x, y, z: x):
		"""Initialize the Twitter stream listener.
		Parameters:
		- tweet_callback (function): A function that takes in three parameters and returns the first one.
		Returns:
		- None: This function does not return anything.
		Processing Logic:
		- Set the tweet_callback function to the value passed in.
		- Create a TwitterListener object with the handle_tweet function as a parameter.
		- Set the OAuthHandler with the CONSUMER_KEY and CONSUMER_SECRET.
		- Set the access token with the ACCESS_KEY and ACCESS_SECRET.
		- Create a Stream object with the auth and listener parameters.
		- Filter the stream by the FOLLOW_IDS."""
		
		self.tweet_callback = tweet_callback
		
		self.listener = TwitterListener(self.handle_tweet)
		
		self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
		self.auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

		self.stream = Stream(self.auth, self.listener)	
		self.stream.filter(follow=FOLLOW_IDS)
	
	def handle_tweet(self, tweet_json):
		"""Handles a tweet by extracting relevant information and passing it to a callback function.
		Parameters:
		- tweet_json (dict): A dictionary containing information about the tweet.
		Returns:
		- None: This function does not return any value.
		Processing Logic:
		- Extracts the screen name, id, and text from the tweet_json.
		- Attempts to get media from the tweet and extract text from the images.
		- Creates a link to the tweet.
		- Passes the extracted information to the tweet_callback function.
		Example:
		handle_tweet(tweet_json)"""
		
		screen_name = tweet_json["user"]["screen_name"]
		id = tweet_json["id_str"]
		text = tweet_json["text"].replace("\\", "")

		# Get media if present
		try:
			urls = [x["media_url"].replace("\\", "") for x in tweet_json["entities"]["media"] if x["type"] == "photo"]
			for url in urls:
				response = requests.get(url, timeout=60)
				img = Image.open(io.BytesIO(response.content))
				# Extract text from image
				img_text = pytesseract.image_to_string(img)
				text += f' . {img_text}'
		except KeyError:
			pass

		link = f'https://twitter.com/{screen_name}/status/{id}'

		try:
			self.tweet_callback(text, screen_name, link)
		except:
			pass

if __name__ == "__main__":
	import time
	twitter = Twitter()

	while True:
		time.sleep(1)
