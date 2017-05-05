from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

import pygame
from pygame.locals import *
from pygame.compat import geterror

commandPort = 9001
dataPort    = 9002
class GameSpace:
    def __init__(self, dataPipe):
        self.connection = dataPipe

    def main(self):
        pygame.init()
        self.clock = pygame.time.Clock()

        while True:
            self.clock.tick(1)
            print("in loop")
            self.connection.transport.write("meow")

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
        self.transport.write("hello")
        gs = GameSpace(self)
        gs.main()

    def dataReceived(self, data):
        print("data from client: ", data)

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


reactor.connectTCP("localhost", commandPort, commandFactory())
reactor.run()
