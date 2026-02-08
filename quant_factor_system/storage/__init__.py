"""
存储层模块
提供 SQLite 数据库、文件读写、缓存功能
"""

import sqlite3
import pandas as pd
import json
import pickle
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class FactorDatabase:
    """
    SQLite 数据库封装
    管理因子定义、评估结果、选股结果、回测记录
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库路径，默认 storage/database/factors.db
        """
        if db_path is None:
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "storage" / "database" / "factors.db"
        
        self.db_path = str(db_path)
        self._ensure_dir()
        self._init_db()
    
    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 因子定义表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                description TEXT,
                params TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 评估结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_id INTEGER NOT NULL,
                eval_date DATE NOT NULL,
                period_start DATE,
                period_end DATE,
                ic REAL,
                ic_ir REAL,
                ic_std REAL,
                win_rate REAL,
                long_short_return REAL,
                group_returns TEXT,
                num_groups INTEGER,
                num_samples INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (factor_id) REFERENCES factors(id),
                UNIQUE(factor_id, eval_date)
            )
        ''')
        
        # 选股结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_id INTEGER,
                factor_name TEXT NOT NULL,
                selection_date DATE NOT NULL,
                stock_code TEXT NOT NULL,
                factor_value REAL,
                rank INTEGER,
                weight REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 回测记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                config TEXT,
                start_date DATE,
                end_date DATE,
                total_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                results TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== 因子 CRUD ==========
    
    def add_factor(self, name: str, category: str = None, 
                   description: str = None, params: Dict = None) -> int:
        """
        添加因子
        
        Args:
            name: 因子名称
            category: 因子类别
            description: 描述
            params: 参数（字典）
            
        Returns:
            因子 ID
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        params_json = json.dumps(params) if params else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO factors (name, category, description, params)
            VALUES (?, ?, ?, ?)
        ''', (name, category, description, params_json))
        
        factor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return factor_id
    
    def get_factor(self, name: str) -> Optional[Dict]:
        """
        获取因子信息
        
        Args:
            name: 因子名称
            
        Returns:
            因子信息字典
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, category, description, params, created_at, updated_at
            FROM factors WHERE name = ?
        ''', (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'description': row[3],
                'params': json.loads(row[4]) if row[4] else None,
                'created_at': row[5],
                'updated_at': row[6]
            }
        return None
    
    def list_factors(self, category: str = None) -> pd.DataFrame:
        """
        获取因子列表
        
        Args:
            category: 筛选类别
            
        Returns:
            因子列表 DataFrame
        """
        conn = self._get_conn()
        
        if category:
            df = pd.read_sql_query('''
                SELECT * FROM factors WHERE category = ?
                ORDER BY created_at DESC
            ''', conn, params=(category,))
        else:
            df = pd.read_sql_query('''
                SELECT * FROM factors ORDER BY created_at DESC
            ''', conn)
        
        conn.close()
        return df
    
    def delete_factor(self, name: str) -> bool:
        """
        删除因子
        
        Args:
            name: 因子名称
            
        Returns:
            是否成功
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM factors WHERE name = ?', (name,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # ========== 评估结果 CRUD ==========
    
    def save_evaluation(self, factor_name: str, results: Dict) -> int:
        """
        保存评估结果
        
        Args:
            factor_name: 因子名称
            results: 评估结果字典
            
        Returns:
            评估记录 ID
        """
        # 获取 factor_id
        factor = self.get_factor(factor_name)
        if factor is None:
            self.add_factor(factor_name, category='custom')
            factor = self.get_factor(factor_name)
        
        factor_id = factor['id']
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 序列化 group_returns
        group_returns_json = json.dumps(results.get('group_returns', {}))
        
        cursor.execute('''
            INSERT OR REPLACE INTO evaluations (
                factor_id, eval_date, period_start, period_end,
                ic, ic_ir, ic_std, win_rate, long_short_return,
                group_returns, num_groups, num_samples
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            factor_id,
            results.get('eval_date', datetime.now().strftime('%Y-%m-%d')),
            results.get('period_start'),
            results.get('period_end'),
            results.get('ic'),
            results.get('ic_ir'),
            results.get('ic_std'),
            results.get('win_rate'),
            results.get('long_short_return'),
            group_returns_json,
            results.get('num_groups'),
            results.get('num_samples')
        ))
        
        eval_id = cursor.lastrowid
        
        # 更新 factor updated_at
        cursor.execute('''
            UPDATE factors SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (factor_id,))
        
        conn.commit()
        conn.close()
        
        return eval_id
    
    def get_evaluations(self, factor_name: str = None,
                        start_date: str = None,
                        end_date: str = None,
                        limit: int = 100) -> pd.DataFrame:
        """
        获取评估结果
        
        Args:
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            
        Returns:
            评估结果 DataFrame
        """
        conn = self._get_conn()
        
        if factor_name:
            query = '''
                SELECT e.*, f.name as factor_name, f.category
                FROM evaluations e
                JOIN factors f ON e.factor_id = f.id
                WHERE f.name = ?
            '''
            params = [factor_name]
            
            if start_date:
                query += ' AND e.eval_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND e.eval_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY e.eval_date DESC LIMIT ?'
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
        else:
            query = '''
                SELECT e.*, f.name as factor_name, f.category
                FROM evaluations e
                JOIN factors f ON e.factor_id = f.id
                ORDER BY e.eval_date DESC LIMIT ?
            '''
            df = pd.read_sql_query(query, conn, params=(limit,))
        
        conn.close()
        return df
    
    def get_latest_evaluations(self, limit: int = 20) -> pd.DataFrame:
        """
        获取最新评估结果（每个因子一条）
        
        Args:
            limit: 返回因子数量限制
            
        Returns:
            最新评估结果 DataFrame
        """
        conn = self._get_conn()
        
        query = '''
            SELECT e.*, f.name as factor_name, f.category
            FROM evaluations e
            JOIN factors f ON e.factor_id = f.id
            WHERE e.id IN (
                SELECT MAX(id) FROM evaluations GROUP BY factor_id
            )
            ORDER BY e.ic DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return df
    
    # ========== 选股结果 CRUD ==========
    
    def save_stock_selection(self, factor_name: str,
                             selection_date: str,
                             stocks: List[Dict]) -> int:
        """
        保存选股结果
        
        Args:
            factor_name: 因子名称
            selection_date: 选股日期
            stocks: 股票列表 [{'stock_code', 'factor_value', 'rank', 'weight'}, ...]
            
        Returns:
            保存的记录数
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 确保 factor 存在
        factor = self.get_factor(factor_name)
        if factor is None:
            self.add_factor(factor_name, category='custom')
            factor = self.get_factor(factor_name)
        
        factor_id = factor['id']
        
        # 清空旧数据
        cursor.execute('''
            DELETE FROM stock_selections 
            WHERE factor_name = ? AND selection_date = ?
        ''', (factor_name, selection_date))
        
        # 插入新数据
        for stock in stocks:
            cursor.execute('''
                INSERT INTO stock_selections (
                    factor_id, factor_name, selection_date,
                    stock_code, factor_value, rank, weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                factor_id, factor_name, selection_date,
                stock.get('stock_code'),
                stock.get('factor_value'),
                stock.get('rank'),
                stock.get('weight')
            ))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    def get_stock_selections(self, factor_name: str,
                             selection_date: str = None,
                             limit: int = 100) -> pd.DataFrame:
        """
        获取选股结果
        
        Args:
            factor_name: 因子名称
            selection_date: 选股日期
            limit: 返回数量限制
            
        Returns:
            选股结果 DataFrame
        """
        conn = self._get_conn()
        
        if selection_date:
            df = pd.read_sql_query('''
                SELECT * FROM stock_selections
                WHERE factor_name = ? AND selection_date = ?
                ORDER BY rank
                LIMIT ?
            ''', conn, params=(factor_name, selection_date, limit))
        else:
            df = pd.read_sql_query('''
                SELECT * FROM stock_selections
                WHERE factor_name = ?
                ORDER BY selection_date DESC, rank
                LIMIT ?
            ''', conn, params=(factor_name, limit))
        
        conn.close()
        return df
    
    # ========== 回测记录 CRUD ==========
    
    def save_backtest(self, name: str, config: Dict,
                      results: Dict) -> int:
        """
        保存回测记录
        
        Args:
            name: 回测名称
            config: 配置字典
            results: 结果字典
            
        Returns:
            回测记录 ID
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        config_json = json.dumps(config)
        results_json = json.dumps(results)
        
        cursor.execute('''
            INSERT INTO backtests (name, config, start_date, end_date,
                                  total_return, sharpe_ratio, max_drawdown, results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            config_json,
            results.get('start_date'),
            results.get('end_date'),
            results.get('total_return'),
            results.get('sharpe_ratio'),
            results.get('max_drawdown'),
            results_json
        ))
        
        backtest_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return backtest_id
    
    def get_backtests(self, limit: int = 20) -> pd.DataFrame:
        """
        获取回测记录列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            回测记录 DataFrame
        """
        conn = self._get_conn()
        
        df = pd.read_sql_query('''
            SELECT * FROM backtests
            ORDER BY created_at DESC
            LIMIT ?
        ''', conn, params=(limit,))
        
        conn.close()
        return df
    
    def get_backtest_detail(self, backtest_id: int) -> Optional[Dict]:
        """
        获取回测详情
        
        Args:
            backtest_id: 回测 ID
            
        Returns:
            回测详情字典
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM backtests WHERE id = ?
        ''', (backtest_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'config': json.loads(row[2]) if row[2] else None,
                'start_date': row[3],
                'end_date': row[4],
                'total_return': row[5],
                'sharpe_ratio': row[6],
                'max_drawdown': row[7],
                'results': json.loads(row[8]) if row[8] else None,
                'created_at': row[9]
            }
        return None
    
    # ========== 统计方法 ==========
    
    def get_factor_stats(self) -> Dict[str, Any]:
        """
        获取因子统计信息
        
        Returns:
            统计信息字典
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        stats = {}
        
        # 因子总数
        cursor.execute('SELECT COUNT(*) FROM factors')
        stats['total_factors'] = cursor.fetchone()[0]
        
        # 最新评估数量
        cursor.execute('SELECT COUNT(DISTINCT factor_id) FROM evaluations')
        stats['evaluated_factors'] = cursor.fetchone()[0]
        
        # 评估记录总数
        cursor.execute('SELECT COUNT(*) FROM evaluations')
        stats['total_evaluations'] = cursor.fetchone()[0]
        
        # 选股记录总数
        cursor.execute('SELECT COUNT(*) FROM stock_selections')
        stats['total_selections'] = cursor.fetchone()[0]
        
        # 回测记录总数
        cursor.execute('SELECT COUNT(*) FROM backtests')
        stats['total_backtests'] = cursor.fetchone()[0]
        
        # 最佳因子（按平均 IC）
        cursor.execute('''
            SELECT f.name, AVG(e.ic) as avg_ic
            FROM evaluations e
            JOIN factors f ON e.factor_id = f.id
            GROUP BY f.id
            ORDER BY avg_ic DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        stats['best_factor'] = row[0] if row else None
        stats['best_ic'] = row[1] if row else None
        
        conn.close()
        
        return stats
    
    def clear_all(self):
        """清空所有数据（谨慎使用）"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM stock_selections')
        cursor.execute('DELETE FROM evaluations')
        cursor.execute('DELETE FROM backtests')
        cursor.execute('DELETE FROM factors')
        
        conn.commit()
        conn.close()


class CSVStorage:
    """
    CSV 文件存储
    用于存储因子原始数据、回测历史
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化
        
        Args:
            base_dir: 基础目录，默认 storage/data
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "storage" / "data"
        
        self.base_dir = Path(base_dir)
        self._ensure_dir()
    
    def _ensure_dir(self):
        """确保目录存在"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, subdir: str, filename: str) -> Path:
        """获取文件路径"""
        dir_path = self.base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path / filename
    
    # ========== 因子数据 ==========
    
    def save_factor_data(self, factor_name: str, data: pd.DataFrame,
                        subdir: str = 'factors'):
        """
        保存因子数据
        
        Args:
            factor_name: 因子名称
            data: 数据
            subdir: 子目录
        """
        filepath = self._get_path(subdir, f"{factor_name}.csv")
        data.to_csv(filepath)
        return str(filepath)
    
    def load_factor_data(self, factor_name: str,
                        subdir: str = 'factors') -> Optional[pd.DataFrame]:
        """
        加载因子数据
        
        Args:
            factor_name: 因子名称
            subdir: 子目录
            
        Returns:
            数据 DataFrame
        """
        filepath = self._get_path(subdir, f"{factor_name}.csv")
        
        if filepath.exists():
            return pd.read_csv(filepath, index_col=0)
        return None
    
    def list_factor_files(self, subdir: str = 'factors') -> List[str]:
        """
        列出因子文件
        
        Args:
            subdir: 子目录
            
        Returns:
            文件名列表
        """
        dir_path = self.base_dir / subdir
        if dir_path.exists():
            return [f.stem for f in dir_path.glob("*.csv")]
        return []
    
    # ========== 回测历史 ==========
    
    def save_backtest_result(self, name: str, data: pd.DataFrame):
        """
        保存回测结果
        
        Args:
            name: 回测名称
            data: 结果数据
        """
        filepath = self._get_path('backtests', f"{name}.csv")
        data.to_csv(filepath)
        return str(filepath)
    
    def load_backtest_result(self, name: str) -> Optional[pd.DataFrame]:
        """
        加载回测结果
        
        Args:
            name: 回测名称
            
        Returns:
            结果 DataFrame
        """
        filepath = self._get_path('backtests', f"{name}.csv")
        
        if filepath.exists():
            return pd.read_csv(filepath, index_col=0)
        return None
    
    # ========== 市场数据 ==========
    
    def save_market_data(self, data: pd.DataFrame, filename: str = 'market.csv'):
        """
        保存市场数据
        
        Args:
            data: 数据
            filename: 文件名
        """
        filepath = self._get_path('market', filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(filepath)
    
    def load_market_data(self, filename: str = 'market.csv') -> Optional[pd.DataFrame]:
        """
        加载市场数据
        
        Args:
            filename: 文件名
            
        Returns:
            数据 DataFrame
        """
        filepath = self._get_path('market', filename)
        
        if filepath.exists():
            return pd.read_csv(filepath, index_col=0)
        return None


class Cache:
    """
    缓存层
    使用 Pickle 存储内存数据
    """
    
    def __init__(self, cache_path: str = None):
        """
        初始化
        
        Args:
            cache_path: 缓存文件路径
        """
        if cache_path is None:
            base_dir = Path(__file__).parent.parent
            cache_path = base_dir / "storage" / "cache" / "cache.pkl"
        
        self.cache_path = str(cache_path)
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        self._data = {}
        self._load()
    
    def _load(self):
        """加载缓存"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'rb') as f:
                    self._data = pickle.load(f)
            except:
                self._data = {}
    
    def _save(self):
        """保存缓存"""
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self._data, f)
    
    def get(self, key: str) -> Any:
        """获取缓存"""
        return self._data.get(key)
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        self._data[key] = value
        self._save()
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._data:
            del self._data[key]
            self._save()
    
    def clear(self):
        """清空缓存"""
        self._data = {}
        self._save()
    
    def keys(self) -> List[str]:
        """列出所有键"""
        return list(self._data.keys())


# ========== 便捷函数 ==========

def get_database() -> FactorDatabase:
    """获取数据库实例"""
    return FactorDatabase()


def get_csv_storage() -> CSVStorage:
    """获取 CSV 存储实例"""
    return CSVStorage()


def get_cache() -> Cache:
    """获取缓存实例"""
    return Cache()


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("测试存储层")
    print("=" * 60)
    
    # 获取实例
    db = get_database()
    csv = get_csv_storage()
    cache = get_cache()
    
    print("\n1. 数据库统计:")
    print(db.get_factor_stats())
    
    print("\n2. 添加测试因子:")
    db.add_factor('Momentum', category='basic', 
                  description='动量因子', params={'period': 20})
    db.add_factor('Value', category='basic',
                  description='价值因子', params={'metric': 'pe'})
    
    print("\n3. 因子列表:")
    print(db.list_factors())
    
    print("\n4. 保存评估结果:")
    db.save_evaluation('Momentum', {
        'eval_date': '2024-01-15',
        'ic': 0.05,
        'ic_ir': 0.8,
        'win_rate': 0.55,
        'long_short_return': 0.02,
        'num_samples': 1000
    })
    
    print("\n5. 最新评估:")
    print(db.get_latest_evaluations())
    
    print("\n✅ 测试完成!")
