
from localclient import LocalClient
import time

#---------
#MAIN GAME
#---------

# _main()

#-------
#POLLERS
#-------

# pollForOurTurn()

# pollForOpponentsTurn()

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
