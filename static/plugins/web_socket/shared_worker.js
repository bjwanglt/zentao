// shared-worker.js
const ports = [];
let websocket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let reconnectTimer = null;

// 连接处理
self.onconnect = function(e) {
    const port = e.ports[0];
    ports.push(port);

    console.log('新的页面连接到 SharedWorker，当前连接数:', ports.length);

    // 如果还没有 WebSocket 连接，创建它
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        initWebSocket();
    } else {
        port.postMessage({
            type: 'CONNECTION_STATUS',
            status: 'connected'
        });
    }

    // 处理来自页面的消息
    port.onmessage = function(e) {
        const data = e.data;

        if (data.type === 'SEND_MESSAGE' && websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify(data.message));
        }

        if (data.type === 'PING') {
            port.postMessage({ type: 'PONG' });
        }
    };

    port.start();

    port.onclose = function() {
        const index = ports.indexOf(port);
        if (index > -1) {
            ports.splice(index, 1);
        }
        console.log('页面断开连接，剩余连接数:', ports.length);

        if (ports.length === 0 && websocket) {
            cleanupWebSocket();
        }
    };
};

function initWebSocket() {
    try {
        if (websocket) {
            cleanupWebSocket();
        }

        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }

        const wsUrl = 'ws://127.0.0.1:8000/ws/aaa/';
        websocket = new WebSocket(wsUrl);

        websocket.onopen = function() {
            console.log('SharedWorker: WebSocket 连接已建立');
            reconnectAttempts = 0;
            broadcast({
                type: 'CONNECTION_STATUS',
                status: 'connected'
            });
        };

        websocket.onmessage = function(event) {
            console.log('SharedWorker: 收到 WebSocket 消息', event.data);

            try {
                const dataList = JSON.parse(event.data);
                // 直接广播服务端的全量数据，不保存状态
                broadcast({
                    type: 'NEW_MESSAGE',
                    messages: dataList,
                    timestamp: Date.now()
                });
            } catch (error) {
                console.error('SharedWorker: 解析消息失败', error);
            }
        };

        websocket.onclose = function(event) {
            console.log('SharedWorker: WebSocket 连接已关闭', event.code, event.reason);
            broadcast({
                type: 'CONNECTION_STATUS',
                status: 'disconnected',
                code: event.code,
                reason: event.reason
            });

            // 如果还有页面连接，尝试重连
            if (ports.length > 0 && reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                console.log(`SharedWorker: ${delay}ms后尝试重连 (${reconnectAttempts}/${maxReconnectAttempts})`);
                reconnectTimer = setTimeout(() => initWebSocket(), delay);
            }
        };

        websocket.onerror = function(error) {
            console.error('SharedWorker: WebSocket 错误', error);
            broadcast({
                type: 'CONNECTION_STATUS',
                status: 'error'
            });
        };

    } catch (error) {
        console.error('SharedWorker: 创建 WebSocket 失败', error);
    }
}

function cleanupWebSocket() {
    if (websocket) {
        websocket.onopen = null;
        websocket.onmessage = null;
        websocket.onclose = null;
        websocket.onerror = null;
        if (websocket.readyState === WebSocket.OPEN) {
            websocket.close(1000, '正常关闭');
        }
        websocket = null;
    }
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
}

// 广播消息给所有页面
function broadcast(message) {
    const activePorts = [];
    const inactiveIndices = [];

    ports.forEach((port, index) => {
        try {
            port.postMessage(message);
            activePorts.push(port);
        } catch (err) {
            console.error('SharedWorker: 广播消息失败，移除无效端口', err);
            inactiveIndices.push(index);
        }
    });

    // 清理无效的端口（从后往前删除）
    inactiveIndices.reverse().forEach(index => {
        ports.splice(index, 1);
    });

    console.log(`SharedWorker: 广播消息给 ${activePorts.length} 个页面`);
}

// SharedWorker 全局错误处理
self.addEventListener('error', function(error) {
    console.error('SharedWorker 全局错误:', error);
});