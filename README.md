### HTTP-文件下载上传服务器
通过二维码扫描下载文件、不需要账号密码授权登录

### centos7安装pip2
```shell script
which git 2>> /dev/null || yum -y install git
which git pip2 >> /dev/null || yum -y install epel-release
which git pip2 >> /dev/null || yum -y install python-pip
# yum install python-markupsafe
```

### 部署安装
```shell script
git clone https://github.com/wanggaolin/fileHttp.git
cd fileHttp
pip2 install -r document/requests.txt
```

### 运行 
```shell script
python main.py
```

### 命令上传文件/安全
```shell script
curl http://0.0.0.0:5001/upload -F "file=@1.txt" -F "token=d329c61a58e37b20c19f723e2b0a8550" -X POST 
```