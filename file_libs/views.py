#coding=utf-8
from flask import Flask,request,render_template,Response,send_file
from pub import file_manger,make_code,api_verfy,get_conf
import random
import json
import urllib
app = Flask(__name__)
import time
n = int(time.time())
cfg_conf = get_conf()

def auth_verify(*args,**kwargs):
    token_name = kwargs["token"]
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            if token_check(req=request,token_name=token_name):
                return func(*args, **kwargs)
            else:
                return ResponseJson(status=10010,msg="check token has failed")
        return wrapper
    return decorator

def api_check_v3(*args,**kwargs):
    min_size = kwargs.get('min_size',-300)
    max_size = kwargs.get('max_size',300)
    def decorator_v3(func):
        def wrapper_v3(*args, **kwargs):
            try:
                import traceback
                print request,args,kwargs,args,1111
                if request.method == "POST":
                    req_token = request.args.get("token", False)
                    req_json = json.loads(urllib.unquote(request.args.get("data", False)))
                    req_time = int(request.args.get("time", False))
                else:
                    req_token = request.args.get("token", False)
                    req_json = json.loads(urllib.unquote(request.args.get("data", False)))
                    req_time = int(request.args.get("time", False))
            except Exception,e:
                print traceback.print_exc()
                return "请求参数格式错误"
            if not min_size < (time.time()-req_time) < max_size:
                return "token已过期"
            if req_token == api_verfy(key=cfg_conf["token"]).verfy(data=req_json, time=req_time):
                return func(*args, **kwargs)
            else:
                return "认证失败"
        return wrapper_v3
    return decorator_v3

@app.route('/',methods=["GET"])
@auth_verify(token="dns_zone")
def views_file_list():
    dir_name = request.args.get("dir", "")
    n = int(time.time())
    return render_template('index.html', file_list=file_manger().file_list(dir_name=dir_name),dir_name=dir_name,n=n)

@app.route('/file/download',methods=["GET"])
def views_file_download():
    req_data = json.loads(urllib.unquote(request.args.get("data", False)))
    dir_name = req_data.get("dir","")
    file_path = req_data.get("file","")
    file_path_full = file_manger().file_path(dir_name=dir_name, path_name=file_path)
    if file_path_full:
        def file_send():
            store_path = file_path_full
            with open(store_path, 'rb') as targetfile:
                while 1:
                    data = targetfile.read(5 * 1024 * 1024)  # every read 5M
                    if not data:
                        break
                    yield data
        response = Response(file_send(), content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % file_path
        return response


@app.route('/file/secure', methods=["GET"])
@api_check_v3(min_size=60*60*5,max_size=60*60*5)
def views_file_download_secure():
    req_data = json.loads(request.args.get("data", "{}"))
    dir_name = req_data.get("dir", "")
    file_path = req_data.get("file", "")
    file_path_full = file_manger().file_path(dir_name=dir_name, path_name=file_path)
    if file_path_full:
        def file_send():
            store_path = file_path_full
            with open(store_path, 'rb') as targetfile:
                while 1:
                    data = targetfile.read(5 * 1024 * 1024)  # every read 5M
                    if not data:
                        break
                    yield data
        response = Response(file_send(), content_type='application/octet-stream')
        response.headers["Content-disposition"] = 'attachment; filename=%s' % file_path
        return response

@app.route('/file/code',methods=["GET"])
def views_file_code():
    dir_name = request.args.get("dir","")
    file_path = request.args.get("file","")
    req_data = {"dir": dir_name, "file": file_path, "n": random.randrange(10000, 99999),"time":int(time.time())}
    req_token = api_verfy(key=cfg_conf["token"]).encryption(time=req_data["time"],data=req_data)
    file_url = "http://%s/file/secure?time=%s&data=%s&token=%s" % (request.headers["Host"],req_data["time"],urllib.quote(json.dumps(req_data)),req_token)
    byte_io = make_code(file_url)
    return send_file(byte_io, mimetype='image/png')

@app.errorhandler(404)
def not_found(error):
    return "not found", 404