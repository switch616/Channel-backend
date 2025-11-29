port=8088; pid=$(lsof -t -i:$port); [ -n "$pid" ] && echo "kill port $port pid $pid" && kill -9 $pid || echo "port $port 未被占用"
python3 main.py