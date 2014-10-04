import vocab
import random

def ChooseResponse(tweet, apiHandler, g_data, attempts = 10):
    tweets = TweetsIterator(tweet apiHandler)
    for i in xrange(attempts):
        tweets.Reset()
        rw = Rewriter(tweets, g_data.NextSentence(tweet["text"]), g_data)
        result = rw.Rewrite()
        if result:
            return result
    return False

class TweetsIterator:
    def __init__(self, original, apiHandler):
        self.ix = 0
        self.original = original
        self.user_name = original.GetUser().GetName()
        self.reply_id = original.GetInReplyToStatusId()
        self.original_reply_id = self.reply_id
        self.reply_id = original.GetInReplyToStatusId()
        self.apiHandler = apiHandler
        self.userTweets = None

    def Next(self, allowUserTweets):
        if ix == -1:
            return False
        if ix == 0:
            ix = ix + 1
            return self.original
        if not reply_id is None:
            assert ix == 1
            try:
                nextTweet = self.apiHandler.ShowStatus(self.reply_id)
                self.reply_id = nextTweet.GetInReplyToStatusId()
                return nextTweet.GetText()
            catch:
                self.reply_id = None
        if allowUserTweets and self.userTweets is None:
            assert ix == 1
            try:
                self.userTweets = [t.GetText() for t in self.apiHandler.ShowStatuses(self.user_id)]
            catch:
                ix = -1
                return False
        if ix <= len(self.userTweets):
            return self.userTweets[ix-1]
        return False

    def Reset(self):
        self.ix = 0
        self.reply_id = self.original_reply_id

def SplitSentence(sentence):
    sentence = sentence.split("(")
    result = []
    for i in xrange(1,len(sentence)):
        sentence[i] = ("(" + sentence[i]).split(")")
        for j in xrange(len(sentence[i])-1):
            sentence[i][j] = sentence[i][j] + ")"
    for s in sentence:
        for t in s:
            result.append(t)
    return result


class Rewriter:
    def __init__(self, tweets, sentence, g_data):
        self.progressEver = False
        self.vocab = Vocab(g_data)
        self.tweets = tweets
        self.sentence = sentence
        assert self.AddVocab()

    # adds the next tweet, if available.  
    #
    def AddVocab(self):
        tweet = self.tweets.Next(self.progressEver)
        if tweet:
            self.vocab.Add(tweet)
            return True
        return False

    # returns true if a change happened, false otherwise
    #
    def RewriteSingle(self, ix):
        if self.sentence[ix][0] != "(":
            return False
        word = self.vocab[self.sentence[ix][0]]
        if word is not None
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
                ix = 0 if self.RewriteSingle(ix) else ix + 1
            if self.AllDone():
                return self.Finalize()
            if not self.AddVocab():
                return False

    def Finalize():
        for i in xrange(len(self.sentence)-1):
            if len(self.sentence[i]) > 3 and self.sentence[i][-3:] == " a ":
                if self.sentence[i+1][0] in ['a','e','i','o']:
                    self.sentence[i][-1] = 'n'
                    self.sentence[i].append(' ')
        return "".join(self.sentence).replace(" ,",",").replace(" .",".").replace(" !","!").replace(" ?","?").strip()
