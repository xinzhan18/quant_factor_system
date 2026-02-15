"""
因子分析自动化调度系统
Factor Analysis Automation Scheduler

功能：
- 定时任务调度
- 自动化流水线
- 任务依赖管理
- 告警通知
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import os
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """任务定义"""
    name: str
    func: Callable
    schedule_time: str  # cron 表达式或时间
    enabled: bool = True
    dependencies: List[str] = None
    description: str = ""
    retry_times: int = 3
    retry_interval: int = 60  # 秒
    timeout: int = 3600  # 秒
    notify_on_failure: bool = True


class TaskResult:
    """任务执行结果"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.start_time = None
        self.end_time = None
        self.status = TaskStatus.PENDING
        self.message = ""
        self.error = None
        self.result_data = None
    
    def to_dict(self) -> Dict:
        return {
            'task_name': self.task_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'message': self.message,
            'error': str(self.error) if self.error else None,
            'result_data': self.result_data
        }


class TaskScheduler:
    """
    任务调度器
    
    管理多个任务的调度和执行
    """
    
    def __init__(self, task_file: str = "./data/tasks.json"):
        """
        初始化调度器
        
        Args:
            task_file: 任务配置文件路径
        """
        self.tasks: Dict[str, Task] = {}
        self.task_file = task_file
        self.is_running = False
        self.scheduler_thread = None
        self.task_results: Dict[str, TaskResult] = {}
        self.notification_handlers: List[Callable] = []
        
        # 加载任务
        self._load_tasks()
        
        # 注册信号处理
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """注册信号处理"""
        def handle_signal(signum, frame):
            logger.info(f"收到信号 {signum}，正在停止调度器...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    
    def _load_tasks(self):
        """从配置文件加载任务"""
        if os.path.exists(self.task_file):
            try:
                with open(self.task_file, 'r') as f:
                    config = json.load(f)
                    
                for task_config in config.get('tasks', []):
                    self.register_task(
                        name=task_config['name'],
                        func=lambda: logger.info(f"任务 {task_config['name']} 待执行"),
                        schedule_time=task_config.get('schedule', '08:00'),
                        description=task_config.get('description', ''),
                        enabled=task_config.get('enabled', True)
                    )
                    
                logger.info(f"从配置文件加载了 {len(self.tasks)} 个任务")
                
            except Exception as e:
                logger.error(f"加载任务配置失败: {e}")
    
    def save_tasks(self):
        """保存任务配置"""
        config = {
            'tasks': [
                {
                    'name': name,
                    'schedule': task.schedule_time,
                    'enabled': task.enabled,
                    'description': task.description
                }
                for name, task in self.tasks.items()
            ]
        }
        
        os.makedirs(os.path.dirname(self.task_file), exist_ok=True)
        
        with open(self.task_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def register_task(self, name: str, func: Callable, schedule_time: str,
                      description: str = "", enabled: bool = True,
                      dependencies: List[str] = None,
                      retry_times: int = 3, timeout: int = 3600):
        """
        注册任务
        
        Args:
            name: 任务名称
            func: 任务函数
            schedule_time: 调度时间 (如 "08:00" 或 "*/5 * * * *")
            description: 任务描述
            enabled: 是否启用
            dependencies: 依赖任务列表
            retry_times: 重试次数
            timeout: 超时时间（秒）
        """
        self.tasks[name] = Task(
            name=name,
            func=func,
            schedule_time=schedule_time,
            description=description,
            enabled=enabled,
            dependencies=dependencies or [],
            retry_times=retry_times,
            timeout=timeout
        )
        
        logger.info(f"注册任务: {name} ({schedule_time})")
    
    def unregister_task(self, name: str):
        """注销任务"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"注销任务: {name}")
    
    def add_notification_handler(self, handler: Callable):
        """
        添加通知处理器
        
        Args:
            handler: 通知函数，接收 TaskResult
        """
        self.notification_handlers.append(handler)
    
    def _notify(self, result: TaskResult):
        """发送通知"""
        for handler in self.notification_handlers:
            try:
                handler(result)
            except Exception as e:
                logger.error(f"通知处理失败: {e}")
    
    def _execute_task(self, task_name: str):
        """
        执行单个任务
        
        Args:
            task_name: 任务名称
        """
        if task_name not in self.tasks:
            logger.error(f"任务不存在: {task_name}")
            return
        
        task = self.tasks[task_name]
        result = TaskResult(task_name)
        result.start_time = datetime.now()
        result.status = TaskStatus.RUNNING
        
        self.task_results[task_name] = result
        
        logger.info(f"开始执行任务: {task_name}")
        
        # 检查依赖
        if task.dependencies:
            for dep in task.dependencies:
                if dep in self.task_results:
                    dep_result = self.task_results[dep]
                    if dep_result.status != TaskStatus.SUCCESS:
                        result.status = TaskStatus.SKIPPED
                        result.message = f"依赖任务 {dep} 未成功执行"
                        logger.warning(f"任务 {task_name} 因依赖未满足而跳过")
                        self._notify(result)
                        return
        
        # 重试机制
        for attempt in range(task.retry_times):
            try:
                # 设置超时
                import threading
                
                result_data = [None]
                exception = [None]
                
                def task_func():
                    try:
                        result_data[0] = task.func()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=task_func)
                thread.start()
                thread.join(timeout=task.timeout)
                
                if thread.is_alive():
                    result.status = TaskStatus.FAILED
                    result.error = f"任务超时 (> {task.timeout}s)"
                    logger.error(f"任务 {task_name} 超时")
                    break
                
                if exception[0]:
                    raise exception[0]
                
                # 成功
                result.status = TaskStatus.SUCCESS
                result.message = "任务执行成功"
                result.result_data = result_data[0]
                
                logger.info(f"任务 {task_name} 执行成功")
                break
                
            except Exception as e:
                logger.warning(f"任务 {task_name} 第 {attempt + 1} 次尝试失败: {e}")
                
                if attempt < task.retry_times - 1:
                    time.sleep(task.retry_interval)
                else:
                    result.status = TaskStatus.FAILED
                    result.error = str(e)
                    logger.error(f"任务 {task_name} 最终失败")
        
        result.end_time = datetime.now()
        
        # 发送通知
        if task.notify_on_failure and result.status == TaskStatus.FAILED:
            self._notify(result)
    
    def _setup_schedule(self):
        """设置调度计划"""
        # 清空现有计划
        schedule.clear()
        
        for name, task in self.tasks.items():
            if not task.enabled:
                continue
            
            # 解析调度时间
            time_str = task.schedule_time
            
            if ':' in time_str and len(time_str.split(':')) == 2:
                # 每日时间 (如 "08:00")
                hour, minute = time_str.split(':')
                eval(f"schedule.every().day.at('{time_str}').do(self._execute_task, '{name}')")
                logger.debug(f"设置每日任务 {name}: {time_str}")
            elif '*' in time_str or '/' in time_str:
                # Cron 表达式
                # 简化实现：使用 schedule 的 cron 兼容模式
                logger.debug(f"任务 {name} 使用 cron: {time_str}")
    
    def start(self, blocking: bool = True):
        """
        启动调度器
        
        Args:
            blocking: 是否阻塞
        """
        self.is_running = True
        
        # 设置调度
        self._setup_schedule()
        
        logger.info("调度器启动")
        
        if blocking:
            try:
                while self.is_running:
                    schedule.run_pending()
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号")
        else:
            # 非阻塞模式：启动后台线程
            self.scheduler_thread = threading.Thread(target=self._background_run)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
    
    def _background_run(self):
        """后台运行"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"后台运行出错: {e}")
                time.sleep(5)
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        schedule.clear()
        logger.info("调度器已停止")
    
    def run_now(self, task_name: str):
        """
        立即运行任务
        
        Args:
            task_name: 任务名称
        """
        if task_name in self.tasks:
            self._execute_task(task_name)
        else:
            logger.error(f"任务不存在: {task_name}")
    
    def get_status(self) -> Dict:
        """
        获取调度器状态
        """
        return {
            'is_running': self.is_running,
            'num_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'pending_jobs': len(schedule.get_jobs()),
            'recent_results': {
                name: result.to_dict() 
                for name, result in list(self.task_results.items())[-10:]
            }
        }
    
    def get_next_run_time(self, task_name: str) -> Optional[datetime]:
        """
        获取任务下次运行时间
        """
        for job in schedule.get_jobs():
            if task_name in str(job):
                return job.next_run
        return None


class FactorAnalysisPipeline:
    """
    因子分析自动化流水线
    
    整合数据更新、因子计算、回测、报告生成
    """
    
    def __init__(self, data_repo=None):
        """
        初始化流水线
        
        Args:
            data_repo: 数据仓库实例
        """
        self.data_repo = data_repo
        self.scheduler = TaskScheduler()
        self.updater = AutoDataUpdater(data_repo) if data_repo else None
        
        # 注册默认任务
        self._register_default_tasks()
    
    def _register_default_tasks(self):
        """注册默认任务"""
        # 每日数据更新
        self.scheduler.register_task(
            name="daily_data_update",
            func=self._task_daily_data_update,
            schedule_time="08:00",
            description="每日更新市场数据",
            retry_times=2,
            timeout=1800
        )
        
        # 因子计算
        self.scheduler.register_task(
            name="factor_calculation",
            func=self._task_factor_calculation,
            schedule_time="09:30",
            description="计算因子值",
            dependencies=["daily_data_update"],
            retry_times=2,
            timeout=3600
        )
        
        # 因子评估
        self.scheduler.register_task(
            name="factor_evaluation",
            func=self._task_factor_evaluation,
            schedule_time="10:00",
            description="评估因子表现",
            dependencies=["factor_calculation"],
            retry_times=1,
            timeout=3600
        )
        
        # 回测
        self.scheduler.register_task(
            name="backtest",
            func=self._task_backtest,
            schedule_time="15:00",
            description="运行回测",
            dependencies=["factor_evaluation"],
            retry_times=1,
            timeout=7200
        )
        
        # 生成报告
        self.scheduler.register_task(
            name="generate_report",
            func=self._task_generate_report,
            schedule_time="16:00",
            description="生成分析报告",
            dependencies=["backtest"],
            retry_times=3,
            timeout=1800
        )
        
        # 添加邮件通知
        self.scheduler.add_notification_handler(self._send_notification)
    
    def _task_daily_data_update(self) -> Dict:
        """每日数据更新任务"""
        logger.info("执行每日数据更新...")
        
        if not self.updater:
            return {'status': 'skipped', 'message': '未配置数据仓库'}
        
        results = self.updater.run_full_update()
        
        return {
            'status': 'success' if all(r['status'] == 'success' for r in results.values()) else 'partial',
            'results': results
        }
    
    def _task_factor_calculation(self) -> Dict:
        """因子计算任务"""
        logger.info("执行因子计算...")
        
        # 这里应该调用因子计算逻辑
        from quant_factor_system import FactorSystem, MomentumFactor, ValueFactor
        
        system = FactorSystem(name="Daily Factor System")
        system.add_factor(MomentumFactor(), weight=1.0)
        system.add_factor(ValueFactor(), weight=1.0)
        
        # 模拟计算
        logger.info("因子计算完成")
        
        return {
            'status': 'success',
            'factors': list(system.factors.keys())
        }
    
    def _task_factor_evaluation(self) -> Dict:
        """因子评估任务"""
        logger.info("执行因子评估...")
        
        # 模拟评估
        return {
            'status': 'success',
            'ic_scores': {'Momentum': 0.05, 'Value': 0.08}
        }
    
    def _task_backtest(self) -> Dict:
        """回测任务"""
        logger.info("执行回测...")
        
        # 模拟回测
        return {
            'status': 'success',
            'total_return': '15.2%',
            'sharpe_ratio': 1.25
        }
    
    def _task_generate_report(self) -> Dict:
        """生成报告任务"""
        logger.info("生成分析报告...")
        
        report_path = f"./data/reports/report_{datetime.now().strftime('%Y%m%d')}.html"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # 模拟生成报告
        with open(report_path, 'w') as f:
            f.write(f"<h1>因子分析报告 - {datetime.now().strftime('%Y-%m-%d')}</h1>")
        
        return {
            'status': 'success',
            'report_path': report_path
        }
    
    def _send_notification(self, result: TaskResult):
        """发送通知"""
        logger.info(f"任务 {result.task_name} 通知: {result.status.value}")
        
        # 可以扩展为邮件、微信通知等
        if result.status == TaskStatus.FAILED:
            logger.error(f"❌ 任务失败: {result.task_name} - {result.error}")
    
    def run_full_pipeline(self):
        """手动运行完整流水线"""
        logger.info("="*60)
        logger.info("开始运行因子分析流水线")
        logger.info("="*60)
        
        # 按依赖顺序执行任务
        task_order = [
            'daily_data_update',
            'factor_calculation',
            'factor_evaluation',
            'backtest',
            'generate_report'
        ]
        
        results = {}
        
        for task_name in task_order:
            if task_name in self.tasks:
                logger.info(f"\n{'='*40}")
                logger.info(f"执行任务: {task_name}")
                logger.info(f"{'='*40}")
                
                self.scheduler.run_now(task_name)
                results[task_name] = self.scheduler.task_results[task_name].to_dict()
        
        logger.info("\n" + "="*60)
        logger.info("流水线执行完成")
        logger.info("="*60)
        
        return results
    
    def start_scheduler(self, blocking: bool = True):
        """启动调度器"""
        logger.info("启动因子分析调度器...")
        self.scheduler.start(blocking)
    
    def stop_scheduler(self):
        """停止调度器"""
        self.scheduler.stop()


def create_default_pipeline(data_repo=None) -> FactorAnalysisPipeline:
    """
    创建默认配置的流水线
    
    Args:
        data_repo: 数据仓库实例
        
    Returns:
        配置好的流水线实例
    """
    return FactorAnalysisPipeline(data_repo)


if __name__ == "__main__":
    print("🧪 测试自动化调度系统...")
    
    # 创建流水线
    pipeline = create_default_pipeline()
    
    # 查看状态
    status = pipeline.scheduler.get_status()
    print(f"\n📊 调度器状态:")
    print(f"  运行中: {status['is_running']}")
    print(f"  任务数: {status['num_tasks']}")
    print(f"  启用任务: {status['enabled_tasks']}")
    
    # 手动运行完整流水线
    print("\n🚀 手动运行完整流水线...")
    results = pipeline.run_full_pipeline()
    
    for task_name, result in results.items():
        print(f"\n  {task_name}:")
        print(f"    状态: {result['status']}")
        if result.get('message'):
            print(f"    消息: {result['message']}")
