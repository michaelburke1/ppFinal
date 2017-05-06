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
        self.size = self.width, self.height = 800, 600
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)

        self.players = []
        self.projectiles = []

        self.player = Sprite('p')
        self.enemy = Sprite('e')
        self.laser = Sprite('l')
        self.asteroid = Sprite('a')

        self.playerX = 100
        self.playerY = 100

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
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                print('keypress caught')
                self.movePlayer(event.key)
                xMouse, yMouse = pygame.mouse.get_pos()
                self.conn.transport.write(self.sendInfo(xMouse, yMouse))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                xMouse, yMouse = pygame.mouse.get_pos()
                self.fired = True
                self.conn.sendData(self.sendInfo(xMouse, yMouse))
                self.fired = False

    def movePlayer(self, key):
        if key == pygame.K_LEFT:
            self.playerX -= 5
        elif key == pygame.K_RIGHT:
            self.playerX += 5
        elif key == pygame.K_UP:
            self.playerY -= 5
        elif key == pygame.K_DOWN:
            self.playerY += 5

    def sendInfo(self, x, y):
        self.pYou = str(self.playerX) + "," + str(self.playerY)

        self.pMouse = str(x) + "," + str(y)

        if self.fired:
            self.pLaser = "True"
        else:
            self.pLaser = "False"

        self.info = str(ID) + ";" + self.pYou + ";" + self.pMouse + ";" +self.pLaser
        return self.info

    def parseData(self, dataString):
        data = dataString.split("#")
        players = data[0]
        projectiles = data[1]

        projectiles = projectiles.split(';')
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
                self.asteroid.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.asteroid.image, self.asteroid.rect)
            if projectile[0] == 'l':
                self.laser.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.laser.image, self.laser.rect)

        for player in self.players:
            if projectile[0] == 'p':
                self.player.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.player.image, self.player.rect)
            if projectile[0] == 'e':
                self.enemy.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.enemy.image, self.enemy.rect)

        pygame.display.flip()
        self.projectiles = []
        # print("data recieved from server, updating")

################################################################################

class Sprite(pygame.sprite.Sprite):
    def __init__(self, sType):
        pygame.sprite.Sprite.__init__(self)

        if sType == 'a':
            self.image, self.rect = load_image('assets/Astroids/astroid.png')
            self.image = pygame.transform.scale(self.image, (75, 75))
        elif sType == 'l':
            self.image, self.rect = load_image('assets/player.png')
            self.image = pygame.transform.scale(self.image, (30, 30))
        elif sType == 'p':
            self.image, self.rect = load_image('assets/player.png')
        else:
            self.image, self.rect = load_image('assets/enemy.png')

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
        self.space.main()

    def dataReceived(self, data):
        # print(data)
        self.space.updateDisplay(data)

    def sendData(self, data):
        self.transport.write(data)

################################################################################

reactor.listenTCP(commandPort, commandFactory())
reactor.run()
