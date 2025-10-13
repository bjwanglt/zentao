/**
 * 优化版确认对话框
 * @param {Object} options 配置选项
 * @returns {Promise} 返回Promise，用户确认时resolve(true)，取消时resolve(false)
 */
function showConfirm(options = {}) {
    return new Promise((resolve) => {
        // 默认配置
        const config = {
            title: '确认操作',
            message: '您确定要执行此操作吗？',
            confirmText: '确认',
            cancelText: '取消',
            type: 'warning', // warning, success, danger
            confirmButtonClass: 'confirm-btn-confirm',
            ...options
        };

        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';

        // 创建对话框
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog';

        // 图标映射
        const iconMap = {
            warning: '⚠️',
            success: '✓',
            danger: '❗'
        };

        // 对话框HTML结构
        dialog.innerHTML = `
            <div class="confirm-header">
                <div class="confirm-icon ${config.type}">
                    ${iconMap[config.type] || iconMap.warning}
                </div>
                <h3 class="confirm-title">${config.title}</h3>
            </div>
            <div class="confirm-message">${config.message}</div>
            <div class="confirm-footer">
                <button type="button" class="confirm-btn confirm-btn-cancel">${config.cancelText}</button>
                <button type="button" class="confirm-btn ${config.confirmButtonClass}">${config.confirmText}</button>
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // 获取按钮元素
        const cancelBtn = overlay.querySelector('.confirm-btn-cancel');
        const confirmBtn = overlay.querySelector(`.${config.confirmButtonClass}`);

        // 显示对话框
        setTimeout(() => {
            overlay.classList.add('active');
        }, 10);

        // 确认按钮点击事件
        confirmBtn.addEventListener('click', () => {
            closeDialog();
            resolve(true);
        });

        // 取消按钮点击事件
        cancelBtn.addEventListener('click', () => {
            closeDialog();
            resolve(false);
        });

        // 点击遮罩层关闭
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeDialog();
                resolve(false);
            }
        });

        // ESC键关闭
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                closeDialog();
                resolve(false);
                document.removeEventListener('keydown', handleKeydown);
            }
        };
        document.addEventListener('keydown', handleKeydown);

        // 关闭对话框函数
        function closeDialog() {
            overlay.classList.remove('active');
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    });
}

/**
 * 快捷方法 - 危险操作确认
 */
function showDangerConfirm(message, title = '危险操作') {
    return showConfirm({
        title,
        message,
        type: 'danger',
        confirmButtonClass: 'confirm-btn-danger'
    });
}

/**
 * 快捷方法 - 成功操作确认
 */
function showSuccessConfirm(message, title = '操作确认') {
    return showConfirm({
        title,
        message,
        type: 'success',
        confirmButtonClass: 'confirm-btn-success'
    });
}