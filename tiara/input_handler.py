import rewriter as r

class InputHandler:
    def __init__(self, name, func, help):
        self.name = name
        self.func = func
        self.help = help

    def Apply(self, g_data, args):
        ret = self.func(g_data, args)
        if isinstance(ret, bool):
            if ret:
                return "ok"
            return "error"
        if ret is None:
            return "error"
        return ret


def HandleSearchReply(g_data, input):
    term = ' '.join(input)
    tweets = g_data.ApiHandler().Search(term)
    if not tweets is None and len(tweets) > 0:
        return g_data.SocialLogic().ReplyTo(tweets[0])
    return "no tweets found matching search term"

def HandleReply(g_data, input):
    if len(input) != 1 or len(input[0]) == 0:
        return "reply takes 1 argument"
    arg = input[0]
    if arg[0] == '@':
        return g_data.SocialLogic().Bother(arg[1:])
    tweet = g_data.ApiHandler().ShowStatus(int(inp[1]))
    if tweet == None:
        return "error"
    return g_data.SocialLogic().ReplyTo(tweet)

def HandleTweet(g_data, input):
    flags = [t for t in input if len(t) >= 2 and t[:2] == "--"]
    input = [t for t in input if len(t) < 2 or t[:2] != "--"]
    input = " ".join(input)
    allit = False
    for f in flags:
        if f not in ["--alliteration-mode"]:
            return "unrecognized flag: %s" % f
        if f == "--alliteration-mode":
            allit = True
    tweet = r.ChooseResponse(g_data, seed = input, alliteration_mode = allit)
    return g_data.ApiHandler().Tweet(tweet)

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

input_handlers = [
    InputHandler("ping", lambda g_data, x: "pong", "ping the server"),
    InputHandler("reply", HandleReply,
                 "'reply @username' picks a tweet by username and replies to it.\n  'reply 12345' replies to tweet id 12345."),
    InputHandler("tweet", HandleTweet,
                 "'tweet word ...' sends a tweet attempting to use words specified.  For instance 'tweet apple penis' will form a tweet using the words apple and/or penis.  Requires real english words, spelled correctly.\n  The flag --alliteration-mode will make the tweet alliterative: example 'tweet --alliteration-mode apple anus'."),
    InputHandler("follow", lambda g_data, x: "syntax error" if len(x) != 1 or len(x[0]) == 0 or x[0][0] != '@' else g_data.ApiHandler().Follow(x[0][1:]),
                 "'follow @username' follows username"),
    InputHandler('search_reply', HandleSearchReply, "search for a tweet based on the twitter search api, reply to it.\n  Example: 'search_reply #poop' finds a tweet containing #poop and replies to it.")
    ]
