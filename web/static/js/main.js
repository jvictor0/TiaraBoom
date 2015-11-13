function makeTweet(t) {
    var $tweet = $('<div>').addClass('tweet');
    var $tweet_row = $('<div>').addClass('row');
    
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

    var tweet_text = t.text.replace(/#([0-9A-Za-z_]*)/g, '<a href="https://twitter.com/hashtag/$1" target="_blank">&#35;$1</a>')
    tweet_text = tweet_text.replace(/@([0-9A-Za-z_]*)/g,'<a href="https://twitter.com/$1" target=\"_blank\">@$1</a>')
    var inner = tweet_text + '&nbsp;<a href="https://www.twitter.com/' + t.sn  + '/status/' + t.tweet_id + '"> Go to tweet&nbsp;&raquo;</a>'; 

    var $left_col = $('<div>').addClass('col-md-2').append(make_link("img"))

    var $right_col = $('<div>').addClass('col-md-10');
    var $right_col_top = $('<div>').addClass('row').append($('<div>').addClass("col-md-12").append(make_link("sn")))
    var $right_col_bottom = $('<div>').addClass('row').append($('<div>').addClass("col-md-12").append($('<p>').addClass("tweet-text").html(inner)))
    $right_col.append($right_col_top).append($right_col_bottom)

    $tweet_row.append($left_col).append($right_col);
    $tweet.append($tweet_row);

    return $tweet;
}

function makeConvo(convo) {
    $convo_div = $('<div>').addClass('col-md-6 col-md-offset-3 conversation')
    var count = 0;
    for (tweet in convos[convo]) {
        if (convos.hasOwnProperty(convo)) {
            if(convos[convo].hasOwnProperty(tweet)) {
                $tweet = makeTweet(convos[convo][tweet]);
                if (count >= 2) $tweet.addClass("more").css("display", "none");
                $convo_div.append($tweet);
                count++;
            }
        }
    }

    $show_more = $('<div>').addClass('text-center').css('margin-bottom','10px').append($('<a>').html("Show more &or;"));
    $show_less = $('<div>').addClass('text-center').css('margin-bottom','10px').append($('<a>').html("Show less &and;"));

    function show_more() {
        $(this).parent().children(".more").css("display", "block");
        $(this).parent().append($show_less);
        $(this).remove()
    }

    function show_less() {
        $(this).parent().children(".more").css("display", "none");
        $(this).parent().append($show_more);
        $(this).remove()
    }

    $show_more.click(show_more);
    $show_less.click(show_less);

    $convo_div.append($show_more);
    return $convo_div;
}

$( document ).ready(function() {
    $( ".tweets").empty();
    for (var c in convos) {
        $( ".tweets" ).append(makeConvo(c));
        
    }
    $('a').attr("target", "_blank")
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
