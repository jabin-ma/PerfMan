# created by jabin ma
import collections
import re
import sqlite3
from sqlite3 import Cursor, Connection

import Utils
from memtype import MEM_TYPE

_FLAG_READ = 1
_FLAG_WRITE = 1 << 1
_FLAG_EXEC = 1 << 2
_FLAG_SHARED = 1 << 3
FLAGS_MMAP = {
    'R': _FLAG_READ,
    'W': _FLAG_WRITE,
    'X': _FLAG_EXEC,
    'S': _FLAG_SHARED
}

VMA_ATTR_START = 'start_addr'
VMA_ATTR_END = 'end_addr'
VMA_ATTR_FLAGS = 'flags'
VMA_ATTR_NAME = 'name'
VMA_ATTR_OFFSET = 'offset'
VMA_ATTR_MAJOR = 'major'
VMA_ATTR_MINOR = 'minor'
VMA_ATTR_INODE = 'inode'

VMA_ATTR_SIZE = 'Size'
VMA_ATTR_KERNEL_PAGE_SIZE = 'KernelPageSize'
VMA_ATTR_MMU_PAGE_SIZE = 'MMUPageSize'
VMA_ATTR_RSS = 'Rss'
VMA_ATTR_PSS = 'Pss'
VMA_ATTR_SHARED_CLEAN = 'Shared_Clean'
VMA_ATTR_SHARED_DIRTY = 'Shared_Dirty'
VMA_ATTR_PRIVATE_CLEAN = 'Private_Clean'
VMA_ATTR_PRIVATE_DIRTY = 'Private_Dirty'
VMA_ATTR_REFERENCED = 'Referenced'
VMA_ATTR_ANONYMOUS = 'Anonymous'
VMA_ATTR_ANON_HUGE_PAGES = 'AnonHugePages'
VMA_ATTR_SHARED_HUGE_TLB = 'Shared_Hugetlb'
VMA_ATTR_PRIVATE_HUGE_TLB = 'Private_Hugetlb'
VMA_ATTR_SWAP = 'Swap'
VMA_ATTR_SWAP_PSS = 'SwapPss'
VMA_ATTR_LOCKED = 'Locked'

TABLE_NAME_RAW = "raw"
TABLE_NAME_SMAPS = "smaps"

TABLE_NAME_SMAPS_SQL = '''CREATE VIEW IF NOT EXISTS {} as 
SELECT name,tag, 
(
 SELECT type FROM memory_type WHERE REGEXP(memory_type.regex,raw.name)
) as type,
(
 SELECT subtype FROM memory_type WHERE REGEXP(memory_type.regex,raw.name)
) as subtype,
size as Vss,
COUNT(name) as times,
TOTAL(Pss + SwapPss) as TotalPss,
TOTAL(Pss) as Pss,
TOTAL(SwapPss) as SwapPss,
TOTAL(Shared_Clean + Shared_Dirty) as Shared,
TOTAL(Shared_clean) as Shared_Clean,
TOTAL(Shared_Dirty) as Shared_Dirty,
TOTAL(Private_Clean + Private_Dirty) as Uss,
TOTAL(Private_Clean) as Private_Clean,
TOTAL(Private_Dirty) as Private_Dirty,
TOTAL(Locked) as Locked
FROM raw 
GROUP BY name,tag'''.format(TABLE_NAME_SMAPS)

TABLE_MEMTYPE_SQL = '''CREATE TABLE IF NOT EXISTS memory_type (
regex TEXT NOT NULL,
type TEXT NOT NULL,
subtype TEXT 
)'''


def make_flags(flags_str: str):
    temp_flags = 0
    for flag_char in flags_str.upper():
        if flag_char in FLAGS_MMAP:
            temp_flags |= FLAGS_MMAP[flag_char]
    return temp_flags


def match_vma(line):
    return re.match(r'^([0-9a-fA-F]+)-'
                    r'([0-9a-fA-F]+)\s'
                    r'([rw\-xsp]+)\s'
                    r'([0-9a-fA-F]+)\s'
                    r'([0-9a-fA-F]+):'
                    r'([0-9a-fA-F]+)\s'
                    r'([0-9a-fA-F]+)\s*'
                    r'(.+)$', line, re.I)


def parser_vma(result: dict, attrs: list):
    result[VMA_ATTR_START], result[VMA_ATTR_END] = Utils.pop_hex(attrs), Utils.pop_hex(attrs)
    result[VMA_ATTR_FLAGS] = make_flags(attrs.pop(0))
    result[VMA_ATTR_NAME] = attrs.pop()
    result[VMA_ATTR_OFFSET], result[VMA_ATTR_MAJOR], result[VMA_ATTR_MINOR], result[VMA_ATTR_INODE] = list(
        map(lambda x: int(x, 16), attrs))


def match_vma_attrs(line):
    return re.match(r'(\w*)\s*:\s+([0-9]+)\skB', line)


def match_vma_vmFlags(line):
    return re.match(r'(\w*)\s*:\s+([0-9]+)\skB', line)


def parseVma(contents):
    vma_list = []
    vma_parsing = None
    for content in contents:
        matched = match_vma(content)
        if matched:
            if vma_parsing:
                vma_list.append(vma_parsing)
            vma_parsing = {}
            parser_vma(vma_parsing, list(matched.groups()))
            continue

        matched = match_vma_attrs(content)
        if matched:
            attr_key = matched.group(1)
            attr_value = matched.group(2)
            vma_parsing[attr_key] = int(attr_value)
    return vma_list


class SmapsDatabase:
    __cursor: Cursor
    __conn: Connection

    def __init__(self, database_name=':memory:'):
        self.__conn = sqlite3.connect(database_name)
        self.__conn.row_factory = Utils.sql_dict_factory
        self.__conn.create_function("REGEXP", 2, Utils.sql_regexp)
        self.__cursor = self.__conn.cursor()
        self.__cursor.execute(TABLE_MEMTYPE_SQL)
        for it in MEM_TYPE:
            if 'subtype' not in it:
                it['subtype'] = None
        self.insertMany(MEM_TYPE, 'memory_type')

    def padding(self, tag: str, contents: collections):
        vma_list = parseVma(contents)
        # append tag
        for tag_temp in vma_list:
            tag_temp['tag'] = tag
        vma_sample = vma_list[0]
        layout = []
        for sample_key, sample_value in vma_sample.items():
            layout.append('{} {} NOT NULL'.format(sample_key, Utils.sql_Type(sample_value)))
        sql_create_table = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(TABLE_NAME_RAW, ','.join(layout))

        # create tables
        self.__cursor.execute(sql_create_table)
        self.__cursor.execute(TABLE_NAME_SMAPS_SQL)

        # insert data
        self.insertMany(vma_list, TABLE_NAME_RAW)
        self.__conn.commit()

    def popColumn(self, tag, column, order=False, limit=0):
        sql_sub = ''
        if order:
            sql_sub += ' ORDER BY {0} DESC'.format(tag)
        if limit > 0:
            sql_sub += ' LIMIT {}'.format(limit)
        self.__cursor.execute(
            'SELECT name,{1} FROM {0} WHERE tag = ? {2}'.format(TABLE_NAME_SMAPS, column, sql_sub), [tag])
        return self.__cursor.fetchall()

    def insertMany(self, dict_list: list[dict], table_name, commit=False):
        sql_temp = Utils.sql_make_from_dict(dict_list[0], table_name)
        self.__cursor.executemany(sql_temp, dict_list)
        del sql_temp
