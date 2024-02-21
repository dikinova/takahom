from __future__ import annotations

import attr.exceptions

from takahom.common.common_util import *
from takahom.common.common_etc import DkFile2
from takahom.server.server_base_a import IServerBaseA, dec_my_log_error_builder


@define(slots=True, frozen=True, kw_only=True)
class DirSizeInfo:
    ctime_ms: int  # epoch millis
    size_n: int  # 该时刻的sdownload目录的大小 字节数


TS_LEN: int = 1000 * 60 * 5  # 5mins长度的毫秒值


@define(slots=True, frozen=True, kw_only=True)
class TimeSpan:
    start: int  # ms
    end: int  # exclusive
    rate: int = -1  # Bytes/sec B/s

    def next_span(self, n: int = 1, rate: int = -1) -> TimeSpan:
        r = TimeSpan(start=self.start + n * TS_LEN,
                     end=self.end + n * TS_LEN,
                     rate=rate)
        return r


class INetCalulator(Protocol):
    dir_size_infos: List[DirSizeInfo]
    rate_timespans: List[TimeSpan]
    scache_size: int
    downloaded_bytes: int

    @dec_my_log_error_builder(message="Error on tgt_job_update_sdownload_size: {e!r}")  # type:ignore
    def tgt_update_sdownload_size(self, dkf: DkFile) -> None:
        # 60s调用一次
        cmd = f'du "{dkf.pathstr}" -d0 --block-size=1'
        rc, out, err = run_simple_b(cmd)
        self.scache_size = int(out.strip().split()[0])
        self.f_add_sizeinfo(DirSizeInfo(ctime_ms=AT.fepochMillis(), size_n=self.scache_size))
        self.tgt_job_update_netrates()

    def f_add_sizeinfo(self, dsi: DirSizeInfo) -> None:
        """
        大概是每40s - 60s的时间间隔产生一个数据
        """
        AT.assert_(dsi.ctime_ms > 0 and dsi.size_n >= 0, 'err87643')
        dus = self.dir_size_infos
        if dus:
            AT.assert_(dus[-1].ctime_ms + 10 < dsi.ctime_ms, 'err14647')
            diff = dsi.size_n - dus[-1].size_n
            if diff > 0:
                self.downloaded_bytes += diff

        dus.append(dsi)
        while len(dus) >= 50:
            dus.pop(0)

    def tgt_job_update_netrates(self) -> None:
        """
        本函数大概是60s的周期被调用

        返回按照每N=5分钟汇总计算的平均网速 KBytes/secons KB/s

        数据参数中
            dus的数据也是按照时间的升序排列 大概是每40s - 60s的时间间隔产生一个数据
            因为是同一个thread内部 所以不需要 临界区了

        最多保存100个5分钟的数据 如果某分钟内无数据 则对应的数据为零
        时间最近的数据排在后面 按照时间升序排列

        约束和校验
            dus中时间值是严格升序的 否则异常 间隔>10s size_n>=0 len(dus)<100 不需要检查已经保证
            rts 也是严格升序的 而且是连续的 如果 len(rts)>100 直接pop(0)即可

        算法
            fa： 输入 时刻点集，返回 包括所有时间的连续的区间遍历器（不会超出这个时间的范围，就是说，最早和最晚的区间，一定包含某个时间点）
                从 最早时刻 一直连续到 最晚的时刻 的区间集合
            fb 两个参数，时间点和区间 返回两者之间的关系 -1表示时间点在区间之前，0表示在区间内 1表示在区间后

            fc 两个参数，区间r和时间点p，返回 区间r+1 ... 区间x 的遍历器。 区间x是所有<p的最大的一个区间
                在fa的基础上实现即可
                所以其实是参数的全开区间的范围内的遍历

            fd 两个参数 区间r和时间点集ps 计算区间内的网速数值
                ps是时间升序排列的
                sum(diff for a,b in pairwise(ps)
                    if b in span_r
                    if (diff := b.sizen -a.sizen)>0
                    )



        """

        L = TS_LEN  # 5mins长度的毫秒值

        def fb_compare(ms: int, span: TimeSpan) -> int:
            assert ms >= 0 and span.start >= 0 and span.end > 0
            if ms < span.start:
                return -1
            elif span.start <= ms < span.end:
                return 0
            else:
                return 1

        def fa_iter(mss: Iterable[int]) -> Iterator[TimeSpan]:
            a, b = min(mss), max(mss)
            assert mss and 0 <= a <= b and L > 0
            start = (a // L) * L
            while True:
                span = TimeSpan(start=start, end=start + L)
                if fb_compare(b, span) >= 0:
                    yield span
                    start += L
                else:
                    return

        def fc_iter(span: TimeSpan, pms: int) -> Iterator[TimeSpan]:
            assert span.start >= 0 and span.end > 0 and pms >= 0, f'err70652 {span} {pms}'
            if fb_compare(pms, span) <= 0:
                return
            assert pms >= span.end
            for _s in fa_iter([span.end, pms]):
                if fb_compare(pms, _s) > 0:
                    yield _s
                else:
                    return

        def fd_rate(span: TimeSpan, mss: Iterable[DirSizeInfo]) -> int:
            """
            fd 两个参数 区间r和时间点集ps 计算区间内的网速数值
                ps是时间升序排列的
                sum(diff for a,b in pairwise(ps)
                    if b in span_r
                    if (diff := b.sizen -a.sizen)>0
                    )
            """
            s = sum(diff for a, b in ite.pairwise(mss)
                    if fb_compare(b.ctime_ms, span) == 0
                    if (diff := b.size_n - a.size_n) > 0
                    )
            return int(s / (TS_LEN / 1000))

        dus = self.dir_size_infos
        rts = self.rate_timespans

        def fcheck() -> None:
            AT.assert_(0 <= len(dus) < 100)
            # rts 也是严格升序的 而且是连续的 如果 len(rts)>100 直接pop(0)即可
            AT.assert_(all((b.start - a.start) == L for a, b in ite.pairwise(rts)), 'err39945')
            while len(rts) >= 100:
                rts.pop(0)
            AT.assert_(0 <= len(rts) < 100)
            AT.assert_(all(ts.rate >= 0 for ts in rts), 'err67961')

        fcheck()

        now = AT.fepochMillis()

        if not rts:
            # 最初始的状态
            sps = list(fa_iter([now]))
            AT.assert_(len(sps) == 1 and fb_compare(now, sps[0]) == 0, 'err54036')
            pre_span = sps[0].next_span(n=-1, rate=0)
            rts.append(pre_span.next_span(n=0, rate=fd_rate(pre_span, dus)))
            iprint_debug(f'add span network rates. {rts}')

        else:
            sps = [_span.next_span(n=0, rate=fd_rate(_span, dus)) for _span in fc_iter(rts[-1], now)]
            rts.extend(sps)
            if sps:
                iprint_debug(f'add span network rates. {sps}')
            fcheck()


