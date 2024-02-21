AppVer="0.7.1"


sed -i "s/^AppVer.*/AppVer = '$AppVer'/" ./src/takahom/common/common_imports.py

sed -i "s/^version =.*/version = '$AppVer'/" ./pyproject.toml

rm ./dist/*

py=python3.8
py=python3.10
py=python

$py -m build

# python3 setup.py sdist build
export PATH=$PATH:~/.local/bin

# test repo
# python3 -m twine upload --repository testpypi dist/*
#        输入用户名 密码 即可完成上传。
$py -m twine upload dist/*

# -----------------------------------------------------------
:<<EOF

在wsl 中执行
    cd ../takahom
    ./docs/upload.sh

更换为apitoken 用户名 __token__ 密码是token值
token值好像是每次都要生成新的值？

sudo apt-get install python3-venv

python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine


    pip服务器可能不再支持search功能
    python3 -m pip search dknovautils


    用如下命令安装特定版本的库 事实证明tuna的更新是明显滞后的 可能滞后一天以上的时间
    python3 -m pip install dknovautils==0.1.9 -i https://pypi.tuna.tsinghua.edu.cn/simple



EOF

