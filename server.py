from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

import pygame, math
from pygame.locals import *
from pygame.compat import geterror

from random import randint

###############################################################################

commandPort = 9001
dataPort    = 9002

###############################################################################

def load_image(name):
    try:
        image = pygame.image.load(name)
    except:
        print("image loading failure")

    # image = image.convert()
    image.convert_alpha
    return image, image.get_rect()

class GameSpace:
    def __init__(self, dataPipe):
        self.connection = dataPipe
        self.eventQueue = []
        self.players = []
        self.projectiles = []

    def main(self):
        myP = Projectile(0, 0, 1, 1, 'a')
        self.projectiles.append(myP)
        gameLoop = LoopingCall(self.loop)
        gameLoop.start(1)

    def loop(self):
        print("performing loop iteration")

        # for items in event loop
        # pop item -> parse item -> apply action
        for playerAction in self.eventQueue:
            laser = self.parseEvent(eventQueue.pop(0))
            if laser:
                self.projectiles.append[laser]

        for projectile in self.projectiles:
            if projectile.rect.x > 700 or projectile.rect.y > 700:
                del self.projectiles[projectile]
            else:
                projectile.update()

        # for items in game check collisions
        for objectOne in self.players:
            for objectTwo in self.projectiles:
                objectOne.checkCollision(objectTwo)

        # get object coords -> concat to one big string
        objectString = ""
        for player in self.players:
            playerString = player.pId + ':' + str(player.X) + ':' + str(player.Y) + ';'
            objectString += playerString

        objectString += '#'

        for projectile in self.projectiles:
            projectileString = projectile.pType + ':' + str(projectile.rect.x) + ':' + str(projectile.rect.y) + ';'
            objectString += projectileString

        # send string to every client
        self.connection.transport.write(objectString.encode('utf-8'))

    def logData(eventString):
        self.eventQueue.append(eventString)

    def parseEvent(eventString):
        data = eventString.split(';')
        pId = data[0]
        pPos = data[1].split(':')
        mPos = data[2].split(':')
        shoot = bool(data[3])

        self.players[pId].updatePos(pPos[0], pPos[1])

        if shoot:
            return self.players[pId].fire(mPos[0], mPos[1])

        return None

###############################################################################

class Player(pygame.sprite.Sprite):
    def __init__(self, pId, X, Y):
        self.pId = pId
        self.X = X
        self.Y = Y

    def updatePos(self, newX, newY):
        self.X = newX
        self.Y = newY

    def fire(self, targetX, targetY):
        newLaser = Projectile(self.X, self.Y, targetX, targetY, 'laser')
        return newLaser

    def checkCollision(self, other):
        if pygame.sprite.collide_rect(self, other):
            self.X = -1
            self.Y = -1

            other.X = -1
            other.Y = -1

class Projectile(pygame.sprite.Sprite):
    def __init__(self, X, Y, targetX, targetY, pType):
        self.speed = 0
        self.pType = 'a'

        pygame.sprite.Sprite.__init__(self)

        if pType == "a":
            iName = 'asteroid.png'
            self.speed = randint(8, 15)
            self.pType = 'a'
        else:
            iName = 'laser.png'
            self.speed = 20
            self.pType = 'l'

        self.image, self.rect = load_image(iName)

        self.rect.x = X + 75
        self.rect.y = Y + 75

        distance = [targetX - X, targetY - Y]
        norm = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
        self.direction = [distance[0] / norm, distance[1] / norm]

    def update(self):
        self.rect.x += (self.direction[0] * self.speed)
        self.rect.y += (self.direction[1] * self.speed)

    def checkCollision(self, other):
        if pygame.sprite.collide_rect(self, other):
            self.rect.x = -1
            self.rect.y = -1

            other.X = -1
            other.Y = -1

###############################################################################

class dataFactory(ClientFactory):
    def __init__(self):
        self.connection = dataConnection()

    def startedConnecting(self, connector):
        print 'connection initiated...'

    def buildProtocol(self, addr):
        return self.connection

    def clientConnectionLost(self, connector, reason):
        print 'connection lost: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed: ', reason

class dataConnection(Protocol):

    def __init__(self):
        print("meow")

    def connectionMade(self):
        print("data connection established...")
        gs = GameSpace(self)
        gs.main()

    def dataReceived(self, data):
        print("data from client: ", data)
        gs.logData(data)

class commandConnection(Protocol):

    def connectionMade(self):
        print "found home client"

    def dataReceived(self, data):
        if data == "Connect to data port 9002\n":
            reactor.connectTCP("localhost", dataPort, dataFactory())

class commandFactory(ClientFactory):
    def __init__(self):
        self.connection = commandConnection()

    def startedConnecting(self, connector):
        print 'connection started...'

    def buildProtocol(self, addr):
        return self.connection

    def clientConnectionLost(self, connector, reason):
        print 'connection lost: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed: ', reason

###############################################################################

reactor.connectTCP("localhost", commandPort, commandFactory())
reactor.run()
