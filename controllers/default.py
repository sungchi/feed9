from urlparse import urlparse
import time
now=time.time()

def author_func():
    login_form=auth.login(next=request.env.http_referer)
    login_form.element('input[name=email]')['_class']='span2'
    login_form.element('input[name=email]')['_placeholder']='email'
    login_form.element('input[name=password]')['_class']='span2'
    login_form.element('input[name=password]')['_placeholder']='password'
    login_form.element('input[type=submit]')['_class']='btn'
    login_form.element('input[type=submit]')['_value']='로그인'
    session.old_referer = request.env.http_referer
    return login_form

def register():
    if auth.user_id:
        redirect(session.old_referer)
    login_form = author_func()
    form = auth.register()
    form.element('input[name=alias]')['_class']='span3'
    form.element('input[name=alias]')['_placeholder']='닉네임'
    form.element('input[name=email]')['_class']='span3'
    form.element('input[name=email]')['_placeholder']='이메일'
    form.element('input[name=password]')['_class']='span3'
    form.element('input[name=password]')['_placeholder']='비밀번호'
    form.element('input[name=password_two]')['_class']='span3'
    form.element('input[name=password_two]')['_placeholder']='비밀번호 확인'
    form.element('input[type=submit]')['_class']='btn'
    form.element('input[type=submit]')['_value']='회원가입'
    session.old_referer = request.env.http_referer
    return dict(login_form=login_form,form=form)

def profile():
    if not auth.user_id:
        redirect(URL(r=request,f='login'))
    form=auth.profile()
    form.element('input[name=alias]')['_class']='span3'
    form.element('input[name=email]')['_class']='span3'
    form.element('input[type=submit]')['_class']='btn'
    form.element('input[type=submit]')['_value']='저장'
    return dict(form=form)
'''
#built-in user function
def user(): 
    login_form = author_func()
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(cat_list=cat_list,login_form=login_form,form=auth())
'''

def login():
    if auth.user_id:
        redirect(session.old_referer)
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    login_form=author_func()
    return dict(cat_list=cat_list,login_form=login_form)


def logout():
    return auth.logout(next=request.env.http_referer)

def index():
    sorts={
           'hot':~db.news.hotness,
           'score':~db.news.score,
           'new':~db.news.post_time}
    try: page=int(request.args[2])
    except: page=0
    try: sort=request.args[1]
    except: sort='new' 
    orderby=sorts[sort]
    limitby=(25*page,25*(page+1)+1)
    try: 
        cat=request.args[0]
        if sort == 'hot' or sort == 'score':#orderby 넣어야함 
            news=db((db.news.category==cat) & (db.news.post_time>(now-2592000.0))).select(cache=(cache.ram,1800))
            if sort=='hot': news=news.sort(lambda row: -row.hotness)[limitby[0]:limitby[1]]
            if sort=='score': news=news.sort(lambda row:~row.score)[limitby[0]:limitby[1]]
        else:
            #news=db(db.news.category==cat).select(orderby=orderby,limitby=limitby) #no cache
            news=db(db.news.category==cat).select(cache=(cache.ram,1800))
            news=news.sort(lambda row: -row.post_time)[limitby[0]:limitby[1]]
        category=db(db.category.name==cat).select(cache=(cache.ram,1800))[0]
        alias=category.alias
        dec=category.description
    except: 
        cat="all"
        alias='모든 이야기'
        dec='이것저것 인기순으로 모아놓습니다'
       
        if sort == 'hot' or sort == 'score':
            news=db(db.news.post_time>(now-2592000.0)).select(cache=(cache.ram,1800))
            if sort=='hot': news=news.sort(lambda row: -row.hotness)[limitby[0]:limitby[1]]
            if sort=='score': news=news.sort(lambda row:~row.score)[limitby[0]:limitby[1]]
        else:
            #news=db().select(db.news.ALL,orderby=orderby,limitby=limitby)
            news=db().select(db.news.ALL,cache=(cache.ram,1800))
            news=news.sort(lambda row: -row.post_time)[limitby[0]:limitby[1]]
        #news=db(db.news.post_time>(now-2592000.0)).select(limitby=limitby,orderby=db.news.post_time|orderby)
        
    db.person.email.requires=IS_NOT_EMPTY()    
    form = author_func()
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL,cache=(cache.ram,1800))]

    return response.render(dict(login_form=form,cat_list=cat_list,category=cat,alias=alias,news=news,dec=dec,sort=sort,page=page))

def bookmark():
    try: item=db(db.news.id==request.args[0]).select()[0]
    except: redirect(URL(r=request,f='index'))
    item.update_record(clicks=item.clicks+1,score=item.score,comments=item.comments,post_time=item.post_time)
    redirect(item.url)

def post(): 
    if not auth.user_id:
        redirect(URL(r=request,f='login'))
    form=SQLFORM(db.news,fields=['url','title','category'])
    form.vars.author=auth.user_id
    form.vars.author_alias=auth.user.alias
    form.element('input[name=url]')['_class']='span11'
    form.element('input[name=url]')['_placeholder']='URL 주소 (입력하지 않으면 스스로를 가르키는 링크)'
    form.element('input[name=title]')['_class']='span11'
    form.element('input[name=title]')['_placeholder']='링크 설명을 입력하세요.'
    form.element('input[type=submit]')['_class']='btn large'
    form.element('input[type=submit]')['_value']='올리기'
    if request.vars.category:
        form.vars.category_alias=db(db.category.name==request.vars.category).select()[0].alias
    if not request.vars.url:
        request.vars.url='self'
    login_form = author_func()
    if form.accepts(request.vars,session):
        session.flash='news posted'
        if not form.vars.category:
            redirect(URL(r=request,f='mylink'))
        else:
            redirect(URL(r=request,f='index',args=[form.vars.category,'new']))
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(login_form=login_form,form=form,cat_list=cat_list)

def report():
    try:
        db(db.news.id==request.args[0]).update(flagged=True)
        session.flash='thanks for your feedback'
    except:
        session.flash='internal error'
    redirect(request.env.http_referer)

def delete():
    if not auth.user_id: redirect(request.env.http_referer)
    try:
        news=db(db.news.id==request.args[0]).select()[0]
        if news.author==auth.user_id:
            db(db.news.id==request.args[0]).delete()
        session.flash='news item deleted'
    except:
        session.flash='internal error'
    redirect(URL(r=request,f='index',args=[news.category]))

def vote():
    if not auth.user_id: redirect(request.env.http_referer)
    news=db(db.news.id==request.args[1]).select()[0]
    try:
        vote = db((db.vote.voter==auth.user_id) & (db.vote.parentv==news)).select()[0]
    except:
        vote = db.vote.insert(parentv=news,voter=auth.user_id)
    if request.args[0]=='up':
        if vote.choice == -1:
            vote.update_record(choice=1)
            news.update_record(score=news.score+2)
        elif vote.choice == 0:
            vote.update_record(choice=1)
            news.update_record(score=news.score+1)
        elif vote.choice == 1:
            vote.update_record(choice=0)
            news.update_record(score=news.score-1)
    elif request.args[0]=='down':
        if vote.choice == 1:
            vote.update_record(choice=-1)
            news.update_record(score=news.score-2)
        elif vote.choice == 0:
            vote.update_record(choice=-1)
            news.update_record(score=news.score-1)
        elif vote.choice == -1:
            vote.update_record(choice=0)
            news.update_record(score=news.score+1)
#    redirect(request.env.http_referer)
    return str(news.score)

def permalink():
    try: comment=db(db.comment.id==request.args[0]).select()[0]
    except: redirect(request.env.http_referer)
    comments=db(db.comment.news==comment.news).select(orderby=db.comment.score)
    news=comment.news
    items=[]
    tree={}
    forms={}
    pivot=None
    for c in comments:
        if not tree.has_key(c.parente): tree[c.parente]=[c]
        else: tree[c.parente].append(c)
        if c.id==comment.id: pivot=c.parente
        if auth.user_id:
           f=SQLFORM(db.comment,fields=['body'],labels={'body':''})
           f.vars.author=auth.user_id          
           f.vars.author_alias=auth.user.alias
           f.vars.news=news
           f.vars.parente=c.id
           if f.accepts(request.vars,formname=str(c.id)):
              session.flash='comment posted'
              redirect(URL(r=request,args=request.args))
           forms[c.id]=f
    tree[pivot]=[comment]
    login_form = author_func()
    response.view='default/comments.html'
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(cat_list=cat_list,item=None,login_form=login_form,form=None,tree=tree,forms=forms,parent=pivot)

def vote_comment():
    if not auth.user_id: redirect(request.env.http_referer)
    comment=db(db.comment.id==request.args[1]).select()[0]
    try:
        vote = db((db.vote_cmt.voter==auth.user_id) & (db.vote_cmt.parentv==comment)).select()[0]
    except:
        vote = db.vote_cmt.insert(parentv=comment,voter=auth.user_id)
    if request.args[0]=='up':
        if vote.choice == -1:
            vote.update_record(choice=1)
            comment.update_record(score=comment.score+2)
        elif vote.choice == 0:
            vote.update_record(choice=1)
            comment.update_record(score=comment.score+1)
        elif vote.choice == 1:
            vote.update_record(choice=0)
            comment.update_record(score=comment.score-1)
    elif request.args[0]=='down':
        if vote.choice == 1:
            vote.update_record(choice=-1)
            comment.update_record(score=comment.score-2)
        elif vote.choice == 0:
            vote.update_record(choice=-1)
            comment.update_record(score=comment.score-1)
        elif vote.choice == -1:
            vote.update_record(choice=0)
            comment.update_record(score=comment.score+1)
    return str(comment.score)

def report_comment():
    try:
        db(db.comment.id==request.args[0]).update(flagged=True)
        session.flash='thanks for your feedback'
    except:
        session.flash='internal error'
    redirect(request.env.http_referer)

def person():
    session.flash='sorry, not yet implemented'
    redirect(request.env.http_referer)


def comments():
    try: news=int(request.args[0])
    except: redirect(URL(r=request,f='index'))
    try:
        item=db(db.news.id==news).select()[0]
        comments=db(db.comment.news==news).select(orderby=~db.comment.score)
    except: redirect(URL(r=request,f='index'))
    if auth.user_id:
        form=SQLFORM(db.comment,fields=['body'],labels={'body':''})
        form.element('textarea[name=body]')['_class']='text span7'
        form.element('textarea[name=body]')['_cols']='70'
        form.element('textarea[name=body]')['_rows']='4'
        form.element('textarea[name=body]')['_placeholder']='코멘트 남기기...'
        form.element('input[type=submit]')['_class']='btn'
        form.element('input[type=submit]')['_value']='올리기'
        form.vars.author=auth.user_id
        form.vars.author_alias=auth.user.alias
        form.vars.news=news
        if form.accepts(request.vars,formname='0'): 
            item.update_record(comments=item.comments+1)
            response.flash='comment posted'
            redirect(URL(r=request,args=request.args))
    else: form=None
    items=[]
    tree={}
    forms={}
    for c in comments:
        if not tree.has_key(c.parente): tree[c.parente]=[c]
        else: tree[c.parente].append(c)
        if auth.user_id:
            f=SQLFORM(db.comment,fields=['body'],labels={'body':''})
            f.element('textarea[name=body]')['_class']='text sub_cmt'
            f.element('textarea[name=body]')['_cols']='70'
            f.element('textarea[name=body]')['_rows']='4'
            f.element('textarea[name=body]')['_placeholder']='코멘트 남기기...'
            f.element('input[type=submit]')['_class']='btn'
            f.element('input[type=submit]')['_value']='올리기'
            f.vars.author=auth.user_id          
            f.vars.author_alias=auth.user.alias
            f.vars.news=news
            f.vars.parente=c.id
            if f.accepts(request.vars,formname=str(c.id)):
                item.update_record(comments=item.comments+1)
                session.flash='comment posted'
                redirect(URL(r=request,args=request.args))
            forms[c.id]=f
    login_form = author_func()
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(cat_list=cat_list,item=item,login_form=login_form,form=form,tree=tree,forms=forms,parent=0)

def edit_comment():
    if not auth.user_id: redirect(request.env.http_referer)
    id=request.args[0]
    try:
        comment=db(db.comment.id==id).select()[0]
        if not comment.author==auth.user_id: raise Exception
    except: redirect(URL(r=request,f='index'))
    form=SQLFORM(db.comment,comment,fields=['body'],showid=False,deletable=True,labels={'body':'Comment'})
    form.element('textarea[name=body]')['_class']='text span11'
    form.element('textarea[name=body]')['_cols']='70'
    form.element('textarea[name=body]')['_rows']='4'
    form.element('input[type=submit]')['_class']='btn'
    form.element('input[type=submit]')['_value']='올리기'
    if form.accepts(request.vars,session):
        session.flash='comment edited'
        redirect(URL(r=request,f='comments',args=[comment.news]))
    login_form = author_func()
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(cat_list=cat_list,login_form=login_form,form=form)

def about():
    return dict(login_form=author_func())

def uplink():
    try: page=int(request.args[1])
    except: page=0
    limitby=(50*page,50*(page+1)+1)
    news=db((db.vote.voter==auth.user_id) & (db.vote.choice==1)).select(limitby=limitby)
    form = author_func()
    return dict(login_form=form,news=news,page=page)

def downlink():
    try: page=int(request.args[1])
    except: page=0
    limitby=(50*page,50*(page+1)+1)
    news=db((db.vote.voter==auth.user_id) & (db.vote.choice==-1)).select(limitby=limitby)
    form = author_func()
    return dict(login_form=form,news=news,page=page)

def mylink():
    try: page=int(request.args[1])
    except: page=0
    limitby=(50*page,50*(page+1)+1)
    news=db(db.news.author==auth.user_id).select(orderby=~db.news.post_time,limitby=limitby)
    form = author_func()
    return dict(login_form=form,news=news,page=page)
def error():
    return dict(login_form=author_func())
def reset_password():
    form=auth.request_reset_password()
    form.element('input[name=email]')['_class']='span5'
    form.element('input[name=email]')['_placeholder']='email'
    form.element('input[type=submit]')['_class']='btn'
    form.element('input[type=submit]')['_value']='패스워드 리셋요청'
    return dict(login_form=author_func(),form=form)

def new_password():
    form=auth.reset_password()
    form.element('input[name=new_password]')['_class']='span3'
    form.element('input[name=new_password]')['_placeholder']='새 비밀번호'
    form.element('input[name=new_password2]')['_class']='span3'
    form.element('input[name=new_password2]')['_placeholder']='새 비밀번호 확인'
    form.element('input[type=submit]')['_class']='btn'
    form.element('input[type=submit]')['_value']='비밀번호 재설정'
    return dict(login_form=author_func(),form=form)
### todo:
"""
allow different types of news sorting
"""

## test article upload
def testukn():
    if auth.user_id:
        for i in range(150):
            db.news.insert(category='movie',author=auth.user_id,author_alias=auth.user.alias,url="http://plan9.kr",title="테스트로 입력하는 글제목")
    redirect(request.env.http_referer)
    
def post_chrome(): 
    if not auth.user_id:
        redirect(URL(r=request,f='login_chrome'))
    form=SQLFORM(db.news,fields=['url','title','category'])
    form.vars.author=auth.user_id
    form.vars.author_alias=auth.user.alias
    form.element('input[name=url]')['_class']='span6'
    form.element('input[name=url]')['_placeholder']='URL 주소 (입력하지 않으면 스스로를 가르키는 링크)'
    #form.element('input[name=url]')['_value']='http://'+request.args[1]
    form.element('input[name=url]')['_value']=request.vars.url
    form.element('input[name=title]')['_class']='span6'
    form.element('input[name=title]')['_placeholder']='링크 설명을 입력하세요.'
    #form.element('input[name=title]')['_value']=request.args[0]
    form.element('input[name=title]')['_value']=request.vars.title
    form.element('input[type=submit]')['_class']='btn large'
    form.element('input[type=submit]')['_value']='올리기'
    form.element('input[type=submit]')['_action']=URL(r=request,args=request.args)
    if request.vars.category:
        form.vars.category_alias=db(db.category.name==request.vars.category).select()[0].alias
    if not request.vars.url:
        request.vars.url='self'
    login_form = author_func()
    if form.accepts(request,session):
        return "올라간듯"+'  <a target="_blank" href="http://www.feed9.com/mylink/">'+"업로드 페이지로 이동"+"</a>"
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    return dict(form=form,cat_list=cat_list)

def login_chrome():
    if auth.user_id:
        redirect(URL(r=request,f='post_chrome'))
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    login_form=auth.login(next=URL(r=request,f='post_chrome'))
    login_form.element('form')['_name']='ext'
    login_form.element('input[name=email]')['_class']='span3'
    login_form.element('input[name=email]')['_placeholder']='email'
    login_form.element('input[name=password]')['_class']='span3'
    login_form.element('input[name=password]')['_placeholder']='password'
    login_form.element('input[type=submit]')['_class']='btn'
    login_form.element('input[type=submit]')['_value']='로그인'
    return dict(cat_list=cat_list,login_form=login_form)

def category():
    cat_list=[[r.alias,r.name] for r in db().select(db.category.ALL)]
    form = author_func()
    return dict(cat_list=cat_list,login_form=form)
