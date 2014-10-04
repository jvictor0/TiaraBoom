# this is a throw-away script for converting AlexRyan_Playwright.rkt from unusable lisp to maintainable python
# I hope it more-or-less works

text = open('AlexRyan_Playwright.rkt', 'r').read()
text = text.replace('\n',' ').replace('\t',' ').replace('`',' ').replace(',',' ')
text = text.replace("%","_").replace("-","_").replace("'",' ').replace("+","_pos").replace("?","_")
text = text.replace("don t","don't").replace("isn t","isn't").replace("aren t","aren't").replace("doesn t","doesn't")
text = text.replace("won t","won't").replace("shouldn t","shouldn't").replace("wouldn t","wouldn't").replace("I m","I'm")
text = text.replace("wasn t","wasn't").replace("weren t","weren't").replace("can t","can't").replace("you re","you're")

def ParseLisp(text, start):
    result = []
    last_token_start = -1
    i = start
    while i < len(text):
        if text[i] == '(':
            if last_token_start != -1:
                result.append(text[last_token_start:i])
            parsed = ParseLisp(text, i+1)
            x,i = parsed
            result.append(x)
            last_token_start = -1
        elif text[i] == ')':
            if last_token_start != -1:
                result.append(text[last_token_start:i])
            return result, i
        elif text[i] == '"':
            if last_token_start != -1:
                result.append(text[last_token_start:i])
            last_token_start = -1
            new_i = text[i+1:].index('"')
            result.append('"' + text[i+1:i+1+new_i] + '"')
            i = i + 1 + new_i
        elif last_token_start != -1 and text[i] == ' ':
            result.append(text[last_token_start:i])
            last_token_start = -1
        elif last_token_start == -1 and text[i] != ' ':
            last_token_start = i
        i = i + 1
    return result, i

def FormatLisp(lispTree, indent):
    if isinstance(lispTree, list):
        if lispTree[0] == 'lambda':
            return "lambda " + ','.join(lispTree[1]) + ": " + FormatLisp(lispTree[2], "")
        elif lispTree[0] == 'if':
            result = "(" + FormatLisp(lispTree[2], "") + " if " 
            result = result +  FormatLisp(lispTree[1], "")  + " else "  + FormatLisp(lispTree[3], "") + ")"
            return result
        elif lispTree[0] == "let" or lispTree[0] == "let*":
            result = ""
            for i,xb in enumerate(lispTree[1]):
                x,b = xb
                result += (indent if i > 0 else "") + x + " = " + FormatLisp(b,indent + (" " * (3 + len(x)))) + "\n"
            result += indent + "return " + FormatLisp(lispTree[2],indent + "       ") + "\n"
            return result
        elif lispTree[0] == "cond":
            result = ""
            for i,xb in enumerate(lispTree[1:]):
                x,b = xb
                if x == "else":
                    result += indent + "else:\n    " + indent + "return " + FormatLisp(b,indent+(" "*3)) + "\n"
                else:
                    result += (indent if i > 0 else "") + "if " + FormatLisp(x,indent) + ":\n    " + indent + "return " + FormatLisp(b,indent + (" " * 4)) + "\n"
            return result
        elif lispTree[0] == 'define_rand_elem' or lispTree[0] == 'define_rand_func':
            result = "def " + lispTree[1][0] + "(" + ','.join(lispTree[1][1:]) + "):\n"
            prefix = "    return RandomChoice(["
            result += prefix
            for i in xrange(len(lispTree[2])):
                if i > 0:
                    result += ",\n" + (" " * len(prefix))
                result += "(" + FormatLisp(lispTree[2][i][0],"") + "," + FormatLisp(lispTree[2][i][1],"") + ")"
            result += "])\n" if lispTree[0] == 'define_rand_elem' else "])()\n"
            return result
        elif lispTree[0] == "define":
            if isinstance(lispTree[1], list):
                result = "def " + lispTree[1][0] + "(" + ", ".join(lispTree[1][1:]) + "):\n    "
                if isinstance(lispTree[2],list) and lispTree[2][0] in ["let","let*","cond"]:
                    return result + FormatLisp(lispTree[2],"    ")
                return result + "return " +  FormatLisp(lispTree[2],"    ") + "\n"
            return lispTree[1] + " = " + FormatLisp(lispTree[2],"") + "\n"
        elif lispTree[0] in ["phrase",]:
            return lispTree[0] + "([" + ", ".join([FormatLisp(l,"") for l in lispTree[1:]]) + "])"
        elif lispTree[0] in ["word_make","word_punc"]:
            return "lit_phrase(" + lispTree[1] + ")"
        elif lispTree[0] == "car":
            return FormatLisp(lispTree[1],"") + "[0]"
        elif lispTree[0] == "cdr":
            return FormatLisp(lispTree[1],"") + "[1]"
        elif lispTree[0] == "cons":
            return "(" + ", ".join([FormatLisp(l,"") for l in lispTree[1:]]) + ")"
        elif lispTree[0] == "list":
            return "[" + ", ".join([FormatLisp(l,"") for l in lispTree[1:]]) + "]"
        elif lispTree[0] == "null":
            return "(" + FormatLisp(lispTree[1],"") + " is None)"
        elif lispTree[0] in ["equal_","eq_","member"]:
            infix_dict = {"equal_" : " == " , "eq_" : " == ",  "member" : " in " }
            return infix_dict[lispTree[0]].join([FormatLisp(l,"") for l in lispTree[1:]])
        else:
            return FormatLisp(lispTree[0],"") + "(" + ", ".join([FormatLisp(l,"") for l in lispTree[1:]]) + ")"
        assert False
    if lispTree[:2] == "#\\":
        return "'" + lispTree[2] + "'"
    if lispTree == "#f": return "False"
    if lispTree == "#t": return "True"
    return lispTree


with open('grammar.py','w') as f:
    print >>f, "from grammar_util import *"
    print >>f, "from grammar_util import _comma, _question\n\n"
    for s in ParseLisp(text,0)[0]:
        fun = FormatLisp(s,"")
        print >>f, fun

