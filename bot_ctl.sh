#!/usr/bin/env bash
# 飞书机器人管理脚本
# 用法: bash bot_ctl.sh {start|stop|restart|status|logs}

BOT_SCRIPT="/workspace/1/feishu_chatbot.py"
PID_FILE="/workspace/1/.bot_pid"
LOG_FILE="/workspace/1/.bot_log"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "🤖 机器人已在运行中 (PID: $(cat $PID_FILE))"
    else
      echo "🚀 启动机器人..."
      cd /workspace/1
      nohup python3 feishu_chatbot.py < <(tail -f /dev/null) > "$LOG_FILE" 2>&1 &
      echo $! > "$PID_FILE"
      sleep 2
      if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 启动成功 (PID: $(cat $PID_FILE))"
        tail -5 "$LOG_FILE"
      else
        echo "❌ 启动失败，查看日志: tail -f $LOG_FILE"
      fi
    fi
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo "🛑 停止机器人 (PID: $PID)..."
      kill $PID 2>/dev/null
      # 也杀掉关联的 lark-cli 进程
      pkill -f "lark-cli event consume" 2>/dev/null
      pkill -f "feishu_chatbot" 2>/dev/null
      rm -f "$PID_FILE"
      echo "✅ 已停止"
    else
      echo "机器人未在运行"
    fi
    ;;
  restart)
    bash "$0" stop
    sleep 2
    bash "$0" start
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      PID=$(cat "$PID_FILE")
      echo "✅ 运行中 (PID: $PID)"
      # 检查子进程
      echo ""
      echo "--- 进程树 ---"
      ps aux | grep -E "feishu_chatbot|lark-cli event" | grep -v grep
    else
      echo "❌ 未运行"
    fi
    ;;
  logs)
    if [ -f "$LOG_FILE" ]; then
      tail -f "$LOG_FILE"
    else
      echo "暂无日志"
    fi
    ;;
  *)
    echo "🤖 飞书机器人管理脚本"
    echo ""
    echo "用法: bash bot_ctl.sh {start|stop|restart|status|logs}"
    echo ""
    echo "  start   — 启动机器人"
    echo "  stop    — 停止机器人"
    echo "  restart — 重启机器人"
    echo "  status  — 查看运行状态"
    echo "  logs    — 查看实时日志"
    ;;
esac