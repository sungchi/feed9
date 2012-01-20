###########################################################
### make sure administrator is on localhost
############################################################

import os, socket
import gluon.contenttype
import gluon.fileutils

http_host = request.env.http_host.split(':')[0]
remote_addr = request.env.remote_addr
try: hosts=(http_host, socket.gethostbyname(remote_addr))
except: hosts=(http_host,)
if remote_addr not in hosts:
    raise HTTP(400)
if not gluon.fileutils.check_credentials(request):
    redirect('/admin')

response.view='appadmin.html'
response.menu=[[T('design'),False,'/admin/default/design/%s' % request.application],
               [T('db'),False,'/%s/%s/index' % (request.application, request.controller)],
               [T('state'),False,'/%s/%s/state' % (request.application, request.controller)]]


###########################################################
### list all tables in database
############################################################

def index():
    import types as _types
    _dbs={}
    try: GQLDB
    except: GQLDB=SQLDB
    for _key,_value in globals().items():
        if isinstance(_value,GQLDB):
           tables=_dbs[_key]=[]
           for _tablename in _value.tables:
               tables.append((_key,_tablename))
    return dict(dbs=_dbs)

###########################################################
### insert a new record
############################################################

def insert():
    try:
        dbname=request.args[0]
        db=eval(dbname)
        table=db[request.args[1]]
    except:
        session.flash=T('invalid request')
        redirect(URL(r=request,f='index'))
    form=SQLFORM(table)
    if form.accepts(request.vars,session):
        response.flash=T('new record inserted')
    return dict(form=form)

###########################################################
### list all records in table and insert new record
############################################################

def download():
    import os
    dbname=request.args[0]
    ### for GAE only ###
    tablename,fieldname=request.args[1].split('.')[:2]
    uploadfield=eval(dbname)[tablename][fieldname].uploadfield
    filename=request.args[1]
    if isinstance(uploadfield,str):
        from gluon.contenttype import contenttype
        response.headers['Content-Type']=contenttype(filename)
        db=eval(dbname)
        rows=db(db[tablename][fieldname]==filename).select()
        return rows[0][uploadfield]
    ### end for GAE ###
    filename=os.path.join(request.folder,'uploads/',filename)
    return response.stream(open(filename,'rb'))

def csv():
    import gluon.contenttype
    response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
    try:
        dbname=request.vars.dbname
        db=eval(dbname)
        response.headers['Content-disposition']="attachment; filename=%s_%s.csv" % (request.vars.dbname, request.vars.query.split('.',1)[0])
        return str(db(request.vars.query).select())
    except:
        session.flash=T('unable to retrieve data')
        redirect(URL(r=request,f='index'))

def import_csv(table,file):
    import csv
    reader = csv.reader(file)
    colnames=None
    for line in reader:
        if not colnames: 
            colnames=[x[x.find('.')+1:] for x in line]
            c=[i for i in range(len(line)) if colnames[i]!='id']            
        else:
            items=[(colnames[i],line[i]) for i in c]
            table.insert(**dict(items))

def select():
    try:
        dbname=request.args[0]
        db=eval(dbname)
        if request.vars.query:
            query=request.vars.query
            orderby=None
            start=0
        elif request.vars.orderby:
            query=session.appadmin_last_query
            orderby=request.vars.orderby
            if orderby==session.appadmin_last_orderby:
                if orderby[-5:]==' DESC': oderby=orderby[:-5]
                else: orderby=orderby+' DESC'
            start=0
        elif request.vars.start!=None:
            query=session.appadmin_last_query
            orderby=session.appadmin_last_orderby
            start=int(request.vars.start)
        else:
            table=request.args[1]
            query='%s.id>0' % table    
            orderby=None
            start=0
        session.appadmin_last_query=query
        session.appadmin_last_orderby=orderby
        limitby=(start,start+100)
    except:
        session.flash=T('invalid request')
        redirect(URL(r=request,f='index'))
    if request.vars.csvfile!=None:        
        try:
            import_csv(db[table],request.vars.csvfile.file)
            response.flash=T('data uploaded')
        except: 
            response.flash=T('unable to parse csv file')
    if request.vars.delete_all and request.vars.delete_all_sure=='yes':
        try:
            db(query).delete()
            response.flash=T('records deleted')
        except:
            response.flash=T('invalid SQL FILTER')
    elif request.vars.update_string:
        try:
            env=dict(db=db,query=query)
            exec('db(query).update('+request.vars.update_string+')') in env
            response.flash=T('records updated')
        except:
            response.flash=T('invalid SQL FILTER or UPDATE STRING')
    try:
        records=db(query).select(limitby=limitby,orderby=orderby)
    except: 
        response.flash=T('invalid SQL FILTER')
        return dict(records=T('no records'),nrecords=0,query=query,start=0)
    linkto=URL(r=request,f='update',args=[dbname])
    upload=URL(r=request,f='download',args=[dbname])
    return dict(start=start,query=query,orderby=orderby, \
                nrecords=len(records),\
                records=SQLTABLE(records,linkto,upload,orderby=True,_class='sortable'))

###########################################################
### edit delete one record
############################################################

def update():
    try:
        dbname=request.args[0]
        db=eval(dbname)
        table=request.args[1]
    except:
        response.flash=T('invalid request')
        redirect(URL(r=request,f='index'))
    try:
        id=int(request.args[2])
        record=db(db[table].id==id).select()[0]
    except:
        session.flash=T('record does not exist')
        redirect(URL(r=request,f='select/%s/%s'%(dbname,table)))
    form=SQLFORM(db[table],record,deletable=True,
                 linkto=URL(r=request,f='select',args=[dbname]),
                 upload=URL(r=request,f='download',args=[dbname]))
    if form.accepts(request.vars,session): 
        response.flash=T('done!')        
        redirect(URL(r=request,f='select/%s/%s'%(dbname,table)))
    return dict(form=form)

###########################################################
### get global variables
############################################################

def state():
    return dict(state=request.env)
