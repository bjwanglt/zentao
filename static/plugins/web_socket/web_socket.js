// 全局消息队列
let messageQueue = [];
let isNotificationOpen = false;

function init_websocket() {
    const socket = new WebSocket(`ws://${window.location.host}:8000/ws/aaa/`)
    window.websocket = socket
    // 消息总数提醒
    setupMessageIndicator();
    updateIndicatorBadge();
    socket.onmessage = function (event) {
        let data_list = JSON.parse(event.data)
        messageQueue = [...data_list];
        // 是否操作过关闭
        if (!sessionStorage.getItem('close_msg')) {
            sessionStorage.setItem('close_msg', false);
        }
        const close_msg = JSON.parse(sessionStorage.getItem('close_msg') || 'false');
        // 判断是否有未读的新消息
        let new_msg_flag = false
        // 初始化 msg_idxs（如果不存在）
        if (!sessionStorage.getItem('msg_idxs')) {
            sessionStorage.setItem('msg_idxs', JSON.stringify([]));
        }
        const currentIndexes = JSON.parse(sessionStorage.getItem('msg_idxs'));
        data_list.forEach((message, index) => {
            if (!currentIndexes.includes(message[0])) {
                new_msg_flag = true;
                currentIndexes.push(message[0]);  // 添加到内存中的数组
            }
        });
        sessionStorage.setItem('msg_idxs', JSON.stringify(currentIndexes));
        if (new_msg_flag) {
            sessionStorage.setItem('close_msg', false)
        }
        if (!close_msg || (close_msg && new_msg_flag)) {
            if (data_list.length > 0) {
                showNotifications(data_list)
            }
        }
        updateIndicatorBadge(); // 更新徽章显示
    }
}

// 创建消息弹窗
function showNotifications(messages) {
    // 将新消息添加到队列
    messageQueue = [...messages];
    updateIndicatorBadge(); // 更新徽章显示
    // 如果弹窗已经打开，只更新内容
    if (isNotificationOpen) {
        updateNotificationContent();
        return;
    }
    createNotificationWindow();
}

// 创建通知窗口
function createNotificationWindow() {
    isNotificationOpen = true;

    // 如果已存在弹窗，先移除
    const existingNotification = document.getElementById('custom-notification');
    if (existingNotification) {
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
    badge.textContent = messageQueue.length > 99 ? '99+' : messageQueue.length;

    iconWrapper.appendChild(messageIcon);
    iconWrapper.appendChild(badge);

    const title = document.createElement('div');
    title.style.cssText = `
                font-weight: 600;
                font-size: 16px;
            `;
    title.textContent = `消息通知 (${messageQueue.length}条)`;

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
                display: ${messageQueue.length > 3 ? 'block' : 'none'};
            `;
    moreLink.onclick = function (e) {
        e.preventDefault();
        e.stopPropagation();
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
    closeBtn.onclick = function (e) {
        e.stopPropagation();
        closeNotification();
        // $.sessionStorage.set('close_msg', true);
        sessionStorage.setItem('close_msg', true)

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

    // 初始渲染内容
    updateNotificationContent();
}

// 更新消息内容
function updateNotificationContent() {
    const content = document.getElementById('notification-content');
    const badge = document.getElementById('notification-badge');
    const moreLink = document.getElementById('more-link');
    const title = document.querySelector('#custom-notification div[style*="font-weight: 600"]');

    if (!content) {
        console.log('未找到内容区域');
        return;
    }

    console.log('更新内容，消息数量:', messageQueue.length);

    // 清空内容
    content.innerHTML = '';

    // 只显示前2条消息
    const displayMessages = messageQueue.slice(0, 3);
    console.log('显示的消息:', displayMessages);

    if (displayMessages.length === 0) {
        content.innerHTML = `
            <div style="padding: 40px 20px; text-align: center; color: #666;">
                <i class="fa fa-check-circle" style="font-size: 48px; color: #48bb78; margin-bottom: 16px;"></i>
                <div>暂无消息</div>
            </div>
        `;

        const title = document.querySelector('#custom-notification div[style*="font-weight: 600"]');
        if (title) {
            title.textContent = `消息通知 (0条)`;
        }

        $('#notification-badge').text(0)

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
        console.log('添加消息行:', message, '索引:', index);

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
        // 假设 message 是 [id, content] 格式
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
        confirmBtn.onclick = function (e) {
            e.stopPropagation();

            const messageId = Array.isArray(message) ? message[0] : index;
            const messageContent = Array.isArray(message) ? message[1] : message;

            // 从队列中移除
            removeMessageFromQueue(messageId);

            // 发送已读消息
            if (window.websocket && window.websocket.readyState === WebSocket.OPEN) {
                const readMessage = messageId
                window.websocket.send(messageId);
                console.log('已发送已读消息:', readMessage);
            }
        };

        buttonCell.appendChild(confirmBtn);
        row.appendChild(messageCell);
        row.appendChild(buttonCell);
        table.appendChild(row);
    });

    content.appendChild(table);

    // 更新UI元素
    if (badge) {
        badge.textContent = messageQueue.length > 99 ? '99+' : messageQueue.length;
    }
    if (moreLink) {
        moreLink.style.display = messageQueue.length > 3 ? 'block' : 'none';
    }
    if (title) {
        title.textContent = `消息通知 (${messageQueue.length}条)`;
    }

    // 如果没有消息了，自动关闭
    if (messageQueue.length === 0) {
        setTimeout(() => {
            closeNotification();
        }, 2000);
    }
}

// 从队列中移除消息
function removeMessageFromQueue(messageId) {
    console.log('移除消息, ID:', messageId);

    // 根据消息ID找到索引
    const messageIndex = messageQueue.findIndex(msg => {
        if (Array.isArray(msg)) {
            return msg[0] === messageId;
        }
        return false;
    });

    if (messageIndex !== -1) {
        messageQueue.splice(messageIndex, 1);
        console.log('移除后队列:', messageQueue);
        updateNotificationContent();
    }

    updateIndicatorBadge(); // 更新徽章显示
}

// 关闭通知
function closeNotification() {
    const notification = document.getElementById('custom-notification');
    if (notification && notification.parentNode) {
        document.body.removeChild(notification);
    }
    isNotificationOpen = false;
    // messageQueue = [];
    // updateIndicatorBadge(); // 更新徽章显示
}