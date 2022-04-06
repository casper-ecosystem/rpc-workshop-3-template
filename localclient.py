import pycspr
from pycspr import NodeClient
from pycspr import NodeConnection
from pycspr.crypto import KeyAlgorithm
import sys
import pycspr.types as types
from pycspr.types import PrivateKey
from pycspr.types import StoredContractByHash, CL_U8, CL_ByteArray
import time
import json
import threading

class LocalClient:
    #-----------
    #CONSTRUCTOR
    #-----------

    def __init__(self, isHost, opponentPublicKeyHex):
        self.isHost = isHost
        self.opponentPublicKeyHex = opponentPublicKeyHex
        self.client = NodeClient(NodeConnection(host = "3.208.91.63", port_rpc = 7777))
        self.privateKey, self.publicKey = self.getKeys() if isHost else self.getGuestKeys()
        self.contractHash = self.getContractHash("tictactoe_contract")
        self.deployFailed = None
        self.mostRecentDeployHash = None
        self.verbose = False
        self.setGameState()
        threading.Thread(target=self.startEventListener).start()

    def makeMove(self, where):
        if where == "q":
            return
        deploy = self.makeTurnDeploy(where)
        deploy.approve(self.privateKey)
        deployHash = self.client.send_deploy(deploy)
        self.mostRecentDeployHash = deployHash


    def setGameState(self):
        try:
            dictState = self.getDictionaryGameState()
            if dictState == None:
                self.gameState = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                return
            stateIntStr = str(dictState)
            state = [int(stateIntStr[i: i + 2]) for i in range(0, len(stateIntStr), 2)]
            self.gameState = state
        except pycspr.api.connection.NodeAPIError as error:
            if "-32003" in str(error):
                self.gameState = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            else:
                return None

    def reset(self):
        if not self.isHost:
            print("Only the host can reset the board")
            return
        params: DeployParameters = pycspr.create_deploy_parameters(account = self.privateKey, chain_name = "casper-test")
        payment: ModuleBytes = pycspr.create_standard_payment(int(3e9))

        session = types.StoredContractByHash(
            entry_point="reset",
            hash = bytes.fromhex(self.contractHash),
            args = {
                "guest": types.CL_ByteArray(self.publicKeyFromHex(self.opponentPublicKeyHex).account_hash)
            }
        )

        deploy: Deploy = pycspr.create_deploy(params, payment, session)
        return deploy

    #-------
    #GETTERS
    #-------

    def hostsTurn(self):
        totalTurns = 0
        for turn in self.gameState:
            if turn != 0:
                totalTurns += 1
        if totalTurns % 2 == 0: #If total turns is divisible by 2 it is the hosts turn.. think about it !
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
        hash = self.publicKey.account_key if self.isHost else self.publicKeyFromHex(self.opponentPublicKeyHex).account_key
        accountInfo = self.client.get_account_info(hash)
        for namedKey in accountInfo["named_keys"]:
            if namedKey["name"] == key:
                return namedKey["key"][5:]

    def getDictionaryGameState(self):
        opponentAccountHashHex = self.publicKeyFromHex(self.opponentPublicKeyHex).account_hash.hex()
        hostHash = self.publicKey.account_hash.hex() if self.isHost else opponentAccountHashHex
        guestHash = self.publicKey.account_hash.hex() if not self.isHost else opponentAccountHashHex
        dictionaryID = types.DictionaryID_ContractNamedKey(dictionary_name = hostHash, dictionary_item_key = guestHash, contract_key = self.contractHash)
        response = self.client.get_dictionary_item(dictionaryID)
        return response.get("stored_value").get("CLValue").get("parsed")

    def gameStateEmpty(self):
        return self.gameState == [0, 0, 0, 0, 0, 0, 0, 0, 0]

    #--------------
    #PURE FUNCTIONS
    #--------------

    def publicKeyFromHex(self, hex):
        return types.PublicKey(KeyAlgorithm(1), bytes.fromhex(hex[2:])) #Need [2:] Because we want to ignore the Key Algorithm identifier "01"

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

    #------
    #EVENTS
    #------

    def startEventListener(self):
        self.client.get_events(self.eventReceived, pycspr.NodeEventChannel.main)

    def eventReceived(self, event):
        if (event.typeof.name != "DeployProcessed" or event.channel.name != "main" or "DeployProcessed" not in event.payload):
            if self.verbose: print("Event found but not DeployProcessed")
            return #Leave as we only care about "DeployProcessed Events" on the main channel
        if (event.payload["DeployProcessed"]["account"].lower() != self.publicKey.account_key.hex().lower() and event.payload["DeployProcessed"]["account"].lower() != self.opponentPublicKeyHex.lower()):
            if self.verbose: print("DeployProcessed Event found but it's not from the host or guest")
            return #Leave if the deployer was not the host or the guest
        if ("execution_result" not in event.payload["DeployProcessed"]):
            if self.verbose: print("Execution results not found in DeployProcessed (From host or guest)")
            return #Leave if execution result is empty
        if ("Failure" in event.payload["DeployProcessed"]["execution_result"]):
            if event.payload["DeployProcessed"]["account"].lower() == self.publicKey.account_key.hex().lower() and self.mostRecentDeployHash and self.mostRecentDeployHash.lower() == event.payload["DeployProcessed"]["deploy_hash"].lower(): #If this is our deploy, and it failed
                self.deployFailed = True
            return
        if ("Success" not in event.payload["DeployProcessed"]["execution_result"] or "effect" not in event.payload["DeployProcessed"]["execution_result"]["Success"] or "transforms" not in event.payload["DeployProcessed"]["execution_result"]["Success"]["effect"]):
            if self.verbose: print("Deploy JSON not valid")
            return
        transforms = [kt["transform"] for kt in event.payload["DeployProcessed"]["execution_result"]["Success"]["effect"]["transforms"] if kt["key"][:4] == "uref"]

        for transform in transforms:
            if "WriteCLValue" in transform and "parsed" in transform["WriteCLValue"]: #Check so we don't throw an error
                if self.verbose: print(transform)
                hostScore = "0"
                guestScore = "0"
                victor = None
                for kv in transform["WriteCLValue"]["parsed"]: #Multiple entries, just need the event type
                    if kv["key"] == "event_type":
                        if kv["value"] == "HostMove" or kv["value"] == "GuestMove" or kv["value"] == "GameStart":
                            if self.verbose: print("Game state set")
                            self.setGameState()
                        elif kv["value"] == "Draw":
                            victor = "draw"
                        elif kv["value"] == "HostVictory":
                            victor = "host"
                        elif kv["value"] == "GuestVictory":
                            victor = "guest"
                    elif kv["key"] == "host_score":
                        hostScore = kv["value"]
                    elif kv["key"] == "guest_score":
                        guestScore = kv["value"]
                if victor:
                    if victor == "draw":
                        print("This game has ended in a draw")

                    print("This game has been won by the " + victor + ".")
                    print("The host now has a cumulative score of " + hostScore)
                    print("The guest now has a cumulative score of " + guestScore)
                    self.gameOn = False
