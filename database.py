import os
import psycopg2
from psycopg2 import sql


class Memory:

    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='prefer')
        self.conn.autocommit = True

    def __del__(self):
        self.conn.close()

    def _insert(self, query, values):
        with self.conn.cursor() as cursor:
            cursor.execute(sql.SQL(query).format(
                sql.SQL(',').join(map(sql.Literal, values))
            ))

    def _select(self, query, values):
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        records = cursor.fetchall()
        return records

    def _update(self, query, values):
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        records = cursor.fetchall()
        return records

    def added_chat(self, **model):
        insert_user = '''
            INSERT INTO public.users (telegram_id, username, first_name, last_name, language_code)
            VALUES {}
            ON CONFLICT (telegram_id) DO NOTHING
        '''
        insert_chat = '''
            INSERT INTO public.chats (chat_id, chat_type, title, username,
                first_name, last_name, bio, description)
            VALUES {}
            ON CONFLICT (chat_id) DO NOTHING
        '''
        self._insert(insert_user, [(model['telegram_id'],
                                    model['t_username'],
                                    model['t_first_name'],
                                    model['t_last_name'],
                                    model['language_code'])])
        self._insert(insert_chat, [(model['chat_id'],
                                    model['chat_type'],
                                    model['title'],
                                    model['c_username'],
                                    model['c_first_name'],
                                    model['c_last_name'],
                                    model['bio'],
                                    model['description'])])

    def added_action(self, **model):
        insert_bot_use = '''
            INSERT INTO public.bot_usage (telegram_id, chat_id)
            VALUES {}
        '''
        self._insert(insert_bot_use, [(model['telegram_id'],
                                       model['chat_id'])])

    def get_settings(self, chat_id):
        select_settings = '''
            SELECT
                c.convert_video ,
                c.convert_audio 
            FROM chats c 
            WHERE c.chat_id = %s
        '''
        res = self._select(select_settings, [chat_id])
        return {"video": res[0][0],
                "audio": res[0][1]} if res and res[0] else None

    def update_settings(self, chat_id, key, value):
        update_settings = '''
            UPDATE chats SET {field} = '%s' WHERE chat_id = %s
            returning convert_video, convert_audio
        '''
        query = sql.SQL(update_settings).format(field=sql.Identifier(str("convert_" + key)))
        res = self._update(query, (value, chat_id))
        return {"video": res[0][0],
                "audio": res[0][1]} if res and res[0] else None