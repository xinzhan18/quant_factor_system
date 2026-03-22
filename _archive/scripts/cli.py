"""
命令行工具
Command Line Interface

功能:
- 系统信息
- 数据库管理
- 数据导入导出
- Pipeline运行
- 测试和基准
"""

import sys
import argparse


def cmd_info(args):
    """系统信息"""
    from quant_factor_system import info
    info()


def cmd_version(args):
    """版本信息"""
    from quant_factor_system import version
    version()


def cmd_init(args):
    """初始化数据库"""
    from quant_factor_system import get_db
    
    print("=" * 60)
    print("🚀 初始化数据库")
    print("=" * 60)
    
    db = get_db()
    status = db.check()
    
    print(f"连接: {status['connected']}")
    print(f"TimescaleDB: {'✅' if status.get('timescaledb') else '❌'}")
    
    if status.get('timescaledb'):
        print("\n初始化...")
        db.init()
        print("✅ 完成")
    else:
        # 即使没有 TimescaleDB，也可以初始化普通表
        print("\n⚠️  TimescaleDB 未安装，使用普通 PostgreSQL")
        print("尝试创建基础表...")
        try:
            db.init()
            print("✅ 基础表创建完成")
        except Exception as e:
            print(f"❌ 表创建失败: {e}")
            print("将使用模拟数据")
    
    db.close()


def cmd_status(args):
    """系统状态"""
    from quant_factor_system import get_config, get_logger
    
    config = get_config()
    logger = get_logger()
    
    print("=" * 60)
    print("📊 系统状态")
    print("=" * 60)
    
    print(f"名称: {config.name}")
    print(f"版本: {config.version}")
    print(f"日志级别: {logger.logger.level}")
    print(f"数据库: {config.database.host}:{config.database.port}")
    
    print("\n配置:")
    print(f"  缓存: {config.cache.enabled}")
    print(f"  Pipeline默认窗口: {config.pipeline.default_window}")


def cmd_data(args):
    """数据管理"""
    from quant_factor_system import create_data_manager
    
    print("=" * 60)
    print("📦 数据管理")
    print("=" * 60)
    
    dm = create_data_manager(use_db=False)
    
    # 生成测试数据
    print("\n生成测试数据...")
    data = dm.get_price_data(
        symbols=['TEST_001', 'TEST_002'],
        frequency=args.frequency or 'daily',
        n_periods=args.count or 100
    )
    
    print(f"✅ 生成 {len(data)} 行数据")
    print(f"频率: {args.frequency or 'daily'}")
    print(f"列: {list(data.columns)}")
    print(data.head())
    
    dm.close()


def cmd_pipeline(args):
    """运行Pipeline"""
    from quant_factor_system import create_data_manager, create_pipeline
    from quant_factor_system.factors.core.pipeline import BuiltInFactors
    
    print("=" * 60)
    print("🔧 运行Pipeline")
    print("=" * 60)
    
    dm = create_data_manager(use_db=False)
    
    # 获取数据
    print("\n获取数据...")
    data = dm.get_price_data(
        symbols=['TEST_001'],
        frequency=args.frequency or 'daily',
        n_periods=100
    )
    
    # 创建Pipeline
    print("创建Pipeline...")
    pipe = create_pipeline(args.name or 'CLI_Pipeline')
    
    factors = args.factors or ['momentum']
    
    for factor in factors:
        if factor == 'momentum':
            pipe.add_factor('momentum', BuiltInFactors.momentum(20))
        elif factor == 'volatility':
            pipe.add_factor('volatility', BuiltInFactors.volatility(20))
    
    print(f"因子: {list(pipe.factors.keys())}")
    
    # 运行
    print("\n运行Pipeline...")
    result = pipe.run(data, frequency=args.frequency or 'daily')
    
    print(f"\n✅ 完成! 计算 {len(result.data)} 行数据")
    print(result.data.head())
    
    dm.close()


def cmd_test(args):
    """运行测试"""
    import subprocess
    import os
    
    os.chdir('/Users/xinzhan/.openclaw/workspace/quant_factor_system')
    
    print("=" * 60)
    print("🧪 运行测试")
    print("=" * 60)
    
    test_files = [
        'test_refactor.py',
        'test_engineering.py',
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n运行 {test_file}...")
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} 通过")
            else:
                print(f"❌ {test_file} 失败")
                print(result.stdout)
                print(result.stderr)


def cmd_benchmark(args):
    """基准测试"""
    import time
    
    from quant_factor_system import create_data_manager, create_pipeline
    from quant_factor_system.factors.core.pipeline import BuiltInFactors
    
    print("=" * 60)
    print("⏱️ 基准测试")
    print("=" * 60)
    
    results = {}
    
    # 1. 数据生成测试
    print("\n1. 数据生成...")
    dm = create_data_manager(use_db=False)
    
    start = time.time()
    data = dm.get_price_data(
        symbols=[f'STOCK_{i:03d}' for i in range(100)],
        frequency='daily',
        n_periods=250
    )
    elapsed = time.time() - start
    results['data_generation'] = elapsed
    
    print(f"   {len(data)} 行: {elapsed:.3f}s")
    
    # 2. Pipeline测试
    print("\n2. Pipeline计算...")
    
    pipe = create_pipeline('Benchmark')
    pipe.add_factor('momentum', BuiltInFactors.momentum(20))
    pipe.add_factor('volatility', BuiltInFactors.volatility(20))
    
    start = time.time()
    result = pipe.run(data, frequency='daily')
    elapsed = time.time() - start
    results['pipeline'] = elapsed
    
    print(f"   4个因子: {elapsed:.3f}s")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 基准测试结果")
    print("=" * 60)
    
    for test, elapsed in results.items():
        print(f"{test}: {elapsed:.3f}s")
    
    total = sum(results.values())
    print(f"\n总计: {total:.3f}s")
    
    dm.close()


def cmd_clean(args):
    """清理"""
    import os
    import shutil
    
    print("=" * 60)
    print("🧹 清理")
    print("=" * 60)
    
    paths_to_clean = [
        './__pycache__',
        './**/__pycache__',
        './logs',
        './cache',
    ]
    
    cleaned = []
    
    for path in paths_to_clean:
        if os.path.exists(path.replace('**', '')):
            try:
                if os.path.isdir(path.replace('**', '')):
                    shutil.rmtree(path.replace('**', ''))
                    cleaned.append(path)
            except Exception as e:
                print(f"⚠️ 清理失败 {path}: {e}")
    
    print(f"清理: {len(clean)} 项")
    print("✅ 完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='量化因子系统 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py info         # 系统信息
  python cli.py init         # 初始化数据库
  python cli.py status       # 系统状态
  python cli.py data         # 数据管理
  python cli.py pipeline     # 运行Pipeline
  python cli.py test         # 运行测试
  python cli.py benchmark    # 基准测试
  python cli.py clean       # 清理
        """
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # info
    parser_info = subparsers.add_parser('info', help='系统信息')
    parser_info.set_defaults(func=cmd_info)
    
    # version
    parser_version = subparsers.add_parser('version', help='版本信息')
    parser_version.set_defaults(func=cmd_version)
    
    # init
    parser_init = subparsers.add_parser('init', help='初始化数据库')
    parser_init.set_defaults(func=cmd_init)
    
    # status
    parser_status = subparsers.add_parser('status', help='系统状态')
    parser_status.set_defaults(func=cmd_status)
    
    # data
    parser_data = subparsers.add_parser('data', help='数据管理')
    parser_data.add_argument('--frequency', '-f', default='daily', help='频率')
    parser_data.add_argument('--count', '-c', default=100, type=int, help='数据量')
    parser_data.set_defaults(func=cmd_data)
    
    # pipeline
    parser_pipeline = subparsers.add_parser('pipeline', help='运行Pipeline')
    parser_pipeline.add_argument('--name', '-n', default='CLI_Pipeline', help='名称')
    parser_pipeline.add_argument('--factors', '-f', 
                                 default=['momentum', 'ma'],
                                 nargs='+',
                                 choices=['momentum', 'ma', 'rsi', 'volatility'],
                                 help='因子列表')
    parser_pipeline.add_argument('--frequency', '-F', default='daily', help='频率')
    parser_pipeline.set_defaults(func=cmd_pipeline)
    
    # test
    parser_test = subparsers.add_parser('test', help='运行测试')
    parser_test.set_defaults(func=cmd_test)
    
    # benchmark
    parser_benchmark = subparsers.add_parser('benchmark', help='基准测试')
    parser_benchmark.set_defaults(func=cmd_benchmark)
    
    # clean
    parser_clean = subparsers.add_parser('clean', help='清理')
    parser_clean.set_defaults(func=cmd_clean)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
