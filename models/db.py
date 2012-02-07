if request.controller.endswith('_examples'): response.generic_patterns.append('*')

import time
from math import log
now=time.time()

from gluon.settings import settings
from gluon.tools import Auth
import mail_setting

# if running on Google App Engine
if settings.web2py_runtime_gae:
    from gluon.contrib.gql import *
    from gluon.contrib.gae_memcache import MemcacheClient
    from gluon.contrib.memdb import MEMDB
    cache.memcache = MemcacheClient(request)
    cache.ram = cache.disk = cache.memcache
    # connect to Google BigTable
    db = DAL('gae')
    # and store sessions there
    #session.connect(request, response, db=db)
    session.connect(request,response,MEMDB(cache.memcache))
else:
    # if not, use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')

auth = Auth(db)
auth.settings.table_user_name = 'person'
auth.settings.request_reset_password_next = URL('index')
auth.settings.reset_password_next = URL('login')
auth.settings.login_next = URL('index')
auth.messages.reset_password= "다음 링크를 클릭하시면 비밀번호 재설정 페이지로 이동합니다. http://"+request.env.http_host+URL(r=request,f='new_password')+'/%(key)s'
auth.settings.formstyle='divs'
mail = auth.settings.mailer
mail.settings.server = 'gae'
mail.settings.sender = mail_setting.sender()
mail.settings.login = mail_setting.login()
db.define_table(
        auth.settings.table_user_name,
        Field('alias', length=128, default='',unique=True),
        Field('email', length=128, default='', unique=True),
        Field('password', 'password', length=512,
            readable=False, label='Password'),
        Field('registration_key', length=512,
            writable=False, readable=False, default=''),
        Field('reset_password_key', length=512,
            writable=False, readable=False, default=''),
        Field('registration_id', length=512,
            writable=False, readable=False, default=''))

custom_auth_table = db[auth.settings.table_user_name]
custom_auth_table.password.requires = [IS_NOT_EMPTY(),CRYPT()]
custom_auth_table.email.requires = [
    IS_EMAIL(error_message=auth.messages.invalid_email),
    IS_NOT_IN_DB(db, custom_auth_table.email),IS_NOT_EMPTY()]

auth.settings.table_user = custom_auth_table
auth.define_tables(username=False)

db.define_table('category',
   Field('name'),
   Field('alias',default='새 카테고리'),
   Field('description','text'))

db.category.name.requires=[IS_MATCH('[a-z_]+'),
                           IS_NOT_IN_DB(db,db.category.name)]
db.category.description.requires=IS_NOT_EMPTY()

db.define_table('news',
   Field('post_time','double',default=now),
   Field('clicks','integer',default=1),
   Field('comments','integer',default=0),
   Field('score','integer',default=1),
   Field('hotness','double',compute=lambda r: log(r['clicks'],10)+log(r['score'],10)+log(max(r['comments'],1),10)+log(max((r['post_time']-(now-2592000.0)),1),10),default=1.0),
   Field('category'),
   Field('category_alias'),
   Field('author',db.person),
   Field('author_alias'),
   Field('url',length=2048), 
   Field('title',length=2048),
   Field('flagged','boolean',default=False))

db.news.url.requires=[IS_NOT_EMPTY()]
db.news.title.requires=IS_NOT_EMPTY()

db.define_table('comment',
   Field('score','integer',default=1),
   Field('post_time','double',default=now),
   Field('author',db.person),
   Field('author_alias'),
   Field('parente','integer',default=0),
   Field('news',db.news),
   Field('body','text'),
   Field('flagged','boolean',default=False))

db.comment.body.requires=IS_NOT_EMPTY()

db.define_table('vote',
    Field('choice','integer',default=0),
    Field('parentv',db.news),
    Field('voter',db.person))

db.define_table('vote_cmt',
    Field('choice','integer',default=0),
    Field('parentv',db.comment),
    Field('voter',db.person))

if len(db().select(db.category.ALL))==0:
   db.category.insert(name='politics',alias='시사정치',description='최근 많이 이야기되는 시사, 정치 뉴스들')
   db.category.insert(name='programming',alias='프로그래밍',description='삶을 윤택하게 만드는 코드')
   db.category.insert(name='technology',alias='테크놀로지',description='새로운 기술과 신제품')
   db.category.insert(name='movie',alias='영화',description='새 예고편, 영화 소식, 좋은 리뷰들')
   db.category.insert(name='accident',alias='사건사고',description='')
   db.category.insert(name='diablo',alias='디아블로',description='그냥 디아블로가 좋아...')
   db.category.insert(name='game',alias='게임',description='게임은 사회를 좀먹게 하는 질병입니다')
   db.category.insert(name='drama',alias='미드',description='미드 소식, 동영상, 추천 정보들...')
   db.category.insert(name='funny',alias='유머',description='조금만 재미있어도 공유합니다.')
   db.category.insert(name='body',alias='사람사진',description='주로 여자 사진이 될 것 같지만')
