### HTTP-文件下载上传服务器
通过二维码扫描下载文件、不需要账号密码授权登录

### centos7安装pip2
which git 2>> /dev/null || yum -y install git
which git pip2 >> /dev/null || yum -y install epel-release
which git pip2 >> /dev/null || yum -y install python-pip
# yum install python-markupsafe

### 部署安装
git clone https://github.com/wanggaolin/fileHttp.git
cd fileHttp
pip2 install -r document/requests.txt 
