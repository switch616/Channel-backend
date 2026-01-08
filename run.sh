source ~/miniconda3/etc/profile.d/conda.sh
conda activate py310_web
port=8088; pid=$(lsof -t -i:$port); [ -n "$pid" ] && echo "kill port $port pid $pid" && kill -9 $pid || echo "port $port 未被占用"
# APP_ENV 现在从 .env 文件中读取，无需在此设置
python3 main.py