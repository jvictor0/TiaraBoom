import sys
import sentence_builder as sb
import database as db

con = db.ConnectToMySQL()
sb.DDL(con,sys.argv[1])
