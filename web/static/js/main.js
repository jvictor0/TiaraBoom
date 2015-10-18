function makeTweet(t) {
    var $tweet = $('<div>').addClass('tweet');
    var $top_row = $('<div>').addClass('row tweet-top-row');
    
    var make_link = function(inner) {
        var $link = $('<a>').attr('href', "http://www.twitter.com/" + t.sn);
        if ( inner === "img") {
            var $img = $('<img>').attr('src', t.pic);
            $link.append($img);
        } else if ( inner === "sn") {
            var $sn = $('<p>').text("@" + t.sn);
            $link.append($sn);
        }
        return $link;
    }

    $top_row.append(make_link("img").addClass("col-md-3")).append(make_link("sn").addClass("col-md-4")); 
    $tweet.append($top_row);
    var inner = t.text + '&nbsp;<a href="http://www.twitter.com/' + t.sn  + '/status/' + t.id + '"> Go to tweet&nbsp;&raquo;</a>'; 
    $tweet.append($('<div>').addClass("row").append($('<div>').addClass("col-md-12").append($('<p>').addClass("tweet-text").html(inner))));
    return $tweet;
}

function makeConvo(mini, convo) {
    $convo_div = $('<div>').addClass('col-md-6 col-md-offset-3 conversation')
    if (mini) {
        var count = 0;
        for (tweet in convo) {
            if (convos.hasOwnProperty(convo)) {
                if(convos[convo].hasOwnProperty(tweet) && count < 2) {
                    $convo_div.append(makeTweet(convos[convo][tweet]));
                    count++;
                }
            }
        }
    } else {
        for (tweet in convo) {
            if (convos.hasOwnProperty(convo)) {
                if(convos[convo].hasOwnProperty(tweet)) {
                    $convo_div.append(makeTweet(convos[convo][tweet]));
                }
            }
        }
    }
    $show_more = $('<div>').addClass('text-center').css('margin-bottom','10px').append($('<a>').html("Show more &#9660;"));
    $convo_div.append($show_more);
    return $convo_div;
}

$( document ).ready(function() {
    $( ".tweets").empty();
    for (var c in convos) {
        $( ".tweets" ).append(makeConvo(false, c));
        
    }
});


/*
                    <div class="row">
                        <div class="col-md-6 col-md-offset-3 tweet">
                            <div class="row tweet-top-row">
                                <div class="col-md-3">
                                    <a href="http://www.twitter.com/ tweet.user.screen_name "><img src=" tweet.user.profile_image_url " ></a>
                                </div>
                                <div class="col-md-4">
                                    <a href="http://www.twitter.com/ tweet.user.screen_name "><p>@ tweet.user.screen_name</p></a>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-12 ">
                                    <p class="tweet-text"> tweet.text &nbsp;<a href="http://twitter.com/ tweet.user.screen_name /status/ tweet.id ">Go to tweet&nbsp;&raquo;</a></p>
                                </div>
                            </div>
                        </div>
                    </div>
                    */
