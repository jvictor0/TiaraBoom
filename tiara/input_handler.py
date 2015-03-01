import rewriter as r
import twitter
import random
from util import *
import artrat_utils as au

class InputHandler:
    def __init__(self, name, func, help):
        self.name = name
        self.func = func
        self.help = help

    def Apply(self, g_data, args):
        ret = self.func(g_data, args)
        if ret is None:
            return "error"
        if isinstance(ret, bool):
            if ret:
                return "ok"
            return "error"
        if isinstance(ret, basestring):
            return ret
        return "ok"

def HandleSearchReply(g_data, input):
    term = ' '.join(input)
    tweets = [t for t in g_data.ApiHandler().Search(term) if g_data.SocialLogic().BotherAppropriate(t)]
    if not tweets is None and len(tweets) > 0:
        tweet = random.choice(tweets)
        result = g_data.SocialLogic().ReplyTo(tweet)
        if not result is None:
            return GetURL(result)
        return "error replying to tweet: %s" % GetURL(tweet)
    if tweets is None:
        return "error searching for term"
    return "no tweets found matching search term"

def HandleSearch(g_data, input):
    term = ' '.join(input)
    tweets = [t for t in g_data.ApiHandler().Search(term)]
    if not tweets is None and len(tweets) > 0:
        return "\n".join(["%s: Repliable = %s" % (GetURL(t),g_data.SocialLogic().BotherAppropriate(t)) for t in tweets])
    if tweets is None:
        return "error searching for term"
    return "no tweets found matching search term"

def HandleReply(g_data, input):
    if len(input) != 1 or len(input[0]) == 0:
        return "reply takes 1 argument"
    arg = input[0]
    if arg[0] == '@':
        result = g_data.SocialLogic().Bother(arg[1:])
        if result is None:
            return "error in bothering %s" % arg
        return GetURL(result)
    try:
        tid = int(arg)
    except Exception as e:
        return "please use either @username or numerical tweet_id"
    tweet = g_data.ApiHandler().ShowStatus(tid)
    if tweet == None:
        return "could not find tweet %s" % input[0]
    result = g_data.SocialLogic().ReplyTo(tweet)
    if result is None:
        return "error responding to tweet at %s" % GetURL(tweet)
    return GetURL(result)

def HandleTweet(g_data, input):
    flags = [t for t in input if len(t) >= 2 and t[:2] == "--"]
    input = [t for t in input if len(t) < 2 or t[:2] != "--"]
    input = " ".join(input)
    allit = False
    to = None
    response_seed = None
    for f in flags:
        if f == "--alliteration-mode":
            allit = True
        elif f[:len("--to=@")] == "--to=@":
            to = f[len("--to=@"):]
        else:
            return "unrecognized flag %s" % f
    if not to is None:
        to_user = g_data.ApiHandler().ShowUser(screen_name = to)
        if to_user is None:
            return "cannot find user @%s" % to
        response_seed = twitter.Status()
        response_seed.SetText(input)
        response_seed.SetUser(to_user)
        seed = None
    tweet = r.ChooseResponse(g_data, seed = input, tweet=response_seed, alliteration_mode = allit)
    result = g_data.ApiHandler().Tweet(tweet)
    if not result is None:
        print "returning GetURL(result)"
        return GetURL(result)
    return "error sending tweet"

def HandleUserInput(g_data, input):
    input = input.split()
    if len(input) == 0:
        return "syntax error"
    command = input[0]
    if command == "help":
        return "\n".join([h.name + "\n  " + h.help for h in input_handlers])
    input = input[1:]
    for h in input_handlers:
        if h.name == command:
            return h.Apply(g_data, input)
    return "syntax error"

def HandleArtrat(g_data, input):
    if len(input) != 1:
        return "syntax error"
    if g_data.SocialLogic().params["reply"]["mode"] != "artrat":
        return "No articles to refresh for mode %s" % g_data.SocialLogic().params["reply"]["mode"]
    if input[0] == "refresh":
        au.RefreshArticles(g_data)
    elif input[0] == "reset":
        au.ResetArticles(g_data)
    else:
        return "syntax error"
    return "ok"

input_handlers = [
    InputHandler("ping", lambda g_data, x: "pong", "ping the server"),
    InputHandler("reply", HandleReply,
                 "'reply @username' picks a tweet by username and replies to it.\n  'reply 12345' replies to tweet id 12345."),
    InputHandler("tweet", HandleTweet,
                 "'tweet word ...' sends a tweet attempting to use words specified.  For instance 'tweet apple penis' will form a tweet using the words apple and/or penis.  Requires real english words, spelled correctly.\n  flags: --alliteration-mode\n         --to=@<username>"),
    InputHandler("follow", lambda g_data, x: "syntax error" if len(x) != 1 or len(x[0]) == 0 or x[0][0] != '@' else g_data.ApiHandler().Follow(x[0][1:]),
                 "'follow @username' follows username"),
        InputHandler('search', HandleSearch, "search for tweets based on the twitter search api, but don't reply to it.\n  Example: 'search_reply #poop' finds a tweets containing #poop."),
    InputHandler('search_reply', HandleSearchReply, "search for a tweet based on the twitter search api, reply to it.\n  Example: 'search_reply #poop' finds a tweet containing #poop and replies to it."),
    InputHandler('artrat', HandleArtrat, "give an artrat specific command.\n  'artrat refresh' will download any new articles\n  'artrat reset' will reset the state of the artrat database")
    ]
