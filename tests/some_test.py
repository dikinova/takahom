from takahom.common.common_util import CommonUtil
from dknovautils import *

from takahom.common.common_ctts_ytb import ytb_reg_simple_shorts, ytb_reg_simple_myid_all
from takahom.common.common_etc import eat_for
from takahom.common.ytb_util import YtbUtil, ln_filter_nor_comments_nor_empty

"""

pip install pytest

运行测试 .venv

PYTHONPATH=$PATHONPATH:./src pytest -s -v

"""


def test_aa():
    assert 1 + 1 == 2

    a = [(i, j) for i in range(3)
         for j in 'abc']

    print(a)

    pass


def test_ab():
    assert len(CommonUtil.parse_rate_limits_from_conf('')) == 24
    assert len(CommonUtil.parse_rate_limits_from_conf('8:23424,0-3:32424,4-6:234324234,*:3242424')) == 24

    arr = CommonUtil.parse_rate_limits_from_conf('8:8000,0-3:3000,4-6:4000,*:3242424')
    print(arr)

    AT.assert_(
        re.fullmatch(
            ytb_reg_simple_shorts, "https://www.youtube.com/shorts/BrkK9WrcRSQ"
        )
    )

    assert re.fullmatch(
        ytb_reg_simple_myid_all, "xxxxxxxxx--x+"
    )

    sa = r'''
    
# 这里面应该有 8 个有效结果 其中有3个列表
; 分号也是注释

https://xxx

#链接 URL
https://www.youtube.com/watch?v=Ch6Ae9DT6Ko
https://www.youtube.com/watch?v=XlnmN4BfCxw&list=PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MBo&_maxitems_=3

# 编号
Ch6Ae9DT6xy
PLC0nd42SBTaMpVAAHCAifm5gN2zLk2MXY

# 目录名
ct-2024-02-03T04-59-21_r-10002880_ok-yes_ytbip-PLTYqHS91RXjz48OJqrU84CITB-IZa-aOU
./a/b/c/ct-2024-02-03T09-39-40_r-10002881_ok-yes_ytbid-YY20TjSyIRa
./a/b/c/ct-2024-02-03T09-39-40_r-10002881_ok-yes_ytbid-YY20TjSyIRg/
.\ct-2024-02-03T09-39-40_r-10002881_ok-yes_ytbid-YY20TjSyIRg\


# mp4 文件
/a/b/c/110上學期期末考試題解析 ➤〈進階憲法對話〉[K81ionkM6_8].mp4    
./a/b/c/110上學期期末考試題解析 ➤〈進階憲法對話〉[K81ionkM5_8].mp4    
s:\a\b\110上學期期末考試題解析 ➤〈進階憲法對話〉[K81ionkM7_8].mp4    
.\a\b\110上學期期末考試題解析 ➤〈進階憲法對話〉[K81ionkM7_8].mp4    

S:\_DISC_S_\thinking\politics\中国近代史文革\时事大家谈：魏京生司马南激辩文革-upQSDcpIm48.webm.mp4
S:\_DISC_S_\thinking\politics\中国近代史文革\时事大家谈：魏京生司马南激辩文革-upQSDcpIm48.mp4


# description 文件
.\a\b\110上學期期末考試題解析 ➤〈進階憲法對話〉[K81ionkM5_9].description    





    '''

    r = list(YtbUtil.parse_ytbid_from_lines(sa.splitlines()))
    eat_for(print(str(ln)) for ln in r)
    assert len(r) == 15
