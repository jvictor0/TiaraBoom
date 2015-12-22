def DoDDL(con):
    con.query("use tiaraboom")

    con.query("""create reference table if not exists sources(
                    user_id bigint not null,
                    source_id bigint auto_increment,
                    source blob default null,
                    primary key(source_id) using hash)""")

    con.query("""create table if not exists sentences(
                   source_id bigint not null,
                   sentence_id bigint auto_increment,
                   sentence_index bigint not null,
                   sentence blob not null,
                   key (source_id, sentence_id) using clustered columnstore,
                   shard (sentence_id))""")
    
    con.query("""create table if not exists tokens(
                   source_id bigint not null, 
                   sentence_id bigint not null,
                   token_id bigint not null,
                   token blob not null,
                   lemma blob not null,
                   start_char bigint not null,
                   end_char bigint not null,
                   pos blob not null,
                   pre blob not null,
                   post blob not null,
                   ner blob not null,
                   normalized_ner blob, 
                   speaker blob not null,
                   original_text blob not null,
                   key (source_id, sentence_id, token_id) using clustered columnstore,
                   shard (sentence_id))""") 

    con.query("""create table if not exists relations(
                   source_id bigint not null, 
                   sentence_id bigint not null,
                   relation_id bigint not null,

                   subject blob not null,
                   subject_start bigint not null,
                   subject_end bigint not null,

                   relation blob not null,
                   relation_start bigint not null,
                   relation_end bigint not null,

                   object blob not null,
                   object_start bigint not null,
                   object_end bigint not null,

                   key (subject, object, relation) using clustered columnstore,
                   shard (sentence_id))""")
