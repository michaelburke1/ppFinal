from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import LoopingCall

import pygame
from pygame.locals import *
from pygame.compat import geterror

commandPort = 9001
dataPort    = 9002

ID = 0

class userSpace:
    def __init__(self, ID):
        pygame.init()
        self.size = self.width, self.height = 640, 420
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)
        #self.ID = ID

        self.you = Player()
        self.opp = Player()
        self.laser = projectile(LASER)
        self.rock = projectile(ROCK)
        self.info = ""
        self.pYou = ""
        self.pMouse = ""
        self.pLaser = ""
        self.pRocks = ""

        self.fired = False

    def main(self):
        gameLoop = LoopingCall(self.loop)
        gameLoop.start(.5)

    def loop(self):
        if event.type == KEYDOWN:
            self.you.move(event.key)

    def sendInfo(self):
        self.pYou = str(self.you.playerX) + "," + str(self.you.playerY)

        xMouse, yMouse = pygame.mouse.get_pos()
        self.pMouse = str(xMouse) + "," + str(yMouse)

        if self.fired:
            self.pLaser = "True"
        else:
            self.pLaser = "False"

        self.info = str(ID) + ";" + self.pYou + ";" + self.pMouse + ";" +self.pLaser
        return self.info

    def refresh(self, data):
        self.screen.fill(self.black)
        pygame.display.flip()

        print("data recieved from server, updating")

class commandFactory(ClientFactory):
    def __init__(self):
        self.connection = commandConnection()

    def buildProtocol(self, addr):
        return self.connection

class dataFactory(ClientFactory):
    def __init__(self, parent):
        self.connection = dataConnection(parent)

    def buildProtocol(self, addr):
        return self.connection

    def clientConnectionLost(self, connector, reason):
        print('connection lost: ', reason)

    def clientConnectionFailed(self, connector, reason):
        print('connection failed: ', reason)

class commandConnection(Protocol):
    def __init__(self):
        self.connection = dataFactory(self)

    def connectionMade(self):
        print("command connection established...")
        reactor.listenTCP(dataPort, self.connection)
        self.transport.write("Connect to data port 9002\n".encode('utf-8'))

class dataConnection(Protocol):
    def __init__(self, parent):
        self.connection = parent
        self.space = userSpace()

    def connectionMade(self):
        print("data connection established...")

    def dataReceived(self, data):
        self.space.refresh(data)

    def sendData(self):
        self.transport.write(self.space.sendInfo)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.playerX = 0
        self.playerY = 0

    def move(self, k):
        if k == pygame.K_LEFT:
            self.playerX = self.playerX - 5
        elif k == pygame.K_RIGHT:
            self.playerX = self.playerX + 5
        elif k == pygame.K_UP:
            self.playerY = self.playerY - 5
        elif k == pygame.K_DOWN:
            self.playerY = self.playerY + 5

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        xMouse = x
        yMouse = y
################################################################################

reactor.listenTCP(commandPort, commandFactory())
reactor.run()
