(function() {
    'use strict';

    // 检查是否已经初始化
    if (window.WebSocketManagerInitialized) {
        console.warn('WebSocket Manager 已经初始化，跳过重复初始化');
        return;
    }
    window.WebSocketManagerInitialized = true;

    let websocketMessageQueue = [];
    let websocketNotificationOpen = false;

    class SharedWebSocketManager {
        constructor() {
            console.log('🚀 SharedWebSocketManager 构造函数被调用');
            try {
                this.worker = new SharedWorker('/static/plugins/web_socket/shared_worker.js');
                this.port = this.worker.port;
                this.isConnected = false;
                this.init();
            } catch (error) {
                console.error('创建 SharedWorker 失败:', error);
                this.fallbackToDirectWebSocket();
            }
        }

        init() {
            console.log('🔧 初始化 SharedWebSocketManager');

            // 监听来自 SharedWorker 的消息
            this.port.onmessage = (event) => {
                const data = event.data;

                switch (data.type) {
                    case 'NEW_MESSAGE':
                        console.log('🎯 收到新消息:', data.messages);
                        this.handleNewMessages(data.messages);
                        break;

                    case 'CONNECTION_STATUS':
                        console.log('🔌 连接状态变化:', data.status);
                        this.handleConnectionStatus(data.status);
                        break;

                    case 'PONG':
                        console.log('💓 收到心跳响应');
                        break;

                    default:
                        console.log('❓ 未知消息类型:', data.type);
                }
            };

            // 启动端口通信
            this.port.start();

            // 页面可见性变化处理
            this.handlePageVisibility();

            // 定期发送心跳
            this.startHeartbeat();

            console.log('✅ SharedWebSocket 管理器初始化完成');
        }

        handleNewMessages(messages) {
            console.log('🔄 处理新消息，数量:', messages.length);

            // 使用服务端的全量数据，不拼接
            websocketMessageQueue = [...messages];

            console.log('📊 更新消息队列:', websocketMessageQueue);

            // 调用显示通知函数
            this.showNotifications(websocketMessageQueue);
        }

        handleConnectionStatus(status) {
            this.isConnected = status === 'connected';
            console.log('WebSocket 连接状态:', status);
            this.updateConnectionIndicator(status);
        }

        updateConnectionIndicator(status) {
            // 可选：在页面某个位置显示连接状态
            let indicator = document.getElementById('websocket-status');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'websocket-status';
                indicator.style.cssText = `
                    position: fixed;
                    bottom: 10px;
                    right: 10px;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 12px;
                    z-index: 10001;
                    background: #666;
                    color: white;
                `;
                document.body.appendChild(indicator);
            }

            const statusColors = {
                connected: '#4CAF50',
                disconnected: '#FF9800',
                error: '#F44336'
            };

            const statusTexts = {
                connected: '已连接',
                disconnected: '已断开',
                error: '连接错误'
            };

            indicator.textContent = `WebSocket: ${statusTexts[status] || status}`;
            indicator.style.background = statusColors[status] || '#666';
        }

        handlePageVisibility() {
            // 页面重新可见时发送心跳检查连接状态
            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    this.sendHeartbeat();
                }
            });
        }

        startHeartbeat() {
            // 每30秒发送一次心跳
            setInterval(() => {
                this.sendHeartbeat();
            }, 30000);
        }

        sendHeartbeat() {
            if (this.port) {
                this.port.postMessage({ type: 'PING' });
            }
        }

        sendMessage(message) {
            if (this.isConnected && this.port) {
                this.port.postMessage({
                    type: 'SEND_MESSAGE',
                    message: message
                });
                return true;
            } else {
                console.warn('WebSocket 未连接，无法发送消息');
                return false;
            }
        }

        // 弹窗函数
        showNotifications(messages) {
            console.log('🪟 显示通知，消息数量:', messages.length);

            // 使用服务端的全量数据
            websocketMessageQueue = [...messages];

            console.log('🏷️ 弹窗当前状态:', websocketNotificationOpen);

            // 如果弹窗已经打开，只更新内容
            if (websocketNotificationOpen) {
                console.log('🔄 弹窗已打开，更新内容');
                this.updateNotificationContent();
                return;
            }

            console.log('🆕 创建新弹窗');
            this.createNotificationWindow();
        }

        createNotificationWindow() {
            console.log('🎪 开始创建通知窗口');

            websocketNotificationOpen = true;

            // 如果已存在弹窗，先移除
            const existingNotification = document.getElementById('custom-notification');
            if (existingNotification) {
                console.log('🗑️ 移除已存在的弹窗');
                document.body.removeChild(existingNotification);
            }

            // 创建弹窗容器
            const notification = document.createElement('div');
            notification.id = 'custom-notification';
            notification.style.cssText = `
                position: fixed;
                top: 62px;
                right: 20px;
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.12);
                padding: 0;
                width: 420px;
                max-height: 500px;
                overflow: hidden;
                z-index: 10000;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            `;

            // 标题栏
            const header = document.createElement('div');
            header.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            `;

            const titleSection = document.createElement('div');
            titleSection.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
            `;

            // 消息图标和计数
            const iconWrapper = document.createElement('div');
            iconWrapper.style.cssText = `
                position: relative;
                display: inline-flex;
            `;

            const messageIcon = document.createElement('i');
            messageIcon.className = 'fa fa-bell';
            messageIcon.style.cssText = `
                font-size: 18px;
                color: white;
            `;

            // 红色小圆点计数
            const badge = document.createElement('div');
            badge.id = 'notification-badge';
            badge.style.cssText = `
                position: absolute;
                top: -6px;
                right: -6px;
                background: #ff4757;
                color: white;
                border-radius: 50%;
                width: 18px;
                height: 18px;
                font-size: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                border: 2px solid white;
            `;
            badge.textContent = websocketMessageQueue.length > 99 ? '99+' : websocketMessageQueue.length;

            iconWrapper.appendChild(messageIcon);
            iconWrapper.appendChild(badge);

            const title = document.createElement('div');
            title.style.cssText = `
                font-weight: 600;
                font-size: 16px;
            `;
            title.textContent = `消息通知 (${websocketMessageQueue.length}条)`;

            titleSection.appendChild(iconWrapper);
            titleSection.appendChild(title);

            // 右侧操作区
            const actionsSection = document.createElement('div');
            actionsSection.style.cssText = `
                display: flex;
                align-items: center;
                gap: 12px;
            `;

            // 查看更多链接
            const moreLink = document.createElement('a');
            moreLink.href = 'javascript:void(0)';
            moreLink.textContent = '查看更多';
            moreLink.id = 'more-link';
            moreLink.style.cssText = `
                color: white;
                text-decoration: none;
                font-size: 13px;
                cursor: pointer;
                padding: 4px 8px;
                border-radius: 4px;
                background: rgba(255,255,255,0.2);
                display: ${websocketMessageQueue.length > 3 ? 'block' : 'none'};
            `;
            moreLink.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔗 点击查看更多');
                window.location.href = '/notification/list/';
            };

            // 关闭按钮
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '&times;';
            closeBtn.style.cssText = `
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                console.log('❌ 点击关闭按钮');
                this.closeNotification();
            };

            actionsSection.appendChild(moreLink);
            actionsSection.appendChild(closeBtn);

            header.appendChild(titleSection);
            header.appendChild(actionsSection);
            notification.appendChild(header);

            // 消息内容区域
            const content = document.createElement('div');
            content.id = 'notification-content';
            content.style.cssText = `
                padding: 0;
                max-height: 350px;
                overflow-y: auto;
            `;

            notification.appendChild(content);

            // 添加到页面
            document.body.appendChild(notification);
            console.log('✅ 弹窗已添加到页面');

            // 初始渲染内容
            this.updateNotificationContent();
        }

        updateNotificationContent() {
            console.log('🔄 更新通知内容');
            const content = document.getElementById('notification-content');

            if (!content) {
                console.error('❌ 未找到内容区域');
                return;
            }

            console.log('📊 更新内容，消息数量:', websocketMessageQueue.length);

            // 清空内容
            content.innerHTML = '';

            // 只显示前3条消息
            const displayMessages = websocketMessageQueue.slice(0, 3);
            console.log('👀 显示的消息:', displayMessages);

            if (displayMessages.length === 0) {
                console.log('ℹ️ 没有消息可显示');
                content.innerHTML = `
                    <div style="padding: 40px 20px; text-align: center; color: #666;">
                        <i class="fa fa-check-circle" style="font-size: 48px; color: #48bb78; margin-bottom: 16px;"></i>
                        <div>暂无消息</div>
                    </div>
                `;
                return;
            }

            // 创建表格
            const table = document.createElement('table');
            table.style.cssText = `
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            `;

            // 添加消息行
            displayMessages.forEach((message, index) => {
                console.log(`📝 添加消息 ${index}:`, message);

                const row = document.createElement('tr');
                row.style.cssText = `
                    border-bottom: 1px solid #f8f9fa;
                `;

                // 消息内容单元格
                const messageCell = document.createElement('td');
                messageCell.style.cssText = `
                    padding: 14px 16px;
                    color: #2d3748;
                    line-height: 1.5;
                    word-break: break-word;
                    font-size: 14px;
                `;

                // 直接使用消息内容，不处理格式
                const messageContent = Array.isArray(message) ? message[1] : message;
                messageCell.textContent = messageContent;

                // 按钮单元格
                const buttonCell = document.createElement('td');
                buttonCell.style.cssText = `
                    padding: 14px 16px;
                    text-align: right;
                    white-space: nowrap;
                    width: 80px;
                `;

                const confirmBtn = document.createElement('button');
                confirmBtn.textContent = '确认';
                confirmBtn.style.cssText = `
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 6px 14px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 12px;
                    min-width: 60px;
                `;

                // 按钮点击事件
                confirmBtn.onclick = (e) => {
                    e.stopPropagation();

                    const messageId = Array.isArray(message) ? message[0] : index;
                    const messageContent = Array.isArray(message) ? message[1] : message;

                    alert(`消息索引: ${index}, 消息ID: ${messageId}, 消息内容: ${messageContent}`);

                    // 从队列中移除
                    this.removeMessageFromQueue(messageId);
                };

                buttonCell.appendChild(confirmBtn);
                row.appendChild(messageCell);
                row.appendChild(buttonCell);
                table.appendChild(row);
            });

            content.appendChild(table);

            // 更新UI元素
            this.updateNotificationUI();

            console.log('✅ 通知内容更新完成');
        }

        updateNotificationUI() {
            const badge = document.getElementById('notification-badge');
            const moreLink = document.getElementById('more-link');
            const title = document.querySelector('#custom-notification div[style*="font-weight: 600"]');

            if (badge) {
                badge.textContent = websocketMessageQueue.length > 99 ? '99+' : websocketMessageQueue.length;
            }
            if (moreLink) {
                moreLink.style.display = websocketMessageQueue.length > 3 ? 'block' : 'none';
            }
            if (title) {
                title.textContent = `消息通知 (${websocketMessageQueue.length}条)`;
            }

            // 如果没有消息了，自动关闭
            if (websocketMessageQueue.length === 0) {
                console.log('⏰ 没有消息，2秒后自动关闭');
                setTimeout(() => {
                    this.closeNotification();
                }, 2000);
            }
        }

        removeMessageFromQueue(messageId) {
            console.log('🗑️ 移除消息, ID:', messageId);

            const messageIndex = websocketMessageQueue.findIndex(msg => {
                if (Array.isArray(msg)) {
                    return msg[0] === messageId;
                }
                return false;
            });

            if (messageIndex !== -1) {
                websocketMessageQueue.splice(messageIndex, 1);
                console.log('📉 移除后队列:', websocketMessageQueue);
                this.updateNotificationContent();
            } else {
                console.warn('⚠️ 未找到要移除的消息:', messageId);
            }
        }

        closeNotification() {
            console.log('🔒 关闭通知');
            const notification = document.getElementById('custom-notification');
            if (notification && notification.parentNode) {
                document.body.removeChild(notification);
            }
            websocketNotificationOpen = false;
            websocketMessageQueue = [];
            console.log('✅ 通知已关闭');
        }

        fallbackToDirectWebSocket() {
            console.warn('SharedWorker 不支持，回退到直接 WebSocket 连接');
            // 这里可以添加直接 WebSocket 连接的代码作为备选方案
        }
    }

    // 全局管理器实例
    let websocketManager;

    // 页面初始化
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📄 DOM 内容加载完成');

        if (window.websocketManager) {
            console.warn('⚠️ WebSocket Manager 已经初始化');
            return;
        }

        window.websocketManager = new SharedWebSocketManager();
        console.log('🎉 SharedWebSocket 管理器已初始化');
    });

    // 测试函数
    window.testNotification = function() {
        console.log('🧪 测试通知');
        const testMessages = [
            [1, '这是测试消息 1'],
            [2, '这是测试消息 2'],
            [3, '这是测试消息 3']
        ];

        if (window.websocketManager) {
            window.websocketManager.handleNewMessages(testMessages);
        } else {
            console.error('❌ WebSocket Manager 未初始化');
        }
    }

    window.sendWebSocketMessage = function(message) {
        if (window.websocketManager) {
            return window.websocketManager.sendMessage(message);
        }
        return false;
    }

    window.closeWebSocketNotification = function() {
        if (window.websocketManager) {
            window.websocketManager.closeNotification();
        }
    }
})();