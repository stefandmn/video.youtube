# -*- coding: utf-8 -*-

import sys
import wrapper
import commons
import modshell
from modshell.utils.FunctionCache import FunctionCache
from modshell.items.DirectoryItem import DirectoryItem
from modshell.items.NextPageItem import NextPageItem
from modshell.items.SearchItem import SearchItem
from modshell.items.VideoItem import VideoItem


class Provider(modshell.AbstractProvider):

	def __init__(self):
		modshell.AbstractProvider.__init__(self)
		pass

	def getAlternativeFanart(self, context):
		return self.getFanart(context)

	def getFanart(self, context):
		return context.createResourcePath('media', 'fanart.jpg')

	def onRoot(self, context, re_match):
		result = []
		context.getFunctionCache().clear()
		item = DirectoryItem(name=context.localize(30001), uri=context.createUri(['category', 'trending']), image=context.createResourcePath('media', 'trending.png'), fanart=self.getFanart(context))
		result.append(item)
		if context.getSettings().getInt("source.count", 0) > 0:
			item = DirectoryItem(name=context.localize(30002), uri=context.createUri(['category', 'channels']), image=context.createResourcePath('media', 'channels.png'), fanart=self.getFanart(context))
			result.append(item)
		item = SearchItem(context=context, name=context.localize(30003), image=context.createResourcePath('media', 'search.png'), fanart=self.getFanart(context))
		result.append(item)
		return result

	def onSearch(self, search_text, context, re_match):
		result = []
		context.setContentType('videos')
		jsondata = context.getFunctionCache().get(FunctionCache.ONE_HOUR, wrapper.get_search, context, search_text)
		page = int(context.getParam('page', 1))
		start = (page - 1) * context.getSettings().getPageSize()
		end = min(start + context.getSettings().getPageSize(), len(jsondata))
		for video in jsondata[start:end]:
			item = None
			if video["type"] == "video":
				item = VideoItem(video["title"], context.createUri(['play'], {'video_id': video["id"]}), image=video["thumb"], fanart=video["thumb"])
			elif video["type"] == "channel":
				item = DirectoryItem(name=video["title"], uri=context.createUri(['channel'], {'channel_id': video['id']}), image=context.createResourcePath('media', 'channel.png'), fanart=video["thumb"])
			elif video["type"] == "playlist":
				item = DirectoryItem(name=video["title"], uri=context.createUri(['playlist'], {'playlist_id': video['id']}), image=context.createResourcePath('media', 'playlist.png'), fanart=video["thumb"])
			if video is not None:
				result.append(item)
		if end < len(jsondata):
			item = NextPageItem(context, page, fanart=self.getFanart(context))
			result.append(item)
		return result

	@modshell.RegisterProviderPath('^/category/trending/$')
	def _category_trending(self, context, re_match):
		result = []
		jsondata = context.getFunctionCache().get(FunctionCache.ONE_HOUR, wrapper.get_trending, context)
		page = int(context.getParam('page', 1))
		start = (page - 1) * context.getSettings().getPageSize()
		end = min(start + context.getSettings().getPageSize(), len(jsondata))
		for video in jsondata[start:end]:
			item = VideoItem(video["title"], context.createUri(['play'], {'video_id': video["id"]}), image=video["thumb"], fanart=video["thumb"])
			result.append(item)
		if end < len(jsondata):
			item = NextPageItem(context, page, fanart=self.getFanart(context))
			result.append(item)
		return result

	@modshell.RegisterProviderPath('^/category/channels/$')
	def _category_channels(self, context, re_match):
		result = []
		jsondata = context.getFunctionCache().get(FunctionCache.ONE_HOUR, wrapper.get_channels, context)
		page = int(context.getParam('page', 1))
		start = (page - 1) * context.getSettings().getPageSize()
		end = min(start + context.getSettings().getPageSize(), len(jsondata))
		for channel in jsondata[start:end]:
			item = DirectoryItem(name=channel["title"], uri=context.createUri(['channel'], {'channel_id': channel['id']}), image=context.createResourcePath('media', 'channel.png'), fanart=context.createResourcePath('media', 'channel.png'))
			result.append(item)
		if end < len(jsondata):
			item = NextPageItem(context, page, fanart=self.getFanart(context))
			result.append(item)
		return result

	@modshell.RegisterProviderPath('^/play/$')
	def _play(self, context, re_match):
		vid = context.getParam('video_id')
		video = wrapper.get_video(context, vid)
		item = VideoItem(video["title"], video["url"], video["thumbnail"])
		item.setDurationFromSeconds(video["duration"])
		item.setPlot(video["description"])
		item.setMediatype('video')
		item.setGenre('Live Stream')
		return item

	@modshell.RegisterProviderPath('^/channel/$')
	def _channel_videos(self, context, re_match):
		result = []
		cid = context.getParam('channel_id')
		jsondata = context.getFunctionCache().get(FunctionCache.ONE_HOUR, wrapper.get_channel_videos, context, cid)
		page = int(context.getParam('page', 1))
		start = (page - 1) * context.getSettings().getPageSize()
		end = min(start + context.getSettings().getPageSize(), len(jsondata))
		for video in jsondata[start:end]:
			item = VideoItem(video["title"], context.createUri(['play'], {'video_id': video["id"]}), image=video["thumb"], fanart=video["thumb"])
			result.append(item)
		if end < len(jsondata):
			item = NextPageItem(context, page, fanart=self.getFanart(context))
			result.append(item)
		return result

	@modshell.RegisterProviderPath('^/playlist/$')
	def _playlist_videos(self, context, re_match):
		result = []
		pid = context.getParam('playlist_id')
		jsondata = context.getFunctionCache().get(FunctionCache.ONE_HOUR, wrapper.get_playlist_videos, context, pid)
		page = int(context.getParam('page', 1))
		start = (page - 1) * context.getSettings().getPageSize()
		end = min(start + context.getSettings().getPageSize(), len(jsondata))
		for video in jsondata[start:end]:
			item = VideoItem(video["title"], context.createUri(['play'], {'video_id': video["id"]}), image=video["thumb"], fanart=video["thumb"])
			result.append(item)
		if end < len(jsondata):
			item = NextPageItem(context, page, fanart=self.getFanart(context))
			result.append(item)
		return result
