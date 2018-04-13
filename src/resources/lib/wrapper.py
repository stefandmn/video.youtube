# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import commons
import requests
import youtube_dl
from bs4 import BeautifulSoup
from urlparse import parse_qs, urlparse
from requests.exceptions import ConnectionError


class Logger:
	"""
	Simple logger class for YouTube_DL engine
	"""
	def debug(self, text):
		commons.debug(text)

	def warning(self, text):
		commons.warn(text)

	def error(self, text):
		commons.error(text)


def _get_key(context):
	"""
	Get YouTube key if is enable and defined
	:param context: modshell provider context
	:return: None or string value. If the value is None means that the key is not defined or the option is not activated
	"""
	if context.getSettings().getBool("youtube.use_key", False):
		key = context.getSettings().getString("youtube.api_key")
		if key.strip() != "":
			return key.strip()
		else:
			return None
	else:
		return None


def _getargs(context, args=None):
	"""
	Read and collect YouTube_DL arguments for data operations
	:param context: modshell provider context
	:param args: context arguments defined as dictionary
	:return: the complete dictionary with arguments needed for YouTube_DL data operations (static and also from plugin configuration)
	"""
	_args = {'quiet': True, 'no_warnings': True, 'prefer_insecure': True,
			'format': context.getSettings().getString("youtube.video_quality", "best"),
			'nocheckcertificate': context.getSettings().getBool("youtube.nocheck_certificate", True)}
	if args is not None and isinstance(args, dict):
		_args.update(args)
	_args['logger'] = Logger()
	return _args


def _getcid(url):
	"""
	Detects and returns YouTube channel id from an YouTube URL
	:param url: YouTube URL (might be a complete one or a relative one - just the URI - starting from the context)
	:return: channel id & type (dictionary variable) or None
	"""
	data = ()
	if url is not None and str(url).strip() != "":
		url = url.strip()
		parts = urlparse(url).path.split('/')
		for index in range(0, len(parts)):
			if parts[index] == "channel" and index + 1 < len(parts):
				data = (parts[index + 1], "channel")
				break
			elif parts[index] == "user" and index + 1 < len(parts):
				data = (parts[index + 1], "user")
				break
			index += 1
	return data


def _getvid(url):
	"""
	Detects and returns YouTube video id from an YouTube URL
	:param url: YouTube URL (might be a complete one or a relative one - just the URI - starting from the context)
	:return: video id & type (dictionary variable) or None
	"""
	data = ()
	if url is not None and str(url).strip() != "":
		url = url.strip()
		data = (parse_qs(urlparse(url).query)['v'][0], "video")
	return data


def _getpid(url):
	"""
	Detects and returns YouTube playlist id from an YouTube URL
	:param url: YouTube URL (might be a complete one or a relative one - just the URI - starting from the context)
	:return: playlist id & type (dictionary variable) or None
	"""
	data = ()
	if url is not None and str(url).strip() != "":
		url = url.strip()
		data = (parse_qs(urlparse(url).query)['list'][0], "playlist")
	return data


def get_video(context, url, args=None):
	"""
	Returns the direct URL of the specified video reference
	:param context: modshell provider context
	:param url: video reference on Youtube website
	:param args: preliminary YouTube_DL parsing arguments
	:return: None or the complete URL to the specified video
	"""
	_args = _getargs(context, args)
	ydl = youtube_dl.YoutubeDL(_args)
	result = ydl.extract_info(url, download=False)
	if 'entries' in result:
		video = result['entries'][0]
	else:
		video = result
	return video


def get_trending(context):
	"""
	Get the list of most popular (trending) videos
	:param context: modshell provider context
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	key = _get_key(context)
	region = context.getSettings().getString("youtube.region")
	if key is None:
		return _get_trending_html(region)
	else:
		return _get_trending_api(key, region)


def get_search(context, query):
	"""
	Search videos using query strings
	:param context: modshell provider context
	:param query: string keywords used to search video references
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	key = _get_key(context)
	if key is None:
		return _get_search_html(query)
	else:
		return _get_search_api(key, query)


def get_channels(context):
	"""
	Read list of channels from plugin configuration and returns a complete list of channel sources
	:param context: modshell provider context
	:return: list of source dictionary objects describing user channels or standard video channels
	"""
	sources = []
	key = _get_key(context)
	count = context.getSettings().getInt("source.count", 0)
	for index in range(1, count+1):
		url = context.getSettings().getString("source.url%d" %index, "")
		data = _getcid(url)
		if data:
			item = dict()
			item['id'] = data[0]
			item['type'] = data[1]
			sources.append(item)
	if key is None:
		return _get_channels_html(sources)
	else:
		return _get_channels_api(key, sources)


def get_channel_videos(context, channel):
	"""
	Returns the list of video objects related to a specific channel (channel id)
	:param context: modshell provider context
	:param channel: channel identifier
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	key = _get_key(context)
	if key is None:
		return _get_channel_videos_html(channel)
	else:
		return _get_channel_videos_api(key, channel)


def get_playlist_videos(context, playlist):
	"""
	Returns the list of video objects related to a specific playlist (playlist id)
	:param context: modshell provider context
	:param channel: playlist identifier
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	key = _get_key(context)
	if key is None:
		return _get_playlist_videos_html(playlist)
	else:
		return _get_playlist_videos_api(key, playlist)


def _get_trending_html(locale='US'):
	"""
	Get the list of most popular (trending) videos using HTML website content
	:param context: modshell provider context
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	result = []
	try:
		response = requests.get("https://www.youtube.com/feed/trending?gl=%s" %locale)
		if response is not None and response.status_code == 200:
			formatter = BeautifulSoup(response.text, "html.parser")
			listing = formatter.find_all(attrs={"class": "expanded-shelf-content-item"})
			for item in listing:
				video = dict()
				try:
					data = item.find(attrs={"class": ["yt-thumb", "video-thumb"]}).find(attrs={"class": "yt-thumb-simple"}).find("img")
					if data.get("data-thumb") is not None:
						video["thumb"] = data["data-thumb"]
					else:
						video["thumb"] = data["src"]
					data = item.find(attrs={"class": "yt-lockup-title"}).find("a")
					video["id"] = _getvid(data["href"])[0]
					video["url"] = 'https://www.youtube.com%s' %data["href"]
					video["title"] = data.text
					data = data.select("span.accessible-description")
					if len(data) != 0:
						video["time"] = data[0].text
					else:
						video["time"] = ""
					data = item.find(attrs={"class": "yt-lockup-meta-info"})
					if data and len(data.contents) > 1:
						video["date"] = data.contents[0].string
						video["views"] = data.contents[1].string.split(" ")[0]
					result.append(video)
				except BaseException as ex:
					commons.warn("Error extracting video from trending list: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to trending video list: %s" %str(err))
	return result


def _get_trending_api(apikey, locale='US'):
	"""
	Get the list of most popular (trending) videos using the content provided through Google API
	:param context: modshell provider context
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	url = "https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=%s&maxResults=50&key=%s" %(locale, apikey)
	return _get_datalist_api(url)


def _get_channels_html(sources):
	"""
	Get list of dictionary channels (user and standard) in order to display them and to list the content.
	Channel details are collected from HTML website content
	:param sources: list of dictionary channels that contain only basic details for identification
	:return: list of improved dictionary channels that contain details for displaying and querying
	"""
	result = []
	if sources is not None and isinstance(sources, list):
		for item in sources:
			url = "https://www.youtube.com/%s/%s/videos" %(item['type'], item['id'])
			channel = dict()
			try:
				response = requests.get(url)
				if response is not None and response.status_code == 200:
					formatter = BeautifulSoup(response.text, "html.parser")
					data = formatter.find(attrs={"class": "qualified-channel-title-text"}).find("a")
					channel['title'] = data.text
					channel['id'] = item['id']
					if item['type'] == "user":
						data = formatter.find(attrs={"class": "channel-header-subscription-button-container"}).find("button")
						channel['id'] = data["data-channel-external-id"]
					result.append(channel)
			except BaseException as ex:
				commons.warn("Error preparing channel dictionary: %s" %str(ex))
	return result


def _get_channels_api(apikey, sources):
	"""
	Get list of dictionary channels (user and standard) in order to display them and to list the content.
	Channel details are collected through Google API
	:param sources: list of dictionary channels that contain only basic details for identification
	:return: list of improved dictionary channels that contain details for displaying and querying
	"""
	result = []
	if sources is not None and isinstance(sources, list):
		users = []
		channels = []
		for item in sources:
			if item['type'] == "user":
				users.append(item['id'])
			elif item['type'] == "channel":
				channels.append(item['id'])
		if len(users) > 0:
			data = ','.join(users)
			url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&forUsername=%s&key=%s" %(data, apikey)
			result = _get_datalist_api(url)
		if len(users) > 0:
			data = ','.join(channels)
			url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&id=%s&key=%s" %(data, apikey)
			result = result + _get_datalist_api(url)
	return result


def _get_channel_videos_html(channel):
	result = []
	url = "https://www.youtube.com/channel/%s/videos" %channel
	try:
		response = requests.get(url)
		if response is not None and response.status_code == 200:
			formatter = BeautifulSoup(response.text, "html.parser")
			listing = formatter.find_all(attrs={"class": "channels-content-item"})
			for item in listing:
				video = dict()
				try:
					data = item.find(attrs={"class": "yt-thumb-clip"}).find("img")
					if data.get("data-thumb") is not None:
						video["thumb"] = data["data-thumb"]
					else:
						video["thumb"] = data["src"]
					data = item.find(attrs={"class": "yt-lockup-title"}).find("a")
					video["id"] = _getvid(data["href"])[0]
					video["url"] = 'https://www.youtube.com%s' %data["href"]
					video["title"] = data.text
					result.append(video)
				except BaseException as ex:
					commons.warn("Error extracting video from channel list: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to channel video list: %s" %str(err))
	return result


def _get_channel_videos_api(apikey, channel):
	"""
	Get the list of most popular (trending) videos using the content provided through Google API
	:param context: modshell provider context
	:return: list of video dictionary objects providing many properties for identification and also for playing
	"""
	url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=50&channelId=%s&key=%s" %(channel, apikey)
	return _get_datalist_api(url)


def _get_playlist_videos_html(playlist):
	result = []
	url = "https://www.youtube.com/playlist?list=%s" %playlist
	try:
		response = requests.get(url)
		if response is not None and response.status_code == 200:
			formatter = BeautifulSoup(response.text, "html.parser")
			listing = formatter.find_all(attrs={"class": "pl-video"})
			for item in listing:
				video = dict()
				try:
					data = item.find(attrs={"class": "yt-thumb-clip"}).find("img")
					if data.get("data-thumb") is not None:
						video["thumb"] = data["data-thumb"]
					else:
						video["thumb"] = data["src"]
					data = item.find(attrs={"class": "pl-video-title"}).find("a")
					video["id"] = _getvid(data["href"])[0]
					video["url"] = 'https://www.youtube.com%s' %data["href"]
					video["title"] = data.text.strip()
					result.append(video)
				except BaseException as ex:
					commons.warn("Error extracting video from playlist: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to playlist video list: %s" %str(err))
	return result


def _get_playlist_videos_api(apikey, playlist):
	url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=%s&key=%s" %(playlist, apikey)
	return _get_datalist_api(url)


def _get_search_html(query):
	result = []
	try:
		query = str(query).strip().replace(' ', '+')
		response = requests.get("https://www.youtube.com/results?search_query=%s" %query)
		if response is not None and response.status_code == 200:
			formatter = BeautifulSoup(response.text, "html.parser")
			listing = formatter.find_all(attrs={"class": "yt-lockup"})
			for item in listing:
				video = dict()
				try:
					data = item.find(attrs={"class": "video-thumb"}).find("img")
					if data.get("data-thumb") is not None:
						video["thumb"] = data["data-thumb"]
					else:
						video["thumb"] = data["src"]
					data = item.find(attrs={"class": "yt-lockup-title"}).find("a")
					video["title"] = data.text.strip()
					video["url"] = 'https://www.youtube.com%s' %data["href"]
					if data["href"].startswith("/watch") and data["href"].find("list=") < 0:
						tmpobj = _getvid(data["href"])
						video["type"] = tmpobj[1]
						video["id"] = tmpobj[0]
					elif data["href"].startswith("/user") or data["href"].startswith("/channel"):
						tmpobj = _getcid(data["href"])
						video["type"] = tmpobj[1]
						video["id"] = tmpobj[0]
					elif data["href"].startswith("/playlist") or data["href"].find("list=") >= 0:
						tmpobj = _getpid(data["href"])
						video["type"] = tmpobj[1]
						video["id"] = tmpobj[0]
					data = item.find(attrs={"class": "video-time"})
					if data:
						video["time"] = data.text
					if video.get('type') is not None and video['type'] == "user":
						data = formatter.find(attrs={"class": "yt-uix-subscription-button"})
						video['id'] = data["data-channel-external-id"]
						video["type"] = "channel"
					result.append(video)
				except BaseException as ex:
					commons.warn("Error extracting video from search list: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to search video list: %s" %str(err))
	return result


def _get_search_api(apikey, query):
	query = str(query).strip().replace(' ', '+')
	url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=50&order=relevance&key=%s&q=%s" %(apikey, query)
	return _get_datalist_api(url)


def _get_datalist_api(base):
	result = []
	try:
		pageno = 0
		token = ""
		while token is not None and pageno <= 20:
			if token is not None and token != "":
				url = "%s&pageToken=%s" %(base,token)
			else:
				url = base
			response = requests.get(url)
			if response is not None and response.status_code == 200:
				data = json.loads(response.text)
				if data.get('nextPageToken') is not None:
					token = data['nextPageToken']
					pageno += 1
				else:
					token = None
				if data.get('items') is not None:
					for item in data['items']:
						video = dict()
						try:
							if item['kind'] == "youtube#video":
								video["id"] = item['id']
								video["type"] = "video"
								video["url"] = 'https://www.youtube.com/watch?v=%s' %video["id"]
							elif item['kind'] == "youtube#searchResult":
								if item['id']['kind'] == 'youtube#video':
									video["id"] = item['id']['videoId']
									video["type"] = "video"
									video["url"] = 'https://www.youtube.com/watch?v=%s' %video["id"]
								elif item['id']['kind'] == 'youtube#channel':
									video["id"] = item['id']['channelId']
									video["type"] = "channel"
									video["url"] = 'https://www.youtube.com/channel/%s' %video["id"]
								elif item['id']['kind'] == 'youtube#playlist':
									video["id"] = item['id']['playlistId']
									video["type"] = "playlist"
									video["url"] = 'https://www.youtube.com/playlist?list=%s' %video["id"]
							elif item['kind'] == "youtube#channel":
								video["id"] = item['id']
								video["type"] = "channel"
								video["url"] = 'https://www.youtube.com/channel/%s' %video["id"]
							snippet = item["snippet"]
							video["title"] = snippet['title']
							if item['kind'] == "youtube#playlistItem" and snippet.get('resourceId') is not None:
								if snippet['resourceId']['kind'] == 'youtube#video':
									video["id"] = snippet['resourceId']['videoId']
									video["type"] = "video"
									video["url"] = 'https://www.youtube.com/watch?v=%s' %video["id"]
							if snippet.get('thumbnails') is not None:
								thumbnails = snippet['thumbnails']
								if thumbnails.get('standard') is not None:
									video["thumb"] = thumbnails['standard']['url']
								elif thumbnails.get('high') is not None:
									video["thumb"] = thumbnails['high']['url']
								elif thumbnails.get('medium') is not None:
									video["thumb"] = thumbnails['medium']['url']
								elif thumbnails.get('default') is not None:
									video["thumb"] = thumbnails['default']['url']
							if snippet.get('publishedAt') is not None:
								video["date"] = snippet['publishedAt']
							result.append(video)
						except BaseException as ex:
							commons.warn("Error extracting video from API list: %s" %str(ex))
			else:
				token = None
	except ConnectionError as err:
		commons.error("Error connecting to API video list: %s" %str(err))
	return result
