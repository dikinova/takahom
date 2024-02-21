py=python3.9
py=python3.10
#py=python


PYTHONPATH=$PYTHONPATH:./src $py -m takahom.server demo \
  --conf ./docs/env.demo.conf --profile dev 2>&1 | tee -a tmp.out



:<<EOF


在wsl下面 venv中 开发本上运行







EOF