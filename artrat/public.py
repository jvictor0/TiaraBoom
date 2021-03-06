import sentence_builder as sb
import database
import depend_tree as deptree
import sys
import traceback

reload(sb)

def Ingest(user, text, con=None):
    if con is None:
        con = database.ConnectToMySQL()
        con.query("use tiaraboom")
    try:
        sb.Ingest(con, text, user)
        return { "success": True }
    except Exception as e:  # Complain if nessesary
        return { "success": False, "error": str(e) }

def IngestFile(user, text, con=None,log=sb.Print):
    if con is None:
        con = database.ConnectToMySQL()
        con.query("use tiaraboom")
    try:
        sb.IngestFile(con, text, user, log=log)
        return { "success": True }
    except Exception as e:  # Complain if nessesary
        con.query("rollback")
        return { "success": False, "error": str(e) }

def Generate(user, symbols, requireSymbols=False, con=None):
    if con is None:
        con = database.ConnectToMySQL()
        con.query("use tiaraboom")        
    dbs = {}
    try:
        gend, syms = sb.GenerateWithSymbols(con, user, symbols,requireSymbols=requireSymbols)
        result = deptree.FromDependTree(gend)
        dbs = sb.g_last_generated.ToDict()
        return { "success": True,   "body": result, "debugging_stuff" : { "original_tree" : dbs }, "symbols" : syms }
    except sb.SentenceBuilderErr as e:
        ex_type, ex, tb = sys.exc_info()
        #traceback.print_tb(tb)
        return { "success": False, "error": str(e), "debugging_stuff" : { "original_tree" : dbs } }

def Reset(user):
    con = database.ConnectToMySQL()
    con.query("use tiaraboom")
    sb.Reset(con, user)
    return { "success": True }

def GetSymbols(text):
    try:
        result = sb.GetSymbols(text)
        return { "success" : True, "symbols" : result }
    except Exception as e:
        return { "success" : False, "error": str(e) }
