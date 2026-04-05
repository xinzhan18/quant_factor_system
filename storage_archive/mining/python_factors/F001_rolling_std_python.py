"""Auto-generated Python factor: rolling_std_python"""
META = {'name': 'rolling_std_python', 'logic_id': 'logic_042', 'params': {'window': 20}, 'param_space': {'window': [5, 10, 20, 40]}, 'lineage': {'parent': 'std_returns_20', 'mutation': 'param_change'}}

def compute(df, params, ops):
    return df['close'].rolling(params['window']).std()
