py=python3.9
py=python3.10
# py=python

PYTHONPATH=$PYTHONPATH:./src $py -m takahom.server run \
  --conf ./docs/env.dknova.conf --profile prod 2>&1 | tee -a tmp.out


:<<EOF


客户端用wget下载资源

wget -r -nH -np --cut-dirs=1 --no-check-certificate \
  -c http://192.168.0.35:8800/file/index.html


EOF

