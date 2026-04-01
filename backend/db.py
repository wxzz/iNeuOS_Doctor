"""
数据库连接和资源释放模块
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Optional

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'ai_doctor'
}

# 连接池（可选，用于生产环境）
_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def init_connection_pool(minconn=1, maxconn=10):
    """
    初始化数据库连接池
    
    Args:
        minconn: 最小连接数
        maxconn: 最大连接数
    """
    global _connection_pool
    try:
        _connection_pool = pool.ThreadedConnectionPool(
            minconn,
            maxconn,
            **DB_CONFIG
        )
        print("数据库连接池初始化成功")
    except Exception as e:
        print(f"数据库连接池初始化失败: {e}")
        raise


def get_connection():
    """
    获取数据库连接
    
    Returns:
        psycopg2.connection: 数据库连接对象
    """
    if _connection_pool:
        return _connection_pool.getconn()
    else:
        return psycopg2.connect(**DB_CONFIG)


def return_connection(conn):
    """
    归还连接到连接池
    
    Args:
        conn: 数据库连接对象
    """
    if _connection_pool:
        _connection_pool.putconn(conn)
    else:
        conn.close()


@contextmanager
def get_db_connection():
    """
    上下文管理器，自动管理数据库连接的获取和释放
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bas_user")
            result = cursor.fetchall()
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            return_connection(conn)


def close_connection_pool():
    """
    关闭所有数据库连接池
    """
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        print("数据库连接池已关闭")
