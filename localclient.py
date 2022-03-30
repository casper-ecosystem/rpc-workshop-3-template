import pycspr
from pycspr import NodeClient
from pycspr import NodeConnection
import sys
import logic
import pycspr.types as types
from pycspr.types import PrivateKey
from pycspr.types import StoredContractByHash, CL_U8, CL_ByteArray
import time

class LocalClient:
    def __init__(self, isHost, opponentPublicKeyHex):
        self.isHost = isHost
        self.opponentPublicKeyHex = opponentPublicKeyHex
        self.client = NodeClient(NodeConnection(host = "3.208.91.63", port_rpc = 7777))
        self.privateKey, self.publicKey = logic.getKeys() if isHost else logic.getGuestKeys()
        self.contractHash = "76dbf4629175c0141f144f690bfef42d9d24795b04dd8a3c125c0eba0158df57" #The contract hash of the TicTacToe contract deploy by Casper
        self.gameState = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def setContractHashFromAccount(self, thisAccount = True, contractDeployerPublicKeyHex = None): #Change the contract to a contract owned by yourself or someone else
        if thisAccount:
            self.contractHash = logic.getContractHash(self.client, self.publicKey, "tictactoe_contract")
        elif contractDeployerPublicKeyHex != None:
            self.contractHash = logic.getContractHash(self.client, logic.publicKeyFromHex(contractDeployerPublicKeyHex), "tictactoe_contract")
        else:
            print("Error")

    def makeMove(self, where):
        if where == "q":
            return
        deploy = logic.makeTurnDeploy(self, where)
        deploy.approve(self.privateKey)
        deployHash = self.client.send_deploy(deploy)
        return deployHash


    def setGameState(self):
        try:
            dictState = logic.getDictionaryGameState(self)
            if dictState == None:
                print("This game is over");
                exit(0)
            stateIntStr = str(dictState)
            state = [int(stateIntStr[i: i + 2]) for i in range(0, len(stateIntStr), 2)]
            self.gameState = state
        except pycspr.api.connection.NodeAPIError as error:
            if "-32003" in str(error):
                self.gameState = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            else:
                return None

    def hostsTurn(self):
        totalTurns = 0
        for turn in self.gameState:
            if turn != 0:
                totalTurns += 1
        if totalTurns % 2 == 0:
            return True
        return False

    def getMoveDeployStatus(self, deployHash):
        return self.client.get_deploy(deployHash)
