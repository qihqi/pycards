
## API

### POST /game 

Creates new game. Returns game id.

### GET /game/\<game_id\> gets the game metadata / status

### PUT /game/\<game_id\> add new player

### POST /game/\<game_id\>/player/name/draw

### POST /game/\<game_id\>/player/name/play


Ideas
====

* Game has:
  = n players,
	  every player have a name and a hand of cards
          player bound to game 
  = deck of cards remaining
  = table of currently visible cards
  = discard piles (not visible)

* Players's action:

1. Start game. shuffles deck, status = started, no new players.
1. End game.
2. Distribute cards (evenly)
3. Each player choose to draw  1 card.
4. Play = put card on table
5. Discard = put card on discard pile
