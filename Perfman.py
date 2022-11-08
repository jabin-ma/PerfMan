import os
from typing import Dict

from pyecharts import options as opts
from pyecharts.charts import Pie

import sysmaps
from sysmaps import SysMaps

_HEAP_BIT = 16
_HEAP_MASK = 0xFFFF << 16
_HEAP_SUB_BIT = 0
_HEAP_SUB_MASK = 0xFFFF


class HeapType:
    raw: int = 0

    def getType(self):
        return (self.raw & _HEAP_MASK) >> _HEAP_BIT

    def getSubType(self):
        return (self.raw & _HEAP_SUB_MASK) >> _HEAP_SUB_BIT

    def sameAs(self, item):
        return item.getType() == self.getType()


def make_HeapType(main_type: int, sub_type=0) -> HeapType:
    maked_type = HeapType()
    maked_type.raw &= ~_HEAP_BIT
    maked_type.raw &= ~_HEAP_SUB_BIT
    maked_type.raw |= main_type << _HEAP_BIT
    maked_type.raw |= sub_type << _HEAP_SUB_BIT
    return maked_type


HEAP_UNKNOWN = make_HeapType(1)
HEAP_DALVIK = make_HeapType(2)
HEAP_NATIVE = make_HeapType(3)

HEAP_DALVIK_OTHER = make_HeapType(5)
HEAP_STACK = make_HeapType(6)
HEAP_CURSOR = make_HeapType(7)
HEAP_ASHMEM = make_HeapType(8)
HEAP_GL_DEV = make_HeapType(9)
HEAP_UNKNOWN_DEV = make_HeapType(10)
HEAP_SO = make_HeapType(11)
HEAP_JAR = make_HeapType(12)
HEAP_APK = make_HeapType(13)
HEAP_TTF = make_HeapType(14)
HEAP_DEX = make_HeapType(15)
HEAP_OAT = make_HeapType(16)
HEAP_ART = make_HeapType(17)
HEAP_UNKNOWN_MAP = make_HeapType(18)
HEAP_GRAPHICS = make_HeapType(19)
HEAP_GL = make_HeapType(20)
HEAP_OTHER_MEMTRACK = make_HeapType(21)

# Dalvik extra sections (heap).               =
HEAP_DALVIK_NORMAL = make_HeapType(2, 1)
HEAP_DALVIK_LARGE = make_HeapType(2, 2)
HEAP_DALVIK_ZYGOTE = make_HeapType(2, 3)
HEAP_DALVIK_NON_MOVING = make_HeapType(2, 4)

# Dalvik other extra sections.                =
HEAP_DALVIK_OTHER_LINEARALLOC = make_HeapType(23, 1)
HEAP_DALVIK_OTHER_ACCOUNTING = make_HeapType(23, 2)
HEAP_DALVIK_OTHER_ZYGOTE_CODE_CACHE = make_HeapType(23, 3)
HEAP_DALVIK_OTHER_APP_CODE_CACHE = make_HeapType(23, 4)
HEAP_DALVIK_OTHER_COMPILER_METADATA = make_HeapType(23, 5)
HEAP_DALVIK_OTHER_INDIRECT_REFERENCE_TABLE = make_HeapType(23, 6)

# Boot vdex / app dex / app vdex              =      make_HeapType(24, 1)
HEAP_DEX_BOOT_VDEX = make_HeapType(24, 2)
HEAP_DEX_APP_DEX = make_HeapType(24, 3)
HEAP_DEX_APP_VDEX = make_HeapType(24, 4)

# App art boot art.                           =
HEAP_ART_APP = make_HeapType(25, 1)
HEAP_ART_BOOT = make_HeapType(25, 2)

HEAP_MMAP: Dict[str, HeapType] = {
    r'^\[heap\]': HEAP_NATIVE,
    r'^\[anon:libc_malloc\]': HEAP_NATIVE,
    r'^\[anon:scudo:': HEAP_NATIVE,
    r'^\[anon:GWP-ASan': HEAP_NATIVE,
    r'^\[stack': HEAP_STACK,
    r'^\[anon:stack_and_tls:': HEAP_STACK,
    r'.+\.so$': HEAP_SO,
    r'.+\.jar$': HEAP_JAR,
    r'.+\.apk$': HEAP_APK,
    r'.+\.ttf$': HEAP_TTF,
    r'.+\.(odex|dex)$': HEAP_DEX_APP_DEX,

    r'.+(\@boot|\/boot|\/apex).+\.vdex$': HEAP_DEX_BOOT_VDEX,  # sub-boot-vdex
    r'.+\.vdex$': HEAP_DEX_APP_VDEX,  # sub-app-vdex

    r'.+\.oat$': HEAP_OAT,
    r'.+\.(art|art\])$': HEAP_ART,
    r'^\/dev\/kgsl-3d0': HEAP_GL_DEV,

    r'^\/dev\/ashmem\/CursorWindow': HEAP_CURSOR,
    r'^\/dev\/ashmem\/jit-zygote-cache': HEAP_DALVIK_OTHER,  # sub-zygote-code-cache
    r'^\/dev\/ashmem': HEAP_ASHMEM,
    r'^\/dev\/': HEAP_UNKNOWN_DEV,
    r'^\/memfd:jit-cache': HEAP_DALVIK_OTHER_APP_CODE_CACHE,
    r'^\/memfd:jit-zygote-cache': HEAP_DALVIK_OTHER_ZYGOTE_CODE_CACHE,

    r'^\[anon:dalvik-LinearAlloc': HEAP_DALVIK_OTHER_LINEARALLOC,
    r'^\[anon:dalvik-alloc space': HEAP_DALVIK_NORMAL,
    r'^\[anon:dalvik-main space': HEAP_DALVIK_NORMAL,
    r'^\[anon:dalvik-large object space': HEAP_DALVIK_LARGE,
    r'^\[anon:dalvik-free list large object space': HEAP_DALVIK_LARGE,
    r'^\[anon:dalvik-non moving space': HEAP_DALVIK_NON_MOVING,
    r'^\[anon:dalvik-zygote space': HEAP_DALVIK_ZYGOTE,
    r'^\[anon:dalvik-indirect ref': HEAP_DALVIK_OTHER_INDIRECT_REFERENCE_TABLE,
    r'^\[anon:dalvik-jit-code-cache': HEAP_DALVIK_OTHER_APP_CODE_CACHE,
    r'^\[anon:dalvik-data-code-cache': HEAP_DALVIK_OTHER_APP_CODE_CACHE,
    r'^\[anon:dalvik-CompilerMetadat': HEAP_DALVIK_OTHER_COMPILER_METADATA,
    r'^\[anon:dalvik-': HEAP_DALVIK_OTHER,
    r'^\[anon:': HEAP_UNKNOWN,
    r'^\s*$': HEAP_UNKNOWN,
    r'.+': HEAP_UNKNOWN_MAP
}


def totalDict(dicts, totalKeys):
    total = 0
    for totalKey in totalKeys:
        total += int(dicts[totalKey])
    return total


def createPie(datas, title) -> Pie:
    pie = Pie()
    pie.add("", datas)
    pie.set_global_opts(title_opts=opts.TitleOpts(title=title),
                        legend_opts=opts.LegendOpts(
                            pos_right="right",
                            orient="vertical",
                            is_show=False)
                        )
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}  {c} : ({d})%"))
    return pie


if __name__ == '__main__':
    # mydata = SysMaps(open("/home/ubuntu/sensors/F10smaps.txt"))
    mydata = SysMaps(os.popen("adb shell cat /proc/$(pidof com.android.settings)/smaps"))
    key = "Pss"
    mydata.sort(key=lambda vma: totalDict(vma, [sysmaps.VMA_ATTR_PSS]), reverse=True)
    mydata.getDataBase().query()

    # print(mydata[0].__dict__)
