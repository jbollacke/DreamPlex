# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012

https://github.com/DonDavici/DreamPlex

Some of the code is from other plugins:
all credits to the coders :-)

DreamPlex Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

DreamPlex Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
"""
#===============================================================================
# IMPORT
#===============================================================================
#noinspection PyUnresolvedReferences
from enigma import eTimer, ePythonMessagePump, eConsoleAppContainer

from threading import Thread
from threading import Lock
from time import sleep

from Screens.MessageBox import MessageBox
from Tools import Notifications

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap

import urllib

from Screens.Screen import Screen

from Tools.Directories import fileExists

from DP_PlexLibrary import PlexLibrary
from DP_ViewFactory import getMovieViewDefaults
from DPH_Singleton import Singleton
from DPH_ScreenHelper import DPH_ScreenHelper

from __common__ import printl2 as printl, isValidSize, encodeThat
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DPS_Syncer(Screen, DPH_ScreenHelper):

	_session = None
	_mode = None

	def __init__(self, session, mode, serverConfig=None):
		Screen.__init__(self, session)
		DPH_ScreenHelper.__init__(self)

		self.setMenuType("syncer")
		self.serverConfig = serverConfig

		if serverConfig is not None:
			# now that we know the server we establish global plexInstance
			self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self._session, self.serverConfig))

		# we are "sync" or "render"
		self._mode = mode

		# we use the global g_mediaSyncerInfo.instance to take care only having one instance
		self.mediaSyncerInfo = g_mediaSyncerInfo.instance

		self._session = session
		self["output"] = ScrollLabel()
		self["progress"] = Label()

		# we use this counter to reset scorll label every x entries to stay responsive
		self.counter = 0

		self["txt_green"] = Label()
		if self._mode == "sync":
			self["txt_green"].setText(_("Start Sync"))
		else:
			self["txt_green"].setText(_("Start Rendering"))
		self["btn_green"] = Pixmap()

		self["txt_blue"] = Label()
		self["txt_blue"].setText(_("Background"))
		self["btn_blue"] = Pixmap()

		self["txt_red"] = Label()
		self["txt_red"].setText(_("Abort"))
		self["btn_red"] = Pixmap()

		self["setupActions"] = ActionMap(["DPS_Syncer"],
		{
			"red": self.keyRed,
			"blue": self.keyBlue,
			"yellow": self.keyYellow,
			"green": self.keyGreen,
			"bouquet_up": self.keyBouquetUp,
			"bouquet_down": self.keyBouquetDown,
			"cancel": self.exit,
		}, -2)

		self.onFirstExecBegin.append(self.startup)
		self.onShown.append(self.finishLayout)
		self.onClose.append(self.__onClose)

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle("Server - Syncer")

		self.initMiniTv()

		if self._mode == "sync":
			self.mediaSyncerInfo.setPlexInstance(self.plexInstance)
			self.mediaSyncerInfo.setServerConfig(self.serverConfig)

		# first we have to check if we are running in another mode
		isRunning = self.mediaSyncerInfo.isRunning()
		if isRunning:
			currentMode = self.mediaSyncerInfo.getMode()
			printl("currentMode: " +  str(currentMode), self, "D")
			printl("_mode: " + str(self._mode), self, "D")

			if currentMode != self._mode:
				if self._mode == "render":
					text = "Can not start renderer because there is still a syncer running."
				else:
					text = "Can not start syncer because there is still a renderer running."
				self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)
				printl("detected another run of syncer", self, "D")
				self.close()
				return

		printl("self.mediaSyncer: " + str(self.mediaSyncerInfo), self, "D")
		self.mediaSyncerInfo.setCallbacks(self.callback_infos, self.callback_finished, self.callback_progress)
		self.mediaSyncerInfo.setMode(self._mode)

		if self.mediaSyncerInfo.isRunning():
			self["txt_green"].hide()
			self["btn_green"].hide()

		else:
			self["txt_red"].hide()
			self["btn_red"].hide()

			self["txt_blue"].hide()
			self["btn_blue"].hide()

		if self._mode == "render" and not isRunning:
			msg_text = _("Please note to run at least once the sync media function within the server menu.\nThis will download the needed files in the right size of 1280x720.")

		elif self._mode == "sync" and not isRunning:
			msg_text = _("This will download all medias from the selected server.\n\nAdditional to this we download the pictures in 1280x720 for better fullscreen backdrops.")
		else:
			msg_text = _("Reconnecting to background task ...\n")

		self["output"].setText(msg_text)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def __onClose(self):
		printl("", self, "S")

		self.mediaSyncerInfo.setCallbacks(None, None, None)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def startup(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		if self.mediaSyncerInfo.isRunning():
			self.cancel()
			self["txt_green"].show()
			self["btn_green"].show()

			self["txt_blue"].hide()
			self["btn_blue"].hide()

			self["txt_red"].hide()
			self["btn_red"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBlue(self):
		printl("", self, "S")

		if self.mediaSyncerInfo.isRunning():
			self.close(1)
		else:
			self.close(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyGreen(self):
		printl("", self, "S")

		if not self.mediaSyncerInfo.isRunning():
			self.doMediaSync()
			self["txt_blue"].show()
			self["btn_blue"].show()
			self["btn_red"].show()
			self["txt_red"].show()
			self["btn_green"].hide()
			self["txt_green"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBouquetUp(self):
		printl("", self, "S")

		self["output"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBouquetDown(self):
		printl("", self, "S")

		self["output"].pageDown ()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def doMediaSync(self):
		printl("", self, "S")

		self.mediaSyncerInfo.startSyncing()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def callback_infos(self, info):
		printl("", self, "S")

		self.counter += 1

		if self.counter > 100:
			self["output"].setText(info + "\n")
			self.counter = 0
		else:
			self["output"].appendText(info + "\n")

		self["output"].lastPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def callback_progress(self, info):
		printl("", self, "S")

		self["progress"].setText(info)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def callback_finished(self):
		printl("", self, "S")

		self["output"].appendText(_("\n\nFinished"))
		self["txt_blue"].hide()
		self["btn_blue"].hide()

		self["txt_red"].hide()
		self["btn_red"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		self.mediaSyncerInfo.cancel()
		self["output"].appendText(_("\n\nCancelled!"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def exit(self):
		printl("", self, "S")

		if not self.mediaSyncerInfo.isRunning():
			self.close(0)
		else:
			self.session.openWithCallback(self.askForBackground,MessageBox,_("Sync or Renderer is still running!\nContinue in background?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def askForBackground(self, answer):
		printl("", self, "S")

		if answer:
			self.close(1)

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class MediaSyncerInfo(object):
	instance = None

	def __init__(self):
		printl("", self, "S")

		assert not MediaSyncerInfo.instance, "only one MediaSyncerInfo instance is allowed!"
		MediaSyncerInfo.instance = self # set instance
		self.syncer = None
		self.running = False
		self.backgroundMediaSyncer = None

		self.callback_infos = None
		self.callback_finished = None
		self.callback_progress = None
		self.mode = None
		self.serverConfig = None
		self.plexInstance = None

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSyncing(self):
		printl("", self, "S")

		if not self.running:
			self.backgroundMediaSyncer = BackgroundMediaSyncer()
			self.backgroundMediaSyncer.MessagePump.recv_msg.get().append(self.gotThreadMsg)
			self.backgroundMediaSyncer.ProgressPump.recv_msg.get().append(self.gotThreadProgressMsg)
			self.backgroundMediaSyncer.setMode(self.mode)

			if self.mode == "sync":
				self.backgroundMediaSyncer.setServerConfig(self.serverConfig)
				self.backgroundMediaSyncer.setPlexInstance(self.plexInstance)

			self.backgroundMediaSyncer.startSyncing()
			self.running = True

		printl("", self, "C")

	#===========================================================================
	# msg as second params is needed -. do not remove even if it is not used
	# form outside!!!!
	#===========================================================================
	# noinspection PyUnusedLocal
	def gotThreadMsg(self, msg):
		printl("", self, "S")

		msg = self.backgroundMediaSyncer.Message.pop()
		self.infoCallBack(msg[1])

		if msg[0] == THREAD_FINISHED:
			# clean up
			self.backgroundMediaSyncer.MessagePump.recv_msg.get().remove(self.gotThreadMsg)
			self.callback = None
			#self.backgroundMediaSyncer = None # this throws a green screen. dont know why
			self.running = False
			self.done()

		printl("", self, "C")

	#===========================================================================
	# msg as second params is needed -. do not remove even if it is not used
	# form outside!!!!
	#===========================================================================
	# noinspection PyUnusedLocal
	def gotThreadProgressMsg(self, msg):
		printl("", self, "S")

		msg = self.backgroundMediaSyncer.Progress.pop()
		self.progressCallBack(msg[1])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setCallbacks(self, callback_infos, callback_finished, callback_progress):
		printl("", self, "S")

		self.callback_infos = callback_infos
		self.callback_finished = callback_finished
		self.callback_progress = callback_progress

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setMode(self, mode):
		printl("", self, "S")

		self.mode = mode

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getMode(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.mode

	#===========================================================================
	#
	#===========================================================================
	def setServerConfig(self, serverConfig):
		printl("", self, "S")

		self.serverConfig = serverConfig

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setPlexInstance(self, plexInstance):
		printl("", self, "S")

		self.plexInstance = plexInstance

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def isRunning(self):
		printl("", self, "S")

		printl("running: " + str(self.running),self , "D")

		printl("", self, "C")
		return self.running

	#===========================================================================
	#
	#===========================================================================
	def infoCallBack(self,text):
		printl("", self, "S")

		printl("Message: " + str(text), self, "D")
		if text and self.callback_infos:
			self.callback_infos(text)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def progressCallBack(self,text):
		printl("", self, "S")

		printl("Message: " + str(text), self, "D")
		if text and self.callback_progress:
			self.callback_progress(text)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def done(self):
		printl("", self, "S")

		if self.callback_finished is not None:
			printl("callback_finished: " + str(self.callback_finished),self, "D")
			self.callback_finished()

		if self.mode == "render":
			Notifications.AddNotification(MessageBox, _("DreamPlex: Rendering finished!\n"), type=MessageBox.TYPE_INFO, timeout=0)
		else:
			Notifications.AddNotification(MessageBox, _("DreamPlex: Mediasync finished!\n"), type=MessageBox.TYPE_INFO, timeout=0)

		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		if self.backgroundMediaSyncer and self.running:
			self.backgroundMediaSyncer.Cancel()
			self.running = False

		printl("", self, "C")

# !!! important !!!!
# this is a singleton implementation so that there is only one instance of this class
# it can be also imported from other classes with from file import g_mediaSyncerInfo
g_mediaSyncerInfo = MediaSyncerInfo()

#===========================================================================
#
#===========================================================================
class BackgroundMediaSyncer(Thread):

	urllibInstance = None

	def __init__ (self):
		Thread.__init__(self)
		self.cancel = False
		self.arg = None
		self.messages = ThreadQueue()
		self.messagePump = ePythonMessagePump()

		self.progress = ThreadQueue()
		self.progressPump = ePythonMessagePump()

		self.running = False

	#===========================================================================
	#
	#===========================================================================
	def getMessagePump(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.messagePump

	#===========================================================================
	#
	#===========================================================================
	def getMessageQueue(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.messages

	#===========================================================================
	#
	#===========================================================================
	def getProgressPump(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.progressPump

	#===========================================================================
	#
	#===========================================================================
	def getProgressQueue(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.progress

	#===========================================================================
	#
	#===========================================================================
	def setMode(self, mode):
		printl("", self, "S")

		self.mode = mode

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setServerConfig(self, serverConfig):
		printl("", self, "S")

		self.serverConfig = serverConfig

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setPlexInstance(self, plexInstance):
		printl("", self, "S")

		self.plexInstance = plexInstance

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def Cancel(self):
		printl("", self, "S")

		self.cancel = True

		printl("", self, "C")

	#===========================================================================
	#PROPERTIES
	#===========================================================================
	MessagePump = property(getMessagePump)
	Message = property(getMessageQueue)

	ProgressPump = property(getProgressPump)
	Progress = property(getProgressQueue)

	#===========================================================================
	#
	#===========================================================================
	def startSyncing(self):
		printl("", self, "S")

		# Once a thread object is created, its activity must be started by calling the thread’s start() method.
		# This invokes the run() method in a separate thread of control.
		self.start()
		printl("mode: " + str(self.mode), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def run(self):
		printl("", self, "S")

		if self.mode == "render":
			self.renderBackdrops()

		elif self.mode == "sync":
			self.syncMedia()

		else:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def renderBackdrops(self):
		printl("", self, "S")

		from PIL import Image

		self.running = True
		self.cancel = False
		msg_text = _("\n\nStarting to search for picture files with 1280x720 in its name ...")
		self.messages.push((THREAD_WORKING, msg_text))
		self.messagePump.send(0)
		import math
		import glob
		import commands
		#try:
		self.count = len(glob.glob1(config.plugins.dreamplex.mediafolderpath.value,"*1280x720_v2.jpg"))

		msg_text = _("\n\nFiles found: ") + str(self.count)
		self.messages.push((THREAD_WORKING, msg_text))
		self.messagePump.send(0)
		from time import sleep
		sleep(1)

		if int(self.count) > 0:
			self.currentIndex = 0
			for myFile in glob.glob1(config.plugins.dreamplex.mediafolderpath.value,"*1280x720_v2.jpg"):
				sleep(0.2)
				self.currentIndex += 1
				if self.cancel:
					break
				try:
					# firt we check for images in the right size
					if "1280x720_v2.jpg" in myFile:
						# if we got one we remove the .jpg at the end to check if there was a backdropmovie generated already
						myFileWoExtension = myFile[:-4]
						extension = str.upper(myFile[-3:])
						if extension == "JPG":
							extension = "JPEG"
						imageLocationWoExtension = config.plugins.dreamplex.mediafolderpath.value + myFileWoExtension

						# location string
						videoLocation = imageLocationWoExtension + ".m1v"
						# check if backdrop video exists
						if fileExists(videoLocation):
							msg_text = _("backdrop video exists under the location ") + self.getCounter()
							self.messages.push((THREAD_WORKING, msg_text))
							self.messagePump.send(0)
							continue
						else:
							msg_text = _("trying to render backdrop now ...: ") + self.getCounter()
							self.messages.push((THREAD_WORKING, msg_text))
							self.messagePump.send(0)
							imageLocation = config.plugins.dreamplex.mediafolderpath.value + myFile

							i = Image.open(imageLocation)
							data = i.size
							printl("data: " + str(data), self, "D")

							xValid, xResult = isValidSize(i.size[0])
							yValid, yResult = isValidSize(i.size[1])

							printl("xValid: " + str(xValid), self, "D")
							printl("yValid: " + str(yValid), self, "D")

							if not xValid or not yValid:
								xResult = math.ceil(xResult) * 16
								yResult = math.ceil(yResult) * 16
								newSize = (int(xResult), int(yResult))
								resizedImage = i.resize(newSize)
								resizedImage.save(imageLocation, format=extension)

							printl("started rendering : " + str(videoLocation),self, "D")

							cmd = "jpeg2yuv -v 0 -f 25 -n1 -I p -j " + imageLocation + " | mpeg2enc -v 0 -f 12 -x 1280 -y 720 -a 3 -4 1 -2 1 -q 1 -H --level high -o " + videoLocation
							printl("cmd: " + str(cmd), self, "D")

							response = commands.getstatusoutput(cmd)

							if fileExists(videoLocation) and response[0] == 0:
								printl("finished rendering myFile: " + str(myFile),self, "D")
							else:
								printl("File does not exist after rendering!", self, "D")
								printl("Error: " + str(response[1]), self, "D")

								self.messages.push((THREAD_WORKING, _("Error: ") + str(response[1]) ))
								self.messagePump.send(0)

								sleep(1)

								self.running = False
								self.cancel = True
								break

				except Exception, e:
					printl("Error: " + str(e), self, "D")
					self.messages.push((THREAD_WORKING, _("Error!\nError-message:%s" % e) ))
					self.messagePump.send(0)
		else:
			msg_text = _("\n\nNo Files found. Nothing to do!")
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)

			sleep(1)

		if self.cancel:
			self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress Exit to close.") ))
		else:
			self.messages.push((THREAD_FINISHED, _("\n\nWe are done!")))

		self.messagePump.send(0)

		sleep(1)
		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getCounter(self):
		printl("", self, "S")

		printl("", self, "C")
		return "(" + str(self.currentIndex) + "/" + str(self.count) + ") "

	#===========================================================================
	#
	#===========================================================================
	def prepareMediaVariants(self):
		# get params
		params = getMovieViewDefaults()

		b_height = params["elements"]["backdrop"]["height"]
		b_width = params["elements"]["backdrop"]["width"]
		b_postfix = params["elements"]["backdrop"]["postfix"]

		p_height = params["elements"]["poster"]["height"]
		p_width = params["elements"]["poster"]["width"]
		p_postfix = params["elements"]["poster"]["postfix"]

		# we use this for fullsize m1v backdrops that can be loaded to miniTv
		l_height = "720"
		l_width = "1280"
		l_postfix = "_backdrop_1280x720_v2.jpg"

		self.backdropVariants = [[b_height, b_width, b_postfix], [l_height, l_width, l_postfix]]
		self.posterVariants = [[p_height, p_width, p_postfix]]

	#===========================================================================
	#
	#===========================================================================
	def syncMedia(self):
		printl("", self, "S")

		self.running = True
		self.cancel = False
		msg_text = _("\n\nstarting ...")
		self.messages.push((THREAD_WORKING, msg_text))
		self.messagePump.send(0)

		# get sections from server
		self.sectionList = self.plexInstance.getAllSections()
		self.sectionCount=len(self.sectionList)
		printl("sectionList: "+ str(self.sectionList),self, "D")

		# get servername
		self.prefix = self.plexInstance.getServerName().lower()

		# prepare variants
		self.prepareMediaVariants()

		self.movieCount = 0
		self.showCount = 0
		self.seasonCount = 0
		self.episodeCount = 0
		self.artistCount = 0
		self.albumCount = 0

		try:
			msg_text = _("\n\nFetching complete library data. This could take a while ...")
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)

			# in this run we gather only the information
			self.cylceThroughLibrary()

			printl( "sectionCount " + str(self.sectionCount),self, "D")
			printl("movieCount " + str(self.movieCount),self, "D")
			printl("showCount  " + str(self.showCount),self, "D")
			printl("seasonCount " + str(self.seasonCount),self, "D")
			printl("episodeCount " + str(self.episodeCount),self, "D")
			printl("artistCount "  + str(self.artistCount),self, "D")
			printl("albumCount " + str(self.albumCount),self, "D")

			# this run really fetches the data
			self.cylceThroughLibrary(dryRun=False)

			if self.cancel:
				self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress Exit to close.") ))
			else:
				self.messages.push((THREAD_FINISHED, _("We did it :-)")))

		except Exception, e:
			self.messages.push((THREAD_FINISHED, _("Error!\nError-message:%s\nPress Exit to close." % e) ))
		finally:
			self.messagePump.send(0)

		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cylceThroughLibrary(self, dryRun=True):
		printl("", self, "S")

		for section in self.sectionList:
			# interupt if needed
			if self.cancel:
				break

			if self.serverConfig.syncMovies.value:
				if section[2] == "movieEntry":
					printl("movie", self, "D")
					movieUrl = section[3]["contentUrl"]

					if "/all" not in movieUrl:
						movieUrl += "/all"

					printl("movieUrl: " + str(movieUrl), self, "D")
					library, mediaContainer = self.plexInstance.getMoviesFromSection(movieUrl)
					self.movieCount += len(library)

					if not dryRun:
						self.syncThrougMediaLibrary(library, myType="Movie")

			if self.serverConfig.syncShows.value:
				if section[2] == "showEntry":
					printl("show: " + str(section))
					showUrl = section[3]["contentUrl"]\

					if "/all" not in showUrl:
						showUrl += "/all"

					printl("showUrl: " + str(showUrl), self, "D")
					library, mediaContainer = self.plexInstance.getShowsFromSection(showUrl)
					self.showCount += len(library)

					if not dryRun:
						self.syncThrougMediaLibrary(library, myType="Show")

					for seasons in library:
						if self.cancel:
							break
						printl("seasons: " + str(seasons))

						seasonsUrl = seasons[1]["server"] +  seasons[1]["key"]
						printl("seasonsUrl: " + str(seasonsUrl), self, "D")
						library, mediaContainer = self.plexInstance.getSeasonsOfShow(seasonsUrl)
						self.seasonCount += len(library)

						if not dryRun:
							self.syncThrougMediaLibrary(library, myType="Season")

						for episodes in library:
							if self.cancel:
								break
							printl("episode: " + str(episodes))

							episodesUrl = episodes[1]["server"] +  episodes[1]["key"]
							printl("episodesUrl: " + str(episodesUrl), self, "D")
							library, mediaContainer = self.plexInstance.getEpisodesOfSeason(episodesUrl)
							self.episodeCount += len(library)

							if not dryRun:
								self.syncThrougMediaLibrary(library, myType="Episode")

			if self.serverConfig.syncMusic.value:
				if section[2] == "musicEntry":
					printl("music", self, "D")

					# first we go through the artists
					url = section[3]["contentUrl"]\

					if "/all" not in url:
						url += "/all"

					printl("url: " + str(url), self, "D")
					library, mediaContainer = self.plexInstance.getMusicByArtist(url)
					self.artistCount += len(library)
					if not dryRun:
						self.syncThrougMediaLibrary(library, myType="Music")

					# now we go through the albums
					url = section[3]["contentUrl"] + "/albums"

					printl("url: " + str(url), self, "D")
					library, mediaContainer = self.plexInstance.getMusicByAlbum(url)
					self.albumCount += len(library)
					if not dryRun:
						self.syncThrougMediaLibrary(library, myType="Albums")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def syncThrougMediaLibrary(self, library, myType):
		printl("", self, "S")

		for media in library:
			if self.cancel:
				break
			printl("media: " + str(media), self, "D")
			msg_text = "\n" + str(myType) + " with ratingKey: " + str(media[1]["ratingKey"])
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)
			msg_text = _("title: " + encodeThat(media[1]["title"]))
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)

			for variant in self.backdropVariants:
				sleep(0.2)
				# interupt if needed
				if self.cancel:
					break

				t_height = variant[0]
				t_width = variant[1]
				t_postfix = variant[2]

				# location string
				location = config.plugins.dreamplex.mediafolderpath.value + str(self.prefix) + "_" +  str(media[1]["ratingKey"]) + str(t_postfix)

				# check if backdrop exists
				if fileExists(location):
					msg_text = _("found backdrop - size(" + str(t_width) +"x" +str(t_height)+ ")")
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)
					continue
				else:
					if "art" in media[1] and media[1]["art"] != "":
						msg_text = _("backdrop not found, trying to download ...")
						self.messages.push((THREAD_WORKING, msg_text))
						self.messagePump.send(0)
						#download backdrop
						self.downloadMedia(media[1]["art"], location, t_width, t_height)

			for variant in self.posterVariants:
				# interupt if needed
				if self.cancel:
					break

				t_height = variant[0]
				t_width = variant[1]
				t_postfix = variant[2]

				# location string
				location = config.plugins.dreamplex.mediafolderpath.value + str(self.prefix) + "_" +  str(media[1]["ratingKey"]) + str(t_postfix)

				# check if poster exists
				if fileExists(location):
					msg_text = _("found poster - size(" + str(t_width) +"x" +str(t_height)+ ")")
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)
					continue
				else:
					if "thumb" in media[1] and media[1]["thumb"] != "":
						msg_text = _("poster not found, trying to download ...")
						self.messages.push((THREAD_WORKING, msg_text))
						self.messagePump.send(0)
						self.downloadMedia(media[1]["thumb"], location, t_width, t_height)

			self.decreaseQueueCount(myType=myType)

			msg_text = "Movies: " + str(self.movieCount) + "\n" + "Shows: " + str(self.showCount)\
						+ "\n" + "Seasons: " + str(self.seasonCount) + "\n" + "Episodes: " + str(self.episodeCount) \
						+ "\n" + "Artists: " + str(self.artistCount) + "\n" + "Albums: " + str(self.albumCount)
			self.progress.push((THREAD_WORKING, msg_text))
			self.progressPump.send(0)


		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def decreaseQueueCount(self, myType):
		printl("", self, "S")

		if myType == "Movie":
			self.movieCount -= 1

		elif myType == "Show":
			self.showCount -= 1

		elif myType == "Season":
			self.seasonCount -= 1

		elif myType == "Episode":
			self.episodeCount -= 1

		elif myType == "Music":
			self.artistCount -= 1

		elif myType == "Albums":
			self.albumCount -= 1

		else:
			raise Exception


		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadMedia(self, download_url, location, width, height):
		printl("", self, "S")

		download_url = download_url.replace('&width=999&height=999', '&width=' + width + '&height=' + height)
		printl( "download url " + download_url, self, "D")

		if self.urllibInstance is None:
			server = self.plexInstance.getServerFromURL(download_url)
			self.initUrllibInstance(server)

		printl("starting download", self, "D")
		try:
			self.urllibInstance.retrieve(download_url, location)

			msg_text = _("... success")
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)
		except Exception, e:
			printl("download not possible: " + str(e), self, "D")

			msg_text = _("... failed")
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)

		printl("", self, "C")
		return True

	#===========================================================================
	#
	#===========================================================================
	def initUrllibInstance(self, server):
		printl("", self, "S")

		# we establish the connection once here
		self.urllibInstance=urllib.URLopener()

		# we add headers only in special cases
		connectionType = self.serverConfig.connectionType.value
		localAuth = self.serverConfig.localAuth.value

		if connectionType == "2" or localAuth:
			authHeader = self.plexInstance.get_hTokenForServer(server)
			self.urllibInstance.addheader("X-Plex-Token", authHeader["X-Plex-Token"])

		printl("", self, "C")


THREAD_WORKING = 1
THREAD_FINISHED = 2
THREAD_ERROR = 3
#===========================================================================
#
#===========================================================================
class ThreadQueue(object):
	def __init__(self):
		self.__list = [ ]
		self.__lock = Lock()

	#===========================================================================
	#
	#===========================================================================
	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__list.append(val)
		lock.release()

	#===========================================================================
	#
	#===========================================================================
	def pop(self):
		lock = self.__lock
		lock.acquire()
		ret = self.__list.pop()
		lock.release()
		return ret