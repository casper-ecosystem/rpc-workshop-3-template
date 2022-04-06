
from localclient import LocalClient
import time

#---------
#MAIN GAME
#---------

def _main():
	localClient = LocalClient(getIsHost(), getOpponentPublicKey()) #Build LocalClient from player-provided isHost and opponentPublicKeyHex
	if localClient.gameStateEmpty(): printGuide() #If the game state is empty it's a new game and we print the guide

	localClient.gameOn = True
	while localClient.gameOn:
		hostsTurn = localClient.hostsTurn()
		if hostsTurn and not localClient.isHost: print("Waiting for host...")
		elif not hostsTurn and localClient.isHost: print("Waiting for guest...")

		if not pollForOurTurn(localClient): #Takes no time if it's our turn, waits otherwise. If returns False game is over
			print("Do you want to play again?[Y|n]: ")
			if getYn(): #If "y" then set gameOn == True and continue back
				localClient.gameOn = True
				continue
		printBoard(localClient.gameState)
		printMakeMove(localClient.isHost)

		move = getMove() #Ask player for move-input
		if move == None: exit(0) #Move will == None if user enters "q"
		localClient.makeMove(move) #Make move
		print("Waiting for execution...")
		while not pollForOpponentsTurn(localClient): #Takes no time if it's the opponent's turn, waits otherwise. Returns false and opens the loop if the deploy fails
			print("Deploy failed, please try again.")
			move = getMove()
			if move == None: exit(0)
			localClient.makeMove(move)
			print("Waiting for execution...")
		if not localClient.gameOn:
			print("Do you want to play again?[Y|n]: ")
			localClient.gameOn = getYn() #If "y" then gameOn is True and the while loop continues, otherwise game ends
	print("Thanks for playing!")

#-------
#POLLERS
#-------
""" DEPRECATED
def pollDeployStatus(localClient, deployHash):
	deployStatus = localClient.getMoveDeployStatus(deployHash)
	while deployStatus.get("execution_results") == None:
		time.sleep(2)
	executionResults = deployStatus.get("execution_results")
	while len(executionResults) == 0:
		time.sleep(2)
		executionResults = localClient.getMoveDeployStatus(deployHash).get("execution_results")
	result = executionResults[0].get("result")
	if result.get("Failure") != None:
		return False
	elif result.get("Success") != None:
		return True
	return None
"""

def pollForOurTurn(localClient):
	while (not localClient.hostsTurn() if localClient.isHost else localClient.hostsTurn()): #If we're the host, run the loop while it's not their turn, and vice versa
		if not localClient.gameOn: #Game has ended
			return False
		time.sleep(2)
	return True

def pollForOpponentsTurn(localClient):
	while (localClient.hostsTurn() if localClient.isHost else not localClient.hostsTurn()): #If we're the host, run the loop while it's not their turn, and vice versa
		if localClient.deployFailed:
			localClient.deployFailed = None
			return False
		if not localClient.gameOn: #Game has ended
			return True
		time.sleep(2)
	return True

#-------
#WAITERS
#-------
""" DEPRECATED
def waitForGuest(localClient, hostsTurn):
	while not hostsTurn:
		time.sleep(2)
		localClient.setGameState()
		hostsTurn = localClient.hostsTurn()

def waitForHost(localClient, hostsTurn):
	while hostsTurn:
		time.sleep(2)
		localClient.setGameState()
		hostsTurn = localClient.hostsTurn()
"""

#--------
#PRINTERS
#--------

def printGuide():
	print()
	board = [0, 1, 2, 3, 4, 5, 6, 7, 8]
	for i in range(len(board)):
		if (i + 1) % 3 == 0:
			print(i)
			if not i + 1 == len(board): #Dont print "---------" on last row
				print("-" * 9)
		else:
			print(str(i) + " | ", end = "")

	print()
	print("Use the guide above to make a move. Enter q at any time to quit")

def printBoard(gameState):
	print()
	for i in range(len(gameState)):
		ch = charFromTurn(gameState[i])
		if (i + 1) % 3 == 0:
			print(ch)
			if not i + 1 == len(gameState): #Dont print "---------" on last row
				print("-" * 9)
		else:
			print(ch + " | ", end = "")

def printMakeMove(isHost):
	mym = ", make your move"
	if isHost:
		print("X" + mym)
	else:
		print("O" + mym)

def charFromTurn(turn):
	if turn == 0:
		return " "
	elif turn == 1:
		return "X"
	elif turn == 2:
		return "O"
	else:
		return " "

#----------
#USER INPUT
#----------

def getIsHost():
	try:
		inp = input("Are you the host? (1) or the guest (0): ")
		if inp == "q":
			exit(0)
		x = int(inp)
		if x > 1 or x < 0:
			raise
		return bool(x)
	except:
		print("Error parsing input")
		return getIsHost()

def getOpponentPublicKey():
	print("Please paste in your opponent's public key")
	try:
		pubkey = input(":")
		if pubkey == "q":
			exit(0)
		return pubkey
	except:
		print("Error reading public key.")
		return getOpponentPublicKey()

def getMove():
	try:
		inp = input("Make a move: ")
		if inp == "q":
			return
		x = int(inp)
		if x > 8 or x < 0:
			raise
		return x
	except:
		print("Error parsing move")
		return getMove()

def getYn():
	try:
		inp = input("")
		if inp == "q" or inp.lower() == "n":
			return False
		if inp.lower() == "y" :
			return True
		raise
	except:
		print("Error parsing yes/no")
		return getYn()

_main() #Entry point
