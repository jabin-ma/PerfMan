import re


def sql_regexp(expr, item):
    print("{},{}".format(expr, item))
    reg = re.compile(expr)
    return reg.search(item) is not None


def sql_Type(typed):
    if type(typed) == int:
        return 'INT'
    elif type(typed) == str:
        return 'TEXT'


def sql_dict_factory(cursor, row):
    # 将游标获取的数据处理成字典返回
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def sql_make_from_dict(dict_sample, table_name):
    columns = ', '.join(dict_sample.keys())
    placeholders = ':' + ', :'.join(dict_sample.keys())
    return 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, columns, placeholders)


def pop_hex(hex_str: list):
    return int(hex_str.pop(0), 16)