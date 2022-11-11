# created by jabin ma
import collections
import re
import sqlite3
from sqlite3 import Cursor, Connection
from typing import Dict, List

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


def make_flags(flags_str: str):
    temp_flags = 0
    for flag_char in flags_str.upper():
        if flag_char in FLAGS_MMAP:
            temp_flags |= FLAGS_MMAP[flag_char]
    return temp_flags


def pop_hex(hex_str: list):
    return int(hex_str.pop(0), 16)


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
    result[VMA_ATTR_START], result[VMA_ATTR_END] = pop_hex(attrs), pop_hex(attrs)
    result[VMA_ATTR_FLAGS] = make_flags(attrs.pop(0))
    result[VMA_ATTR_NAME] = attrs.pop()
    result[VMA_ATTR_OFFSET], result[VMA_ATTR_MAJOR], result[VMA_ATTR_MINOR], result[VMA_ATTR_INODE] = list(
        map(lambda x: int(x, 16), attrs))


def match_vma_attrs(line):
    return re.match(r'(\w*)\s*:\s+([0-9]+)\skB', line)


def match_vma_vmFlags(line):
    return re.match(r'(\w*)\s*:\s+([0-9]+)\skB', line)


class SmapsDatabase:
    cursor: Cursor
    conn: Connection

    @staticmethod
    def dict_factory(cursor, row):
        # 将游标获取的数据处理成字典返回
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @staticmethod
    def sqType(typed):
        if type(typed) == int:
            return 'INT'
        elif type(typed) == str:
            return 'TEXT'

    def __init__(self, sample: dict, database_name):
        self.conn = sqlite3.connect(database_name)
        self.conn.row_factory = SmapsDatabase.dict_factory
        self.cursor = self.conn.cursor()
        layout = ""
        for sample_key, sample_value in sample.items():
            layout += '{} {} NOT NULL,'.format(sample_key, SmapsDatabase.sqType(sample_value))
        layout = layout[0:-1]
        sql_create_table = "CREATE TABLE smaps ({});".format(layout)
        self.cursor.execute(sql_create_table)
        self.conn.commit()

    #
    # def __init__(self, sample: str):
    #     self.conn = sqlite3.connect(':memory:')
    #     self.conn.row_factory = SmapsDatabase.dict_factory
    #     self.cursor = self.conn.cursor()
    #     layout = ""
    #     for sample_key, sample_value in sample.items():
    #         layout += '{} {} NOT NULL,'.format(sample_key, SmapsDatabase.sqType(sample_value))
    #     layout = layout[0:-1]
    #     sql_create_table = "CREATE TABLE smaps ({});".format(layout)
    #     self.cursor.execute(sql_create_table)
    #     self.conn.commit()

    def insert(self, dict_data):
        columns = ', '.join(dict_data.keys())
        placeholders = ':' + ', :'.join(dict_data.keys())
        query = 'INSERT INTO smaps (%s) VALUES (%s)' % (columns, placeholders)
        self.cursor.execute(query, dict_data)
        self.conn.commit()

    def execute(self, sql_command, commit=False):
        result = self.cursor.execute(sql_command)
        if commit:
            self.conn.commit()
        return result


class SysMaps(List[Dict]):
    db: SmapsDatabase = None
    label = None

    def __init__(self, contents: collections, label=':memory:'):
        super().__init__()
        self.label = label
        vma_parsing = None
        for content in contents:
            matched = match_vma(content)
            if matched:
                if vma_parsing:
                    self.append(vma_parsing)
                vma_parsing = {}
                parser_vma(vma_parsing, list(matched.groups()))
                continue

            matched = match_vma_attrs(content)
            if matched:
                attr_key = matched.group(1)
                attr_value = matched.group(2)
                vma_parsing[attr_key] = int(attr_value)

    def getDataBase(self):
        if self.db:
            return self.db
        else:
            self.db = SmapsDatabase(self[0], self.label)
            for i in self:
                self.db.insert(i)

        return self.db
