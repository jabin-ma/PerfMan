import sqlite3

if __name__ == '__main__':
    conn = sqlite3.connect(':memory:')
    print("数据库打开成功")
    c = conn.cursor()
    c.execute('''CREATE TABLE COMPANY
           (ID INT PRIMARY KEY     NOT NULL,
           NAME           TEXT    NOT NULL,
           AGE            INT     NOT NULL,
           ADDRESS        CHAR(50),
           SALARY         REAL);''')
    print("数据表创建成功")
    conn.commit()
    conn.close()
