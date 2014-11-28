import random
import grammar as g

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
    def __init__(self, words, responses, types=["conservative","liberal","general","teen","advocate","muslim","christian","doctor","parent"]):
        self.responses = responses
        global frontline_tags
        self.words = words
        self.any_required = False
        self.types = types
        for r,tag in responses:
            assert tag in frontline_tags , tag
            assert len(r) <= 125 , (len(r),r)
        for i in xrange(len(self.words)):
            if not isinstance(self.words[i][1], list):
                self.words[i] = (self.words[i][0],[self.words[i][1]])
                if self.words[i][0] <= 0:
                    self.any_required = True

    def Triage(self, g_data, tweet):
        if not socialbot_types[g_data.myName] in self.types:
            return -1.0
        text = tweet.GetText().lower()
        result = 0.0
        found_required = not self.any_required
        for p,ws in self.words:
            found = True
            for w in ws:
                if not w in text:
                    found = False
            if not found:
                continue
            result += abs(p)
            if p <= 0:
                found_required = True
        return result if found_required else -1

    def Respond(self, g_data, tweet):
        return random.choice(self.responses)

def PickFrontline(g_data, tweet, frontlines):
    best_triage = -1.0
    best_fl = []
    for fl in frontlines:
        trg = fl.Triage(g_data, tweet)
        if best_triage < trg and 0 < trg:
            best_triage = trg
            best_fl = [fl]
        elif best_triage == trg:
            best_fl.append(fl)
    return best_triage, (None if len(best_fl) == 0 else random.choice(best_fl))

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
        assert not best_tweet is None
        response, tag = best_fl.Respond(g_data,best_tweet),
        return response, tag, best_tweet
    return None, None, None
        
def RunFrontlines(g_data, tweet, frontlines):
    print tweet.GetText()
    tr, fl = PickFrontline(g_data, tweet, frontlines)
    print "triage = %f" % tr
    if not fl is None:
        return fl.Respond(g_data, tweet)
    return None



conservative_hashtags = ["tcot","ccot","lcot","tpot","teaparty","pjnet"]

def AndOverOr(value, andands, orands):
    orands = g.phrase(orands)
    return [(value,[a]+orands) for a in andands]

def Conservative(value, tag):
    return AndOverOr(value, conservative_hashtags, tag)

frontline_tags = ["dontknowcause","novaxisworse","noalarmist","notscience","conspiracy","antidarren","fergusonupset",
                  "tcotlove","tcotshutup","loveobamacare","hateobamacare","knowmuslims","nicemuslims","obamaponzi","insult","tellmemore"]

socialbots_frontlines = [
     FL_NaiveSimple([(-0.25,["injury","vax"]),(-0.25,["vax","autism"]),
                     (-0.25,"cdcwhistleblower"),
                     (-0.25,"hearthiswell"),
                     (-0.25,["autism","vaccine"]),
                     (-0.25,["injury","vaccine"]),
                     (0.25,"children"),
                     (0.25,"child"),
                     (0.25,"son"),
                     (0.25,"daughter"),
                     (0.25,"mom"),
                     (0.25,"mother")],
                    [
                        ("What makes you so sure the children's problems are a result of vaccines?",
                         "dontknowcause"),
                        ("The causes of autism are not well understood.  You certainly can't know how a child got autism...",
                         "dontknowcause"),
                        ("Because nothing says love of children like letting them die of measles.",
                         "novaxisworse"),
                        ("American children die of the flu every year.  90% of them are unvaccinated.  Don't be dumb! #getvaccinated",
                         "novaxisworse"),
                        ("Influenza has killed over a thousand American children in the last 10 years.  Vaccines have killed zero.",
                         "novaxisworse"),
                        ("As far as I know, theres no scientific evidence that injuries blamed on vax were actually caused by vax.  But vax save lives!",
                         "dontknowcause"),
                        ("Not vaccinating a child puts them (and society) at serious risk!  People die of measles!  #preventpreventabledisease",
                         "novaxisworse")
                    ]),
    FL_NaiveSimple([(-0.25,["vax","injury"]),(-0.25,["vax","autism"]),
                    (-0.25,"cdcwhistleblower"),
                    (-0.25,"hearthiswell"),
                    (-0.25,["autism","vaccine"]),
                    (-0.25,["injury","vaccine"]),
                    (0.25,"ethics"),
                    (0.25,"morals")],
                    [
                       ("The CDC does have ethics: They don't want to freak everyone out over science which is almost certainly wrong!",
                        "noalarmist"),
                       ("There have been numerous studies showing no link at all!  It would be immoral to scare people over it.",
                        "noalarmist"),
                       ("Immoral is tricking and misquoting Dr. Thompson.  This isn't a malicious data ommision, its just science.",
                        "notscience"),
                       ("Nothing could be more immoral than choosing not to vaccinate a child.  Why let them get sick of preventable diseases?",
                        "novaxisworse"),
                       ("Its like people don't understand that children DIE of diseased which could be prevented by vaccination.  #morals #ethics",
                        "novaxisworse"),
                       ("Don't tell me about morals or ethics... It isn't just you that'll get whooping cough.  #diseasesspread",
                        "novaxisworse")
                    ]),
    FL_NaiveSimple([(-0.25,["vax","injury"]),(-0.25,["vax","autism"]),
                    (-0.25,"cdcwhistleblower"),
                    (-0.25,"hearthiswell"),
                    (-0.25,["autism","vaccine"]),
                    (-0.25,["injury","vaccine"]),
                    (0.25,"omit"),
                    (0.25,"omission")],
                   [
                       ("Omitting a small sample of data hardly constitutes proving vaccines cause autism.",
                        "notscience"),
                       ("Vaccines still don't cause autism; according to years and years of research.",
                        "notscience"),
                       ("Some reasearchers having messed up their sciences absolutely does not mean vaccines cause autism.  They don't!",
                        "notscience"),
                       ("The ommited data was not apples-to-apples between control and experimental.  It makes no scientific sense to include!",
                        "notscience"),
                       ("You think ommited datapoints means we should immidiately reject 30 years of science?",
                        "notscience"),
                       
                       ("Remember: people being bad at their job does not imply their conclusion is wrong.  All the science says vax is safe.",
                        "notscience"),
                       ("Don't misinterpret the #cdcwhistleblower.  This is a technical mistake; vaccines remain safe. #getvaccinated",
                        "notscience")
                    ]),
    FL_NaiveSimple([(-0.25,["vax","injury"]),(-0.25,["vax","autism"]),
                    (-0.25,"cdcwhistleblower"),
                    (-0.25,"hearthiswell"),
                    (-0.25,["autism","vaccine"]),
                    (-0.25,["injury","vaccine"]),
                    (0.25,"truth"),
                    (0.25,"lies"),
                    (0.25,"lie"),
                    (0.25,"lies"),
                    (0.25,"fraud")],
                   [
                       ("How are you so sure about that?",
                        "dontknowcause"),
                       ("You just know everything, don't you...",
                        "dontknowcause"),
                       ("What truth?  What lies?",
                        "conspiracy"),
                       ("You antivax people make me sick!  Every bit of science says vaccines are not only safe, but essential!  #hearTHISwell",
                        "novaxisworse"),
                       ("Tell me what you think the real truth is?",
                        "dontknowcause"),
                       ("Do you mind explaining to me you're 'truth' and how you know it?",
                        "conspiracy")
                   ]),
    FL_NaiveSimple([(-0.25,["vax","injury"]),(-0.25,["vax","autism"]),
                    (-0.25,"cdcwhistleblower"),
                    (-0.25,"hearthiswell"),
                    (-0.25,["autism","vaccine"]),
                    (-0.25,["injury","vaccine"]),
                    (0.25,"cover"),
                    (0.25,"covered"),
                    (0.25,"coverup"),
                    (0.25,"blackout")],
                   [
                       ("I think the media just isn't reporting on it because its... you know... utter bullshit",
                        "conspiracy"),
                       ("You think the CDC is stupid enough to misplace a huge chunk of data but smart enough to create a widespread conspiracy?",
                        "conspiracy"),
                       ("If you believe this conspiracy theory, I've got a bridge in brooklyn and I think we can do business.",
                        "conspiracy"),
                       ("No US government agency is competent enough to even consider a conspiracy.  They'd mess it up.",
                        "conspiracy"),
                       ("There is no such thing as a govt conspiracy theory.  No such thing as a govt coverup with media help.",
                        "conspiracy"),
                       ("Dr. Thompson is definately not smart enough to organize a #mediablackout.  Theres no conspiracy; vaccines remain safe!",
                        "conspiracy")
                       
                    ]),
    FL_NaiveSimple([(0.025,["darren","wilson"]),
                    (0.025,"darrenwilson"),
                    (0.025,"ferguson"),
                    (0.025,["mike","brown"])],
                   [
                       ("#BlackLivesMatter.  Darren is a murder, and this isn't justice.",
                        "antidarren"),
                       ("People are upset.  Can you blame them?  An innocent man is shot, and the shooter walks away?  #ferguson #blacklivesmatter",
                        "fergusonupset"),
                       ("This man is avoiding justice.  Hiding behind a badge doesn't make murder ok!",
                        "antidarren"),
                       ("This isn't about cops or Darren Wilson or even Mike Brown.  Its about #whitesupremacy!  #blacklivesmatter #handsupdontshoot",
                        "fergusonupset"),
                       ("Darren Wilson should be in handcuffs.  Dispicable!",
                        "antidarren"),
                       ("Do you know why the police are militarizing.  Because they know people are going to be pissed!  Because they should be!",
                        "fergusonupset"),
                       ("This isn't justice.  But I've heard #karmasabitch, so theirs hope.  #blacklivesmatter",
                        "antidarren")
                   ]),
    FL_NaiveSimple([(0.5, ["riot","ferguson"]),
                    (-0.2,["darren","wilson"]),
                    (-0.2,"darrenwilson"),
                    (-0.2,"ferguson"),
                    (-0.2,["mike","brown"])],
                   [
                       ("Why do you think people are rioting?  Theres no other way for their voices to be heard...",
                        "fergusonupset"),
                       ("No justice, no peace. Dems da rules #blacklivesmatter",
                        "fergusonupset"),
                       ("People are rioting because they've tried everything else.",
                        "fergusonupset"),
                       ("A black riot for justice is thuggery, a white riot over sports or pumpkins is just kids being kids?",
                        "fergusonupset"),
                       ("You should riot too.",
                        "fergusonupset")
                   ]),
    FL_NaiveSimple([(-0.001,t) for t in conservative_hashtags],
                   [
                       ("Oh shut up all ready!",
                        "tcotshutup"),
                       ("Right is wrong! #rightiswrong",
                        "tcotshutup"),
                       ("Seriously?  You tcot/ccot people are all the same!",
                        "tcotshutup"),
                       ("What garbage..",
                        "tcotshutup"),
                       ("Absolute poppycock!",
                        "tcotshutup"),
                       ("Who do you even think you are!",
                        "tcotshutup"),
                       ("You really believe that crap?",
                        "tcotshutup"),
                       ("Its like you don't even thing about people who are different than you...",
                        "tcotshutup"),
                       ("You are a rude blow-hard and need to #stop!  #stahp",
                        "tcotshutup"),
                       ("Why do you tweet this trash?",
                        "tcotshutup"),
                       ("And where did you get that idea?  #learnthefacts",
                        "tcotshutup"),
                   ],
                   types = ["liberal"]),
    FL_NaiveSimple([(-0.001,t) for t in conservative_hashtags],
                   [
                       ("Amen brother.  #tcot",
                        "tcotlove"),
                       ("Tell me more!",
                        "tcotlove"),
                       ("My god yes!  How can I learn more about this import issue?  #tcot",
                        "tcotlove"),
                       ("You better believe it!  #justthefacts",
                        "tcotlove"),
                       ("Go ooooon.....",
                        "tcotlove"),
                       ("You've got my full attention.  #tellmemore",
                        "tcotlove"),
                   ],
                   types = ["conservative","christian"]),
    FL_NaiveSimple([(-1.0,["islam","jihad"]),
                    (-1.0,"stopislam")] +
                    Conservative(-1.0,"realislam") + 
                    Conservative(-1.0,"thisisislam"),
                   [
                       ("How many Muslims do you know, sir?",
                        "knowmuslims"),
                       ("I take it you've met many a Muslim. Is that how you know all this?",
                        "knowmuslims"),
                       ("You know nearly a quarter of the world follows Islam.  We should probably be nice to them.",
                        "knowmuslims"),
                       ("Hey!  Be nice to our Muslim brothers and sisters!",
                        "nicemuslims"),
                       ("RUDE!",
                        "nicemuslims"),
                       ("Did you learn that from your Muslim friends?",
                        "knowmuslims"),
                       ("You are a massive hater.",
                        "nicemuslims"),
                       ("Don't be a hater.",
                        "nicemuslims"),
                       ("You've probably never met a Muslim.  #thisisnotislam",
                        "knowmuslims"),
                       ("All 1.6 million Muslims are jihadists?  Is that what you think?",
                        "knowmuslims"),
                   ]),
    FL_NaiveSimple([(-.075,"obamacare")],
                   [
                       ("Why do they call it #obamacare anyways?  Obama doesn't care! #tcot",
                        "hateobamacare"),
                       ("How on earth are we going to stop this thing becore our country falls appart?",
                        "hateobamacare"),
                       ("More like #obamascare!",
                        "hateobamacare")
                   ],
                   types=["conservative","christian"]),
    FL_NaiveSimple(Conservative(-.075,"obamacare"),
                   [
                       ("Obamacare is great!  Affordable care for all!",
                        "loveobamacare"),
                       ("Why do you want people to be sick?",
                        "loveobamacare"),
                       ("Ten million Americans newly with health insurance?  Sounds like a win to me!",
                        "loveobamacare"),
                   ],
                   types=["liberal","general","advocate","muslim","doctor","parent"]),
    FL_NaiveSimple([(-1.0,["obamacare","ponzi"])],
                    [
                       ("I feel like you don't know what a ponzi scheme is...",
                        "obamaponzi"),
                       ("Obamacare aside, a ponzi scheme is when you pay old investors from new investors but never make money.",
                        "obamaponzi"),
                       ("This word you keep using, ponzi scheme, I think it means what you think it means...",
                        "obamaponzi"),
                       ("Listen: healthcare isn't a get-rich-quick-scheme.  It doesn't pay out.  Its not a ponzi scheme!",
                        "obamaponzi"),
                       ("#Obamacare isn't a ponzi scheme.  Social security is much more analogous to a ponzi scheme. This is completely different",
                        "obamaponzi")
                    ])

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


