#!/bin/bash
log() {
    local message="$1"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $message" | tee -a "$LOG_FILE"
}
log "开始克隆 Binance binance-public-data github repo..."
git clone https://github.com/binance/binance-public-data.git
cd binance-public-data/python
log "开始安装依赖..."
pip install -r requirements.txt

# 运行Python脚本下载比特币历史1/3/5/15分钟快照数据
log "开始下载 1m 比特币快照数据..."
python download-kline.py -t spot -s BTCUSDT -i 1m
log "开始下载 3m 比特币快照数据..."
python download-kline.py -t spot -s BTCUSDT -i 3m
log "开始下载 5m 比特币快照数据..."
python download-kline.py -t spot -s BTCUSDT -i 5m
log "开始下载 15m 比特币快照数据..."
python download-kline.py -t spot -s BTCUSDT -i 15m

log "数据下载完成，至 binance-public-data/python/data"