$(document).ready(function() {
    let searchBar = $('#searchbar');
    let monsterCardList = $('#monster-card-list');
    let spellCardList = $('#spell-card-list');

    searchBar.keyup(function(event) {
        // User pressed key in search bar
        let query = searchBar.val();
        console.log(query);
        // send query but do not wait
        $.ajax({
            url: searchBar.attr('data-card-query-url'),  // resource to request
            data: {
                query: query
            },
            dataType: 'json',
            type: 'GET',
            success: function (data) {  // invoked upon server response
                let monsterCards = data['monster_cards'];
                let monsterCardsSize = Object.keys(monsterCards).length;
                let spellCards = data['spell_cards'];
                let spellCardsSize = Object.keys(spellCards).length;

                // test
                console.log(data);

                /* render */

                // clear lists
                monsterCardList.empty();

                // display each monster card
                for (let i=0; i<monsterCardsSize; ++i) {
                    // TODO: URL is hardcoded, because templating can only occur before server serves client. Fix.
                    let url = '/game/' + monsterCards[i].pk + '/monster_card_detail';
                    monsterCardList.append(
                        '<li><a href="' + url + '">' + monsterCards[i].name + '</li>'
                    );
                }

                // display each spell card
                for (let i=0; i<spellCardsSize; ++i) {
                    // TODO: URL is hardcoded, because templating can only occur before server serves client. Fix.
                    let url = '/game/' + spellCards[i].pk + '/spell_card_detail';
                    spellCardList.append(
                        '<li><a href="' + url + '">' + spellCards[i].name + '</li>'
                    );
                }
            }
        });

    })

});