$(document).ready( function () {
    let chatLog = $('#chat-log');
    let chatInput = $('#chat-input');
    let chatSubmit = $('#chat-submit');


    /* Chat Event Listeners */
    // focus
    chatInput.focus();

    // user sends message by pressing enter on input
    chatInput.keyup(function (e) {
        if (e.keyCode === 13) {
            chatSubmit.click();
            chatInput.val('');
        }
    });

    // user sends message by clicking submit
    chatSubmit.click(function () {
        let data = {
            message: chatInput.val(),
        };
        let message = JSON.stringify(data);
        chatSocket.send(message)

    });

    /* Chat WebSocket */

    // connect to chat websocket
    let chatSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/chat/' + roomName + '/'
    );

    // client receives message
    chatSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);  // deserialize string into JS object
        let message = data['message'];
        let author = data['author'];
        chatLog.val(chatLog.val() + author + ': ' + message + '\n');  // display the message
    };

    // client connection closed
    chatSocket.onclose = function (e) {
        console.error('WebSocket closed unexpectedly.');
    };



    /* Game Event Listeners */

    // Reference DOM elements

    let startGameButton = $('#start-game-button');
    let endTurnButton = $('#end-turn-button');
    let surrenderButton = $('#surrender-button');
    let deleteGameButton = $('#delete-game');
    let summonButton = $('#summon-button');
    let attackButton = $('#attack');

    let turnText = $('#turn');

    let winnerElement = $('#winner');

    // Player
    let player1 = $('#player-1');
    let player2 = $('#player-2');


    let player1HpText = $('#player-1-hp');
    let player2HpText = $('#player-2-hp');
    let player1ManaText = $('#player-1-mana');
    let player2ManaText = $('#player-2-mana');
    let player1MaxManaText = $('#player-1-max-mana');
    let player2MaxManaText = $('#player-2-max-mana');
    let player1DeckCounter = $('#player-1-deck-counter');  // Deck
    let player2DeckCounter = $('#player-2-deck-counter');

    // TODO: Uniquely identify each card in a message to server

    // Hand
    let handCardElements = $(".hand-card");
    let handCardPositionElements = $(".hand-card-position");  // Reference div tags that have this attribute

    // var companyElements = $("ul:data(group) li:data(company)");

    // Field
    let player1FieldCardElements = $('.player-1-field-card');
    let player2FieldCardElements = $('.player-2-field-card');



    /* Game WebSocket */

    // connect to game websocket
    let gameSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/game/' + roomName + '/'
    );

    // client response to server message
    gameSocket.onmessage = function (e) {
        console.log('onmessage');
        let data = JSON.parse(e.data);
        render(data);
    };



    function render(data) {
        console.log('render');

        // Retrieve message data

        // Game
        let isStarted = data['is_started'];
        let turn = data['turn'];
        let winner = data['winner'];

        // Player
        let player1Hp = data['player_1_hp'];
        let player2Hp = data['player_2_hp'];
        let player1Mana = data['player_1_mana'];
        let player2Mana = data['player_2_mana'];
        let player1MaxMana = data['player_1_max_mana'];
        let player2MaxMana = data['player_2_max_mana'];

        // Deck
        let player1DeckCount = data['player_1_deck_counter'];
        let player2DeckCount = data['player_2_deck_counter'];

        // TODO: Handle the fact that these cards may not exist

        // Hand
        let handCards = [];
        for (let i = 0; i < 10; ++i) {
            let position = data['hand_card_' + i + '_position'];
            if (position !== undefined) {
                handCards[position] =
                    {
                        position: data['hand_card_' + i + '_position'],
                        name: data['hand_card_' + i + '_name'],
                        description: data['hand_card_' + i + '_description'],
                        cost: data['hand_card_' + i + '_cost'],
                        picture: data['hand_card_' + i + '_picture'],
                    };
            }

        }

        // Field
        let player1FieldCards = [];
        let player2FieldCards = [];

        // Index field cards by position
        for (let i = 0; i < 7; ++i) {
            let position = data['player_1_field_card_' + i + '_position'];
            if (position !== undefined) {
                player1FieldCards[position] = {
                    position: data['player_1_field_card_' + i + '_position'],
                    name: data['player_1_field_card_' + i + '_name'],
                    description: data['player_1_field_card_' + i + '_description'],
                    cost: data['player_1_field_card_' + i + '_cost'],
                    picture: data['player_1_field_card_' + i + '_picture'],

                    attack: data['player_1_field_card_' + i + '_attack'],
                    hp: data['player_1_field_card_' + i + '_hp'],
                };
            }
        }
        for (let i = 0; i < 7; ++i) {
            let position = data['player_2_field_card_' + i + '_position'];
            if (position !== undefined) {
                player2FieldCards[position] = {
                    position: data['player_2_field_card_' + i + '_position'],
                    name: data['player_2_field_card_' + i + '_name'],
                    description: data['player_2_field_card_' + i + '_description'],
                    cost: data['player_2_field_card_' + i + '_cost'],
                    picture: data['player_2_field_card_' + i + '_picture'],

                    attack: data['player_2_field_card_' + i + '_attack'],
                    hp: data['player_2_field_card_' + i + '_hp'],
                };
            }
        }


        // Update DOM

        // GameState
        if (isStarted) {
            startGameButton.css({'display': 'none'})
        } else {
            startGameButton.css({'display': 'inline-block'})
        }

        turnText.html(turn);

        if (winner) {
            winnerElement.html(winner + ' has won the game!');
        }


        // Players
        player1HpText.html(player1Hp);
        player2HpText.html(player2Hp);
        player1ManaText.html(player1Mana);
        player2ManaText.html(player2Mana);
        player1MaxManaText.html(player1MaxMana);
        player2MaxManaText.html(player2MaxMana);
        player1DeckCounter.html(player1DeckCount);
        player2DeckCounter.html(player2DeckCount);

        console.log(handCards);
        console.log(player1FieldCards);
        console.log(player2FieldCards);

        // Hand
        handCardElements.each(function (i) {
            if (handCards[i]) {
                // Element render hand card
                handCardElements.eq(i).find('.name').html(handCards[i].name);
                handCardElements.eq(i).find('.description').html(handCards[i].description);
                handCardElements.eq(i).find('.cost').html(handCards[i].cost);
                handCardElements.eq(i).find('.picture').attr('src', handCards[i].picture);
            } else {
                // Element should render empty card
                handCardElements.eq(i).find('.name').empty();
                handCardElements.eq(i).find('.description').empty();
                handCardElements.eq(i).find('.cost').empty();
                handCardElements.eq(i).find('.picture').attr('src', '');
            }
        });

        // Field
        player1FieldCardElements.each(function (i) {
           if (player1FieldCards[i]) {
                player1FieldCardElements.eq(i).find('.name').html(player1FieldCards[i].name);
                player1FieldCardElements.eq(i).find('.description').html(player1FieldCards[i].description);
                player1FieldCardElements.eq(i).find('.cost').html(player1FieldCards[i].cost);
                player1FieldCardElements.eq(i).find('.picture').attr('src', player1FieldCards[i].picture);
                player1FieldCardElements.eq(i).find('.attack').html(player1FieldCards[i].attack);
                player1FieldCardElements.eq(i).find('.hp').html(player1FieldCards[i].hp);
           } else {
                player1FieldCardElements.eq(i).find('.name').empty();
                player1FieldCardElements.eq(i).find('.description').empty();
                player1FieldCardElements.eq(i).find('.cost').empty();
                player1FieldCardElements.eq(i).find('.picture').attr('src', '');
                player1FieldCardElements.eq(i).find('.attack').empty();
                player1FieldCardElements.eq(i).find('.hp').empty();
           }
        });
        player2FieldCardElements.each(function (i) {
           if (player2FieldCards[i]) {
                player2FieldCardElements.eq(i).find('.name').html(player2FieldCards[i].name);
                player2FieldCardElements.eq(i).find('.description').html(player2FieldCards[i].description);
                player2FieldCardElements.eq(i).find('.cost').html(player2FieldCards[i].cost);
                player2FieldCardElements.eq(i).find('.picture').attr('src', player2FieldCards[i].picture);
                player2FieldCardElements.eq(i).find('.attack').html(player2FieldCards[i].attack);
                player2FieldCardElements.eq(i).find('.hp').html(player2FieldCards[i].hp);
           }
           else {
                player2FieldCardElements.eq(i).find('.name').empty();
                player2FieldCardElements.eq(i).find('.description').empty();
                player2FieldCardElements.eq(i).find('.cost').empty();
                player2FieldCardElements.eq(i).find('.picture').attr('src', '');
                player2FieldCardElements.eq(i).find('.attack').empty();
                player2FieldCardElements.eq(i).find('.hp').empty();
           }
        });
    }

    startGameButton.click(function() {
        console.log('start game');
        let data = {
            command: 'start_game',
        };
        gameSocket.send(JSON.stringify(data));
    });

    endTurnButton.click(function() {
        console.log('end turn');
        let data = {
            command: 'end_turn',
        };
        gameSocket.send(JSON.stringify(data));
    });

    surrenderButton.click(function() {
        console.log('surrender');
        let data = {
            command: 'surrender',
        };
        gameSocket.send(JSON.stringify(data));
    });

    deleteGameButton.click(function() {
        console.log('delete game');
        let data = {
            command: 'delete_game',
        };
        gameSocket.send(JSON.stringify(data));
    });

    summonButton.click(function() {
        // When user summons, set up click listeners for each hand card
        handCardElements.click(function () {
            // What to do after a hand card has been clicked

            let handCardPosition = parseInt($(this).find('.position').html());
            // console.log(handCardPosition);

            // Set up listeners for each field card element
            let playerFieldCardElements = undefined;
            if (username === player1Name) {
                playerFieldCardElements = player1FieldCardElements;
            } else if (username === player2Name) {
                playerFieldCardElements = player2FieldCardElements;
            }

            playerFieldCardElements.click(function () {
                let fieldCardPosition = parseInt($(this).find('.position').html());
                // console.log(fieldCardPosition);
                let data = {
                    command: 'summon',
                    handCardPosition: handCardPosition,
                    fieldCardPosition: fieldCardPosition,
                };
                gameSocket.send(JSON.stringify(data));

                // remove listeners for all player field cards
                playerFieldCardElements.off('click');
            });
            // remove listeners for all hand cards
            handCardElements.off('click');
        })
    });

    attackButton.click(function () {
        let attackingPlayerFieldCardElements = undefined;
        let defendingPlayerFieldCardElements = undefined;
        let defendingPlayer = undefined;
        let defendingPlayerName;

        if (username === player1Name) {
            attackingPlayerFieldCardElements = player1FieldCardElements;
            defendingPlayerFieldCardElements = player2FieldCardElements;
            defendingPlayer = player2;
            defendingPlayerName = player2Name;

        } else if (username === player2Name) {
            attackingPlayerFieldCardElements = player2FieldCardElements;
            defendingPlayerFieldCardElements = player1FieldCardElements;
            defendingPlayer = player1;
            defendingPlayerName = player1Name;
        }

        attackingPlayerFieldCardElements.click(function () {
            let attackingFieldCardPosition = parseInt($(this).find('.position').html());
            console.log(attackingFieldCardPosition);

            defendingPlayerFieldCardElements.click(function () {
                let defendingFieldCardPosition = parseInt($(this).find('.position').html());
                console.log(defendingFieldCardPosition);

                let data = {
                    command: 'attack',
                    attackingFieldCardPosition: attackingFieldCardPosition,
                    defendingFieldCardPosition: defendingFieldCardPosition,
                };
                gameSocket.send(JSON.stringify(data));

                defendingPlayerFieldCardElements.off('click');
                defendingPlayer.off('click');
            });

            defendingPlayer.click(function () {
                console.log(defendingPlayerName);
                let data = {
                    command: 'attack_player',
                    attackingFieldCardPosition: attackingFieldCardPosition,
                    defendingPlayerName: defendingPlayerName,
                };
                gameSocket.send(JSON.stringify(data));

                defendingPlayerFieldCardElements.off('click');
                defendingPlayer.off('click');
            });

            attackingPlayerFieldCardElements.off('click');
        });

    });












});


