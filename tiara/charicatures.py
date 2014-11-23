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
            "post_adjectives" : ["in bed","at home","at dad's house","on tv"]
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

socialbots = {
    "VanTheWinterer" : conservative,
    "ImDrErnst" : liberal,
    "MarzipanIAm" : housewife,
    "Rianna__Taylor" : housewife,
    "AntonioBacusAmI" : housewife,
    "Alexa_Smith9584" : housewife,
    "LeeeroyOOOOman" : housewife,
    "KarlKreegz20" : housewife,
    "QueenNatLat" : housewife,
    "Anold__Doyle" : housewife,
    "geneverasalomon" : housewife,
    "AppleBottomGrg" : housewife,
    "MariaMunozOhMy" : housewife,
    "SammyHerzt" : housewife,
    "LydiaGoldman253" : housewife,
    }
