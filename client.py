from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import LoopingCall

import pygame
from pygame.locals import *
from pygame.compat import geterror

###############################################################################

commandPort = 9001
dataPort    = 9002

ID = 0

def load_image(name):
    try:
        image = pygame.image.load(name)
    except:
        print("image loading error")

    image.convert_alpha
    return image, image.get_rect()

class userSpace:
    def __init__(self, connection):
        self.conn = connection
        pygame.init()
        self.size = self.width, self.height = 640, 420
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)

        self.players = []
        self.projectiles = []

        self.genericAsteroid = ProjectileSprite('a')
        # self.info = ""
        # self.pYou = ""
        # self.pMouse = ""
        # self.pLaser = ""
        # self.pRocks = ""

        # self.fired = False

    # def main(self):
        # gameLoop = LoopingCall(self.loop)
        # gameLoop.start(.5)

    # def loop(self):
    #     if event.type == KEYDOWN:
    #         self.you.move(event.key)
    #         xMouse, yMouse = pygame.mouse.get_pos()
    #         self.conn.senData(self.sendInfo(xMouse,yMouse))

    #     if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    #         xMouse, yMouse = pygame.mouse.get_pos()
    #         self.fired = true
    #         self.conn.sendData(self.sendInfo(xMouse, yMouse))
    #         self.fired = false

    # def sendInfo(self, x, y):
    #     self.pYou = str(self.players[ID].playerX) + "," + str(self.players[ID].playerY)

    #     #xMouse, yMouse = pygame.mouse.get_pos()
    #     self.pMouse = str(x) + "," + str(y)

    #     if self.fired:
    #         self.pLaser = "True"
    #     else:
    #         self.pLaser = "False"

    #     self.info = str(ID) + ";" + self.pYou + ";" + self.pMouse + ";" +self.pLaser
    #     return self.info

    def parseData(self, dataString):
        data = dataString.split("#")
        players = data[0]
        projectiles = data[1]

        projectiles = projectiles.split(';')
        print(projectiles)
        for projectile in projectiles:
            data = projectile.split(':')
            if len(data) == 3:
                temp = []
                temp.append(data[0])
                temp.append(int(data[1]))
                temp.append(int(data[2]))
                self.projectiles.append(temp)

    def updateDisplay(self, eventString):
        self.parseData(eventString)

        self.screen.fill(self.black)

        for projectile in self.projectiles:
            if projectile[0] == 'a':
                self.genericAsteroid.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.genericAsteroid.image, self.genericAsteroid.rect)

        pygame.display.flip()
        self.projectiles = []
        print("data recieved from server, updating")

################################################################################
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

class ProjectileSprite(pygame.sprite.Sprite):
    def __init__(self, pType):
        pygame.sprite.Sprite.__init__(self)

        if pType == 'a':
            iName = 'asteroid.png'
        else:
            iName = 'laser.png'

        self.image, self.rect = load_image(iName)

    def setPosition(self, X, Y):
        self.rect.x = X
        self.rect.y = Y

###############################################################################

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
        self.space = userSpace(self)

    def connectionMade(self):
        print("data connection established...")

    def dataReceived(self, data):
        print(data)
        self.space.updateDisplay(data)

    def sendData(self, data):
        self.transport.write(data)

################################################################################

reactor.listenTCP(commandPort, commandFactory())
reactor.run()
