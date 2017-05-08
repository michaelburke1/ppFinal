from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

import pygame, math, Queue
from pygame.locals import *
from pygame.compat import geterror

from random import randint

###############################################################################

connectionPort = 9001

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
        self.eventQueue = Queue.Queue()
        self.players = {}
        self.projectiles = []
        self.asteroidCount = 0
        self.clients = {}
        # player = Player(0, 100, 100, 0, 0)
        # self.players[0] = player


    def addClient(self, clientList, pID):
        self.clients = clientList

        player = Player(int(pID), 100, 100, 0, 0)
        self.players[int(pID)] = player

    def main(self):
        gameLoop = LoopingCall(self.loop)
        gameLoop.start(1/float(60))

    def loop(self):
        # for items in event loop
        # pop item -> parse item -> apply action
        while not self.eventQueue.empty():
            print("player event")
            laser = self.parseEvent(self.eventQueue.get())
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
            #asteroid = Projectile(300, 0, 300, 1, 'a')
            asteroid = Projectile(randint(75, 725), randint(75, 525), randint(75, 725), randint(75, 525), 'a')
            self.projectiles.append(asteroid)
            self.asteroidCount += 1

        # for items in game check collisions
        destroyed= []
        for players, objectOne in self.players.items():
            for objectTwo in self.projectiles:
                if objectTwo.parent != objectOne:
                    temp = objectOne.checkCollision(objectTwo)
                    if temp == True:
                        destroyed.append(objectOne)
                        destroyed.append(objectTwo)

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

        for item in destroyed:
            if item in self.projectiles:
                self.projectiles.remove(item)
            else:
                del self.players[item.pId]

        # get object coords -> concat to one big string
        objectString = ""
        for temp, player in self.players.items():
            playerString = str(player.pId) + ':' + str(player.X) + ':' + str(player.Y) + ':' + str(player.mX) + ':' + str(player.mY) + ';'
            objectString += playerString

        objectString += '#'

        for projectile in self.projectiles:
            projectileString = projectile.pType + ':' + str(projectile.rect.x) + ':' + str(projectile.rect.y) + ':' + str(projectile.rotAngle) + ';'
            objectString += projectileString

        # send string to every client
        # print(objectString)
        for client, protocol in self.clients.items():
            if protocol != self:
                protocol.transport.write(objectString.encode('utf-8'))

    def logData(self, eventString):
        self.eventQueue.put(eventString)

    def parseEvent(self, eventString):
        data = eventString.split(';')
        print(data)
        pId = int(data[0])
        pPos = data[1].split(',')
        mPos = data[2].split(',')
        shoot = data[3]
        # print(shoot)

        print(pId)
        # print(self.players)
        self.players[pId].updatePos(int(pPos[0]), int(pPos[1]))
        self.players[pId].updateMouse(int(mPos[0]), int(mPos[1]))

        if 'True' in shoot:
            # print("player fired")
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
        self.image = pygame.transform.scale(self.image, (75, 75))
        self.rect = self.image.get_rect()

    def updatePos(self, newX, newY):
        self.X = newX
        self.Y = newY
        self.rect.x = newX
        self.rect.y = newY

    def updateMouse(self, newX, newY):
        self.mX = newX
        self.mY = newY

    def fire(self, targetX, targetY):
        newLaser = Projectile(self.X, self.Y, targetX, targetY, 'laser', self)
        newLaser.setRotation(targetX, targetY)
        return newLaser

    def checkCollision(self, other):
        if pygame.sprite.collide_rect(self, other):
            return True
        return False

class Projectile(pygame.sprite.Sprite):
    def __init__(self, X, Y, targetX, targetY, pType, parent=None):
        self.speed = 0
        self.pType = 'a'

        self.parent = parent

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
        self.gs = GameSpace()
        self.gs.main()
        self.pID = -1

        # self.connection = dataConnection()

    def startedConnecting(self, connector):
        print 'connection initiated...'

    def buildProtocol(self, addr):
        return dataConnection(self.clients, self)

    def clientConnectionLost(self, connector, reason):
        print 'connection lost: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed: ', reason

class dataConnection(Protocol):

    def __init__(self, users, parent):
        self.users = users
        self.pID = 0
        self.parent = parent

    def connectionMade(self):
        print("client connection established...")
        self.parent.pID += 1
        self.pID = self.parent.pID
        self.transport.write('player ID:' + str(self.pID))
        self.users[self.pID] = self
        self.parent.gs.addClient(self.users, self.pID)

    def dataReceived(self, data):
        # print("data from client: ", data)
        self.parent.gs.logData(data)

###############################################################################

reactor.listenTCP(connectionPort, serverFactory())
reactor.run()
