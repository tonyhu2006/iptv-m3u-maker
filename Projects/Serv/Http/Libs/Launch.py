from Http.Libs import DB
from pathlib import Path

class Launch(DB):

    @classmethod
    def chkDB(cls):
        db_name = 'Data/config.db'
        if not Path(db_name).exists():
            cls.initDB(db_name)
            print('no')
        else:
            print('yes')

    @classmethod
    def initDB(cls, db_name):
        cls.connect(db_name)
        queries = [
            '''
            CREATE TABLE "admin" (
                "id" integer,
                "uname" varchar,
                "pwd" varchar DEFAULT '',
                "lastlogin" varchar DEFAULT '',
                "logintime" varchar DEFAULT '',
                PRIMARY KEY (id)
            );
            ''',
            '''
            INSERT INTO  "admin" (
                "uname",
                "pwd",
                "lastlogin"
            ) VALUES (
                'admin',
                '39faf0e6a00286cc6c67adae18cfc7de70a19fa70c2851f411b6e6ec0476ffdb',
                '0'
            );
            ''',
            '''
            CREATE TABLE "channel" ("id" integer,"title" varchar,"url" varchar,"alive" int DEFAULT '1',"ping" int DEFAULT '0',"addtime" varchar,"isdel" int DEFAULT '0', PRIMARY KEY (id));
            '''
        ]
        for query in queries:
            cls.execute(query)

        cls.close()