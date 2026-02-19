#!/bin/bash
# ============================================================
# QuantFactorSystem - 数据库管理脚本
# ============================================================

CONTAINER_NAME="timescaledb"
DB_PORT="${DB_PORT:-5432}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

echo "============================================================"
echo "🗄️ TimescaleDB 数据库管理"
echo "============================================================"
echo ""

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker未安装"
        echo ""
        echo "安装Docker:"
        echo "  macOS: https://docs.docker.com/docker-for-mac/install/"
        echo "  Ubuntu: sudo apt-get install docker.io"
        return 1
    fi
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        echo "⚠️ Docker未运行"
        echo ""
        echo "启动Docker后重试"
        return 1
    fi
    return 0
}

case "${1:-status}" in
    start)
        check_docker || exit 1
        
        if docker ps | grep -q "$CONTAINER_NAME"; then
            echo "✅ 数据库已在运行"
            docker ps | grep $CONTAINER_NAME
        else
            echo "🚀 启动数据库..."
            docker run -d \
                --name $CONTAINER_NAME \
                -p $DB_PORT:5432 \
                -e POSTGRES_PASSWORD=$DB_PASSWORD \
                timescale/timescaledb:latest-pg16
            
            echo ""
            echo "✅ 数据库已启动!"
            echo ""
            echo "连接信息:"
            echo "  主机: localhost"
            echo "  端口: $DB_PORT"
            echo "  用户: postgres"
            echo "  密码: $DB_PASSWORD"
        fi
        ;;
    
    stop)
        if docker ps | grep -q "$CONTAINER_NAME"; then
            echo "🛑 停止数据库..."
            docker stop $CONTAINER_NAME
            docker rm $CONTAINER_NAME
            echo "✅ 已停止"
        else
            echo "ℹ️ 数据库未运行"
        fi
        ;;
    
    status)
        if check_docker 2>/dev/null; then
            if docker ps | grep -q "$CONTAINER_NAME"; then
                echo "✅ 数据库运行中"
                docker ps | grep $CONTAINER_NAME
            else
                echo "❌ 数据库未运行"
                echo ""
                echo "启动: ./scripts/db.sh start"
            fi
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    shell)
        if check_docker 2>/dev/null; then
            if docker ps | grep -q "$CONTAINER_NAME"; then
                echo "🔌 连接数据库..."
                docker exec -it $CONTAINER_NAME psql -U postgres
            else
                echo "❌ 数据库未运行"
            fi
        fi
        ;;
    
    logs)
        if check_docker 2>/dev/null; then
            docker logs -f $CONTAINER_NAME
        fi
        ;;
    
    connection)
        echo "连接信息:"
        echo ""
        echo "  主机: localhost"
        echo "  端口: $DB_PORT"
        echo "  用户: postgres"
        echo "  密码: $DB_PASSWORD"
        echo ""
        echo "连接命令:"
        echo "  psql -h localhost -U postgres"
        ;;
    
    *)
        echo "用法: $0 {start|stop|status|restart|shell|logs|connection}"
        echo ""
        echo "命令:"
        echo "  start      - 启动数据库"
        echo "  stop       - 停止数据库"
        echo "  status     - 查看状态"
        echo "  restart    - 重启数据库"
        echo "  shell      - 进入数据库命令行"
        echo "  logs       - 查看日志"
        echo "  connection - 查看连接信息"
        exit 1
        ;;
esac
