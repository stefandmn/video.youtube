# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import commons
import requests
import youtube_dl
from bs4 import BeautifulSoup
from urlparse import parse_qs, urlparse
from requests.exceptions import ConnectionError


class Logger:

	def debug(self, text):
		commons.debug(text)

	def warning(self, text):
		commons.warn(text)

	def error(self, text):
		commons.error(text)


def get_trending(context):
	key = context.getSettings().getString("youtube.api_key")
	if key is None or key == "":
		region = context.getSettings().getString("youtube.region")
		return _get_trending_html(region)


def _get_trending_html(locale='US'):
	result = []
	try:
		response = requests.get("https://www.youtube.com/feed/trending?gl=%s" %locale)
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
				video["id"] = parse_qs(urlparse(data["href"]).query)['v'][0]
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
				commons.debug("Error extracting video from trending list: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to trending video list: %s" %str(err))
	return result


def get_channels(context):
	result = []
	count = context.getSettings().getInt("source.count", 0)
	for index in range(1, count+1):
		url = context.getSettings().getString("source.url%d" %index, "")
		if url is not None and str(url).strip() != "":
			channel = dict()
			url = url.strip()
			if url.startswith('/'):
				url = "https://www.youtube.com%s" %url
			elif not url.startswith('http://') and not url.startswith('https://'):
				url = "https://www.youtube.com/%s" %url
			response = requests.get(url)
			formatter = BeautifulSoup(response.text, "html.parser")
			data = formatter.find(attrs={"class": "qualified-channel-title-text"}).find("a")
			channel['id'] = str(index)
			channel['title'] = data.text
			result.append(channel)
	return result


def get_channel(context, id):
	result = []
	if (isinstance(id, int) or commons.any2int(id) is not None) and commons.any2int(id) <= context.getSettings().getInt("source.count", 0):
		url = context.getSettings().getString("source.url%d" %commons.any2int(id), "")
	else:
		url = str(id)
	if url is not None and str(url).strip() != "":
		if url.startswith('/channel/'):
			url = "https://www.youtube.com%s" %url
		elif url.startswith('channel/'):
			url = "https://www.youtube.com/%s" %url
		elif url.startswith('/user/'):
			url = "https://www.youtube.com%s" %url
		elif url.startswith('user/'):
			url = "https://www.youtube.com/%s" %url
		elif not url.startswith("http://") and not url.startswith("https://"):
			url = "https://www.youtube.com/channel/%s" %url
		result = _get_channel_videos_html(url)
	return result


def _get_channel_videos_html(url):
	result = []
	if url is not None and (str(url).startswith("http://") or str(url).startswith("https://")):
		if not url.endswith('/videos') and not url.endswith('/videos/'):
			url += "/videos"
		response = requests.get(url)
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
				video["id"] = parse_qs(urlparse(data["href"]).query)['v'][0]
				video["url"] = 'https://www.youtube.com%s' %data["href"]
				video["title"] = data.text
				result.append(video)
			except BaseException as ex:
				commons.debug("Error extracting video from trending list: %s" %str(ex))
	return result


def get_search(context, query):
	key = context.getSettings().getString("youtube.api_key")
	if key is None or key == "":
		return _get_search_html(query)


def _get_search_html(query):
	result = []
	try:
		query = str(query).strip().replace(' ', '+')
		response = requests.get("https://www.youtube.com/results?search_query=%s" %query)
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
				video["title"] = data.text
				video["url"] = 'https://www.youtube.com%s' %data["href"]
				if data["href"].startswith("/watch"):
					video["type"] = "video"
					video["id"] = parse_qs(urlparse(data["href"]).query)['v'][0]
				if data["href"].startswith("/user") or data["href"].startswith("/channel"):
					video["type"] = "channel"
					video["id"] = data["href"]
				data = item.find(attrs={"class": "video-time"})
				if data:
					video["time"] = data.text
				result.append(video)
			except BaseException as ex:
				commons.debug("Error extracting video from search list: %s" %str(ex))
	except ConnectionError as err:
		commons.error("Error connecting to search video list: %s" %str(err))
	return result


def _getargs(context, args):
	_args = {'quiet': True, 'no_warnings': True,
			'format': context.getSettings().getString("youtube.video_quality", "best"),
			'prefer_insecure': context.getSettings().getBool("youtube.prefer_insecure", True),
			'nocheckcertificate': context.getSettings().getBool("youtube.nocheck_certificate", True)}
	if args is not None and isinstance(args, dict):
		_args.update(args)
	_args['logger'] = Logger()
	return _args


def get_video(context, url, args=None):
	_args = _getargs(context, args)
	ydl = youtube_dl.YoutubeDL(_args)
	result = ydl.extract_info(url, download=False)
	if 'entries' in result:
		video = result['entries'][0]
	else:
		video = result
	return video
