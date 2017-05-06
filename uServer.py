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

connectionPort = 9001
pID = 0

###############################################################################

def load_image(name):
    try:
        image = pygame.image.load(name)
    except:
        print("image loading failure")

    image.convert_alpha
    return image

class GameSpace:
    def __init__(self):
        self.eventQueue = []
        self.players = []
        self.projectiles = []
        self.asteroidCount = 0
        self.clients = None

    def addClient(self, clientList):
        self.clients = clientList

    def main(self):
        # playerOne = Player(0, 100, 100, 0, 0)
        # self.players.append(playerOne)

        gameLoop = LoopingCall(self.loop)
        gameLoop.start(1/float(60))

    def loop(self):
        # for items in event loop
        # pop item -> parse item -> apply action
        for playerAction in self.eventQueue:
            laser = self.parseEvent(self.eventQueue.pop(0))
            if laser != None:
                self.projectiles.append(laser)

        for projectile in self.projectiles:
            if projectile.rect.x > 650 or projectile.rect.y > 850 or projectile.rect.x < -50 or projectile.rect.y < -50:
                self.projectiles.remove(projectile)
                if projectile.pType == 'a':
                    self.asteroidCount -= 1
            else:
                projectile.update()

        if self.asteroidCount < 1:
            asteroid = Projectile(0, 0, 1, 1, 'a')
            self.projectiles.append(asteroid)
            self.asteroidCount += 1

        # for items in game check collisions
        # for objectOne in self.players:
        #     for objectTwo in self.projectiles:
        #         objectOne.checkCollision(objectTwo)

        destroyed= []
        for objectOne in self.projectiles:
            if objectOne not in destroyed:
                for objectTwo in self.projectiles:
                    if objectTwo not in destroyed:
                        temp = None
                        if objectOne != objectTwo:
                            temp = objectOne.checkCollision(objectTwo)
                        if temp == True:
                            destroyed.append(objectOne)
                            destroyed.append(objectTwo)
                            if objectOne.pType == 'a' or objectTwo.pType == 'a':
                                self.asteroidCount -= 1

        for projectile in destroyed:
            self.projectiles.remove(projectile)

        # get object coords -> concat to one big string
        objectString = ""
        for player in self.players:
            playerString = str(player.pId) + ':' + str(player.X) + ':' + str(player.Y) + ':' + str(player.mX) + ':' + str(player.mY) + ';'
            objectString += playerString

        objectString += '#'

        for projectile in self.projectiles:
            projectileString = projectile.pType + ':' + str(projectile.rect.x) + ':' + str(projectile.rect.y) + ':' + str(projectile.rotAngle) + ';'
            objectString += projectileString

        # send string to every client
        for pID, protocol in self.clients.items():
            if protocol != self:
                protocol.transport.write(objectString.encode('utf-8'))

    def logData(self, eventString):
        self.eventQueue.append(eventString)

    def parseEvent(self, eventString):
        data = eventString.split(';')
        pId = int(data[0])
        pPos = data[1].split(',')
        mPos = data[2].split(',')
        shoot = data[3]
        print(shoot)

        self.players[pId].updatePos(int(pPos[0]), int(pPos[1]))
        self.players[pId].updateMouse(int(mPos[0]), int(mPos[1]))

        if shoot == 'True0':
            print("player fired")
            return self.players[pId].fire(int(mPos[0]), int(mPos[1]))

        return None

###############################################################################

class Player(pygame.sprite.Sprite):
    def __init__(self, pId, X, Y, mX, mY):
        self.pId = pId

        self.X = X
        self.Y = Y

        self.mX = mX
        self.mY = mY

        self.image = load_image('assets/player.png')
        self.rect = self.image.get_rect()

    def updatePos(self, newX, newY):
        self.X = newX
        self.Y = newY

    def updateMouse(self, newX, newY):
        self.mX = newX
        self.mY = newY

    def fire(self, targetX, targetY):
        newLaser = Projectile(self.X, self.Y, targetX, targetY, 'laser')
        newLaser.setRotation(targetX, targetY)
        return newLaser

    def checkCollision(self, other):
        if pygame.sprite.collide_rect(self, other):
            return True
        return False

class Projectile(pygame.sprite.Sprite):
    def __init__(self, X, Y, targetX, targetY, pType):
        self.speed = 0
        self.pType = 'a'

        pygame.sprite.Sprite.__init__(self)

        if pType == "a":
            self.image = load_image('assets/Astroids/astroid.png')
            self.image = pygame.transform.scale(self.image, (75, 75))
            self.rect = self.image.get_rect()
            self.speed = randint(2, 4)
            self.pType = 'a'
        else:
            self.image = load_image('assets/Effects/blueLaser.png')
            self.image = pygame.transform.scale(self.image, (30, 30))
            self.rect = self.image.get_rect()
            self.speed = 10
            self.pType = 'l'

        self.rect.x = X + 30
        self.rect.y = Y + 30

        self.rotAngle = 0

        distance = [targetX - X, targetY - Y]
        norm = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
        self.direction = [distance[0] / norm, distance[1] / norm]

    def update(self):
        self.rect.x += (self.direction[0] * self.speed)
        self.rect.y += (self.direction[1] * self.speed)

    def setRotation(self, X, Y):
        rotAngle = math.atan2(self.rect.y - Y, X-self.rect.x)
        self.rotAngle = math.degrees(rotAngle) - 90

    def checkCollision(self, other):
        if pygame.sprite.collide_rect(self, other):
            return True
        return False

###############################################################################

class serverFactory(ClientFactory):
    def __init__(self):
        self.clients = {}
        # self.connection = dataConnection()

    def startedConnecting(self, connector):
        print 'connection initiated...'

    def buildProtocol(self, addr):
        return dataConnection(self.clients)

    def clientConnectionLost(self, connector, reason):
        print 'connection lost: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed: ', reason

class dataConnection(Protocol):

    def __init__(self, users):
        self.users = users
        self.pID = None
        self.gs = GameSpace(self)
        self.gs.main()

    def connectionMade(self):
        print("client connection established...")
        self.transport.write('player ID:' + str(pID))
        self.pID = pID
        self.users[pID] = self
        pID += 1
        gs.addClient(self.users)

    def dataReceived(self, data):
        # print("data from client: ", data)
        self.gs.logData(data)

###############################################################################

reactor.connectTCP("localhost", connectionPort, serverFactory())
reactor.run()
