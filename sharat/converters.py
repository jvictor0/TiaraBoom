import nlpclasses

def Token2Row(source_id, sentence_id, tk):
    if __debug__:
        tk.Validate()
    return {"source_id"   : source_id,
            "sentence_id" : sentence_id,
            "lemma"       : tk["lemma"],
            "token_id"    : tk["index"],
            "token"       : tk["word"],
            "start_char"  : tk['characterOffsetBegin'],
            "end_char"    : tk['characterOffsetEnd'],
            "pos"         : tk['pos'],
            "pre"         : tk['before'],
            "post"        : tk['after'],
            "ner"         : tk["ner"],
            "speaker"     : tk["speaker"],
            "original_text": tk["originalText"],
            "normalized_ner" : tk["normalizedNER"] if "normalizedNER" in tk else None}

def Relation2Row(source_id, sentence_id, relation_id, r):
    if __debug__:
        r.Validate()
    return {"source_id"      : source_id,
            "sentence_id"    : sentence_id,
            "relation_id"    : relation_id,
            "subject"        : r["subject"],
            "object"         : r["object"],
            "relation"       : r["relation"],
            "subject_start"  : r["subjectSpan"][0],
            "subject_end"    : r["subjectSpan"][1],
            "object_start"   : r["objectSpan"][0],
            "object_end"     : r["objectSpan"][1],
            "relation_start" : r["relationSpan"][0],
            "relation_end"   : r["relationSpan"][1]}

def Sentence2Row(source_id, s):
    if __debug__:
        s.Validate()
    return {"source_id"      : source_id,
            "sentence_index" : s["index"],
            "sentence"       : s.Text()}

def Row2Token(r):
    json = {"word"                 : r["token"],
            "characterOffsetBegin" : int(r["start_char"]),
            "characterOffsetEnd"   : int(r["end_char"]),
            "pos"                  : r["pos"],
            "index"                : int(r["token_id"]),
            "lemma"                : r["lemma"],
            "before"               : r["pre"],
            "after"                : r["post"],
            "ner"                  : r["ner"],
            "speaker"              : r["speaker"],
            "originalText"         : r["original_text"]}
    if r["normalized_ner"] is not None:
        json["normalizedNER"] = r["normalized_ner"]
    result = nlpclasses.Token(json)
    if __debug__:
        result.Validate()
    return result

def Row2Relation(r):
    result = nlpclasses.Rel({"subject"       : r["subject"],
                             "object"        : r["object"],
                             "relation"      : r["relation"],
                             "subjectSpan"   : [int(r["subject_start"]), 
                                                int(r["subject_end"])],
                             "objectSpan"    : [int(r["object_start"]), 
                                                int(r["object_end"])],
                             "relationSpan"  : [int(r["relation_start"]), 
                                                int(r["relation_end"])]})
    if __debug__:
        result.Validate()
    return result

def Rows2Sentence(sentence_row, relation_rows, token_rows):
    relation_rows = sorted(relation_rows, key = lambda x: int(x["relation_id"]))
    token_rows = sorted(token_rows, key = lambda x: int(x["token_id"]))
    openie = [Row2Relation(r).json for r in relation_rows]
    tokens = [Row2Token(tk).json for tk in token_rows]
    result = nlpclasses.Sentence({"openie" : openie, 
                                  "tokens" : tokens, 
                                  "index"  : int(sentence_row["sentence_index"])})
    if __debug__:
        result.Validate()
    return result

def Rows2Parse(coref_rows, sentence_rows, relation_rows, token_rows):
    rels = {}
    toks = {}
    sentence_rows = sorted(sentence_rows, key = lambda s: int(s["sentence_id"]))
    for s in sentence_rows:
        rels[int(s["sentence_id"])] = []
        toks[int(s["sentence_id"])] = []
    for r in relation_rows:
        rels[int(r["sentence_id"])].append(r)
    for r in token_rows:
        toks[int(r["sentence_id"])].append(r)
    sentences = []
    for s in sentence_rows:
        sid = ["sentence_id"]
        sentences.append(Rows2Sentence(s, rels[sid], toks[sid]))
    result = nlpclasses.Parse({"sentences" : sentences})
    if __debug__:
        result.Validate()
    return result
