def cross(as_, bs_, sep=' '):
    return [(a + sep + b).strip() for a in as_ for b in bs_]

# this is just an example charicature called housewife, used basically for (sanity) testing
#
housewife = {
    "interests" : {
        "drink_liquor" : {
            "trans"           : "trans",
            "subjects"        : ["I","Jimmy", ["Jimmy","I"]],
            "objects"         : cross(["some","","a","a glass of"],
                                      ["wine","penot","beer","YellowTail","Smirnoff","champaign_"]),
            "verbs"           : ["drink","have"],
            "verb_adapters"   : ["loves","enjoys","always #enjoys","seldom #gets to enjoy"],
            "post_adjectives" : ["in bed","at home","at dad's house"],
            "being_targs"     : {
                "this"    : ["fun","yummy","great","the best"],
                "subject" : ["drunk","sleepy"]
                }
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


socialbots = {
    "VanTheWinterer" : housewife,
    "ImDrErnst" : housewife,
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
