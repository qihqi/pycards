// encoding: utf-8

var card_img_urls = [
"/static/2C.png",
"/static/3C.png",
"/static/4C.png",
"/static/5C.png",
"/static/6C.png",
"/static/7C.png",
"/static/8C.png",
"/static/9C.png",
"/static/0C.png",
"/static/JC.png",
"/static/QC.png",
"/static/KC.png",
"/static/AC.png",
"/static/2D.png",
"/static/3D.png",
"/static/4D.png",
"/static/5D.png",
"/static/6D.png",
"/static/7D.png",
"/static/8D.png",
"/static/9D.png",
"/static/0D.png",
"/static/JD.png",
"/static/QD.png",
"/static/KD.png",
"/static/AD.png",
"/static/2H.png",
"/static/3H.png",
"/static/4H.png",
"/static/5H.png",
"/static/6H.png",
"/static/7H.png",
"/static/8H.png",
"/static/9H.png",
"/static/0H.png",
"/static/JH.png",
"/static/QH.png",
"/static/KH.png",
"/static/AH.png",
"/static/2S.png",
"/static/3S.png",
"/static/4S.png",
"/static/5S.png",
"/static/6S.png",
"/static/7S.png",
"/static/8S.png",
"/static/9S.png",
"/static/0S.png",
"/static/JS.png",
"/static/QS.png",
"/static/KS.png",
"/static/AS.png",
"/static/joker.jpg",
"/static/XX.png",
];

function check_hand_card() {
    var card_id = $(this).attr('card_id');
    game.selected[card_id] = $(this).is(':checked');
    if ($(this).is(':checked')) {
        game.selected[card_id] = true;
    } else {
        if (card_id in game.selected) {
            delete game.selected[card_id];
        }
    }
    update_ui();
}

function check_table_card() {
    var card_id = $(this).attr('card_id');
    if ($(this).is(':checked')) {
        game.table_selected[card_id] = true;
    } else {
        if (card_id in game.table_selected) {
            delete game.table_selected[card_id];
        }
    }
    update_ui();
}

function card_text(card) {
    var suite = {
        C: '\u2663',
        D: '\u2666', 
        H: '\u2665',
        S: '\u2660',
    };
    var value = card.value[1];
    if (card.value[0] in suite) {
        if (value == 14) {
            value = 'A';
        }
        if (value == 10) {
            value = '0';
        }
        if (value == 11) {
            value = 'J'
        }
        if (value == 12) {
            value = 'Q'
        }
        if (value == 13) {
            value = 'K'
        }
        return  suite[card.value[0]] + value;
    } else {
        if (value == 20) {
            return '小'
        }
        if (value == 21) {
            return '大'
        }
    }
}

function make_card(card, is_hand) {
    var x = $('<div class="one_card">');
    var label = $('<label>');
    label.text(card_text(card));
    var input = $('<input type="checkbox">');
    if (is_hand) {
        input.change(check_hand_card);
        if (card.id in game.selected) {
            input.prop('checked', true);
        }
    } else {
        input.change(check_table_card);
        if (card.id in game.table_selected) {
            input.prop('checked', true);
        }
    }
    input.attr('card_id', card.id);
    var card_img = $('<img height="120" >');
    card_img.attr('src', card_img_urls[card.id % 54]);
    card_img.click(function(input) { 
        input.prop('checked', !input.is(':checked'));
        input.trigger('change');
    }.bind(null, input));
    x.append(input);
    x.append(label);
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
    draw_until: 0, // stop automatic drawing until
    points: {},
};  // game has player, table, and hand as property

var auto_end_turn = true;

game.is_my_turn = function() {
    return this.turn_number % this.players.length == this.player_id;
}

game.player = function() {
    return this.players[this.turn_number % this.players.length];
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
    }
    if (current_val == tval) {
        var bonus = current_suite == tsuite ? 2 : 1;
        current_suite = 'Z';
        current_val = 14 + bonus;
    }
    if (tsuite != 'NT' && current_suite == tsuite) {
        current_suite = 'Z';
    }
    return [current_suite, current_val];
}

function update_ui() {
    $('#players').empty();
    $('#starting_players').empty();
    var current_player = game.player();
    var players =  game.status == 'NEW' ? $('#starting_players') : $('#players');
    if (conn != null) {
      $('#show_player').show();
    }

    if (game.status != 'NEW' && conn != null) {
      $('#start_area').hide();
      $('#play_area').show();
    } else {
      $('#start_area').show();
      $('#play_area').hide();
    }

    for (var i in game.players) {
        var c = $('<div class="col-sm">') ;
        var p;
        if (game.players[i] == current_player) {
            p = '<b>' + current_player + '</b>';
        } else {
            p = game.players[i];
        }
        c.html(p);
        players.append(c);
    }
    if (game.status == 'NEW') {
      if (game.player_id == 0) {
        $('#start_button_area').show();
      } else {
        $('#start_button_area').hide();
      }
    }
    if (game.player_id == 0) {
        $('.master').show();
    } else {
        $('.master').hide();
    }
    $('#table').empty();
    for (var i in game.table) {
        var player_name = game.table[i][0];
        var cards = game.table[i][1];
        var col = $('<div class="player_table">');
        var slot = $('<div class="mygrid">');
        for (var j in cards) {
            var c = make_card(cards[j], false);
            slot.append(c);
        }
        col.append(slot);
        col.append($('<span class="player_name">' + player_name + '</span>'));
        var width = 50 * (cards.length + 1);
        width += Math.min(20, 5 * player_name.length);
        col.width(width);

        $('#table').append(col);
    }
    $('#hand').empty();
    if (sort_function != null) {
        game.hand.sort(sort_function);
    }
    $('#hand_size').text(game.hand.length);
    for (var i in game.hand) {
        var c = make_card(game.hand[i], true);
        $('#hand').append(c);
    }

    $('#deck_cards').text(game.deck_cards);

    if (game.is_my_turn()) {
        $('#turn').text('YOUR TURN');
    } else {
        var player = game.player();
        $('#turn').text(player + '\'s turn');
    } 
    $('.turn_control').prop('disabled', !game.is_my_turn());
    if (Object.keys(game.selected).length == 0) {
        $('#send').prop('disabled', true);
        $('#return_to_deck').prop('disabled', true);
    }
    if (Object.keys(game.table_selected).length == 0) {
        $('#takeback').prop('disabled', true);
    }
    if (game.status == 'PLAYING') {
        $('#draw').prop('disabled', true);
        $('#return_to_deck').prop('disabled', true);
        $('#draw_continuesly').prop('disabled', true);
    }
    
    $('#points').empty();
    for (var p in game.points) {
        $('#points').append($('<p>' + p + ': ' + game.points[p] + '</p>'));
    }
}


var conn = null;
var should_continuesly_draw = false;
var last_draw_turn = -1;
function continuesly_draw() {
    if (!should_continuesly_draw) {
        return;
    }
    if (game.deck_cards <= game.draw_until) {
        return;
    }
    if (game.status != 'STARTED') {
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
        } else if ('msg' in data) {
            var t = $('#chat_text');
            t.html(t.html() +'<br />' + data.msg);
        } else {
            Object.assign(game, data);
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

        if (auto_end_turn) {
            conn.send( JSON.stringify({
                action: 'END_TURN',
                arg: '' 
            }));
        }

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
        var t = { 
            action: 'START', 
            arg: {
                num_decks: num_decks, 
                draw_until: 0,
            }
         };
        conn.send(JSON.stringify(t));
        return false;
    });
    $('#draw').on('click', function() {
        var t = { action: 'DRAW', arg: 1 };
        conn.send(JSON.stringify(t));
        if (auto_end_turn) {
            conn.send( JSON.stringify({
                action: 'END_TURN',
                arg: '' 
            }));
        }

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
            var lid = l.id;
            var rid = r.id;
            l = normalize_card_val(l.value[0], l.value[1], suite, val);
            r = normalize_card_val(r.value[0], r.value[1], suite, val);
            var result;
            result = l[1] - r[1];
            if (l[0] != r[0]) {
                result = l[0].charCodeAt(0) - r[0].charCodeAt(0);
            }
            if (result == 0) {
                // tie breaker
                result = lid - rid;
            }
            return result;
        }.bind(null, suite, val);

        update_ui();
        event.preventDefault();
    });
    $('#return_to_deck').on('click', function() {
        var to_play = [];
        for (var k in game.selected) {
            if (game.selected[k]) {
                to_play.push(k);
                delete game.selected[k];
            }
        }
        console.log(to_play);
        conn.send( JSON.stringify({
            action: 'RETURN_TO_DECK',
            arg: to_play
        }));

        return false;
    });
    $('#end_draw').on('click', function() {
        conn.send(JSON.stringify({
            action: 'END_DRAW',
            arg: ''
        }));
    });

    $('#auto_end_turn').change(function() {
        auto_end_turn = $(this).is(':checked');
    });

    $('#take_turn').click(function() {
        conn.send(JSON.stringify({
            action: 'TAKE_TURN',
            arg: ''
        }));
    });

    $('#chat_window').keyup(function(event) {
        if (event.keyCode == 13 ) {
            var name = $('#name').val();
            var message = $('#chat_window').val();
            conn.send(JSON.stringify( {
                action: 'MESSAGE',
                arg: name + ': ' + message,
            }));
            $('#chat_window').val('');
            if (message.startsWith('!')) {
                message = message.substr(1);
                var tokens = message.split(' ');
                var objs = [' function test() {'];
                for (var t of tokens) {
                    if (t.charAt(0).match(/[a-z]/i)) {
                        objs.push(' game.points.' + t + ' ');
                    } else {
                        objs.push(t);
                    }
                }
                objs.push('} \n');
                objs.push('test');
            }
            var source = objs.join(' ');
            console.log(source);
            var func = eval(source);
            func();
            conn.send(JSON.stringify( {
                action: 'SET_POINTS',
                arg: game.points
            }));
        }
    });

    $('#spread_cards').on('click', function() {
        var count = $('#spread_count').val();
        conn.send( JSON.stringify( {
            action: 'SPREAD_CARDS',
            arg: count
        }));
        return false;
    });

    $('#deal_from_deck').on('click', function() {
        var count = $('#spread_count').val();
        conn.send( JSON.stringify ({
            action: 'DEAL',
            arg: count,
        }));
    });

    $('#sort_by_number').on('click', function() {
        sort_function = function(l, r) {
            var result;
            console.log('here');
            result = l.value[0].charCodeAt(0) - r.value[0].charCodeAt(0);
            if (l.value[1] != r.value[1]) {
                result = l.value[1] - r.value[1];
            }
            if (result == 0) {
                // tie breaker
                result = l.id - r.id;
            }
            return result;
        };
        update_ui();
        return false;
    });
});
