## Ready Player Casper Workshop 3 Template
A game of tic-tac-toe playable by two different players via Casper smart contracts.
Expanded to support emitting and subscribing to events.

## Install
```bash
cd ~
git clone https://github.com/casper-ecosystem/rpc-workshop-3-template.git
cd rpc-workshop-3-template
python3 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt
casper-client keygen hostkeys/
casper-client keygen guestkeys/
```
## Fund Accounts
[Import the accounts](https://docs.casperlabs.io/workflow/signer-guide/#3-importing-an-account) in Casper Signer.
Follow [this guide](https://docs.casperlabs.io/workflow/testnet-faucet/) to fund the accounts.

## Compile the Contract
```bash
cd ~/rpc-workshop-3-template/tictactoe_event
make prepare
make build-contract
```

## Deploy the Contract
```bash
cd ~/rpc-workshop-3-template
casper-client put-deploy \
    --node-address http://95.216.67.162:7777/rpc \
    --chain-name casper-test \
    --secret-key hostkeys/secret_key.pem \
    --payment-amount 50000000000 \
    --session-path tictactoe_event/target/wasm32-unknown-unknown/release/tictactoe.wasm
```

## Implement Methods
#### *localclient.py*
* `startEventListener(LocalClient)`
    * Should call `get_events(callback, NodeEventChannel)` on a NodeClient instance.
* `eventReceived(LocalClient, NodeEventInfo)`
    * Should parse `NodeEventInfo` object and react appropriately.
* *Note: See the methods with working functionality [here](https://github.com/casper-ecosystem/rpc-workshop-3/blob/main/localclient.py#L148)*
#### *game.py*
* `_main()`
    * The main entry point of the game. Where the control flow of the game is executed.
* `pollForOurTurn(LocalClient)`
    * Continually checks the game state to wait for the turn of the player, considering their `isHost` value.
* `pollForOpponentsTurn(LocalClient)`
    * Polls for the completion of our turn. When complete, should return `True` when it is the opponent's turn. Should return `False` if our `LocalClient().deployFailed` is `True`.
* *Note: See the methods with working functionality [here](https://github.com/casper-ecosystem/rpc-workshop-3/blob/main/game.py#L9)*

## Play
Play as either the host or guest:
```bash
python3 game.py
```
