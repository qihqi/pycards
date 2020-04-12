// encoding: utf-8
'use strict';

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

class Card {
    constructor(numeric_val) {
        this._id = numeric_val;
        this._val = Math.floor(this._id % 54);
    }

    get suite() {
        return Math.floor(this._id / 13);
    }

    get value {
        num = this._id % 13 + 2;
        if (this.suite == 4) {
            // joker
            num += 20;
        }
        return num;
    }

    get card_text() {
        var suite = [
            '\u2663',
            '\u2666', 
            '\u2665',
            '\u2660',
            ];
        let value = this.value;
        if (this.suite < 4) {
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
            return  suite[this.suite] + value;
        } else {
            if (value == 22) {
                return '小'
            }
            if (value == 23) {
                return '大'
            }
        }

    }
}



function card_text(card) {
    if (typeof card === 'string') {
        card = parseInt(card);
    }
    var suite = [
        '\u2663',
        '\u2666', 
        '\u2665',
        '\u2660',
        ];
    card = card % 54;
    var value = card % 13 + 2;
    var s = Math.floor( card / 13);
    if (s < 4) {
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
        return  suite[s] + value;
    } else {
        if (value == 2) {
            return '小'
        }
        if (value == 3) {
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
        input.addClass('hand_card');
    } else {
        input.addClass('table_card');
    }
    input.attr('card_id', card);
    var card_img = $('<img height="120" >');
    card_img.attr('src', card_img_urls[card % 54]);
    card_img.click(function(input) { 
        input.prop('checked', !input.is(':checked'));
    }.bind(null, input));
    x.append(input);
    x.append(label);
    x.append(card_img);
    return x;
}

var game = {
    room: {
        game: null,
        players: [],
        observers: [],
        current_player: null, // current player
    },

    hand: [],
    my_name: null,  // name of this player
    my_team: null,
    ws: null,
    auto_end_turn: true,

    join(name) {
        if (this.ws != null) {
            console.log('already connected.');
            return;
        }
        let wsUri = (window.location.protocol=='https:'&&'wss://'||'ws://')+window.location.host;
        this.ws = new WebSocket(wsUri);
        var self = this;
        this.ws.onopen = function() {
            console.log('Connected');
            self.ws.send(
                JSON.stringify({action: 'NEW_PLAYER', 
                    name: name,
                    arg: name
                }));
            self.my_name = name;
            update_ui();
        };

        this.ws.onerror = function(e) {
          alert('Failed to connect! Please retry.');
        };

        this.ws.onmessage = function(e) {
            console.log(e.data);
            var data = JSON.parse(e.data);
            if ('error' in data) {
                alert(data.error);
            } else if ('msg' in data) {
                var t = $('#chat_text');
                t.append($('<p>' + data.msg + '</p>'));
            } else {
                self.handle_message(data.name, data.action, data.arg);
            }
            update_ui();
        };
    },

    start(num_decks) {
        var t = { 
            name: this.my_name,
            action: 'START', 
            arg: {
                num_decks: num_decks, 
            }
        };
        this.ws.send(JSON.stringify(t));
    },

    draw() {
        var t = { action: 'DRAW', arg: {num_cards: 1 },
            name: this.my_name};
        this.ws.send(JSON.stringify(t));
        if (this.auto_end_turn) {
            this.ws.send( JSON.stringify({
                name: this.my_name,
                action: 'END_TURN',
                arg: {}
            }));
        }
        return false;
    },

    play(cards) {
        if (cards.length == 0) {
            return;
        }
        var card_set = new Set(cards);
        game.hand = game.hand.filter((x) => { return !card_set.has(x); });

        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'PLAY',
            arg: { cards: cards}
        }));

        if (this.auto_end_turn) {
            this.ws.send( JSON.stringify({
                name: this.my_name,
                action: 'END_TURN',
                arg: {}
            }));
        }
    },

    take_back(cards) {
        if (cards.length == 0) {
            return;
        }
        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'TAKE_BACK',
            arg: {
                cards: cards
            }
        }));
    },

    clear_table() {
        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'CLEAN_TABLE',
            arg: ''
        }));
    },

    end_turn() {
        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'END_TURN',
            arg: ''
        }));
    },

    add_points(points) {
        this.ws.send( JSON.stringify({
            action: 'ADD_POINTS',
            name: this.my_name,
            arg: {
                points: points 
            }
        }));
    },

    take_turn() {
        this.ws.send( JSON.stringify({
            action: 'TAKE_TURN',
            name: this.my_name,
            arg: {
            }
        }));
    },

    is_my_turn() {
        return this.room.current_player.name == this.my_name;
    },

    return_to_deck(cards) {
        if (cards.length == 0) {
            return;
        }
        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'RETURN_TO_DECK',
            arg: {cards: cards }
        }));
        var card_set = new Set(cards);
        game.hand = game.hand.filter((x) => { return !card_set.has(x); });
    },

    clean_table() {
        this.ws.send( JSON.stringify({
            name: this.my_name,
            action: 'CLEAN_TABLE',
            arg: {}
        }));
    },

    // handle messages (mostly because of actions of other ppl)
    handle_message(name, action, arg) {
        let game = this.room.game;
        switch(action) {
            case 'DRAW':
                // some one draw a card
                game.deck_count -= arg.num_cards;
                break;
            case 'CLEAN_TABLE':
                game.table = [];
                break;
            case 'PLAY':
                if (arg.cards.length > 0) { 
                    game.table.push([name, arg.cards]);
                }
                break;
            case 'RETURN_TO_DECK':
                game.deck_count += arg.num_cards;
                break;
            case 'TAKE_TURN':
                for (var p of this.room.players) {
                    if (p.name == name) {
                        this.room.current_player = p;
                    }
                }
                break;
            case 'SET_STATE':
                console.log('set state', arg);
                if ('room' in arg) {
                    this.room = Object.assign(this.room, arg.room);
                }
                if ('hand' in arg) {
                    this.hand = arg.hand;
                }
                break;
            case 'SET_TEAM':
                this.my_team = arg.team;
                break;
            case 'DRAWED':
                for (var x of arg) {
                    this.hand.push(x);
                }
                break;
            case 'ADD_POINTS':
                for (let p of this.room.players) {
                    if (p.name == name) {
                        p.score += arg.points;
                    }
                }
                break;
        }
    }

}; 

function default_sort_func(suite, val, l, r) {
    l = normalize_card_val(l, suite, val);
    r = normalize_card_val(r, suite, val);
    var result;
    result = l[1] - r[1];
    if (l[0] != r[0]) {
        result = l[0] - r[0];
    }
    return result;
}

var sort_function = default_sort_func.bind(null, 'S', 2);

const CLUBBER = 0;
const DIAMOND = 1;
const HEART = 2;
const SPADE = 3;
const JOKER = 4;

function normalize_card_val(id, tsuite, tval) {
    let card = new Card(id);
    tsuite = {
        'C': 0,
        'D': 1,
        'H': 2,
        'S': 3,
        'NT': 3,
    }[tsuite];
    let suite = card.suite;
    let value = card.value;

    if (value == tval) {
        var bonus = suite == tsuite ? 2 : 1;
        suite = JOKER;
        value = 14 + bonus;
    }
    if (suite == tsuite) {
        suite = JOKER;
    }
    return [suite, value];
}

function update_ui() {
    $('#players').empty();
    $('#starting_players').empty();
    var current_player = game.room.current_player;
    if (game.ws != null) {
      $('#show_player').show();
    }

    if (game.room.game != null && game.ws != null) {
      $('#start_area').hide();
      $('#play_area').show();
    } else {
      $('#start_area').show();
      $('#play_area').hide();
    }

    for (var p of game.room.players) {
        var c = $('<div class="col-sm">') ;
        var text;
        if (p.name == current_player) {
           text = `<b> ${p.name} (${p.score}) </b>`;
        } else {
            text = `${p.name} (${p.score})`;
        }
        c.html(text);
        $('#players').append(c);
    }

    for (var p of game.room.observers) {
        var c = $('<div class="col-sm">') ;
        c.html(`${p.name} (waiting)`);
        if (game.room.game == null) {
            $('#starting_players').append(c);
        } else {
            $('#players').append(c);
        }
    }


    if (game.my_name == 'han') {
        $('.master').show();
    } else {
        $('.master').hide();
    }

    if (game.room.game == null) {
      if (game.my_name == 'han') {
        $('#start_button_area').show();
      } else {
        $('#start_button_area').hide();
      }
      return;
    }

    $('#table').empty();
    for (var i in game.room.game.table) {
        var player_name = game.room.game.table[i][0];
        var cards = game.room.game.table[i][1];
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

    $('#deck_cards').text(game.room.game.deck_count);

    if (game.is_my_turn()) {
        $('#turn').text('YOUR TURN');
    } else {
        $('#turn').text(game.room.current_player.name + '\'s turn');
    } 
    $('.turn_control').prop('disabled', !game.is_my_turn());
}



$(function() {

    $('#connect').on('click', function() {
        let name = $('#name').val();
        game.join(name);
    });
    $('#send').on('click', function() {
        var to_play = [];
        $('input.hand_card').each( (i, e) => {
            let elem = $(e);
            if (e.checked) { 
                to_play.push(parseInt(elem.attr('card_id')));
            }
        });
        console.log(to_play);
        game.play(to_play);
        return false;
    });
    $('button.start').on('click', function() {
        var num_decks = parseInt($('#num_decks').val());
        game.start(num_decks);
        return false;
    });
    $('#new_game').on('click', function() {
        var num_decks = parseInt($('#spread_count').val()) || parseInt($('#num_decks').val());
        game.start(num_decks);
        $('#pread_count').val('');
        return false;
    });
    $('#draw').on('click', function() {
        game.draw();
        return false;
    });
    $('#takeback').on('click', function() {
        var to_play = [];
        $('input.table_card').each( (i, e) => {
            let elem = $(e);
            if (elem.is(':checked')) { 
                to_play.push(parseInt(elem.attr('card_id')));
            }
        });
        console.log(to_play);
        game.take_back(to_play);
        return false;
    });

    $('#clear_table').on('click', function() {
        game.clean_table();
        return false;
    });

    $('#end_turn').on('click', function() {
        game.end_turn();
        return false;
    });

    $('#sort_form').on('submit', function(event) {
        var data = new FormData(this); 
        console.log(data);
        var suite = $('.suite_radio:checked').val();
        var val =  $('#number_input').val();
        console.log(suite, val);
        sort_function = default_sort_func.bind(null, suite, val);
        update_ui();
        event.preventDefault();
    });
    $('#return_to_deck').on('click', function() {
        var to_play = [];
        $('input.hand_card').each( (i, e) => {
            let elem = $(e);
            if (e.checked) { 
                to_play.push(parseInt(elem.attr('card_id')));
            }
        });
        console.log(to_play);
        game.return_to_deck(to_play);
        return false;
    });
    $('#end_draw').on('click', function() {
        game.ws.send(JSON.stringify({
            name: game.my_name,
            action: 'END_DRAW',
            arg: ''
        }));
    });

    $('#auto_end_turn').change(function() {
        game.auto_end_turn = $(this).is(':checked');
    });

    $('#take_turn').click(function() {
        game.take_turn();
    });

    $('#refresh').click(function() {
            game.ws.send(JSON.stringify( {
                name: game.my_name,
                action: 'GET_STATE',
                arg: {},
            }));
    });

    $('#chat_window').keyup(function(event) {
        if (event.keyCode == 13 ) {
            var name = $('#name').val();
            var message = $('#chat_window').val();
            game.ws.send(JSON.stringify( {
                name: game.my_name,
                action: 'MESSAGE',
                arg: name + ': ' + message,
            }));
            $('#chat_window').val('');
            if (message.startsWith('!')) {
                message = message.substr(1);
                let points = parseInt(message);
                game.add_points(points);
            }
        }
    });

    $('#spread_cards').on('click', function() {
        var count = $('#spread_count').val();
        game.ws.send( JSON.stringify( {
            name: game.my_name,
            action: 'SPREAD_CARDS',
            arg: count
        }));
        $('#spread_count').val('');
        return false;
    });

    $('#deal_from_deck').on('click', function() {
        var count = parseInt($('#spread_count').val());
        game.ws.send( JSON.stringify ({
            name: game.my_name,
            action: 'DEAL',
            arg: { num_cards: count }
        }));
        $('#spread_count').val('');
        return false;
    });

    $('#sort_by_number').on('click', function() {
        sort_function = function(l, r) {
            l = l % 54;
            r = r % 54;
            let lvalue = l % 13;
            let lsuite = l / 13;
            let rvalue = r % 13;
            let rsuite = r / 13;
            var result;
            console.log('here');
            result = lsuite - rsuite;
            if (lvalue != rvalue) {
                result = lvalue - rvalue;
            }
            return result;
        };
        update_ui();
        return false;
    });
});
