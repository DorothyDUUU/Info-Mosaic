#!/bin/bash

# 初始化conda环境
echo "正在初始化conda环境..."

# 尝试多种方式加载conda
success=0

# 方法1: 尝试直接加载conda.sh
echo "尝试直接加载conda环境配置..."
if [ -f "/root/miniconda3/etc/profile.d/conda.sh" ];
then
    source /root/miniconda3/etc/profile.d/conda.sh
    success=1
elif [ -f "/opt/conda/etc/profile.d/conda.sh" ];
then
    source /opt/conda/etc/profile.d/conda.sh
    success=1
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ];
then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    success=1
fi

# 方法2: 如果方法1失败，尝试使用conda init的非交互方式
if [ $success -eq 0 ] && command -v conda &> /dev/null;
then
    echo "尝试使用conda init初始化..."
    # 创建临时环境文件
    TEMP_CONDA_INIT=$(mktemp)
    # 运行conda init并捕获输出
    conda init bash --no-user-shell-setup > "$TEMP_CONDA_INIT" 2>&1
    # 提取关键的初始化命令并执行
    grep -E 'export|PATH' "$TEMP_CONDA_INIT" | sed 's/\r//g' > "$TEMP_CONDA_INIT.tmp"
    source "$TEMP_CONDA_INIT.tmp"
    rm -f "$TEMP_CONDA_INIT" "$TEMP_CONDA_INIT.tmp"
    success=1
fi

# 如果还是无法初始化，显示错误信息
if [ $success -eq 0 ] && ! command -v conda &> /dev/null;
then
    echo "错误: 未找到conda安装或无法初始化conda。请确保conda已正确安装。"
    echo "提示: 您可以手动运行 'conda init' 命令，然后重新启动终端。"
    exit 1
fi

# 确认conda可用
echo "conda环境初始化成功，当前conda版本: $(conda --version 2>/dev/null || echo '未知')"

# 检查是否在Docker容器内运行
if [ -f "/.dockerenv" ]; then
    echo "检测到在Docker容器内运行，使用/mnt路径..."
    BASE_PATH="/mnt"
else
    echo "在宿主机上运行，使用脚本所在目录的相对路径..."
    # 使用脚本所在目录的相对路径
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_PATH="$SCRIPT_DIR/../.."
fi

# 停止所有服务的函数
stop_all_services() {
    echo "正在停止所有SSE服务..."
    
    # 查找并停止所有相关进程
    pkill -f "biomcp run --mode worker --port 8001"
    pkill -f "python -m src.server --sse --port 8002"
    pkill -f "python run_server.py.*serper"
    pkill -f "python run_server.py.*Youtube"
    
    echo "所有SSE服务已停止"
    exit 0
}

# 检查是否是停止命令
if [ "$1" = "stop" ]; then
    stop_all_services
fi

# 检查并创建所需的conda环境
echo "正在检查并创建所需的conda环境..."

# 检查base环境是否存在
base_env_exists=$(conda info --envs | grep -w base | wc -l)
if [ $base_env_exists -eq 0 ]; then
    echo "创建base环境..."
    conda create -n base python=3.8 -y
fi

# 检查fmp环境是否存在
fmp_env_exists=$(conda info --envs | grep -w fmp | wc -l)
if [ $fmp_env_exists -eq 0 ]; then
    echo "创建fmp环境..."
    conda create -n fmp python=3.8 -y
fi

# 激活基础环境
echo "正在激活基础环境..."
conda activate base

# 创建日志目录
LOG_DIR="$BASE_PATH/MCP/logs"
mkdir -p $LOG_DIR

# 1. 启动 biomcp server
echo "正在启动 biomcp server (端口: 8001)..."
export FDA_API_KEY=your_fda_api_key
cd $BASE_PATH/MCP/sse_server/biomcp-main
biomcp run --mode worker --port 8001 > $LOG_DIR/biomcp.log 2>&1 &
echo "biomcp server 已启动 (PID: $!)"

# 2. 启动 fmp server
echo "正在启动 fmp server (端口: 8002)..."
conda deactivate
conda activate fmp
export FMP_API_KEY=your_fmp_api_key
cd $BASE_PATH/MCP/sse_server/fmp-mcp-server
python -m src.server --sse --port 8002 > $LOG_DIR/fmp.log 2>&1 &
echo "fmp server 已启动 (PID: $!)"

# 3. 启动 serper server
echo "正在启动 serper server (端口: 8004)..."
conda deactivate
conda activate base
# 安装serper所需依赖
pip install aiohttp -q
export SERPER_API_KEY=your_serper_api_key
cd $BASE_PATH/MCP/sse_server/serper-mcp-server-main
python run_server.py > $LOG_DIR/serper.log 2>&1 &
echo "serper server 已启动 (PID: $!)"

# 4. 启动 Youtube server
echo "正在启动 Youtube server (端口: 8005)..."
# 安装YouTube所需依赖
pip install google-api-python-client youtube-transcript-api google-search-results -q
export YOUTUBE_API_KEY=your_youtube_api_key
export SERPAPI_KEY=your_serpapi_key
cd $BASE_PATH/MCP/sse_server/Youtube-Server
python run_server.py > $LOG_DIR/youtube.log 2>&1 &
echo "Youtube server 已启动 (PID: $!)"

# 恢复到基础目录
cd $BASE_PATH/MCP

# 显示帮助信息
echo ""
echo "所有SSE服务已成功启动!"
echo "服务列表:"
echo "- biomcp server: http://localhost:8001/sse"
echo "- fmp server: http://localhost:8002/sse"
echo "- serper server: http://localhost:8004/sse"
echo "- Youtube server: http://localhost:8005/sse"
echo ""
echo "要停止所有服务，请运行: ./deploy_sse_servers.sh stop"
echo "日志文件位于: $LOG_DIR/"

# 保持脚本运行，以便可以看到输出
sleep 2