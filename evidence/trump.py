import thought

reload(thought.snode)
reload(thought)

ctx = thought.Context()
ctx.FromJSON({    
    "entities"  :
    [{
        "name" : "Trump",
        "type" : "person",
        "gender" : "male",        
    },
    {
        "name" : "The Illuminati",
        "type" : "group"        
    },
    {
        "name" : "Chris Christie",
        "type" : "person",
        "gender" : "male"
    },
    {
        "name" : "the people",
        "type" : "group",
        "person" : 1
    }],
    
    "facts" :
    [{
        "id" : 0,
        "subject" : "Trump",
        "relation": "did",
        "infinitive": "use",
        "object"  : "mind control",
    },
    {
        "id" : 1,
        "subject" : "Trump",
        "relation": "be",
        "object"  : "The Illuminati",
        "tenses" : ["present"],
    },
    {
        "id" : 2,
        "subject" : "The Illuminati",
        "relation" : "did",
        "infinitive" : "hypnotize",
        "object"   : "the people",
        "frequency"    : "recurring"
    },
    {
        "id" : 3,
        "subject" : "Trump",
        "relation" : "be",
        "object" : "the president",
        "tenses" : ["future"],
        "frequency" : "event"
    },
    {
        "id" : 4,
        "subject" : "the people",
        "relation" : "be",
        "object"   : "duped"
    },
    {
        "id" : 5,
        "subject": "Chris Christie",
        "infinitive": "endorse",
        "object" : "Trump",
        "tenses" : ["past"],
        "frequency" : "event"
    },
    {
        "id" : 6,
        "subject" : "Trump",
        "infinitive" : "hypnotize",
        "object" : "Chris Christie",
        "frequency": "recurring"
    },
    {
        "id" : 7
    }],

    "relations" :
    [
        { "gov" : 1, "dep" : 0, "type" : "evidence"   },
        { "gov" : 3, "dep" : 1, "type" : "why"        },
        { "gov" : 3, "dep" : 2, "type" : "why"        },
        { "gov" : 2, "dep" : 0, "type" : "similar"    },
        { "gov" : 3, "dep" : 4, "type" : "why"        },
        { "gov" : 5, "dep" : 6, "type" : "why"        },
        { "gov" : 6, "dep" : 5, "type" : "evidence"   },
        { "gov" : 0, "dep" : 6, "type" : "evidence"   }
    ]
})
