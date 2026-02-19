"""
任务监控页面
Task Monitoring Page

功能:
- 数据下载任务
- 因子计算任务
- 回测任务
- 定时任务状态
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List
import time


class TaskMonitor:
    """任务监控器"""
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.max_tasks = 100
    
    def add_task(
        self,
        task_type: str,
        name: str,
        status: str = 'pending',
        progress: int = 0,
        message: str = ''
    ) -> str:
        """添加任务"""
        task_id = f"{task_type}_{len(self.tasks)}_{int(time.time())}"
        
        task = {
            'task_id': task_id,
            'task_type': task_type,
            'name': name,
            'status': status,  # pending, running, completed, failed
            'progress': progress,
            'message': message,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        self.tasks.append(task)
        
        # 限制任务数量
        if len(self.tasks) > self.max_tasks:
            self.tasks = self.tasks[-self.max_tasks:]
        
        return task_id
    
    def update_task(
        self,
        task_id: str,
        status: str = None,
        progress: int = None,
        message: str = None
    ):
        """更新任务"""
        for task in self.tasks:
            if task['task_id'] == task_id:
                if status is not None:
                    task['status'] = status
                if progress is not None:
                    task['progress'] = progress
                if message is not None:
                    task['message'] = message
                task['updated_at'] = datetime.now()
                break
    
    def get_tasks(
        self,
        task_type: str = None,
        status: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """获取任务列表"""
        result = self.tasks
        
        if task_type:
            result = [t for t in result if t['task_type'] == task_type]
        
        if status:
            result = [t for t in result if t['status'] == status]
        
        return sorted(result, key=lambda x: x['created_at'], reverse=True)[:limit]
    
    def clear_completed(self):
        """清除已完成的任务"""
        self.tasks = [t for t in self.tasks if t['status'] in ['pending', 'running']]


# 全局任务监控器
task_monitor = TaskMonitor()


def render_task_monitor():
    """渲染任务监控页面"""
    st.title("📋 任务监控")
    
    # 1. 任务统计
    tasks = task_monitor.get_tasks()
    
    if tasks:
        running = len([t for t in tasks if t['status'] == 'running'])
        pending = len([t for t in tasks if t['status'] == 'pending'])
        completed = len([t for t in tasks if t['status'] == 'completed'])
        failed = len([t for t in tasks if t['status'] == 'failed'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("运行中", running)
        
        with col2:
            st.metric("等待中", pending)
        
        with col3:
            st.metric("已完成", completed)
        
        with col4:
            st.metric("失败", failed)
    
    # 2. 任务列表
    st.subheader("📝 任务列表")
    
    # 筛选器
    col1, col2 = st.columns(2)
    
    with col1:
        filter_type = st.selectbox(
            "任务类型",
            ['all', 'data_download', 'factor_calc', 'backtest', 'scheduler']
        )
    
    with col2:
        filter_status = st.selectbox(
            "状态",
            ['all', 'running', 'pending', 'completed', 'failed']
        )
    
    # 获取任务
    task_type = None if filter_type == 'all' else filter_type
    status = None if filter_status == 'all' else filter_status
    
    current_tasks = task_monitor.get_tasks(task_type=task_type, status=status)
    
    # 显示任务
    if current_tasks:
        for task in current_tasks:
            render_task_item(task)
    else:
        st.info("暂无任务")
    
    # 3. 手动触发任务
    st.subheader("🚀 手动触发任务")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 触发数据下载"):
            task_id = task_monitor.add_task(
                task_type='data_download',
                name='下载日线数据',
                status='pending'
            )
            st.success(f"任务已添加: {task_id}")
    
    with col2:
        if st.button("📊 触发因子计算"):
            task_id = task_monitor.add_task(
                task_type='factor_calc',
                name='计算所有因子',
                status='pending'
            )
            st.success(f"任务已添加: {task_id}")
    
    # 4. 清除按钮
    if st.button("🗑️ 清除已完成任务"):
        task_monitor.clear_completed()
        st.success("已清除")
        st.rerun()


def render_task_item(task: Dict):
    """渲染单个任务"""
    # 状态颜色
    status_colors = {
        'running': '🔄',
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌'
    }
    
    emoji = status_colors.get(task['status'], '📋')
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"{emoji} **{task['name']}**")
            st.caption(f"任务ID: {task['task_id']}")
        
        with col2:
            if task['progress'] > 0 and task['progress'] < 100:
                st.progress(task['progress'] / 100)
                st.caption(f"{task['progress']}%")
            else:
                st.write(task['status'])
        
        with col3:
            updated_at = task['updated_at'].strftime('%H:%M:%S')
            st.caption(updated_at)
        
        if task['message']:
            st.info(task['message'])
        
        st.divider()


def render_scheduler_status():
    """渲染定时任务状态"""
    st.title("⏰ 定时任务状态")
    
    # 示例定时任务
    scheduler_tasks = [
        {
            'name': '每日收盘数据下载',
            'schedule': '每天 16:00',
            'status': 'active',
            'last_run': '2024-01-15 16:00:00',
            'next_run': '2024-01-16 16:00:00'
        },
        {
            'name': '因子计算任务',
            'schedule': '每天 16:30',
            'status': 'active',
            'last_run': '2024-01-15 16:30:15',
            'next_run': '2024-01-16 16:30:00'
        },
        {
            'name': 'Dashboard缓存更新',
            'schedule': '每天 17:00',
            'status': 'active',
            'last_run': '2024-01-15 17:00:00',
            'next_run': '2024-01-16 17:00:00'
        }
    ]
    
    # 显示任务表格
    df = pd.DataFrame(scheduler_tasks)
    st.table(df)
    
    # 任务控制
    st.subheader("控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⏸️ 暂停所有任务"):
            st.warning("已暂停所有定时任务")
    
    with col2:
        if st.button("▶️ 恢复所有任务"):
            st.success("已恢复所有定时任务")


def main():
    """主函数"""
    render_task_monitor()
    st.markdown("---")
    render_scheduler_status()


if __name__ == "__main__":
    main()
