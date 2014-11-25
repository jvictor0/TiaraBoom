from util import *

def cross(as_, bs_, sep=' '):
    return [(a + sep + b).strip() for a in as_ for b in bs_]

# this is just an example charicature called housewife, used basically for (sanity) testing
#
housewife = {
    "interests" : {
        "drink_liquor" : {
            "trans"           : "trans",
            "subjects"        : ["I","Jimmy", ["Jimmy","I"]],
            "objects"         : cross(["some","","a glass of"],
                                      ["wine","penot","beer","YellowTail","Smirnoff","champaign_"]),
            "verbs"           : ["drink","have"],
            "verb_adapters"   : ["loves","enjoys","always #enjoys","seldom #gets to enjoy"],
            "post_adjectives" : ["in bed","at home","at dad's house"],
            "being_targets"   : {
                "this"    : ["fun","yummy","great","the best"],
                "subject" : ["drunk","sleepy"]
                },
            "pronouns"         : { "Jimmy" : "he" }
            },
        "watch_sports" : {
            "trans"           : "trans",
            "subjects"        : ["I","Jimmy","the kids",["Jimmy","I"],["the kids","Jimmy"],["the kids","I"]],
            "objects"         : ["HBO","Game of Thrones","Mad Men","the game","football"],
            "verbs"           : ["watch"],
            "secondary_clauses" : ["in bed","at home","at dad's house","on tv"]
            }
        },
    }

conservative = {
    "interests" : {
        "america" : {
            "trans"             : "trans",
            "subjects"          : ["I","my grandpappy",["my grandpappy","I"]],
            "objects"           : ["fireworks","cans of beer"],
            "verbs"             : ["#shoot","#launch"],
            "post_adjectives"   : ["daily","nightly","when I damn well please"]
        },
        "obama" : {
            "subjects"          : ["King Obama","Emperor Obama"],
            "trans"             : "trans",
            "verbs"             : ["destroy","#rip apart"],
            "post_adjectives"   : ["like it's his job","because he hates america"],
            "objects"           : ["the american way of life","the economy"]
        },
        "media" : {
            "trans"             : "intrans",
            "subjects"          : ["the media","the mainstream media","everyone other than Fox News"],
            "verbs"             : ["lies"],
            "being_targets"     : {
                "this"      : ["treacherous","kniving"],
                "subject"   : ["always defending #KingObama","good for nothing"]
            }
        }
    }
}

liberal = {
    "interests" : {
        "rich_people" : {
            "trans"             : "trans",
            "subjects"          : ["the 1%","banks","republicans"],
            "verbs"             : ["destroy","threaten"],
            "objects"           : ["the middle_ class_","the american dream","american values"],
            "post_adjectives"   : ["tremendously","constantly"]
        },
        "subaru" : {
            "trans"             : "trans",
            "subjects"          : ["I","our family"],
            "verbs"             : ["love","practically #live in"],
            "objects"           : ["our Subaru"]
        }
    }
}

general = {
    "interests" : {
        "weather" : {
            "trans"             : "intrans",
            "subjects"          : ["the weather","the temperature"],
            "verbs"             : ["#get to me"],
            "being_target"      : {
                "this"          : ["unusual","all over the place"],
                "subject"       : ["better","too moist"]
                },
            "post_adjectives"   : ["sometimes"]
        },
        "news" : {
            "trans"             : "trans",
            "subjects"          : ["politicians","current events"],
            "verbs"              : ["depress","rarely #inspire"],
            "objects"            : ["me_"],
            "being_target"      : {
                "this"          : ["profoundly","all over the place"],
                "subject"       : ["better","too moist"]
                }
        },
        "blah" : {
            "trans"             : "trans",
            "subjects"          : ["I"],
            "verbs"             : ["hate","#deal with"],
            "objects"           : ["traffic","crowds","zoos"],
            "post_adjectives"   : ["like a boss","grudgingly"]
        }
    }
}

christian = {
    "interests" : {
        "god" : {
            "trans"             : "trans",
            "subjects"          : ["I","we christians"],
            "verbs"             : ["#believe in","follow"],
            "objects"           : ["God","Jesus","the righteous path"],
            "post_adjectives"   : ["religiously","always"]
        },
        "news" : {
            "trans"             : "trans",
            "subjects"          : ["politicians","current events"],
            "verbs"              : ["depress","rarely #inspire"],
            "objects"            : ["me_"],
            "being_target"      : {
                "this"          : ["profoundly","all over the place"],
                "subject"       : ["better","too moist"]
                }
        },
        "values" : {
            "trans"             : "trans",
            "subjects"          : ["I","my family","my church community",["my family","I"]],
            "verbs"             : ["value","practice"],
            "objects"           : ["abstinence","righteousness","Godliness"],
            "post_adjectives"   : ["when no one is watching","even when it's not convenient"]
        }
    }
}

teen = {
    "interests" : {
        "dating" : {
            "trans"             : "trans",
            "subjects"          : ["dating","the opposite_ sex_"],
            "verbs"             : ["intrigue","motivate"],
            "objects"           : ["teens","me"],
            "post_adjectives"   : ["very deeply","when no one else is around"],
            "being_targets"   : {
                "this"    : ["all I care about","so confusing"],
                "subject" : ["too real"]
                },
        },
        "one_direction" : {
            "trans"             : "trans",
            "subjects"          : ["1D","Harry","Zayne"],
            "verbs"             : ["make"],
            "objects"           : ["me feel alive","me so happy"],
        },
        "school" : {
            "trans"             : "intrans",
            "subjects"          : ["high_ school_","homework_"],
            "verbs"             : ["sucks"],
            "being_targets"   : {
                "this"    : ["for nerds","so confusing"],
                "subject" : ["the death of me"]
                },
            "post_adjectives"   : ["big time","hardcore"]
        }
    }
}

doctor = {
    "interests" : {
        "health" : {
            "trans"             : "trans",
            "subjects"          : ["regular exercise","fresh vegetables"],
            "verbs"             : ["promote","#help with"],
            "objects"           : ["longevity","wellness"],
            "post_adjectives"   : ["for most patients","in the majority of clinical trials"]
        },
        "disease" : {
            "trans"             : "trans",
            "subjects"          : ["disease","viruses"],
            "verbs"             : ["threaten"],
            "objects"           : ["public health","herd immunity"],
            "being_targets"   : {
                "this"    : ["unavoidable"],
                "subject" : ["scary"]
                },
        },
        "medecine" : {
            "trans"             : "trans",
            "subjects"          : ["medecine","vaccines","vitamins"],
            "verbs"             : ["treats","cures"],
            "objects"           : ["disease","malnutrition"],
            "post_adjectives"   : ["scientifically","reliably"]
        }
    }
}

socialbots = {
    "VanTheWinterer" : general,
    "ImDrErnst" : doctor,
    "MarzipanIAm" : doctor,
    "Rianna__Taylor" : teen,
    "AntonioBacusAmI" : teen,
    "Alexa_Smith9584" : general,
    "LeeeroyOOOOman" : general,
    "KarlKreegz20" : liberal,
    "QueenNatLat" : liberal,
    "Anold__Doyle" : conservative,
    "geneverasalomon" : conservative,
    "AppleBottomGrg" : christian,
    "MariaMunozOhMy" : christian,
    "SammyHerzt" : general,
    "LydiaGoldman253" : general,
    }

