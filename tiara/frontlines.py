import random

# A Frontline is a simple class with two methods: Triage and Respond
# Triage returns a number [0,1] or -1 to say if it thinks its response is approproate.
# Response generates a response

class Frontline(object):
    pass

# An extremely simple Frontline example.
# We probably want to use pattern's parse library to really make this work
#
class FL_Example(Frontline):
    def Triage(self, g_data, tweet):
        if tweet.GetText() == "I think vaccines cause autism":
            return 1.0
        return -1
    
    def Respond(self, g_data, tweet):
        if g_data.myName == "VanTheWinterer": # since both functions take g_data, the response can depend on the individual
            return "I'm Van the Man, and I think Autism causes Vaccines!"
        elif socialbot_types[g_data.myName] == "doctor":
            return "As a doctor, I can assure you they do not"
        else:
            return random.choice(["No they dont!",
                                  "You're a moron"])


class FL_NaiveSimple(Frontline):
    def __init__(self, hashtags, words, responses):
        self.responses = responses
        self.hashtags = hashtags
        self.words = words

    def Triage(self, g_data, tweet):
        if len(self.hashtags) > 0:
            for h in self.hashtags:
                if h in [ht.lower() for ht in tweet["hashtags"]]:
                    return 1.0 - 0.5**len([i for i in self.words if i in tweet["text"].lower()])
            return -1.0
        return 1.0 - 0.5**len([i for i in self.words if i in tweet["text"].lower()])

    def Respond(self, g_data, tweet):
        return random.choice(self.responses)

def PickFrontline(g_data, tweet, frontlines):
    best_triage = -1.0
    best_fl = None
    for fl in frontlines:
        trg = fl.Triage(g_data, tweet)
        if best_triage < trg and 0 < trg:
            best_triage = trg
            best_fl = fl
    return best_triage, best_fl

def TargetAndRespond(g_data, tweets, frontlines):
    best_tweet = None
    best_fl = None
    best_triage = -1.0
    for tweet in tweets:
        trg, fl = PickFrontline(g_data, tweet, frontlines)
        if best_triage < trg and 0 < trg:
            best_triage = trg
            best_tweet = tweet
            best_fl = fl
    if best_triage > -1.0:
        return best_fl.Respond(g_data,best_tweet), best_tweet
    return None, None
        
def RunFrontlines(g_data, tweet, frontlines):
    print tweet['text']
    tr, fl = PickFrontline(g_data, tweet, frontlines)
    print "triage = %f" % tr
    if not fl is None:
        return fl.Respond(g_data, tweet)
    return None

socialbots_frontlines = [
     FL_NaiveSimple(["cdcwhistleblower","hearthiswell"],
                    ["children","child","son","daughter","mom","mother"],
                    [
                        "What makes you so sure the children's problems are a result of vaccines?",
                        "The causes of autism are not well understood.  You certainly can't know how a child got autism...",
                        "Because nothing says love of children like letting them die of measles.",
                        "Influenza has killed over a thousand American children in the last 10 years.  Vaccines have killed zero."
                    ]),
    FL_NaiveSimple(["cdcwhistleblower","hearthiswell"], #this is clearly a bad argument, but no matter
                   ["ethics","morals"],
                   [
                       "The CDC does have ethics: They don't want to freak everyone out over science which is almost certainly wrong!",
                       "There have been numerous studies showing no link at all!  It would be immoral to scare people over it.",
                       "Immoral is tricking and misquoting Dr. Thompson.  This isn't a malicious data ommision, its just science."
                   ]),
    FL_NaiveSimple(["cdcwhistleblower","hearthiswell"],
                   ["omit","omission"],
                   [
                       "Omitting a small sample of data hardly constitutes proving vaccines cause autism.",
                       "Vaccines still don't cause autism; according to years and years of research.",
                       "Some reasearchers having messed up their sciences absolutely does not mean vaccines cause autism.  They don't!",
                       "The ommited data was not apples-to-apples with between control and experimental.  It doesn't make scientific sense to include!"
                   ]),
    FL_NaiveSimple(["cdcwhistleblower","hearthiswell","vaxtruth"],
                   ["truth","lies","lie","lies"],
                   [
                       "How are you so sure about that?",
                       "You just know everything, don't you...",
                       "What truth?  What lies?",
                       "You antivax people make me sick!  Every bit of science says vaccines are not only safe, but essential!  #hearTHISwell"
                   ]),
    FL_NaiveSimple(["cdcwhistleblower","hearthiswell"],
                   ["cover","covered","coverup","blackout"],
                   [
                       "I think the media just isn't reporting on it because its... you know... utter bullshit",
                       "You the the CDC is stupid enough to misplace a huge chunk of data but smart enough to create a widespread conspiracy... riiight.",
                       "If you believe this conspiracy theory, I've got a bridge in brooklyn and I think we can do business.",
                       "You, sir, are a dumbfuck."
                    ]),
    FL_NaiveSimple(["tcot","pjnet"],
                   ["Darren","Wilson","DarrenWilson"],
                   [
                       "#BlackLivesMatter.  Darren is a murder, and this isn't justice.",
                       "People are upset.  Can you blame them.  An innocent man is shot, and the shooter walks away?  #ferguson #blacklivesmatter",
                       "This man is avoiding justice.  Hiding behind a badge doesn't make murder ok!",
                       "This isn't about cops or Darren Wilson or even Mike Brown.  Its about #whitesupremacy!  #blacklivesmatter #handsupdontshoot",
                       "Darren Wilson should be in handcuffs.  Dispicable!",
                       "Do you know why the police are militarizing.  Because they know people are going to be pissed!  Because they should be!",
                       "This isn't justice.  But I've heard #karmasabitch, so theirs hope"
                   ]),
    ]
    
socialbot_types = {
    "VanTheWinterer" : "advocate",
    "ImDrErnst" : "doctor",
    "MarzipanIAm" : "doctor",
    "Rianna__Taylor" : "teen",
    "AntonioBacusAmI" : "teen",
    "Alexa_Smith9584" : "parent",
    "LeeeroyOOOOman" : "parent",
    "KarlKreegz20" : "liberal",
    "QueenNatLat" : "liberal",
    "Anold__Doyle" : "conservative",
    "geneverasalomon" : "conservative",
    "AppleBottomGrg" : "christian",
    "MariaMunozOhMy" : "christian",
    "SammyHerzt" : "muslim",
    "LydiaGoldman253" : "advocate",
    }


