import vocab as v
import random
import twitter
from sentence_gen import Sentence

def ChooseResponse(g_data, user=None, tweet=None, attempts = 10):
    assert user is None or tweet is None, "cannot ChooseResponse to both user_name and tweet"
    inReply = user is None
    tweets = TweetsIterator(g_data, original=tweet, user=user)
    for i in xrange(attempts):
        tweets.Reset()
        sentence = Sentence()
        g_data.TraceInfo("Rewriting sentence \"%s\"" % " ".join(sentence))
        rw = Rewriter(tweets, sentence, inReply, g_data)
        result = rw.Rewrite()
        if result and inReply:
            result = '@' + tweet.GetUser().GetScreenName() + ": " + result
        if result and len(result) <= 140:
            return result
        elif result:
            g_data.TraceWarn("Failing long tweet \"%s\"" % result)
        else:
            g_data.TraceWarn("Failed to rewrite \"%s\"" % ' '.join(sentence))
    return None

class RandomWordIterator:
    def __init__(self, g_data):
        self.g_data = g_data

    def Next(self, ignore):
        result = twitter.Status()
        result.SetText(self.g_data.RandomEnglishWord())
        result.SetUser(twitter.User())
        return result

    def Reset(self):
        pass

class TweetsIterator:
    def __init__(self, g_data, original = None, user=None):
        self.ix = 0
        self.g_data = g_data
        self.userTweets = None
        self.reply_id = None
        self.original = None
        if not original is None:
            self.original = original
            self.user_id = original.GetUser().GetScreenName()
            self.reply_id = original.GetInReplyToStatusId()
        else:
            self.user_id = user.GetScreenName()
        self.original_reply_id = self.reply_id

    def Next(self, allowUserTweets):
        if self.ix == -1:
            return False
        if self.ix == 0:
            self.ix = self.ix + 1
            if not self.original is None:
                return self.original
        if not self.reply_id is None:
            assert self.ix == 1
            nextTweet = self.g_data.ApiHandler().ShowStatus(self.reply_id)
            if not nextTweet is None:
                self.reply_id = nextTweet.GetInReplyToStatusId()
                return nextTweet
            else:
                self.reply_id = None
                g_data.TraceWarn("Unable to get reply, resorting to getting all user tweets")
        if allowUserTweets and self.userTweets is None:
            assert self.ix == 1
            self.userTweets = self.g_data.ApiHandler().ShowStatuses(screen_name = self.user_id)
            if self.userTweets is None:
                self.ix = -1
                self.g_data.TraceWarn("Unable to get user tweets, failing TweetsIterator")
                return False
            self.userTweets = self.userTweets
        if allowUserTweets and self.ix <= len(self.userTweets):
            self.ix += 1
            return self.userTweets[self.ix-2]
        elif allowUserTweets:
            result = twitter.Status()
            result.SetText(self.g_data.RandomEnglishWord())
            result.SetUser(twitter.User())
            return result
        return False

    def Reset(self):
        self.ix = 0
        self.reply_id = self.original_reply_id


class Rewriter:
    def __init__(self, tweets, sentence, inReply, g_data):
        self.g_data = g_data
        self.progressEver = not inReply
        self.vocab = v.Vocab(g_data)
        self.tweets = tweets
        self.sentence = sentence
        assert self.AddVocab()

    # adds the next tweet, if available.  
    #
    def AddVocab(self):
        tweet = self.tweets.Next(self.progressEver)
        if tweet:
            self.vocab.Add(tweet.GetText(), addSimilar = tweet.GetUser().GetScreenName() == self.g_data.myName)
            return True
        return False

    # returns true if a change happened, false otherwise
    #
    def RewriteSingle(self, ix):
        if self.sentence[ix][0] != "(":
            return False
        word = self.vocab[self.sentence[ix]]
        if not word is None:
            self.sentence[ix] = word
            self.vocab.Register(word)
            self.progressEver = True
            return True
        return False

    def AllDone(self):
        return all([s[0] != '(' for s in self.sentence])

    # returns sentence if rewrite is sucessful, false otherwise
    #
    def Rewrite(self):
        while True:
            ix = 0
            while ix < len(self.sentence):
                ix = (0 if self.RewriteSingle(ix) else ix + 1)
            if self.AllDone():
                return self.Finalize()
            if not self.AddVocab():
                return False

    def Finalize(self):
        return Finalize(self.sentence)

def Finalize(sentence):
    for i in xrange(len(sentence)-1):
        if sentence[i] == "a" and sentence[i+1][0] in ['a','e','i','o']:
            sentence[i] = "an"
    return " ".join(sentence).replace(" ,",",").replace(" .",".").replace(" !","!").replace(" ?","?").replace(" ;",";").replace(" - ","-").strip()
