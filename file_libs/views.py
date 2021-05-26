#coding=utf-8
from flask import Flask,request,render_template,Response,send_file
from pub import file_manger,make_code,api_verfy,get_conf
import random
import json
import urllib
app = Flask(__name__)
import time
import traceback
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
                if request.method == "POST":
                    req_token = request.form.get("token", False)
                    req_json = json.loads(urllib.unquote(request.form.get("data", False)))
                    req_time = int(request.form.get("time", False))
                else:
                    req_token = request.args.get("token", False)
                    req_json = json.loads(urllib.unquote(request.args.get("data", False)))
                    req_time = int(request.args.get("time", False))
            except Exception,e:
                return "请求参数格式错误"
            if not min_size < (time.time()-req_time) < max_size:
                return "token已过期"
            if req_token == api_verfy(key=cfg_conf["token"]).verfy(data=req_json, time=req_time):
                return func(*args, **kwargs)
            else:
                return "认证失败"
        return wrapper_v3
    return decorator_v3

# def error_code(*args,**kwargs):
#     def decorator_error(func_error):
#         def wrapper_error(*args, **kwargs):
#             try:
#                 return func_error(*args, **kwargs)
#             except ValueError,e:
#                 return e.message,503
#             except Exception,e:
#                 return "code error",500
#         return wrapper_error
#     return decorator_error

def error_code(*args,**kwargs):
    def decorator_error(func2):
        def wrapper_error(*args, **kwargs):
            return func2(*args, **kwargs)
        return wrapper_error
    return decorator_error

@app.route('/',methods=["GET"])
@auth_verify(token="dns_zone")
@error_code()
def views_file_list():
    dir_name = request.args.get("dir", "")
    n = int(time.time())
    return render_template('index.html', file_list=file_manger().file_list(dir_name=dir_name),dir_name=dir_name,n=n)

@app.route('/file/download',methods=["GET"])
@error_code()
def views_file_download():
    dir_name = request.args.get("dir","")
    file_path = request.args.get("file","")
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
@api_check_v3(min_size=-(60*60*5),max_size=60*60*5)
@error_code()
def views_file_download_secure():
    req_data = json.loads(urllib.unquote(request.args.get("data", False)))
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

@app.route('/file/upload',methods=["POST"])
def views_file_upload():
    file_status = []
    df = file_manger()
    try:
        ss = {"files": [], "name": ""}
        for file_info in request.files.getlist('fileupload'):
            upload_status = df.file_save(path_name=file_info.filename,obj=file_info,dir_name=request.args.get("dir",""))
            if upload_status[0]:
                file_status.append({"name": file_info.filename, "size": df.file_size(upload_status[1]["file_path"])})
            else:
                file_status.append({"name": file_info.filename, "size": 0,"error":upload_status[1]["msg"]})
        ss["files"] = file_status
    except ValueError,e:
        ss["error"] = e.message
    except Exception,e:
        ss["error"] = "code error"
        print traceback.format_exc()
    return json.dumps(ss)

@app.route('/upload',methods=["POST"])
def views_file_secure_upload():
    error_msg = ""
    file_info = request.files.get('file')
    try:
        if request.form.get("token") != cfg_conf["token"]:
            error_msg = "token error"
        elif file_info:
            upload_status = file_manger().file_save(path_name=file_info.filename,obj=file_info,dir_name="/")
            if upload_status[0]:
                return "update success"
        else:
            error_msg = "上传为空对象"
    except ValueError,e:
        error_msg = e.message
    except Exception,e:
        error_msg = "code error"
        print traceback.format_exc()
    return error_msg, 503

@app.errorhandler(404)
def not_found(error):
    return "not found", 404