from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import LoopingCall

from random import randint
import pygame, math
from pygame.locals import *
from pygame.compat import geterror

###############################################################################

serverPort = 9001


################################################################################
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
        self.size = self.width, self.height = 1000, 720
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)

        self.players = []
        self.projectiles = []
        self.explosions = []

        self.uID = 0

        self.player = Sprite('p')
        self.enemy = Sprite('e')
        self.laser = Sprite('l')
        self.asteroid = Sprite('a')
        self.explosion = Explosion

        self.playerX = randint(75, 725)
        self.playerY = randint(75, 525)

        self.info = ""
        self.pYou = ""
        self.pMouse = ""
        self.pLaser = ""
        self.pRocks = ""

        self.fired = False

    def setID(self, uid):
        self.uID = uid
        print("client id is: " + str(uid))

    def main(self):
        pygame.key.set_repeat(1, 60)
        gameLoop = LoopingCall(self.loop)
        gameLoop.start(1/float(60))

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

            xMouse, yMouse = pygame.mouse.get_pos()
            self.conn.transport.write(self.sendInfo(xMouse, yMouse))

    def movePlayer(self, key):
        if key == pygame.K_LEFT:
            self.playerX -= 6
        elif key == pygame.K_RIGHT:
            self.playerX += 6
        elif key == pygame.K_UP:
            self.playerY -= 6
        elif key == pygame.K_DOWN:
            self.playerY += 6

    def sendInfo(self, x, y):
        self.pYou = str(self.playerX) + "," + str(self.playerY)

        self.pMouse = str(x) + "," + str(y)

        if self.fired:
            self.pLaser = "True"
        else:
            self.pLaser = "False"

        self.info = str(self.uID) + ";" + self.pYou + ";" + self.pMouse + ";" +self.pLaser
        return self.info

    def parseData(self, dataString):
        data = dataString.split("#")

        players = data[0]
        players = players.split(';')
        for player in players:
            playerData = player.split(':')
            if len(playerData) == 5:
                temp = []
                if int(playerData[0]) == self.uID:
                    temp.append('p')
                else:
                    temp.append('e')
                temp.append(int(playerData[1]))
                temp.append(int(playerData[2]))
                temp.append(int(playerData[3]))
                temp.append(int(playerData[4]))
                self.players.append(temp)

        if len(data[1]) > 2:
            projectiles = data[1]
            projectiles = projectiles.split(';')
            for projectile in projectiles:
                projData = projectile.split(':')
                if len(projData) == 4:
                    temp = []
                    temp.append(projData[0])
                    temp.append(int(projData[1]))
                    temp.append(int(projData[2]))
                    temp.append(float(projData[3]))
                    self.projectiles.append(temp)

    def updateDisplay(self, eventString):
        self.parseData(eventString)

        self.screen.fill(self.black)

        for projectile in self.projectiles:
            if projectile[0] == 'a':
                self.asteroid.setRotation(projectile[2])
                self.asteroid.setPosition(projectile[1], projectile[2])
                self.screen.blit(self.asteroid.image, self.asteroid.rect)
            if projectile[0] == 'l':
                self.laser.setPosition(projectile[1], projectile[2])
                self.laser.setRotation(projectile[3])
                self.screen.blit(self.laser.image, self.laser.rect)
            if projectile[0] == 'x':
                self.explosions.append(Explosion((projectile[1], projectile[2]), 50))
                for explosion in self.explosions:
                    if explosion.frame == 16:
                        self.explosions.remove(explosion)
                    else:
                        explosion.update()
                        self.screen.blit(explosion.image, explosion.rect)

        for player in self.players:
            if player[0] == 'p':
                self.player.setPosition(player[1], player[2])
                self.player.setRotation(player[3], player[4])
                self.screen.blit(self.player.image, self.player.rect)
            if player[0] == 'e':
                self.enemy.setPosition(player[1], player[2])
                self.enemy.setRotation(player[3], player[4])
                self.screen.blit(self.enemy.image, self.enemy.rect)

        pygame.display.flip()
        self.projectiles = []
        self.players = []
        # print("data recieved from server, updating")

################################################################################

class Sprite(pygame.sprite.Sprite):
    def __init__(self, sType):
        pygame.sprite.Sprite.__init__(self)

        if sType == 'a':
            self.image, self.rect = load_image('assets/Astroids/astroid.png')
            self.image = pygame.transform.scale(self.image, (200, 200))
        elif sType == 'l':
            self.image, self.rect = load_image('assets/Effects/blueLaser.png')
            self.image = pygame.transform.scale(self.image, (30, 30))
        elif sType == 'p':
            self.image, self.rect = load_image('assets/player.png')
            self.image = pygame.transform.scale(self.image, (75, 75))
        else:
            self.image, self.rect = load_image('assets/enemy.png')
            self.image = pygame.transform.scale(self.image, (75, 75))

        self.unrotatedImage = self.image

    def setPosition(self, X, Y):
        self.rect.centerx = X
        self.rect.centery = Y

    def setRotation(self, X, Y=None):
        if Y != None:
            rotAngle = math.atan2(self.rect.y - Y, X - self.rect.x)
            rotAngle = math.degrees(rotAngle) - 90
        else:
            rotAngle = X

        self.image = pygame.transform.rotate(self.unrotatedImage, rotAngle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.frame = 0

        self.loadFiles()

        self.image = self.explosion_anim[0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.rect.y -= 100
        self.rect.y -= 100

    def loadFiles(self):
        self.explosion_anim = []
        for i in range(15):
            i+=1
            filename = 'assets/Effects/Red_Ex/1_' + str(i) + '.png'
            img = pygame.image.load(filename).convert()
            img.convert_alpha()
            img_lg = pygame.transform.scale(img, (250, 250))
            self.explosion_anim.append(img_lg)

    def update(self):
        self.frame += 1
        if self.frame == len(self.explosion_anim):
            return False
        else:
            center = self.rect.center
            self.image = self.explosion_anim[self.frame]
            self.rect = self.image.get_rect()
            self.rect.center = center

        return True

###############################################################################

class clientFactory(ClientFactory):
    def __init__(self):
        self.connection = dataConnection()

    def buildProtocol(self, addr):
        return self.connection

    def clientConnectionLost(self, connector, reason):
        print('connection lost: ', reason)

    def clientConnectionFailed(self, connector, reason):
        print('connection failed: ', reason)

class dataConnection(Protocol):
    def __init__(self):
        self.space = userSpace(self)

    def connectionMade(self):
        print("data connection established...")

    def dataReceived(self, data):
        # print(data)
        if data[0] == 'p':
            temp = data.split(':')
            uID = int(temp[1][0])
            print('got my uid')
            self.space.setID(uID)
            self.space.main()
            return None
        self.space.updateDisplay(data)

    def sendData(self, data):
        self.transport.write(data)

################################################################################

reactor.connectTCP('localhost', serverPort, clientFactory())
reactor.run()
