
var card_img_urls = [
"https://deckofcardsapi.com/static/img/2C.png",
"https://deckofcardsapi.com/static/img/3C.png",
"https://deckofcardsapi.com/static/img/4C.png",
"https://deckofcardsapi.com/static/img/5C.png",
"https://deckofcardsapi.com/static/img/6C.png",
"https://deckofcardsapi.com/static/img/7C.png",
"https://deckofcardsapi.com/static/img/8C.png",
"https://deckofcardsapi.com/static/img/9C.png",
"https://deckofcardsapi.com/static/img/0C.png",
"https://deckofcardsapi.com/static/img/JC.png",
"https://deckofcardsapi.com/static/img/QC.png",
"https://deckofcardsapi.com/static/img/KC.png",
"https://deckofcardsapi.com/static/img/AC.png",
"https://deckofcardsapi.com/static/img/2D.png",
"https://deckofcardsapi.com/static/img/3D.png",
"https://deckofcardsapi.com/static/img/4D.png",
"https://deckofcardsapi.com/static/img/5D.png",
"https://deckofcardsapi.com/static/img/6D.png",
"https://deckofcardsapi.com/static/img/7D.png",
"https://deckofcardsapi.com/static/img/8D.png",
"https://deckofcardsapi.com/static/img/9D.png",
"https://deckofcardsapi.com/static/img/0D.png",
"https://deckofcardsapi.com/static/img/JD.png",
"https://deckofcardsapi.com/static/img/QD.png",
"https://deckofcardsapi.com/static/img/KD.png",
"https://deckofcardsapi.com/static/img/AD.png",
"https://deckofcardsapi.com/static/img/2H.png",
"https://deckofcardsapi.com/static/img/3H.png",
"https://deckofcardsapi.com/static/img/4H.png",
"https://deckofcardsapi.com/static/img/5H.png",
"https://deckofcardsapi.com/static/img/6H.png",
"https://deckofcardsapi.com/static/img/7H.png",
"https://deckofcardsapi.com/static/img/8H.png",
"https://deckofcardsapi.com/static/img/9H.png",
"https://deckofcardsapi.com/static/img/0H.png",
"https://deckofcardsapi.com/static/img/JH.png",
"https://deckofcardsapi.com/static/img/QH.png",
"https://deckofcardsapi.com/static/img/KH.png",
"https://deckofcardsapi.com/static/img/AH.png",
"https://deckofcardsapi.com/static/img/2S.png",
"https://deckofcardsapi.com/static/img/3S.png",
"https://deckofcardsapi.com/static/img/4S.png",
"https://deckofcardsapi.com/static/img/5S.png",
"https://deckofcardsapi.com/static/img/6S.png",
"https://deckofcardsapi.com/static/img/7S.png",
"https://deckofcardsapi.com/static/img/8S.png",
"https://deckofcardsapi.com/static/img/9S.png",
"https://deckofcardsapi.com/static/img/0S.png",
"https://deckofcardsapi.com/static/img/JS.png",
"https://deckofcardsapi.com/static/img/QS.png",
"https://deckofcardsapi.com/static/img/KS.png",
"https://deckofcardsapi.com/static/img/AS.png",
"/static/joker.jpg",
"https://deckofcardsapi.com/static/img/XX.png",
];

function check_hand_card() {
    var card_id = $(this).attr('card_id');
    game.selected[card_id] = $(this).is(':checked');

}

function check_table_card() {
    var card_id = $(this).attr('card_id');
    game.table_selected[card_id] = $(this).is(':checked');
}

function make_card(card, is_hand) {
    var x = $('<div>');
    var input = $('<input type="checkbox">');
    if (is_hand) {
        input.change(check_hand_card);
    } else {
        input.change(check_table_card);
    }
    input.attr('card_id', card.id);
    var card_img = $('<img height="120" >');
    card_img.attr('src', card_img_urls[card.id % 54]);
    x.append(input);
    x.append(card_img);
    return x;
}

var game = {
    players: [],
    table: [],
    hand: [],
    selected: {},
    table_selected: {},
    deck_cards: 0,
    status: '',
    player_id: null,  // id of this player
    turn_number: null, // number of current turn    
};  // game has player, table, and hand as property

game.is_my_turn = function() {
    return this.turn_number % this.players.length == this.player_id;
}

var sort_function =  function(suite, val, l, r) {
    l = normalize_card_val(l.value[0], l.value[1], suite, val);
    r = normalize_card_val(r.value[0], r.value[1], suite, val);
    var result;
    result = l[1] - r[1];
    if (l[0] != r[0]) {
        result = l[0].charCodeAt(0) - r[0].charCodeAt(0);
    }
    if (result == 0) {
        // tie breaker
        result = l.id - r.id;
    }
    return result;
}.bind(null, 'S', 2);

function normalize_card_val(current_suite, current_val, tsuite, tval) {
    if (current_suite == 'JOKER') {
        current_suite = 'Z';  
        current_val = 15 + current_val;
    }
    if (current_val == tval) {
        var bonus = current_suite == tsuite ? 2 : 1;
        current_suite = 'Z';
        current_val = 13 + bonus;
    }
    if (tsuite != 'NT' && current_suite == tsuite) {
        current_suite = 'Z';
    }
    return [current_suite, current_val];
}

function update_ui() {
    $('#players').empty();
    $('#starting_players').empty();
    var players =  game.status == 'STARTED' ? $('#players') : $('#starting_players');
    if (conn != null) {
      $('#show_player').show();
    }

    if (game.status == 'STARTED') {
      $('#start_area').hide();
      $('#play_area').show();
    } else {
      $('#start_area').show();
      $('#play_area').hide();
    }

    for (var i in game.players) {
        var c = $('<div class="col-sm">') ;
        c.text(game.players[i]);
        players.append(c);
    }
    if (game.status == 'NEW') {
      if (game.player_id == 0) {
        $('#start_button_area').show();
      }
    }
    if (game.player_id == 0) {
        $('#new_game').show();
    } else {
        $('#new_game').hide();
    }
    $('#table').empty();
    for (var i in game.table) {
        var player_name = game.table[i][0];
        var cards = game.table[i][1];
        var col = $('<div class="col-sm">');
        var slot = $('<div class="mygrid">');
        for (var j in cards) {
            var c = make_card(cards[j], false);
            slot.append(c);
        }
        col.append($('<p>' + player_name + '</p>'));
        col.append(slot);
        $('#table').append(col);
    }
    $('#hand').empty();
    if (sort_function != null) {
        game.hand.sort(sort_function);
    }
    for (var i in game.hand) {
        var c = make_card(game.hand[i], true);
        $('#hand').append(c);
    }

    $('#deck_cards').text(game.deck_cards);

    if (game.is_my_turn()) {
        $('#turn').text('YOUR TURN');
    } else {
        $('#turn').text('NOT YOUR TURN');
    } 
    $('#draw').prop('disabled', !game.is_my_turn());
    $('#send').prop('disabled', !game.is_my_turn());
    $('#takeback').prop('disabled', !game.is_my_turn());
    $('#clear_table').prop('disabled', !game.is_my_turn());
}


var conn = null;
var should_continuesly_draw = false;
var last_draw_turn = -1;
function continuesly_draw() {
    if (!should_continuesly_draw) {
        return;
    }
    if (game.deck_cards == 0) {
        return;
    }
    if (game.is_my_turn() && last_draw_turn < game.turn_number) {
        last_draw_turn = game.turn_number;
        conn.send( JSON.stringify( {
          action: 'DRAW',
          arg: 1
        }));
    } else if (game.is_my_turn()) {
        conn.send( JSON.stringify( {
          action: 'END_TURN',
          arg: ''
        }));
    }


    setTimeout(continuesly_draw, 300);
}


function connect() {
    var wsUri = (window.location.protocol=='https:'&&'wss://'||'ws://')+window.location.host;
    conn = new WebSocket(wsUri);
    var name = $('#name').val()
    console.log('Connecting...');
    conn.onopen = function() {
        console.log('Connected');
        conn.send(
            JSON.stringify({action: 'NEW_PLAYER', 
                arg: name}));
    };
    conn.onerror = function(e) {
      alert('Failed to connect! Please retry.');
    };
    conn.onmessage = function(e) {
        var data = JSON.parse(e.data);
        if ('error' in data) {
            alert(data.error);
        }
        if ('players' in data) {
            game.players = data.players
        }
        if ('table' in data) {
            game.table = data.table
        }
        if ('hand' in data) {
            game.hand = data.hand
        }
        if ('deck_cards' in data) {
            game.deck_cards = data.deck_cards;
        }
        if ('player_id' in data) {
            game.player_id = data.player_id;
        }
        if ('turn_number' in data) {
            game.turn_number = data.turn_number;
        }
        if ('status' in data) {
            game.status = data.status;
        }
        update_ui();

    };
    conn.onclose = function() {
        conn = null;
        update_ui();
    };
}

$(function() {

    $('#connect').on('click', function() {
        if (conn == null) {
            connect();
        } else {
           console.log('already connected.');
        }

        return false;
    });
    $('#send').on('click', function() {
        var to_play = [];
        for (var k in game.selected) {
            if (game.selected[k]) {
                to_play.push(k);
                delete game.selected[k];
            }
        }
        console.log(to_play);
        conn.send( JSON.stringify({
            action: 'PLAY',
            arg: to_play
        }));

        return false;
    });
    $('#text').on('keyup', function(e) {
        if (e.keyCode === 13) {
            $('#send').click();
            return false;
        }
    });
    $('button.start').on('click', function() {
        var num_decks = parseInt($('#num_decks').val());
        var t = { action: 'START', arg: num_decks };
        conn.send(JSON.stringify(t));
        return false;
    });
    $('#draw').on('click', function() {
        var t = { action: 'DRAW', arg: 1 };
        conn.send(JSON.stringify(t));
        return false;
    });
    $('#takeback').on('click', function() {
        var to_play = [];
        for (var k in game.table_selected) {
            if (game.table_selected[k]) {
                to_play.push(k);
                delete game.table_selected[k];
            }
        }
        console.log(to_play);
        conn.send( JSON.stringify({
            action: 'TAKE_BACK',
            arg: to_play
        }));

        return false;
    });

    $('#clear_table').on('click', function() {
        conn.send( JSON.stringify({
            action: 'CLEAN_TABLE',
            arg: ''
        }));
        return false;
    });

    $('#end_turn').on('click', function() {
        conn.send( JSON.stringify({
            action: 'END_TURN',
            arg: ''
        }));
        return false;
    });

    $('#draw_continuesly').on('click', function() {
        should_continuesly_draw = !should_continuesly_draw;
        if (should_continuesly_draw) {
           $(this).text('停止摸牌');
           continuesly_draw();
        } else {
           $(this).text('持续摸牌');
        }
    });

    $('#sort_form').on('submit', function(event) {
        var data = new FormData(this); 
        console.log(data);
        var suite = $('.suite_radio:checked').val();
        var val =  $('#number_input').val();
        console.log(suite, val);
        sort_function = function(suite, val, l, r) {
            l = normalize_card_val(l.value[0], l.value[1], suite, val);
            r = normalize_card_val(r.value[0], r.value[1], suite, val);
            var result;
            result = l[1] - r[1];
            if (l[0] != r[0]) {
                result = l[0].charCodeAt(0) - r[0].charCodeAt(0);
            }
            if (result == 0) {
                // tie breaker
                result = l.id - r.id;
            }
            return result;
        }.bind(null, suite, val);

        update_ui();
        event.preventDefault();
    });
});
