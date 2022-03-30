import pycspr
from pycspr import NodeClient
from pycspr import NodeConnection
from pycspr.crypto import KeyAlgorithm
import sys
import pycspr.types as types
from pycspr.types import PrivateKey
from pycspr.types import StoredContractByHash, CL_U8, CL_ByteArray
import time

class LocalClient:
    #-----------
    #CONSTRUCTOR
    #-----------

    def __init__(self, isHost, opponentPublicKeyHex):
        self.isHost = isHost
        self.opponentPublicKeyHex = opponentPublicKeyHex
        self.client = NodeClient(NodeConnection(host = "3.208.91.63", port_rpc = 7777))
        self.privateKey, self.publicKey = self.getKeys() if isHost else self.getGuestKeys()
        self.contractHash = "76dbf4629175c0141f144f690bfef42d9d24795b04dd8a3c125c0eba0158df57" #The contract hash of the TicTacToe contract deploy by Casper
        self.gameState = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    #-------
    #SETTERS
    #-------

    def setContractHashFromAccount(self): #Change the contract to a contract owned by yourself or someone else
        self.contractHash = self.getContractHash("tictactoe_contract")


    def makeMove(self, where):
        if where == "q":
            return
        deploy = self.makeTurnDeploy(where)
        deploy.approve(self.privateKey)
        deployHash = self.client.send_deploy(deploy)
        return deployHash


    def setGameState(self):
        try:
            dictState = self.getDictionaryGameState()
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

    #-------
    #GETTERS
    #-------

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

    def getKeys(self):
        privateKey = pycspr.parse_private_key("hostkeys/secret_key.pem", KeyAlgorithm.ED25519.name)
        publicKey = pycspr.parse_public_key("hostkeys/public_key_hex")
        return privateKey, publicKey

    def getGuestKeys(self):
        privateKey = pycspr.parse_private_key("guestkeys/secret_key.pem", KeyAlgorithm.ED25519.name)
        publicKey = pycspr.parse_public_key("guestkeys/public_key_hex")
        return privateKey, publicKey

    def getContractHash(self, key):
        accountInfo = client.get_account_info(self.publicKey.account_key)
        for namedKey in accountInfo["named_keys"]:
            if namedKey["name"] == key:
                return namedKey["key"][5:]

    def publicKeyFromHex(self, hex):
        return types.PublicKey(KeyAlgorithm(1), bytes.fromhex(hex[2:])) #Need [2:] Because we want to ignore the Key Algorithm identifier "01"

    def getDictionaryGameState(self):
        opponentAccountHashHex = self.publicKeyFromHex(self.opponentPublicKeyHex).account_hash.hex()
        hostHash = self.publicKey.account_hash.hex() if self.isHost else opponentAccountHashHex
        guestHash = self.publicKey.account_hash.hex() if not self.isHost else opponentAccountHashHex
        dictionaryID = types.DictionaryID_ContractNamedKey(dictionary_name = hostHash, dictionary_item_key = guestHash, contract_key = self.contractHash)
        response = self.client.get_dictionary_item(dictionaryID)
        return response.get("stored_value").get("CLValue").get("parsed")


    #--------
    #BUILDERS
    #--------

    def makeTurnDeploy(self, where):
        params: DeployParameters = pycspr.create_deploy_parameters(account = self.privateKey, chain_name = "casper-test")
        payment: ModuleBytes = pycspr.create_standard_payment(int(1e9))
        entryPoint, opponentRole = ("host_move", "guest") if self.isHost else ("guest_move", "host") #host_move contract entry point if host, else guest_move entry point. Need to pass "host" or "guest" as player argument, because we'll need both in the contract but the contract can infer the acct hash of the caller

        session = types.StoredContractByHash(
            entry_point=entryPoint,
            hash = bytes.fromhex(self.contractHash),
            args = {
                "player_move": types.CL_U8(where),
                opponentRole: types.CL_ByteArray(self.publicKeyFromHex(self.opponentPublicKeyHex).account_hash)
            }
        )

        deploy: Deploy = pycspr.create_deploy(params, payment, session)
        return deploy
