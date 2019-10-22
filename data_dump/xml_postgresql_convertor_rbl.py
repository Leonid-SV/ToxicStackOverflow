# -*- coding: utf-8 -*-

# import sqlite3
import psycopg2
from psycopg2 import sql
import os
import xml.etree.cElementTree as etree
import logging

from contextlib import closing

ANATHOMY = {
  # 'badges': {
  #   'Id': 'INTEGER',
  #   'UserId': 'INTEGER',
  #   'Class': 'INTEGER',
  #   'Name': 'TEXT',
  #   'Date': 'TIMESTAMP',
  #   'TagBased': 'BOOLEAN',
  # },
  # 'comments_short': {
  #   'Id': 'INTEGER',
  #   'PostId': 'INTEGER',
  #   'Score': 'INTEGER',
  #   'Text': 'TEXT',
  #   'CreationDate': 'TIMESTAMP',
  #   'UserId': 'INTEGER',
  #   'UserDisplayName': 'TEXT'
  # },
  'posts': {
      'Id': 'INTEGER',
      'PostTypeId': 'INTEGER',  # 1: Question, 2: Answer
      'ParentId': 'INTEGER',  # (only present if PostTypeId is 2)
      'AcceptedAnswerId': 'INTEGER',  # (only present if PostTypeId is 1)
      'CreationDate': 'TIMESTAMP',
      'Score': 'INTEGER',
      'ViewCount': 'INTEGER',
      'Body': 'TEXT',
      'OwnerUserId': 'INTEGER',  # (present only if user has not been deleted)
      'OwnerDisplayName': 'TEXT',
      'LastEditorUserId': 'INTEGER',
      'LastEditorDisplayName': 'TEXT',  # ="Rich B"
      'LastEditDate': 'TIMESTAMP',  #="2009-03-05T22:28:34.823"
      'LastActivityDate': 'TIMESTAMP',  #="2009-03-11T12:51:01.480"
      'CommunityOwnedDate': 'TIMESTAMP',  #(present only if post is community wikied)
      'Title': 'TEXT',
      'Tags': 'TEXT',
      'AnswerCount': 'INTEGER',
      'CommentCount': 'INTEGER',
      'FavoriteCount': 'INTEGER',
      'ClosedDate': 'TIMESTAMP'
  },
  # 'votes': {
  #     'Id': 'INTEGER',
  #     'PostId': 'INTEGER',
  #     'UserId': 'INTEGER',
  #     'VoteTypeId': 'INTEGER',
  #     # -   1: AcceptedByOriginator
  #     # -   2: UpMod
  #     # -   3: DownMod
  #     # -   4: Offensive
  #     # -   5: Favorite
  #     # -   6: Close
  #     # -   7: Reopen
  #     # -   8: BountyStart
  #     # -   9: BountyClose
  #     # -  10: Deletion
  #     # -  11: Undeletion
  #     # -  12: Spam
  #     # -  13: InformModerator
  #     'CreationDate': 'TIMESTAMP',
  #     'BountyAmount': 'INTEGER'
  # },
  # 'posthistory': {
  #     'Id': 'INTEGER',
  #     'PostHistoryTypeId': 'INTEGER',
  #     'PostId': 'INTEGER',
  #     'RevisionGUID': 'TEXT',
  #     'CreationDate': 'TIMESTAMP',
  #     'UserId': 'INTEGER',
  #     'UserDisplayName': 'TEXT',
  #     'Comment': 'TEXT',
  #     'Text': 'TEXT'
  # },
  # 'postlinks': {
  #     'Id': 'INTEGER',
  #     'CreationDate': 'TIMESTAMP',
  #     'PostId': 'INTEGER',
  #     'RelatedPostId': 'INTEGER',
  #     'PostLinkTypeId': 'INTEGER',
  #     'LinkTypeId': 'INTEGER'
  # },
  # 'users': {
  #     'Id': 'INTEGER',
  #     'Reputation': 'INTEGER',
  #     'CreationDate': 'TIMESTAMP',
  #     'DisplayName': 'TEXT',
  #     'LastAccessDate': 'TIMESTAMP',
  #     'WebsiteUrl': 'TEXT',
  #     'Location': 'TEXT',
  #     'Age': 'INTEGER',
  #     'AboutMe': 'TEXT',
  #     'Views': 'INTEGER',
  #     'UpVotes': 'INTEGER',
  #     'DownVotes': 'INTEGER',
  #     'AccountId': 'INTEGER',
  #     'ProfileImageUrl': 'TEXT'
  # },
  # 'tags': {
  #     'Id': 'INTEGER',
  #     'TagName': 'TEXT',
  #     'Count': 'INTEGER',
  #     'ExcerptPostId': 'INTEGER',
  #     'WikiPostId': 'INTEGER'
  # }
}


def dump_files(file_names, anathomy,
             dump_path='.',
             create_query='CREATE TABLE IF NOT EXISTS {table} ({fields})',
             insert_query='INSERT INTO {table} ({columns}) VALUES ({values})',
             log_filename='so-parser.log'):

    logging.basicConfig(filename=os.path.join(dump_path, log_filename), level=logging.INFO)

    # подключение к базе данных ToxicStackOverflow
    with closing(psycopg2.connect(dbname='ToxicStackOverflow', user='postgres', password='2409', host='localhost')) as conn:
        with conn.cursor() as cursor:

            for file in file_names:
              print("Opening {0}.xml".format(file))

              with open(os.path.join(dump_path, file + '.xml'), encoding='utf8') as xml_file:

                  table_name = file.lower()

                  sql_create = create_query.format(
                      table=table_name,
                      fields=", ".join(['{0} {1}'.format(name, type) for name, type in anathomy[
                      table_name].items()]))
                  print('Creating table {0}'.format(table_name))

                  try:
                      logging.info(sql_create)
                      print('*' * 40)
                      print(sql_create) ############
                      cursor.execute(sql_create)
                      print('*' * 40)
                  except Exception as e:
                      logging.warning(e)

                  tree = etree.iterparse(xml_file)
                  tree = iter(tree)

                  count = 0
                  for events, row in tree:
                      try:
                          if row.attrib.values():
                              logging.debug(row.attrib.keys())
                              vals = []
                              keys = []
                              for key, val in row.attrib.items():
                                  keys.append(key)
                                  if anathomy[table_name][key] == 'INTEGER':
                                      vals.append(int(val))
                                  elif anathomy[table_name][key] == 'BOOLEAN':
                                      vals.append(1 if val == "TRUE" else 0)
                                  else:
                                      vals.append(val)

                              query = insert_query.format(
                                  table = table_name,
                                  columns = (', ').join(k for k in keys),
                                  values = sql.SQL(', ').join(sql.Literal(v) for v in vals).as_string(conn)
                              )

                              # print(query)
                              cursor.execute(query)

                              count += 1
                              if (count % 1000 == 0):
                                  print("{}".format(count))

                          conn.commit()

                      except Exception as e:
                          logging.warning(e)
                          print("x", end="")
                      finally:
                          row.clear()


                  print("\n")
                  conn.close()
                  del (tree)


if __name__ == '__main__':
  dump_files(ANATHOMY.keys(), ANATHOMY)