#!/usr/bin/env python

import requests
from textblob import TextBlob
from telegram import TelegramBot
from twitter import Twitter
import time

symbol_name = {}
name_symbol = {}

bot = None

def get_coins_bittrex():
	"""Populate symbol_name and name_symbol dictionaries with markets trading on Bittrex"""
		
	endpoint = "https://bittrex.com/api/v1.1/public/getmarkets"
	try:
		markets = requests.get(endpoint, timeout=60).json(timeout=60)["result"]
		for market in markets:
			symbol = market["MarketCurrency"]
			name = market["MarketCurrencyLong"].lower()
			symbol_name[symbol] = name
			name_symbol[name] = symbol
		# print(f'Found {len(markets)} markets.')
	except Exception as e:
		print(f'Failed to get markets from {endpoint} ({e})')
	

def extract_symbols(text):
	"""Return trading symbols of cryptocurrencies in text in format (symbol, name) e.g. ("BTC", "bitcoin")"""
	symbols = set()
	ignore_tags = ["DT"]
	words = [w[0].lower() for w in TextBlob(text).tags if w[1] not in ignore_tags]
	for word in words:
		if word.upper() in symbol_name:
			symbols.add((word.upper(), symbol_name[word.upper()]))
			# print(f'Found symbol: {word.upper()}')
		elif word.lower() in name_symbol:
			symbols.add((name_symbol[word.lower()], word.lower()))   
			# print(f'Found symbol: {name_symbol[word]}')

	return symbols

def get_sentiment_analysis(text, coins):
	"""Return the sentiment analysis of coins mentioned in text in
	the form of a dictionary that aggregates the sentiment of
	sentences that include each of the coins.
	"""
	sentiment = {}
	blob = TextBlob(text)
	for sentence in blob.sentences:
		lowercase_words = [x.lower() for x in sentence.words]
		for coin in coins:
			if coin[0].lower() in lowercase_words or coin[1].lower() in lowercase_words:
				try:
					sentiment[coin] += sentence.sentiment.polarity
				except:
					sentiment[coin] = sentence.sentiment.polarity
	
	return sentiment, blob.sentiment.polarity

def get_verdict(sentiment, overall):
	"""Use the result from get_sentiment_analysis to determine which coins to buy and
	return an array of coin symbols e.g. ["XVG", "DGB"]"""
	to_buy = [x for x in sentiment.keys() if sentiment[x] >= 0]
	if overall >= 0:
		# Filter out large coins (ideally take out coins in top 10)
		to_buy = [x for x in to_buy if x[0] not in ["BTC", "LTC", "ETH"]]
		return to_buy
	else:
		return []

def analyze(text):
	"""
	1. Extract symbols
	2. Get sentiment analysis
	3. Determine which coins to buy
	"""
	coins = extract_symbols(text)
	sentiment, overall = get_sentiment_analysis(text, coins)
	to_buy = get_verdict(sentiment, overall)

	return to_buy

def telegram_order_callback(coin, amount):
	"""Sends a message with the coin and amount to a telegram bot.
	Parameters:
	- coin (str): The name of the cryptocurrency.
	- amount (float): The amount of the cryptocurrency to be ordered.
	Returns:
	- None: This function does not return any value.
	Processing Logic:
	- Sends a message to a telegram bot.
	- Includes the name of the cryptocurrency.
	- Includes the amount of the cryptocurrency.
	- Example: telegram_order_callback("Bitcoin", 0.5) will send a message to the telegram bot with the text "Bitcoin 0.5"."""
	
	print(coin, amount)

def twitter_tweet_callback(text, user, link):
	""""This function analyzes a tweet and sends a notification to a bot if there are any items to buy mentioned in the tweet."
	Parameters:
	- text (str): The text of the tweet.
	- user (str): The username of the tweet's author.
	- link (str): The link to the tweet.
	Returns:
	- to_buy (list): A list of items mentioned in the tweet that the bot should buy.
	Processing Logic:
	- Analyzes the tweet's text.
	- Sends a notification to the bot if there are items to buy mentioned.
	- Only sends a notification if there is at least one item mentioned.
	- The notification includes the tweet's text, author's username, and link to the tweet."""
	
	to_buy = analyze(text)
	
	if len(to_buy) > 0:
		bot.notify_tweet(text, user, link, to_buy)
    
if __name__ == "__main__":
	# Populate coins
	get_coins_bittrex()
	# Telegram bot
	bot = TelegramBot(order_callback=telegram_order_callback)
	# Twitter stream
	twitter = Twitter(tweet_callback=twitter_tweet_callback)

	while True:
		time.sleep(1)
