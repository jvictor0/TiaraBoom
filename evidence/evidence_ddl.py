
def EvidenceCreateTables(con):
    con.query(("create table if not exists evidence_tweets("
               "user_id bigint not null,"
               "id bigint not null,"
               "facts json not null,"
               "primary key(user_id, id),"
               "shard (user_id))"))
    
