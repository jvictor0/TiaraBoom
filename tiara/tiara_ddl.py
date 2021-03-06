
def TiaraCreateTables(con):
    # tweet tables
    con.query(("create table if not exists tweets("                        
               "id bigint not null,"
               "user_id bigint not null,"                        
               "retweets bigint not null,"
               "favorites bigint not null,"
               "primary key(user_id, id) using hash,"
               "shard (user_id))"))
    followback_terms = ['follow','seguro','retweet','mgwv','followback','followtrain','followtrick','teamfollowback']
    followbacker_regex = " + ".join([("(lcase_body regexp '%s')" % ("[^a-z][^a-z]*".join(fl))) for fl in followback_terms])
    maybe_followbacker_regex = " + ".join([("(lcase_body regexp '%s')" % fl) for fl in followback_terms])
    con.query(("create columnar table if not exists tweets_storage("                        
               "id bigint not null,"
               "parent bigint default null,"                        
               "user_id bigint not null,"                        
               "parent_id bigint default null,"                        
               "body blob, "                        
               "ts datetime not null,"
               "json json ," 
               "lcase_body as lcase(cast(body as char)) persisted blob,"
               "num_hashtags as ifnull(json_length(json::hashtags),0) persisted bigint, "
               "num_media as ifnull(json_length(json::media),0) persisted bigint, "
               "num_user_mentions as ifnull(json_length(json::user_mentions),0) persisted bigint, "
               "num_urls as ifnull(json_length(json::urls),0) persisted bigint, "
               "is_retweet as not isnull(json::retweeted_status) persisted boolean, "
               "language as json::$lang persisted varbinary(200), "
               "is_followbacker as %s persisted tinyint,"
               "maybe_followbacker as %s persisted tinyint,"
               "shard(user_id),"
               "index(user_id, id) using clustered columnar)" % (followbacker_regex, maybe_followbacker_regex)))
    con.query(("create table if not exists bot_tweets ("
               "id bigint not null,"
               "parent bigint default null,"                        
               "user_id bigint not null,"                        
               "parent_id bigint default null,"                        
               "body blob, "                        
               "ts datetime not null,"
               "json json ,"
               "conversation_id bigint not null, "
               "favorites bigint not null, "
               "retweets bigint not null, "
               "key (conversation_id), "
               "key (parent_id,parent), "
               "primary key(user_id, id), "
               "shard (user_id))"))
    con.query(("create table if not exists ungettable_tweets("
               "id bigint primary key,"
               "errorcode int)"))
    con.query(("create reference table if not exists conversation_upvotes("
               "user_id bigint not null,"
               "conversation_id bigint not null,"
               "upvotes int not null,"
               "primary key(user_id, conversation_id))"))


    # user tables
    con.query(("create table if not exists user_afflictions("
               "id bigint,"
               "affliction int,"
               "primary key(id, affliction),"
               "shard(id))"))
    
    con.query(("create table if not exists users("
               "id bigint primary key,"
               "screen_name varbinary(200) not null,"
               "num_followers bigint not null,"
               "num_friends bigint not null,"
               "language varbinary(200) not null,"
               "updated timestamp default current_timestamp on update current_timestamp,"
               "image_url varbinary(200),"
               "key (screen_name))"))
    con.query(("create table if not exists user_following_status("
               "id bigint not null,"
               "bot_id bigint not null,"
               "following tinyint not null,"
               "has_followed tinyint not null,"
               "updated timestamp default current_timestamp on update current_timestamp,"
               "unfollow_reason tinyint not null,"
               "primary key(id, bot_id),"
               "shard(id))"))

    # TFIDF token tables
    #
    con.query(("create reference table if not exists token_id("
               "id bigint primary key auto_increment,"
               "token varbinary(200) not null,"
               "unique key(token))"))
    con.query(("create reference table if not exists token_representatives("
               "id bigint not null,"
               "token varbinary(200) primary key)"))
    con.query(("create table if not exists user_token_frequency_proj_token("
               "user_id bigint not null,"
               "token bigint not null,"
               "count bigint not null,"
               "shard(token),"
               "key(token, user_id) using clustered columnstore)"))
    con.query(("create table if not exists user_token_frequency_proj_user("
               "user_id bigint not null,"
               "token bigint not null,"
               "count bigint not null,"
               "shard(token),"
               "key(token, user_id) using clustered columnstore)"))
    con.query(("create table if not exists tweet_tokens("
               "user_id bigint not null,"
               "id bigint not null,"
               "token bigint not null,"
               "shard(user_id),"
               "key(user_id, id, token) using clustered columnstore)"))
    con.query(("create reference table if not exists tweet_document_frequency("
               "token bigint not null,"
               "count bigint not null,"
               "primary key(token) using hash)"))
    con.query(("create reference table if not exists user_document_frequency("
               "token bigint not null,"
               "count bigint not null,"
               "primary key(token) using hash)"))

    # targeting tables
    #
    con.query(("create table if not exists ignored_users("
               "id bigint primary key)"))
    con.query(("create table if not exists target_candidates("
               "id bigint not null,"
               "bot_id bigint not null,"
               "primary key(bot_id, id),"
               "shard(id),"
               "processed datetime default null,"
               "eliminated tinyint not null)"))
    con.query(("create reference table if not exists follower_cursors("
               "id bigint not null,"
               "bot_id bigint not null,"
               "cursr bigint not null,"                        
               "primary key(bot_id, id, cursr),"
               "processed datetime default null)"))
    con.query(("create reference table if not exists bots("
               "id bigint primary key,"
               "screen_name varbinary(200))"))

    # materialized view for targeting state
    #
    con.query(("create table if not exists targeting_state("
               "bot_id bigint not null,"
               "user_id bigint not null,"
               "last_targeted datetime not null,"
               "tweets_to bigint not null,"
               "primary key(bot_id, user_id),"
               "shard(user_id))"))

    
def DropViews(con):
    while True:
        views = [r["table_name"] for r in con.query("select table_name from information_schema.views where table_schema='tiaraboom'")]
        if len(views) == 0:
            break
        for v in views:
            try:
                con.query("drop view if exists %s" % v)
            except Exception:
                pass
    
def TiaraCreateViews(con):
    views = {}
    default_args = {}
    
    DropViews(con)

    # views for convinience
    #
    con.query(("create view tweets_joined as "
               "select ts.id, ts.user_id, ts.parent_id, ts.parent, tweets.favorites, tweets.retweets, ts.body, ts.json, ts.ts "
               "from tweets_storage ts join tweets tweets "
               "on ts.user_id = tweets.user_id and ts.id = tweets.id "))
    con.query(("create view tweets_joined_no_json as "
               "select ts.id, ts.user_id, ts.parent_id, ts.parent, tweets.favorites, tweets.retweets, ts.body, ts.ts, '{}' as json "
               "from tweets_storage ts join tweets tweets "
               "on ts.user_id = tweets.user_id and ts.id = tweets.id "))
    # views for user level TFIDF
    #
    con.query("create view user_document_frequency_view as "
              "select token, count(distinct user_id) as count from user_token_frequency_proj_token group by 1")
    con.query("create view user_token_frequency_aggregated "
              "as select user_id, token, sum(count) as count "
              "from user_token_frequency_proj_user "
              "group by 1,2")
    con.query("create view max_df_view as "
              "select max(count) as val from user_document_frequency")
    con.query("create view tfidf_view_internal as "
              "select termfreq.token, termfreq.user_id, termfreq.count as tf, docfreq.count as df, "
              "log(1 + termfreq.count) * log((select val from max_df_view)/(1+docfreq.count)) as tfidf "
              "from user_token_frequency_aggregated termfreq join user_document_frequency docfreq "
              "on termfreq.token = docfreq.token")
    con.query("create view tfidf_view as "
              "select tid.token, tid.id as token_id, users.screen_name, tf.user_id, tf.tf, tf.df, tf.tfidf "
              "from tfidf_view_internal tf join token_id tid join users "
              "on tf.token = tid.id and tf.user_id = users.id")

    # views for tweet level TFIDF
    #
    con.query("create view max_tweet_df_view as "
              "select max(count) as val from tweet_document_frequency ")
    con.query("create view tweet_tfidf_view_internal as "
              "select user_id, id, tt.token, "
              "log(1000000/(1+tdf.count)) as tfidf "
              "from tweet_tokens tt join tweet_document_frequency tdf "
              "on tt.token = tdf.token " )

    # views for selecting users to follow
    #
    con.query("create view followbackers_view as "
              "select user_id from tweets_storage "
              "group by 1 "
              "having sum(is_followbacker) > 0 or avg(maybe_followbacker) > 0.5 ")
    views["candidates_joined_view"] = """
                select users.screen_name, users.id as uid, users.num_followers, users.num_friends, users.language, 
                        ts.id as tid, ts.lcase_body, 
                        ts.num_hashtags, ts.num_media, ts.num_urls, ts.num_user_mentions, ts.language as tweet_language, 
                        ts.is_retweet, ts.ts, ts.is_followbacker, ts.maybe_followbacker, ts.parent_id, 
                        tc.bot_id, tc.processed 
                 from tweets_storage ts join users join target_candidates tc 
                 on ts.user_id = users.id and users.id = tc.id 
                 where not tc.eliminated 
                 and users.id not in (select user_id from followbackers_view) 
                 and users.id not in (select id from user_following_status where has_followed) 
                 and users.id not in (select id from user_afflictions)
                 %(and_bot_id)s"""
    default_args["and_bot_id"] = ""    
    con.query("create view candidates_joined_view as %s" % (views["candidates_joined_view"] % default_args))

    views["candidates_joined_filtered_view"] = """
                 select bot_id, screen_name, uid, lcase_body, parent_id, num_followers, num_friends, processed, ts, is_followbacker, maybe_followbacker 
                 from (%s) candidates_joined_view 
                 where num_user_mentions <= 1 and num_media = 0 and num_hashtags <= 2 and num_urls = 0 
                 and not is_retweet and ts > processed - interval 7 day and ts < processed 
                 and num_followers <= 2500 and num_friends <= 2500 and num_followers >= 100 and num_friends >= 100 
                 and language like 'en%%%%' and tweet_language like 'en%%%%' """
    views["candidates_joined_filtered_view"] = views["candidates_joined_filtered_view"] % views["candidates_joined_view"]
    con.query("create view candidates_joined_filtered_view as %s" % (views["candidates_joined_filtered_view"] % default_args))
    
    views["candidates_view"] = """
              select %%(bot_id_comma)s screen_name, uid, num_followers, num_friends, sum(if(parent_id is null, %%(extra_agg)s, 0)) as count, approx_count_distinct(parent_id) as convos
              from (%s) candidates_joined_filtered_view 
              group by %%(bot_id_comma)s uid
              having sum(%%(extra_agg)s) > 0"""
    views["candidates_view"] = views["candidates_view"] % views["candidates_joined_filtered_view"]
    default_args["bot_id_comma"] = "bot_id,"
    default_args["extra_agg"] = "1"
    con.query("create view candidates_view as %s" % (views["candidates_view"] % default_args))
    
    views["candidates_predictors_view"] = """
              select %%(bot_id_comma)s cv.screen_name, uid, 
                     3 * (1 - (1 - num_followers/500) * (1 - num_followers/500)) as follower_score, 
                     3 * (1 - (1 - num_friends/500)   * (1 - num_friends/500))   as friend_score, 
                     (1/2) * convos as convos_score,
                     (1/25) * cv.count as count_score
              from (%s) cv """
    views["candidates_predictors_view"] = views["candidates_predictors_view"] % views["candidates_view"]
    con.query("create view candidates_predictors_view as %s" % (views["candidates_predictors_view"] % default_args))

    views["candidates_scored_view"] = """
              select %%(bot_id_comma)s screen_name, uid, 
                     follower_score , friend_score , count_score , convos_score,
                     follower_score + friend_score + count_score + convos_score as score 
              from (%s) candidates_predictors_view"""
    views["candidates_scored_view"] = views["candidates_scored_view"] % views["candidates_predictors_view"]
    con.query("create view candidates_scored_view as %s" % (views["candidates_scored_view"] % default_args))

    # bother targeting views
    #
    views["targeting_state_view"] = """
              select user_id as ts_bot_id, parent_id as user_id, max(ts) as last_targeted, count(*) as tweets_to 
              from bot_tweets join bots 
              on bot_tweets.user_id = bots.id 
              where parent_id is not null %(and_bots_dot_id)s
              group by %(user_id_comma)s bot_tweets.parent_id """
    default_args["and_bots_dot_id"] = ""
    default_args["user_id_comma"] = "user_id,"
    con.query("create view targeting_state_view as %s" % views["targeting_state_view"] % default_args)
    
    views["botherable_friends_view"] = """
              select %%(bot_id_comma)s ufs.id as user_id 
              from user_following_status ufs 
              left join bot_tweets bs on bs.user_id = ufs.id and bs.parent_id = ufs.bot_id 
              left join (%s) ltv on ufs.id = ltv.user_id and ufs.bot_id = ltv.ts_bot_id 
              where ufs.following = 1 
              and (ltv.last_targeted is null or ltv.last_targeted < now() - interval 7 day) 
              and ufs.id not in (select id from user_afflictions) 
              and ufs.id not in (select user_id from followbackers_view) 
              %%(and_bot_id)s
              group by %%(bot_id_comma)s ufs.id 
              having count(bs.user_id) > 0 or ltv.tweets_to is null or ltv.tweets_to <= 1"""
    views["botherable_friends_view"] = views["botherable_friends_view"] % views["targeting_state_view"]
    con.query("create view botherable_friends_view as %s" % (views["botherable_friends_view"] % default_args))
    
    views["botherable_tweets_view"] = """
              select %%(bot_id_comma)s bfv.user_id, ts.id, ts.lcase_body, timestampdiff(second, ts.ts, now()) as recentness, 
                     tweets.favorites, tweets.retweets 
              from (%s) bfv join tweets_storage ts join tweets tweets 
              on bfv.user_id = ts.user_id and ts.user_id = tweets.user_id and ts.id = tweets.id 
              where ts.num_user_mentions = 0 and ts.num_media = 0 and ts.num_hashtags <= 2 and ts.num_urls = 0 
              and ts.parent_id is null and not ts.is_retweet and ts.ts > now() - interval 7 day 
              and ts.maybe_followbacker = 0 
              and ts.language like 'en%%%%' 
              %%(and_extra_pred)s"""
    default_args["and_extra_pred"] = ""
    views["botherable_tweets_view"] = views["botherable_tweets_view"] % views["botherable_friends_view"]
    con.query("create view botherable_tweets_view as %s" % (views["botherable_tweets_view"] % default_args))
    
    views["botherable_tweets_predictors_view"] = """
              select %%(bot_id_comma)s btv.user_id, btv.id, 
                     - recentness / (24 * 60 * 60) as recentness_score, 
                     2 * (1 - (favorites/3 - 1) * (favorites/3 - 1)) as favorites_score, 
                     2 * (1 - (retweets/2 - 1)  * (retweets/2 - 1))  as retweets_score
              from (%s) btv"""
    views["botherable_tweets_predictors_view"] = views["botherable_tweets_predictors_view"] % views["botherable_tweets_view"]
    con.query("create view botherable_tweets_predictors_view as %s" % (views["botherable_tweets_predictors_view"] % default_args))
    
    views["botherable_tweets_scored_view_internal"] = """
              select %%(bot_id_comma)s user_id, id, 
                     recentness_score , favorites_score , retweets_score ,
                     recentness_score + favorites_score + retweets_score as score 
              from (%s) subq"""
    views["botherable_tweets_scored_view_internal"] = views["botherable_tweets_scored_view_internal"] % views["botherable_tweets_predictors_view"]
    con.query("create view botherable_tweets_scored_view_internal as %s" % (views["botherable_tweets_scored_view_internal"] % default_args))
    
    con.query("create view botherable_tweets_scored_view as "
              "select bots.screen_name as bot_name, concat('www.twitter.com/', users.screen_name, '/status/',csv.id) as url, "
              "       recentness_score , favorites_score , retweets_score , score "
              "from botherable_tweets_scored_view_internal csv join bots join users "
              "on bots.id = csv.bot_id and users.id = csv.user_id ")


    # GC friend view
    con.query("""
              create view gc_friends_view as
              select bot_id, ufs.id as user_id 
              from user_following_status ufs 
              left join bot_tweets bs on bs.user_id = ufs.id and bs.parent_id = ufs.bot_id 
              left join targeting_state_view ltv on ufs.id = ltv.user_id and ufs.bot_id = ltv.ts_bot_id 
              where ufs.following = 1 
              and (ltv.last_targeted < now() - interval 7 day) 
              and ufs.id not in (select id from user_afflictions) 
              group by bot_id, ufs.id 
              having count(bs.user_id) = 0 and ltv.tweets_to >= 2""")
    
    # web populating views
    con.query("create view conversations_view as "
              "select bot_tweets.conversation_id, max(bot_tweets.id) as max_id, count(*) as count, "
              "       count(bots.id) as to_bots, count(bots2.id) as from_bots, max(bots2.screen_name) as bot_name, "
              "       ifnull(sum(cu.upvotes), 0) as upvotes, "
              "       sum((not isnull(bots2.id)) * bot_tweets.favorites) as bot_favorites, "
              "       sum((not isnull(bots2.id)) * bot_tweets.retweets)  as bot_retweets   "
              "from bot_tweets "
              "     left join bots bots  on bot_tweets.parent_id = bots.id "
              "     left join bots bots2 on bot_tweets.user_id = bots2.id "
              "     left join conversation_upvotes cu on cu.conversation_id = bot_tweets.conversation_id "
              "group by bot_tweets.conversation_id")

    return views
