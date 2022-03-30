import pycspr
from pycspr import NodeClient
from pycspr import NodeConnection
from pycspr.crypto import KeyAlgorithm
import pycspr.types as types
import sys

import requests

#-------
#GETTERS
#-------

def getKeys():
    privateKey = pycspr.parse_private_key("hostkeys/secret_key.pem", KeyAlgorithm.ED25519.name)
    publicKey = pycspr.parse_public_key("hostkeys/public_key_hex")
    return privateKey, publicKey

def getGuestKeys():
    privateKey = pycspr.parse_private_key("guestkeys/secret_key.pem", KeyAlgorithm.ED25519.name)
    publicKey = pycspr.parse_public_key("guestkeys/public_key_hex")
    return privateKey, publicKey

def getContractHash(client, publicKey, key):
    accountInfo = client.get_account_info(publicKey.account_key)
    for namedKey in accountInfo["named_keys"]:
        if namedKey["name"] == key:
            return namedKey["key"][5:]

def publicKeyFromHex(hex):
    return types.PublicKey(KeyAlgorithm(1), bytes.fromhex(hex[2:])) #Need [2:] Because we want to ignore the Key Algorithm identifier "01"

def getStateRootHash(client):
    response = client.get_state_root_hash()
    return response.hex()

def getDictionaryGameState(localClient):
    opponentAccountHashHex = publicKeyFromHex(localClient.opponentPublicKeyHex).account_hash.hex()
    hostHash = localClient.publicKey.account_hash.hex() if localClient.isHost else opponentAccountHashHex
    guestHash = localClient.publicKey.account_hash.hex() if not localClient.isHost else opponentAccountHashHex
    dictionaryID = types.DictionaryID_ContractNamedKey(dictionary_name = hostHash, dictionary_item_key = guestHash, contract_key = localClient.contractHash)
    response = localClient.client.get_dictionary_item(dictionaryID)
    return response.get("stored_value").get("CLValue").get("parsed")



#--------
#BUILDERS
#--------

def makeTurnDeploy(localClient, where):
    params: DeployParameters = pycspr.create_deploy_parameters(account = localClient.privateKey, chain_name = "casper-test")
    payment: ModuleBytes = pycspr.create_standard_payment(int(1e9))
    entryPoint, opponentRole = ("host_move", "guest") if localClient.isHost else ("guest_move", "host") #host_move contract entry point if host, else guest_move entry point. Need to pass "host" or "guest" as player argument, because we'll need both in the contract but the contract can infer the acct hash of the caller

    session = types.StoredContractByHash(
        entry_point=entryPoint,
        hash = bytes.fromhex(localClient.contractHash),
        args = {
            "player_move": types.CL_U8(where),
            opponentRole: types.CL_ByteArray(publicKeyFromHex(localClient.opponentPublicKeyHex).account_hash)
        }
    )

    deploy: Deploy = pycspr.create_deploy(params, payment, session)
    return deploy
