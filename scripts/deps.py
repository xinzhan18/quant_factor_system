"""
依赖管理
Dependency Management

功能:
- 依赖检查
- 版本管理
- 安装验证
- 环境检测
"""

import sys
import subprocess
from typing import Dict, List, Optional, Tuple


# ==================== 依赖定义 ====================

REQUIRED_PACKAGES = {
    # 核心依赖
    'sqlalchemy': {
        'min_version': '1.4.0',
        'recommended': '2.0.0',
        'purpose': '数据库ORM',
        'required': True,
    },
    'psycopg2-binary': {
        'min_version': '2.9.0',
        'recommended': '2.9.9',
        'purpose': 'PostgreSQL驱动',
        'required': True,
    },
    'pandas': {
        'min_version': '1.3.0',
        'recommended': '2.0.0',
        'purpose': '数据处理',
        'required': True,
    },
    'numpy': {
        'min_version': '1.20.0',
        'recommended': '1.24.0',
        'purpose': '数值计算',
        'required': True,
    },
    # 可选依赖
    'plotly': {
        'min_version': '5.0.0',
        'recommended': '5.15.0',
        'purpose': '可视化',
        'required': False,
    },
    'streamlit': {
        'min_version': '1.0.0',
        'recommended': '1.27.0',
        'purpose': 'Dashboard',
        'required': False,
    },
    'jupyter': {
        'min_version': '1.0.0',
        'recommended': '1.0.0',
        'purpose': '笔记本环境',
        'required': False,
    },
}

PYTHON_REQUIREMENT = {
    'min_version': '3.8',
    'recommended': '3.10',
}


def get_python_version() -> Tuple[int, int, int]:
    """获取Python版本"""
    version = sys.version_info
    return (version.major, version.minor, version.micro)


def check_python_version() -> Dict:
    """检查Python版本"""
    current = get_python_version()
    min_req = tuple(map(int, PYTHON_REQUIREMENT['min_version'].split('.')))
    
    result = {
        'current': f"{current[0]}.{current[1]}.{current[2]}",
        'min_required': PYTHON_REQUIREMENT['min_version'],
        'recommended': PYTHON_REQUIREMENT['recommended'],
        'passed': current >= min_req,
    }
    
    return result


def get_package_version(package: str) -> Optional[str]:
    """获取包版本"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    
    return None


def check_package(name: str) -> Dict:
    """检查单个包"""
    info = REQUIRED_PACKAGES.get(name, {})
    
    installed_version = get_package_version(name)
    
    result = {
        'name': name,
        'installed': installed_version is not None,
        'installed_version': installed_version,
        'min_required': info.get('min_version'),
        'recommended': info.get('recommended'),
        'purpose': info.get('purpose'),
        'required': info.get('required', False),
        'status': 'unknown',
    }
    
    if installed_version:
        from packaging import version as pkg_version
        
        min_ver = info.get('min_version', '0.0.0')
        
        if pkg_version.parse(installed_version) >= pkg_version.parse(min_ver):
            result['status'] = 'ok'
        else:
            result['status'] = 'outdated'
    else:
        if info.get('required', False):
            result['status'] = 'missing_required'
        else:
            result['status'] = 'missing_optional'
    
    return result


def check_all_packages() -> Dict:
    """检查所有包"""
    results = {
        'python': check_python_version(),
        'packages': {},
        'summary': {
            'total': len(REQUIRED_PACKAGES),
            'ok': 0,
            'outdated': 0,
            'missing_required': 0,
            'missing_optional': 0,
        }
    }
    
    for name in REQUIRED_PACKAGES:
        check_result = check_package(name)
        results['packages'][name] = check_result
        
        status = check_result['status']
        if status == 'ok':
            results['summary']['ok'] += 1
        elif status == 'outdated':
            results['summary']['outdated'] += 1
        elif status == 'missing_required':
            results['summary']['missing_required'] += 1
        elif status == 'missing_optional':
            results['summary']['missing_optional'] += 1
    
    return results


def print_check_results(results: Dict):
    """打印检查结果"""
    print("=" * 70)
    print("🔍 依赖检查结果")
    print("=" * 70)
    
    # Python版本
    py = results['python']
    status = "✅" if py['passed'] else "❌"
    print(f"\nPython: {status}")
    print(f"  当前: {py['current']}")
    print(f"  最低要求: {py['min_required']}")
    print(f"  推荐: {py['recommended']}")
    
    # 包
    print("\n" + "-" * 70)
    print("包依赖:")
    print("-" * 70)
    
    summary = results['summary']
    
    for name, info in results['packages'].items():
        # 状态图标
        if info['status'] == 'ok':
            icon = "✅"
        elif info['status'] == 'outdated':
            icon = "⚠️"
        elif info['status'] == 'missing_required':
            icon = "❌"
        else:
            icon = "🤔"
        
        required_tag = "[必装]" if info['required'] else "[可选]"
        
        print(f"\n{icon} {name} {required_tag}")
        print(f"   用途: {info['purpose']}")
        
        if info['installed']:
            print(f"   已安装: {info['installed_version']}")
            if info['status'] == 'outdated':
                print(f"   推荐更新: >= {info['recommended']}")
        else:
            print(f"   状态: 未安装")
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 总结")
    print("=" * 70)
    print(f"总计: {summary['total']} 个依赖")
    print(f"正常: {summary['ok']} 个")
    print(f"可更新: {summary['outdated']} 个")
    print(f"缺失(必装): {summary['missing_required']} 个")
    print(f"缺失(可选): {summary['missing_optional']} 个")
    
    # 建议
    if summary['missing_required'] > 0:
        print(f"\n💡 建议: 安装必装依赖")
        print(f"   pip install -r requirements.txt")


def generate_requirements() -> str:
    """生成requirements.txt"""
    lines = [
        "# QuantFactorSystem 依赖",
        f"# 生成时间: 2026-02-09",
        "",
        "# 核心依赖 (必装)",
        "",
    ]
    
    for name, info in REQUIRED_PACKAGES.items():
        if info['required']:
            min_ver = info.get('min_version', '')
            info.get('recommended', '')
            lines.append(f"{name}>={min_ver}")
    
    lines.extend([
        "",
        "# 可选依赖",
        "",
    ])
    
    for name, info in REQUIRED_PACKAGES.items():
        if not info['required']:
            min_ver = info.get('min_version', '')
            lines.append(f"# {name}>={min_ver}  # 可选: {info['purpose']}")
    
    return '\n'.join(lines)


def install_packages(packages: List[str], upgrade: bool = False):
    """安装包"""
    cmd = [sys.executable, '-m', 'pip', 'install']
    
    if upgrade:
        cmd.append('--upgrade')
    
    cmd.extend(packages)
    
    print(f"安装: {' '.join(packages)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 安装成功")
    else:
        print("❌ 安装失败")
        print(result.stderr)


def check_environment() -> bool:
    """完整环境检查"""
    print("=" * 70)
    print("🚀 QuantFactorSystem 环境检查")
    print("=" * 70)
    
    # 1. Python版本
    py = check_python_version()
    print(f"\nPython: {py['current']}")
    
    if not py['passed']:
        print(f"❌ Python版本过低, 需要 >= {py['min_required']}")
        return False
    
    # 2. 包依赖
    results = check_all_packages()
    print_check_results(results)
    
    # 3. 返回是否通过
    passed = (
        py['passed'] and 
        results['summary']['missing_required'] == 0
    )
    
    if passed:
        print("\n✅ 环境检查通过!")
    else:
        print("\n❌ 环境检查未通过, 请安装缺失依赖")
    
    return passed


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='依赖管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deps.py check       # 检查环境
  python deps.py install    # 安装依赖
  python deps.py generate   # 生成requirements.txt
        """
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # check
    parser_check = subparsers.add_parser('check', help='检查环境')
    parser_check.set_defaults(func=check_environment)
    
    # install
    parser_install = subparsers.add_parser('install', help='安装依赖')
    parser_install.add_argument('packages', nargs='+', help='包名')
    parser_install.add_argument('--upgrade', '-u', action='store_true', help='升级')
    parser_install.set_defaults(
        func=lambda args: install_packages(args.packages, args.upgrade)
    )
    
    # generate
    parser_generate = subparsers.add_parser('generate', help='生成requirements.txt')
    parser_generate.set_defaults(
        func=lambda args: print(generate_requirements())
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        check_environment()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
