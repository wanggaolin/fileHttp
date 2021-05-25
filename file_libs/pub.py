#!/usr/bin/env python
#coding=utf-8
# date: 2021/05/25
import re
import os
import logging
import json
import time
from PIL import Image
import qrcode
from io import BytesIO
import hmac
import hashlib
from configparser import ConfigParser

def log():
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(get_conf()["log_file"], maxBytes=1024 * 1024 * 1024 * 1024, backupCount=5)
    fmt = '%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] [pid:%(process)d] %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    return handler


def dir_files(x):
    """
    :param x: file path name
    :return: /a/b
    """
    if x:
        x = dir_name(x)
        x = re.sub('^/+', '',str(x))
        x = re.sub('/+$', '',str(x))
    return x


def dir_name(x):
    """
    :param x: directory path name
    :return: /a/b
    """
    if x:
        if x[-1] == '/':
            x = x[0:-1]
    return x


def get_conf():
    cfg = ConfigParser()
    config_dict = {}
    cfg.read('file.conf', encoding='UTF-8')
    config_dict["host"] = cfg.get('GLOABLE','LISTEN_HOST')
    config_dict["port"] = cfg.getint('GLOABLE','LISTEN_PORT')
    config_dict["debug"] = cfg.getboolean('GLOABLE','DEGUT')
    config_dict["log_file"] = cfg.get('GLOABLE','LOG_FILE')
    config_dict["token"] = cfg.get('GLOABLE','TOKEN_HASH')
    config_dict["base_dir"] = cfg.get('FILE','DIRECOTRY_NAME')
    return config_dict

class file_manger:
    def __init__(self):
        self.base_dir = get_conf()["base_dir"]
        self.re_base_dir = re.compile(r'^%s/' % self.base_dir)
        self.re_filter1 = re.compile(r'\\|\'|\"|\&|\=|\ |\%|\.\.|,|\*|\+|\./')
        self.re_filter2 = re.compile(r'\\|\'|\"|\&|\=|\ |\%|\.\.|,|\*|\+|/|\./')
        self.re_hide_file = re.compile(r'\.svn$|\.git$')

    def check(Fn):
        def Test(self, *args, **kwargs):
            args_dir_name = kwargs.get("dir_name",False)
            args_path_name = kwargs.get("path_name",False)
            if args_dir_name is None:
                kwargs["dir_name"] = "/"
                args_dir_name = "/"
            if not args_dir_name is False:
                end = re.findall(self.re_filter1, args_dir_name)
                if end:
                    if end[0] == " ":
                        end[0] = "空格"
                    raise ValueError("目录名不得包含特殊字符:%s" % end[0])
                elif re.search(self.re_hide_file, args_dir_name):
                    raise ValueError("该目录禁止操作")
            if not args_path_name is False:
                end = re.findall(self.re_filter2, args_path_name)
                if end:
                    if end[0] == " ":
                        end[0] = "空格"
                    raise ValueError("文件名不得包含特殊字符:%s" % end[0])
                elif re.search(self.re_hide_file, args_path_name):
                    raise ValueError("该文件禁止操作")
            if kwargs.get("path_name",False):
                kwargs["path_name"] = kwargs["path_name"].encode("utf-8").strip()
                if kwargs["path_name"] == "":
                    raise ValueError("文件名不得为空")
            return Fn(self, *args, **kwargs)
        return Test

    def dir_name(self,x):
        x = re.sub(r'^/+','',str(x).strip())
        x = re.sub(r'/+$','',x)
        x = dir_files(x)
        return x

    @check
    def file_list(self, **kwargs):
        data = []
        name = self.dir_name(kwargs["dir_name"])
        root_dir_name = os.path.join(self.base_dir, name)
        if not os.path.exists(root_dir_name):
            raise ValueError("%s: 目录不存在" % root_dir_name)
        if name == "":
            path_dir = []
        else:
            path_dir = self.dir_path(**kwargs)

        for file_number, file_path in enumerate(os.listdir(root_dir_name)):
            file_full = os.path.join(root_dir_name, file_path)
            hide_file_full = re.sub(self.re_base_dir, "", os.path.join(root_dir_name, file_path))
            if re.search(self.re_hide_file, file_full):
                continue
            if os.path.isfile(file_full):
                default_type = ""
                data.append({
                    "id": file_number,
                    "file_name": file_path,
                    "file_full": hide_file_full,
                    "file_type": default_type,
                    "size": self.file_size(x=file_full),
                    "time": time.strftime('%Y-%m-%d %H:%M:%S', (time.localtime(os.stat(file_full).st_mtime))),
                })
            else:
                data.append({
                    "id": file_number,
                    "directory": True,
                    "file_name": file_path,
                    "file_full": hide_file_full,
                    "size": "-",
                    "time": time.strftime('%Y-%m-%d %H:%M:%S', (time.localtime(os.stat(file_full).st_mtime))),
                })
        return {"file_list": data, "path_dir": path_dir}

    def file_size(self,x):
        s = float(os.path.getsize(x))
        if (s/1024/1024/1024) > 1:
            s = "%sG" % round(s/1024/1024/1024,1)
        elif (s/1024/1024) > 1:
            s = "%sM" % round(s/1024/1024,1) #ok
        elif (s / 1024 ) > 1:
            s = "%sK" % round(s / 1024 , 1) #ok
        else:
            s = round(s,1)
        return s


    @check
    def dir_path(self,**kwargs):
        path_dir = []
        name = self.dir_name(kwargs["dir_name"])
        root_dir_name = os.path.join(self.base_dir, name)
        root_dir_name_list = re.sub(self.re_base_dir, "", root_dir_name).split("/")
        path_dir = []
        for i in range(1, len(root_dir_name_list) + 1):
            path_dir.append({
                "path": "/".join(root_dir_name_list[:i]),
                "name": root_dir_name_list[:i][-1],
            })
        return  path_dir
    #
    # @check
    # def file_save(self,**kwargs):
    #     name = self.dir_name(kwargs["dir_name"])
    #     root_dir_name = os.path.join(self.base_dir,name)
    #     file_path = os.path.join(root_dir_name,dir_files(kwargs["path_name"]))
    #     if os.path.exists(file_path):
    #         raise ValueError("文件已经存在")
    #     with open(file_path,r'w+') as w:
    #         for chunk in kwargs["obj"].chunks():
    #             w.write(chunk)
    #     return True,{"msg":"上传文件: %s" % self.hide(x=file_path),"file_path":file_path}
    #
    # def file_type(self,x):
    #     try:
    #         file_name,file_ext = os.path.splitext(x)
    #         return file_ext
    #     except Exception,e:
    #         Loging().error(traceback.format_exc())
    #     return ""

    @check
    def file_path(self,**kwargs):
        name = self.dir_name(kwargs["dir_name"])
        root_dir_name = os.path.join(self.base_dir,name)
        file_path = os.path.join(root_dir_name,dir_files(kwargs["path_name"]))
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")
        if not os.path.isfile(file_path):
            raise ValueError("仅支持下载文件")
        return file_path

def make_code(url):
    qr = qrcode.QRCode(version=8, error_correction=3, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    img = img.convert("RGBA")
    icon = Image.open("file_libs/static/image/logo.png")
    img_w, img_h = img.size
    icon_w = 180
    icon_h = 120
    icon = icon.resize((icon_w, icon_h), Image.ANTIALIAS)
    w = int((img_w - icon_w)/2)
    h = int((img_h - icon_h)/2)
    icon = icon.convert("RGBA")
    img.paste(icon, (w, h), icon)
    # img.show()
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)
    return byte_io


class api_verfy:
    def __init__(self,**kwargs):
        self.key = kwargs["key"].encode("utf-8")

    def encryption(self,**kwargs):
        text = json.dumps(sorted(kwargs["data"].items(), key=lambda parameters: parameters[0]))+str(kwargs["time"])
        mac = hmac.new(self.key, text.encode("utf-8"), hashlib.sha1)
        return mac.hexdigest()

    def verfy(self,**kwargs):
        text = json.dumps(sorted(kwargs["data"].items(), key=lambda parameters: parameters[0]),ensure_ascii=False)+str(kwargs["time"])
        mac = hmac.new(self.key, text.encode("utf-8"), hashlib.sha1)
        return mac.hexdigest()


# print file_manger().file_list(dir_name="/")
