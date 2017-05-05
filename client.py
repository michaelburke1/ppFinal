from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

import pygame
from pygame.locals import *
from pygame.compat import geterror

commandPort = 9001
dataPort    = 9002

class meee:
    def __init__(self):
        pygame.init()
        self.size = self.width, self.height = 640, 420
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)

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
        self.meow = meee()

    def connectionMade(self):
        print("data connection established...")

    def dataReceived(self, data):
        self.meow.refresh(data)

################################################################################

reactor.listenTCP(commandPort, commandFactory())
reactor.run()
