import data_gatherer as dg
from util import *
import re

class NewsFeedGenerator(object):
    def __init__(self, bots, database):
        self.bots = bots
        self.database = database

    # returns a list of lists of tweets, representing recent conversations between bots and the outside world
    def GetConversations(self):
        convos = []
        for b in self.bots:
            convos.extend(dg.MakeFakeDataMgr(b, self.database).RecentConversations(100))
        for c in convos:
            c.sort(key = lambda b: b.GetId())
        convos.sort(key = lambda c: -c[-1].GetId())
        return convos

    def FormatTweet(self, tweet):
        fmt = ("<blockquote><a href=\"%s\" target=\"_blank\">"
               "<img border=0 src=\"/images/%s\" alt=\"View Original Tweet\" width=50 height=50/>"
               "<strong>%s:</strong></a><blockquote><div>%%s</div></blockquote>"
               "</blockquote>")
        fmt = fmt % (GetURL(tweet), 
                     "tiaraboom.jpeg" if tweet.GetUser().GetScreenName() in self.bots else "egg.png", 
                     tweet.GetUser().GetScreenName())
        return fmt % self.FormatTweetText(tweet)

    def FormatTweetText(self, tweet):
        result = tweet.GetText().encode("utf8")
        result = re.sub(r'#([0-9A-Za-z_]*)',
                        r'<a href="https://twitter.com/hashtag/\1" target="_blank">&#35;\1</a>',
                        result)
        result = re.sub(r'@([0-9A-Za-z_]*)',
                        r'<a href="https://twitter.com/\1" target=\"_blank\">@\1</a>',
                        result)
        return result

    def FormatConversation(self, convo):
        return "\n".join([self.FormatTweet(t) for t in convo])
        
    def GetAndFormatConversations(self):
        return "<br><br><br><br>\n".join([self.FormatConversation(t) for t in self.GetConversations()])
