function showAlert(type, title, message, duration = 3000) {
    const alertEl = document.createElement('div');
    alertEl.className = `custom-alert alert-${type}`;

    let icon = 'i';
    switch(type) {
        case 'success': icon = '✓'; break;
        case 'error': icon = '×'; break;
        case 'warning': icon = '!'; break;
        case 'info': icon = 'i'; break;
    }

    alertEl.innerHTML = `
        <div class="alert-content">
            <div class="alert-icon">${icon}</div>
            <div class="alert-text">
                <div class="alert-title">${title}</div>
                <div class="alert-message">${message ? message : ''}</div>
            </div>
            <button class="alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;

    document.body.appendChild(alertEl);

    setTimeout(() => alertEl.classList.add('show'), 10);

    if (duration > 0) {
        setTimeout(() => {
            alertEl.classList.remove('show');
            setTimeout(() => alertEl.remove(), 300);
        }, duration);
    }

    return alertEl;
}

function showSuccess(message, title = '操作成功') {
    return showAlert('success', title, message);
}

function showError(message, title = '操作失败') {
    return showAlert('error', title, message, 4000);
}

function showWarning(message, title = '警告') {
    return showAlert('warning', title, message, 4000);
}

function showInfo(message, title = '提示') {
    return showAlert('info', title, message);
}