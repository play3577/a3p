from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *
import engine
import components
import controllers
import particles
import entities
import audio

from direct.gui.DirectGui import *
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText

class GameUI(DirectObject):
	def __init__(self):
		self.localTeam = None
		self.aspectRatio = float(base.win.getProperties().getXSize()) / float(base.win.getProperties().getYSize())
		
		self.crosshairs = []
		self.crosshairs.append(None)
		crosshairFiles = ["images/wide-crosshair.png", "images/narrow-crosshair.png", "images/sniper-crosshair.png"]
		for file in crosshairFiles:
			c = OnscreenImage(image = file, pos = (0, 0, 0), scale = 0.2)
			c.setTransparency(TransparencyAttrib.MAlpha)
			c.setColor(1, 1, 1, 0.5)
			c.setBin("transparent", 0)
			c.hide()
			self.crosshairs.append(c)
		self.currentCrosshair = 1
		
		visitorFont = loader.loadFont("images/visitor2.ttf")
		self.specialReadySound = audio.FlatSound("sounds/special-ready.ogg")
		self.lastSpecialReady = True
		
		self.damageImage = OnscreenImage(image = "images/tunnel-vision.png", pos = (0, 0, 0), scale = (16.0 / 9.0, 0, 1))
		self.damageImage.setTransparency(TransparencyAttrib.MAlpha)
		self.damageImage.hide()
		self.damageImage.setBin("transparent", 0)
		self.damageTransparency = 0.0
		self.lastPlayerHealth = 0
		
		self.teamGroups = []
		self.playerUsernames = []
		self.teams = []
		self.teamScores = []
		font = loader.loadFont("images/DejaVuSans.ttf")

		self.healthBar = StatusBar(range = 100, pos = (-0.25, 0, -0.94), hpr = (0, 0, 90), width = 0.075, height = 0.5)
		
		self.scoreChangeText = OnscreenText(pos = (0, 0.4), scale = 0.5, fg = (1, 1, 1, 0), font = visitorFont, mayChange = True)
		self.scoreChangeTextAlpha = 0.0
		self.scoreChangeTextSize = 0.1
		self.lastTeamScore = 0
		
		self.moneyText = OnscreenText(pos = (-0.26, -0.95), scale = 0.075, align = TextNode.ARight, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = True)
		
		self.specialBar = StatusBar(range = entities.SPECIAL_DELAY, pos = (0.25, 0, -0.94), hpr = (0, 0, 90), width = 0.075, height = 0.2)
		color = Vec3(0.6, 0.6, 0.6)
		self.specialBar.setColors((color.getX() + 0.4, color.getY() + 0.4, color.getZ() + 0.4, 0.5), (color.getX(), color.getY(), color.getZ(), 0.5))
		
		self.ammoText = TextNode("ammoText")
		self.ammoText.setText("")
		self.ammoText.setFont(visitorFont)
		self.ammoText.setTextColor(1, 1, 1, 1)
		self.ammoText.setAlign(TextNode.ACenter)
		self.ammoText.setCardColor(0, 0, 0, 0.7)
		self.ammoText.setCardAsMargin(0.02, 0.02, 0.02, 0.02)
		self.ammoText.setCardDecal(True)
		self.ammoTextNode = render.attachNewNode(self.ammoText)
		self.ammoTextNode.setTwoSided(True)
		self.ammoTextNode.setBin("fixed", 101) # 101 so it's in front of all the MeshDrawer particles.
		self.ammoTextNode.setScale(0.4)
		self.ammoTextNode.hide(BitMask32.bit(4)) # Don't cast shadows
		
		self.healthBars = []
		
		self.cursorX = 0
		self.cursorY = 0
		self.hidden = False
		self.overrideUsernameHide = False
		
		self.chatLog = ChatLog()
	
	def setTeams(self, teams, team):
		self.localTeam = team
		self.teams = teams
		for username in self.playerUsernames:
			username.removeNode()
		del self.playerUsernames[:]
		font = loader.loadFont("images/DejaVuSans.ttf")
		for team in teams:
			text = TextNode("playerId")
			text.setText("")
			text.setFont(font)
			text.setAlign(TextNode.ACenter)
			textNp = render.attachNewNode(text)
			textNp.setBillboardPointEye()
			textNp.setBin("fixed", 101) # 101 so it's in front of all the MeshDrawer particles.
			self.playerUsernames.append(textNp)

		for t in self.teamScores:
			t.delete()
		del self.teamScores[:]
		yOffsets = [-0.96, -0.91, -0.86, -0.81]
		for i in range(len(self.teams)):
			color = self.teams[i].color
			yOffset = yOffsets[i]
			xOffset = -engine.aspectRatio + 0.02
			bar = ScoreBar(range = 100, pos = (xOffset, 0, yOffset), hpr = (0, 0, 90), width = 0.04, height = 0.6)
			bar.setColors(fg = (1, 1, 1, 1), bg = (color.getX(), color.getY(), color.getZ(), 0.5))
			if self.hidden:
				bar.hide()
			self.teamScores.append(bar)

		self.chatLog.setTeam(self.localTeam)
		color = self.localTeam.color
		self.healthBar.setColors((color.getX() + 0.4, color.getY() + 0.4, color.getZ() + 0.4, 0.5), (color.getX(), color.getY(), color.getZ(), 0.5))
	
	def hide(self):
		if self.crosshairs[self.currentCrosshair] != None:
			self.crosshairs[self.currentCrosshair].hide()
		for h in self.healthBars:
			h.hide()
		for t in self.teamScores:
			t.hide()
		self.specialBar.hide()
		self.healthBar.hide()
		self.hideUsernames()
		self.hidden = True
		self.scoreChangeText.hide()
		self.ammoTextNode.hide()
		self.damageImage.hide()
		self.moneyText.hide()
	
	def hideUsernames(self):
		for u in self.playerUsernames:
			u.hide()
	
	def showUsernames(self):
		for u in self.playerUsernames:
			u.show()
	
	def show(self):
		if self.crosshairs[self.currentCrosshair] != None:
			self.crosshairs[self.currentCrosshair].show()
		self.ammoTextNode.show()
		for h in self.healthBars:
			h.show()
		for t in self.teamScores:
			t.show()
		self.showUsernames()
		self.specialBar.show()
		self.healthBar.show()
		self.hidden = False
		self.moneyText.show()
		self.scoreChangeText.show()
		if self.damageTransparency > 0:
			self.damageImage.show()
	
	def setCursorPos(self, x, y):
		self.cursorX = x
		self.cursorY = y
		self.cursorX = min(self.aspectRatio, max(-self.aspectRatio, self.cursorX))
		self.cursorY = min(1, max(-1, self.cursorY))
		self.crosshairs.setPos(self.cursorX, 0, self.cursorY)

	def update(self, scoreLimit):
		if self.hidden or self.localTeam == None:
			return
		
		specialReady = self.localTeam.specialAvailable()
		if specialReady and not self.lastSpecialReady:
			self.specialReadySound.play()
		self.lastSpecialReady = specialReady
		self.specialBar.setValue(max(0, engine.clock.getTime() - self.localTeam.lastSpecialActivated))
		
		allyList = []
		enemyList = []
		for i in range(len(self.teams)):
			team = self.teams[i]
			for bot in (x for x in team.actors if x.spawned and x.active):
				self.droidReloadCrosshair(bot)
				if bot.team.isAlly(self.localTeam):
					allyList.append(bot)
				else:
					enemyList.append(bot)
			player = team.getPlayer()
			self.droidReloadCrosshair(player)
			if team != self.localTeam:
				if player != None and player.active and player.spawned:
					self.playerUsernames[i].node().setTextColor(team.color.getX() + 0.25, team.color.getY() + 0.25, team.color.getZ() + 0.25, 1)
					self.playerUsernames[i].node().setText(player.username)
					self.playerUsernames[i].setPos(player.getPosition() + Vec3(0, 0, player.radius + 0.5))
					self.playerUsernames[i].setScale(pow((camera.getPos() - self.playerUsernames[i].getPos()).length(), 0.5) * 0.15)
					self.playerUsernames[i].show()
				else:
					self.playerUsernames[i].hide()
			else:
				self.playerUsernames[i].hide()

		while len(self.healthBars) < len(allyList):
			self.healthBars.append(UnitStatusBar())
		
		while len(self.healthBars) > len(allyList):
			self.healthBars[0].removeNode()
			del self.healthBars[0]
		
		for i in range(len(allyList)):
			actor = allyList[i]
			self.healthBars[i].show()
			self.healthBars[i].setPos(actor.getPosition() + Vec3(0, 0, actor.radius + 1))
			self.healthBars[i].setValue(actor.health, actor.maxHealth)
			self.healthBars[i].setColor(actor.team.color)
			self.healthBars[i].setScale(pow((camera.getPos() - self.healthBars[i].getPos()).length(), 0.3) * 0.5)

		i = 0
		for t in self.teams:
			self.teamScores[i].setValue(t.score, scoreLimit)
			self.teamScores[i].setUsername(t.username)
			i += 1
		
		self.moneyText.setText("$" + str(self.localTeam.money))
		
		if self.localTeam.score > self.lastTeamScore:
			self.scoreChangeTextAlpha = 1.0
			self.scoreChangeTextScale = 0.04
			sign = ""
			if self.localTeam.score > self.lastTeamScore:
				sign = "+"
			self.scoreChangeText.setText(sign + str(int(self.localTeam.score - self.lastTeamScore)))
		self.lastTeamScore = self.localTeam.score

		if self.scoreChangeTextAlpha > 0.0:
			self.scoreChangeTextAlpha -= engine.clock.timeStep * 0.7
			self.scoreChangeTextScale += engine.clock.timeStep * 0.3
			self.scoreChangeText["fg"] = (1, 1, 1, self.scoreChangeTextAlpha)
			self.scoreChangeText["shadow"] = (0, 0, 0, self.scoreChangeTextAlpha * 0.5)
			self.scoreChangeText["scale"] = self.scoreChangeTextScale

		player = self.localTeam.getPlayer()
		if player != None and player.active:
			if player.controller.targetedEnemy != None and player.controller.targetedEnemy.active:
				particles.EnemySelectorParticleGroup.draw(player.controller.targetedEnemy.getPosition())
			self.healthBar.setValue(player.health, player.maxHealth)
			weapon = player.components[player.controller.activeWeapon]
			if isinstance(weapon, components.Gun) and weapon.selected:
				self.ammoTextNode.setQuat(weapon.node.getQuat())
				self.ammoTextNode.setPos(render.getRelativePoint(weapon.node, Vec3(0.5, 0, 0.5)))
				self.ammoTextNode.setH(self.ammoTextNode.getH() - 15) # Angle the text toward the camera
				self.ammoTextNode.setP(self.ammoTextNode.getP() - 15)
				self.ammoText.setText(str(weapon.ammo))
				val = 1
				if weapon.ammo <= weapon.clipSize * 0.25:
					val = 0
				self.ammoText.setTextColor(1, val, val, 1)
			else:
				self.ammoText.setText("")
			if player.health < self.lastPlayerHealth:
				self.damageTransparency += (self.lastPlayerHealth - player.health) / (.2 * player.maxHealth)
				self.damageTransparency = min(self.damageTransparency, 0.8)
			self.lastPlayerHealth = player.health
			if self.currentCrosshair != player.controller.currentCrosshair:
				if self.crosshairs[self.currentCrosshair] != None:
					self.crosshairs[self.currentCrosshair].hide()
				self.currentCrosshair = player.controller.currentCrosshair
				if self.crosshairs[self.currentCrosshair] != None:
					self.crosshairs[self.currentCrosshair].show()

		if self.damageTransparency > 0.0:
			self.damageImage.show()
			self.damageTransparency -= engine.clock.timeStep * 0.4
			self.damageImage.setColor(1, 1, 1, self.damageTransparency)
		else:
			self.damageImage.hide()
		
		self.chatLog.update()
	
	def droidReloadCrosshair(self, droid):
		if droid != None and droid.active:
			weapon = droid.components[droid.controller.activeWeapon]
			if isinstance(weapon, components.Gun) and weapon.reloadActive:
				particles.CrosshairParticleGroup.draw(droid.getPosition(), engine.clock.getTime() * 80, droid.team.color)

	def delete(self):
		self.crosshairs.destroy()
		self.specialBar.delete()
		self.scoreChangeText.destroy()
		self.moneyText.destroy()
		self.damageImage.destroy()
		self.ammoTextNode.removeNode()
		for h in self.healthBars:
			h.removeNode()
		for t in self.teamScores:
			t.delete()
		for u in self.playerUsernames:
			u.removeNode()
		self.ignoreAll()
		self.chatLog.delete()
		self.healthBar.delete()

class Message:
	def __init__(self, text, time):
		self.text = text
		self.time = time
		
class ChatLog(DirectObject):
	def __init__(self):
		self.localTeam = None
		self.displayTime = 15.0 # Fifteen seconds before chats disappear
		font = loader.loadFont("images/DejaVuSans.ttf")
		self.chatTexts = []
		self.messages = []
		# Chats start at 0 at the bottom and count up
		# Maximum of 8 chats on screen at once
		for i in range(8):
			text = OnscreenText(pos = (-engine.aspectRatio + 0.02, -0.72 + (i * 0.05)), scale = 0.035, align = TextNode.ALeft, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = font, mayChange = True)
			text.setBin("fixed", 200)
			self.chatTexts.append(text)
		self.chatBox = DirectEntry(text = "", entryFont = font, pos = (-engine.aspectRatio + 0.02, 0, -0.77), scale = .035, text_fg = Vec4(1, 1, 1, 1), frameColor = (0, 0, 0, 0.5), width = 35, initialText="", numLines = 1, focus = 0, rolloverSound = None, clickSound = None,)
		self.chatBox.setTransparency(TransparencyAttrib.MAlpha)
		self.chatBox.setBin("fixed", 200)
		self.chatBox.hide()
		self.accept("t", self.focusChat)
		self.accept("chat-incoming", self.displayChat)
		self.accept("chat-outgoing", self.displayChat)
		self.accept("enter", self.submitChat)
		self.hidden = False
	
	def setTeam(self, team):
		self.localTeam = team
	
	def show(self):
		self.hidden = False
		for text in self.chatTexts:
			text.show()
	
	def hide(self):
		self.hidden = True
		self.chatBox.hide()
		for text in self.chatTexts:
			text.hide()
	
	def focusChat(self):
		"Brings focus to the chatbox."
		if self.chatBox.isHidden() and not self.hidden:
			engine.Mouse.showCursor()
			# Show and focus chatbox
			self.chatBox.enterText("")
			self.chatBox.show()
			self.chatBox["focus"] = 1
	
	def submitChat(self):
		if not self.chatBox.isHidden() and not self.hidden:
			# Submit chat message, hide chat box
			username = "Unnamed"
			player = self.localTeam.getPlayer()
			if player != None and player.active:
				username = player.username
			engine.Mouse.hideCursor()
			message = self.chatBox.get()
			if message != "":
				messenger.send("chat-outgoing", [username, message])
			if message[:9] == "changemap":
				messenger.send("change-map", [message[10:]])
			self.chatBox.hide()
			self.chatBox["focus"] = 0
			self.chatBox.enterText("")
		
	def displayChat(self, username, message):
		self.messages.insert(0, Message(username + ": " + message, engine.clock.getTime()))
		self.updateChatLog()
	
	def update(self):
		numMessages = len(self.messages)
		if numMessages > 0:
			message = self.messages[numMessages - 1]
			if engine.clock.getTime() - message.time > self.displayTime:
				del self.messages[numMessages - 1:]
				self.updateChatLog()
	
	def updateChatLog(self):
		self.messages = self.messages[0:len(self.chatTexts)]
		index = 0
		for index in range(len(self.messages)):
			message = self.messages[index]
			self.chatTexts[index].setText(message.text)
		index = len(self.messages)
		while index < len(self.chatTexts):
			self.chatTexts[index].setText("")
			index += 1
	
	def delete(self):
		self.ignoreAll()
		del self.messages[:]
		for text in self.chatTexts:
			text.removeNode()
		self.chatBox.destroy()

class UnitSelectorScreen(DirectObject):
	def __init__(self, startCallback):
		self.types = {
			components.CHAINGUN:("images/chaingun-icon.png", "Chaingun", "High rate of fire. Inaccurate and weak at long ranges. Cheap but less effective than most weapons."),
			components.SHOTGUN:("images/shotgun-icon.png", "Shotgun", "Slow rate of fire. Effective at close range. Holds eight shells."),
			components.SNIPER:("images/sniper-icon.png", "Sniper", "Medium rate of fire. 2X zoom. Infinite range. Capable of one-shot kills. Holds four bullets."),
			components.GRENADE_LAUNCHER:("images/grenade-icon.png", "Grenade", "Very slow rate of fire. Blasts surrounding units and objects away upon detonation. Good area damage."),
			components.PISTOL:("images/pistol-icon.png", "Pistol", "High rate of fire. Medium range. Holds twelve bullets. Capable of pinning enemies to walls."),
			components.MOLOTOV_THROWER:("images/molotov-icon.png", "Molotov", "Very slow rate of fire. Catches nearby enemies on fire, causing lethal damage over time. Good for weakening enemies before switching weapons."),
			controllers.KAMIKAZE_SPECIAL:("images/kamikaze-icon.png", "Kamikaze", "Unleashes a powerful suicidal explosion after a three second delay upon activation."),
			controllers.SHIELD_SPECIAL:("images/shield-icon.png", "Shield", "Permanently decreases ranged damage for one unit by 50%. When activated, shields the whole squad for ten seconds. Useless against fire, grenades, and melee weapons."),
			controllers.CLOAK_SPECIAL:("images/cloak-icon.png", "Cloak", "Permanently cloaks one unit from enemy AI units. When activated, cloaks the whole squad from AI units for ten seconds."),
			controllers.AWESOME_SPECIAL:("images/awesome-icon.png", "Awesome", "Renders one unit invincible for ten seconds upon activation. Also drastically increases movement, firing, and reload speed."),
			controllers.ROCKET_SPECIAL:("images/rocket-icon.png", "Rocket", "Upon activation, launches one unit toward the targeted enemy, causing a devastating explosion upon impact.")
		}
		
		self.startCallback = startCallback
		self.team = None
		self.hidden = False
		self.pressed = False
		self.selectedIcon = None
		self.icons = []
		self.buySlots = []
		self.inventorySlots = []
		self.playerSlots = []
		self.unitSlots = []
		self.purchases = []
		
		self.accept("mouse1", self.click)
		self.accept("mouse1-up", self.release)
		self.accept("mouse3", self.rightClick)
		
		self.container = DirectFrame(frameColor = (0.0, 0.0, 0.0, 0.6), frameSize=(-1.15, 1.15, -0.85, 0.75), pos = (0, 0, 0), sortOrder = -1)
		self.container.setBin("fixed", 0)
		
		# UI elements
		visitorFont = loader.loadFont("images/visitor2.ttf")
		self.balanceText = OnscreenText(parent = self.container, pos = Vec3(1.05, -0.55, 0), text = "$0", align = TextNode.ARight, scale = 0.1, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = True)
		inventoryLabel = OnscreenText(parent = self.container, pos = Vec3(0.7, -0.15, 0), text = "Inventory", align = TextNode.ACenter, scale = 0.07, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = False)
		playerLabel = OnscreenText(parent = self.container, pos = Vec3(-0.8, -0.575, 0), text = "Player", align = TextNode.ACenter, scale = 0.07, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = False)
		unitQLabel = OnscreenText(parent = self.container, pos = Vec3(-0.2, -0.575, 0), text = "Unit Q", align = TextNode.ACenter, scale = 0.07, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = False)
		unitELabel = OnscreenText(parent = self.container, pos = Vec3(0.3, -0.575, 0), text = "Unit E", align = TextNode.ACenter, scale = 0.07, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = False)
		undoButton = DirectButton(parent = self.container, text = "Undo", pos = (0.65, 0, -0.75), relief = DGG.FLAT, text_font = visitorFont, frameSize = (-0.5, 0.5, -.15, .15), frameColor = (0.3, 0.3, 0.3, 1), text_fg = (1, 1, 1, 1), text_scale = 0.3, text_pos = (0, -0.04), scale = 0.2, rolloverSound = None, clickSound = None, command = self.undo)
		startButton = DirectButton(parent = self.container, text = "Start", pos = (0.95, 0, -0.75), relief = DGG.FLAT, text_font = visitorFont, frameSize = (-0.5, 0.5, -.15, .15), frameColor = (0.0, 0.0, 0.0, 1), text_fg = (1, 1, 1, 1), text_scale = 0.3, text_pos = (0, -0.04), scale = 0.35, rolloverSound = None, clickSound = None, command = self.startCallback)
		
		# Info dialog
		self.infoDialog = DirectFrame(sortOrder = 100, frameColor = (0.03, 0.03, 0.03, 1.0), frameSize=(0, 1.05, -0.3, 0.3), pos = (0, 0, 0))
		self.infoDialog.hide()
		self.infoTitle = OnscreenText(pos = Vec3(0.075, 0.2, 0), parent = self.infoDialog, align = TextNode.ALeft, scale = 0.1, fg = (1, 1, 1, 1), font = visitorFont, mayChange = True)
		self.infoCostText = OnscreenText(pos = Vec3(0.97, 0.2, 0), parent = self.infoDialog, align = TextNode.ARight, scale = 0.1, fg = (1, 1, 1, 1), font = visitorFont, mayChange = True)
		dejavuFont = loader.loadFont("images/DejaVuSans.ttf")
		self.infoText = OnscreenText(pos = Vec3(0.075, 0.12, 0), parent = self.infoDialog, wordwrap = 18, align = TextNode.ALeft, scale = 0.05, fg = (1, 1, 1, 1), font = dejavuFont, mayChange = True)
		self.infoPromptText = OnscreenText(pos = Vec3(0.97, -0.24, 0), text = "Click to purchase", parent = self.infoDialog, align = TextNode.ARight, scale = 0.05, fg = (1, 1, 1, 1), font = visitorFont, mayChange = False)
		
		# Buy slots
		
		# Specials
		origin = Vec3(-0.25, 0, 0.6)
		offset = Vec3()
		for i in range(5):
			code = self.types.keys()[i]
			slot = UnitIconSlot(code, UnitIconSlot.AcceptsSpecials, origin + offset, "images/buy-slot.png", self.types[code][1], isSpecial = True)
			self.buySlots.append(slot)
			offset += Vec3(0, 0, -0.2)
			
		# Weapons
		origin = Vec3(-1.0, 0, 0.6)
		offset = Vec3()
		for i in range(5, 11):
			code = self.types.keys()[i]
			slot = UnitIconSlot(code, UnitIconSlot.AcceptsWeapons, origin + offset, "images/buy-slot.png", self.types[code][1], isSpecial = False)
			self.buySlots.append(slot)
			offset += Vec3(0, 0, -0.2)
		
		# Inventory slots
		origin = Vec3(0.4, 0, 0.6)
		for x in range(4):
			for y in range(4):
				slot = UnitIconSlot(-1, UnitIconSlot.AcceptsAny, origin + Vec3(x * 0.2, 0, -y * 0.2))
				self.inventorySlots.append(slot)
		
		# Player slots
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsWeapons, Vec3(-1.0, 0, -0.7), "images/weapon-slot.png")
		self.playerSlots.append(slot)
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsWeapons, Vec3(-0.8, 0, -0.7), "images/weapon-slot.png")
		self.playerSlots.append(slot)
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsSpecials, Vec3(-0.6, 0, -0.7), "images/special-slot.png", isSpecial = True)
		self.playerSlots.append(slot)
		
		# Unit 1 slots
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsWeapons, Vec3(-0.3, 0, -0.7), "images/weapon-slot.png")
		self.unitSlots.append(slot)
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsSpecials, Vec3(-0.1, 0, -0.7), "images/special-slot.png", isSpecial = True)
		self.unitSlots.append(slot)
		
		# Unit 2 slots
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsWeapons, Vec3(0.2, 0, -0.7), "images/weapon-slot.png")
		self.unitSlots.append(slot)
		slot = UnitIconSlot(-1, UnitIconSlot.AcceptsSpecials, Vec3(0.4, 0, -0.7), "images/special-slot.png", isSpecial = True)
		self.unitSlots.append(slot)
		
	
	def rightClick(self):
		if not self.hidden:
			pos = self._getMousePos()
			

	def click(self):
		if not self.hidden:
			self.pressed = True
			pos = self._getMousePos()
			selected = False
			for icon in self.icons:
				if (icon.getPos() - pos).length() < 0.1:
					icon.pickup()
					self.selectedIcon = icon
					selected = True
					break
			if not selected:
				for slot in self.buySlots: # Check if the user is clicking a buy slot
					if slot.icon == None and (slot.getPos() - pos).length() < 0.1:
						if self.team.purchaseItem(slot.type):
							icon = UnitSelectIcon(slot.type, slot.isSpecial, self.types[slot.type][0])
							self.icons.append(icon)
							self.purchases.append(icon)
							icon.drop(slot)
							break
	
	def release(self):
		if self.pressed and self.selectedIcon != None:
			closestSlot = None
			closest = 10
			for slot in (x for x in self.buySlots + self.inventorySlots + self.playerSlots + self.unitSlots if x.icon == None and (x.type == self.selectedIcon.type or x.type == -1)):
				if self.selectedIcon.isSpecial and slot.accepts == UnitIconSlot.AcceptsWeapons:
					continue
				elif not self.selectedIcon.isSpecial and slot.accepts == UnitIconSlot.AcceptsSpecials:
					continue
				dist = (slot.getPos() - self.selectedIcon.getPos()).length()
				if dist < closest:
					closest = dist
					closestSlot = slot
			if closestSlot != None and closest < 0.2:
				self.selectedIcon.drop(closestSlot)
			else:
				self.selectedIcon.drop(self.selectedIcon.lastSlot)
		self.pressed = False
		self.selectedIcon = None
	
	def update(self):
		if not self.hidden:
			if engine.Mouse.enabled:
				engine.Mouse.showCursor()
			pos = self._getMousePos()
			# Determine whether to show info popup
			showInfo = False
			for slot in self.buySlots:
				if (slot.getPos() - pos).length() < 0.1:
					self.infoDialog.setPos(pos + Vec3(0.2, 0, 0))
					self.infoDialog.show()
					self.infoTitle.setText(self.types[slot.type][1])
					cost = entities.TeamEntity.costs[slot.type]
					if cost > self.team.money:
						self.infoCostText["fg"] = (1, 0, 0, 1)
					else:
						self.infoCostText["fg"] = (1, 1, 1, 1)
					self.infoCostText.setText("$" + str(cost))
					self.infoText.setText(self.types[slot.type][2])
					showInfo = True
					break
			if not showInfo:
				self.infoDialog.hide()
			if self.pressed and self.selectedIcon != None:
				self.selectedIcon.image["pos"] = pos
			self.balanceText["text"] = "$" + str(self.team.money)
	
	def _getMousePos(self):
		pointer = base.win.getPointer(0)
		x = pointer.getX()
		y = pointer.getY()
		props = base.win.getProperties()
		width = float(props.getXSize())
		height = float(props.getYSize())
		aspectRatio = width / height
		return Vec3(((float(x) / width) - 0.5) * aspectRatio * 2, 0, (-float(y) / height) * 2.0 + 1.0)
	
	def setTeam(self, team):
		self.team = team

	def show(self):
		self.hidden = False
		engine.Mouse.showCursor()
		for slot in self.buySlots + self.inventorySlots + self.playerSlots + self.unitSlots:
			slot.show()
		self.container.show()
	
	def hide(self):
		self.hidden = True
		engine.Mouse.hideCursor()
		for slot in self.buySlots + self.inventorySlots + self.playerSlots + self.unitSlots:
			slot.hide()
		self.container.hide()
		self.infoDialog.hide()
	
	def reset(self):
		for icon in self.icons:
			icon.delete()
		del self.icons[:]
	
	def clearPurchases(self):
		del self.purchases[:]
	
	def undo(self):
		if len(self.purchases) > 0:
			icon = self.purchases.pop()
			self.team.money += entities.TeamEntity.costs[icon.type]
			self.icons.remove(icon)
			icon.delete()
	
	def disableUnits(self):
		# Permanently deletes the unit selection slots
		for slot in self.unitSlots:
			slot.delete()
		del self.unitSlots[:]
	
	def getUnitWeapons(self):
		return [None if x.icon == None else x.icon.type for x in self.unitSlots if not x.isSpecial]
	
	def getUnitSpecials(self):
		return [None if x.icon == None else x.icon.type for x in self.unitSlots if x.isSpecial]
	
	def getPrimaryWeapon(self):
		icon = self.playerSlots[0].icon
		return None if icon == None else icon.type
	
	def getSecondaryWeapon(self):
		icon = self.playerSlots[1].icon
		return None if icon == None else icon.type
	
	def getSpecial(self):
		icon = self.playerSlots[2].icon
		return None if icon == None else icon.type
	
	def delete(self):
		self.ignoreAll()
		self.container.destroy()
		self.infoDialog.destroy()
		for icon in self.icons:
			icon.delete()
		for slot in self.buySlots + self.inventorySlots + self.playerSlots + self.unitSlots:
			slot.delete()
		del self.icons[:]
		del self.buySlots[:]
		del self.inventorySlots[:]
		del self.playerSlots[:]
		del self.unitSlots[:]

class UnitSelectIcon(DirectObject):
	def __init__(self, type, isSpecial, file):
		self.isSpecial = isSpecial
		self.type = type
		self.image = OnscreenImage(image = file, scale = 0.1)
		self.image.setTransparency(TransparencyAttrib.MAlpha)
		self.slot = None
		self.lastSlot = None
	def pickup(self):
		if self.slot != None:
			self.slot.icon = None
			self.lastSlot = self.slot
			self.slot = None
	def drop(self, slot):
		self.slot = slot
		self.slot.icon = self
		self.setPos(Vec3(slot.getPos()))
	def setPos(self, pos):
		self.image["pos"] = pos
	def getPos(self):
		return self.image["pos"]
	def show(self):
		self.image.show()
	def hide(self):
		self.image.hide()
	def delete(self):
		if self.slot != None:
			self.slot.icon = None
		self.image.destroy()

class UnitIconSlot(DirectObject):
	AcceptsAny = 0
	AcceptsWeapons = 1
	AcceptsSpecials = 2
	def __init__(self, type, accepts, pos, file = "images/slot.png", label = None, isSpecial = False):
		self.accepts = accepts
		self.isSpecial = isSpecial
		self.label = None
		if label != None:
			visitorFont = loader.loadFont("images/visitor2.ttf")
			self.label = OnscreenText(pos = Vec3(pos.getX() + 0.125, pos.getZ(), 0), text = label, align = TextNode.ALeft, scale = 0.075, fg = (1, 1, 1, 1), shadow = (0, 0, 0, 0.5), font = visitorFont, mayChange = False)
		self.type = type
		self.image = OnscreenImage(image = file, pos = pos, scale = 0.1)
		self.image.setTransparency(TransparencyAttrib.MAlpha)
		self.icon = None
	def setPos(self, pos):
		self.image["pos"] = pos
	def getPos(self):
		return self.image["pos"]
	def show(self):
		self.image.show()
		if self.label != None:
			self.label.show()
		if self.icon != None:
			self.icon.show()
	def hide(self):
		self.image.hide()
		if self.label != None:
			self.label.hide()
		if self.icon != None:
			self.icon.hide()
	def delete(self):
		self.image.destroy()

class StatusBar(DirectObject):
	def __init__(self, range, pos, hpr, width, height):
		self.baseNode = NodePath("status-bar")
		self.baseNode.reparentTo(render)
		self.range = float(range)
		self.value = self.range
		cmfg = CardMaker("bar")
		cmfg.setFrame(-width / 2, width / 2, 0, height)
		bar = self.baseNode.attachNewNode(cmfg.generate())
		self.bar = OnscreenGeom(geom = bar, pos = pos, hpr = hpr)
		bar.removeNode()
		self.bar.setTransparency(TransparencyAttrib.MAlpha)

		cmbg = CardMaker("background")
		cmbg.setFrame(-width / 2, width / 2, 0, height)
		background = self.baseNode.attachNewNode(cmbg.generate())
		self.background = OnscreenGeom(geom = background, pos = pos, hpr = hpr)
		background.removeNode()
		self.background.setTransparency(TransparencyAttrib.MAlpha)
	
	def setColors(self, fg, bg):
		self.bar["color"] = fg
		self.background["color"] = bg
	
	def hide(self):
		self.bar.hide()
		self.background.hide()

	def show(self):
		self.bar.show()
		self.background.show()

	def setValue(self, value, range = None):
		self.value = value
		if range != None:
			self.range = float(range)
		self.bar.setScale(1, 1, max(min(float(self.value) / self.range, 1), 0))
	
	def delete(self):
		self.bar.removeNode()
		self.background.removeNode()
		self.baseNode.removeNode()

class ScoreBar(StatusBar):
	def __init__(self, range, pos, hpr, width, height):
		StatusBar.__init__(self, range, pos, hpr, width, height)
		self.usernameText = OnscreenText(pos = (pos[0] + 0.0075, pos[2] - 0.0075, 0), align = TextNode.ALeft, scale = 0.05, fg = (1, 1, 1, 1), font = loader.loadFont("images/visitor2.ttf"), mayChange = True)
	
	def setUsername(self, name):
		self.usernameText.setText(name)
	
	def hide(self):
		StatusBar.hide(self)
		self.usernameText.hide()
	
	def show(self):
		StatusBar.show(self)
		self.usernameText.show()
	
	def delete(self):
		StatusBar.delete(self)
		self.usernameText.destroy()

class StatusBar3D(NodePath): 
	def __init__(self, fg, bg, range):
		NodePath.__init__(self, "status-bar")
		self.reparentTo(render)

		self.range = float(range)
		self.value = self.range

		cmfg = CardMaker("fg")
		cmfg.setFrame(0, 1, -0.1, 0.1)
		self.fg = self.attachNewNode(cmfg.generate())
		self.fg.setPos(-0.5, 0, 0)

		cmbg = CardMaker("bg")
		cmbg.setFrame(-1, 0, -0.1, 0.1)
		self.bg = self.attachNewNode(cmbg.generate())
		self.bg.setPos(0.5, 0, 0)

		self.fg.setColor(fg)
		self.bg.setColor(bg)
		self.fg.setTransparency(TransparencyAttrib.MAlpha)
		self.fg.setTransparency(TransparencyAttrib.MAlpha)

		self.setBillboardPointEye()
		self.setDepthTest(False)
		self.setDepthWrite(False)
		self.setBin("fixed", 101) # 101 so it's in front of all the MeshDrawer particles.

	def setValue(self, value, range = None):
		if range != None:
			self.range = float(range)
		self.value = float(value)
		scale = self.value / self.range
		self.fg.setScale(scale, 1, 1)
		self.bg.setScale(1.0 - scale, 1, 1)

class UnitStatusBar(StatusBar3D):
	def __init__(self):
		StatusBar3D.__init__(self, Vec4(), Vec4(), 100)
		offset = 0
		self.fg.setPos(-0.5 + offset, 0, 0)
		self.bg.setPos(0.5 + offset, 0, 0)
	
	def setColor(self, color):
		self.fg.setColor(Vec4(color.getX() + 0.4, color.getY() + 0.4, color.getZ() + 0.4, 0.5))
		self.bg.setColor(Vec4(color.getX(), color.getY(), color.getZ(), 0.5))

class EditorUI(DirectObject):
	def __init__(self):
		self.mouse = engine.Mouse()
		self.crosshairs = OnscreenImage(image = "images/narrow-crosshair.png", pos = (0, 0, 0), scale = 0.1)
		self.crosshairs.setTransparency(TransparencyAttrib.MAlpha)
		self.crosshairs.setColor(1, 1, 1, 0.7)
		self.crosshairs.setScale(0.3)
		self.crosshairs.setBin("transparent", 0)
		self.cursorX = 0
		self.cursorY = 0
		self.currentPhysicsEntityFile = "block/block"
		font = loader.loadFont("images/DejaVuSans.ttf")
		self.entry = DirectEntry(text = "", entryFont = font, pos = (-engine.aspectRatio + 0.02, 0, -0.77), scale = .035, text_fg = Vec4(1, 1, 1, 1), frameColor = (0, 0, 0, 0.5), width = 35, initialText="", numLines = 1, focus = 0, rolloverSound = None, clickSound = None,)
		self.entry.setTransparency(TransparencyAttrib.MAlpha)
		self.entry.hide()
		self.entry.enterText(self.currentPhysicsEntityFile)
		self.accept("tab", self.toggleTextEntry)

	def update(self):
		self.mouse.update()
		aspectRatio = float(base.win.getProperties().getXSize()) / float(base.win.getProperties().getYSize())
		self.cursorX += self.mouse.getDX()
		self.cursorY += self.mouse.getDY()
		self.cursorX = min(max(self.cursorX, -aspectRatio), aspectRatio)
		self.cursorY = min(max(self.cursorY, -1), 1)
		self.crosshairs.setPos(self.cursorX, 0, self.cursorY)
		
	def delete(self):
		self.crosshairs.removeNode()
		self.ignoreAll()

	def toggleTextEntry(self):
		if self.entry.isHidden():
			self.entry.show()
			self.entry["focus"] = 1
		else:
			self.currentPhysicsEntityFile = self.entry.get()
			self.entry.hide()
			self.entry["focus"] = 0

class Menu(DirectObject):
	def __init__(self):
		visitorFont = loader.loadFont("images/visitor2.ttf")
		self.dialog = DirectFrame(frameColor = (0.0, 0.0, 0.0, 0.6), frameSize=(-.45, .45, -.3375, .3375), pos = (0.8, 0, 0))
		self.postProcessingCheckBox = DirectCheckButton(parent = self.dialog, text = "Post-processing", indicatorValue = engine.enablePostProcessing, pos = (0, 0, 0.225), boxRelief = DGG.FLAT, relief = DGG.FLAT, boxPlacement = "left", text_font = visitorFont, text_fg = (1, 1, 1, 1), text_scale = 2.0, boxImage = ("images/checkbox-disabled.png", "images/checkbox-enabled.png", None), frameColor = (0, 0, 0, 0), scale = 0.04, rolloverSound = None, clickSound = None, command = self.togglePostProcessing)
		self.shadersCheckBox = DirectCheckButton(parent = self.dialog, text = "Shaders", indicatorValue = engine.enableShaders, pos = (0, 0, 0.1), boxRelief = DGG.FLAT, relief = DGG.FLAT, boxPlacement = "left", text_font = visitorFont, text_fg = (1, 1, 1, 1), text_scale = 2.0, boxImage = ("images/checkbox-disabled.png", "images/checkbox-enabled.png", None), frameColor = (0, 0, 0, 0), scale = 0.04, rolloverSound = None, clickSound = None, command = self.toggleShaders)
		self.distortionEffectsCheckBox = DirectCheckButton(parent = self.dialog, text = "Distortion effects", indicatorValue = engine.enableDistortionEffects, pos = (0, 0, -0.025), boxRelief = DGG.FLAT, relief = DGG.FLAT, boxPlacement = "left", text_font = visitorFont, text_fg = (1, 1, 1, 1), text_scale = 2.0, boxImage = ("images/checkbox-disabled.png", "images/checkbox-enabled.png", None), frameColor = (0, 0, 0, 0), scale = 0.04, rolloverSound = None, clickSound = None, command = self.toggleDistortionEffects)
		exitButton = DirectButton(parent = self.dialog, text = "Exit game", pos = (-0.25, 0, -0.25), relief = DGG.FLAT, text_font = visitorFont, frameSize = (-0.75, 0.75, -.15, .15), frameColor = (0.3, 0.3, 0.3, 1), text_fg = (1, 1, 1, 1), text_scale = 0.3, text_pos = (0, -0.04), scale = 0.2, rolloverSound = None, clickSound = None, command = engine.exit)
		resumeButton = DirectButton(parent = self.dialog, text = "Resume", pos = (0.2, 0, -0.25), relief = DGG.FLAT, text_font = visitorFont, frameSize = (-0.5, 0.5, -.15, .15), frameColor = (0.0, 0.0, 0.0, 1), text_fg = (1, 1, 1, 1), text_scale = 0.3, text_pos = (0, -0.04), scale = 0.35, rolloverSound = None, clickSound = None, command = self.toggle)
		self.dialog.hide()
		self.hidden = True
		self.accept("escape-up", self.toggle)
	
	def toggle(self):
		self.hidden = not self.hidden
		if self.hidden:
			self.dialog.hide()
			engine.Mouse.hideCursor()
		else:
			self.dialog.show()
			engine.Mouse.showCursor()

	def togglePostProcessing(self, value):
		engine.enablePostProcessing = value
		engine.postProcessingChanged()

	def toggleShaders(self, value):
		engine.enableShaders = value
		engine.shadersChanged()

	def toggleDistortionEffects(self, value):
		engine.enableDistortionEffects = value
		engine.distortionEffectsChanged()