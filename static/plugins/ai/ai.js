function init_ai_events() {
    // 切换折叠/展开
    $('#ai-toggle-chat').click(function () {
        const $chatBox = $('#ai-chat-box');
        const $input = $('#ai-chat-input');
        const $icon = $(this).find('i');

        $chatBox.toggleClass('collapsed');
        $input.toggleClass('collapsed');

        if ($chatBox.hasClass('collapsed')) {
            $icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
        } else {
            $icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
            // 展开时滚动到底部
            scrollToBottom();
        }
    });

    // 清空对话
    $('#ai-clear-chat').click(function () {
        if (confirm('确定要清空对话记录吗？')) {
            $('#ai-chat-messages').html(`
                        <div class="empty-state">
                            <i class="fa fa-comments"></i>
                            <div>我是您的AI助手，有什么可以帮您的？</div>
                        </div>
                    `);
        }
    });

    // 发送消息
    $('#ai-send-btn').click(sendMessage);

    // 回车发送
    $('#ai-question').keypress(function (e) {
        if (e.which === 13 && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 输入框获取焦点时自动展开
    $('#ai-question').focus(function () {
        if ($('#ai-chat-box').hasClass('collapsed')) {
            $('#ai-chat-box').removeClass('collapsed');
            $('#ai-chat-input').removeClass('collapsed');
            $('#ai-toggle-chat i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
        }
    });
}

// 发送消息 获取响应
function sendMessage() {
    const question = $('#ai-question').val().trim();
    if (!question) return;

    // 移除空状态
    if ($('#ai-chat-messages .empty-state').length) {
        $('#ai-chat-messages').empty();
    }

    appendMessage(question, false);
    $('#ai-question').val('');
    $('#ai-send-btn').prop('disabled', true);

    const typingId = showTypingIndicator();

    fetch('/account/ask_ai/', {
        method: "POST",
        body: JSON.stringify({question}),
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        credentials: "same-origin"
    }).then(response => {
        // 移除打字指示器
        $(`#${typingId}`).remove();

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let $aiMsg = null;

        function read() {
            reader.read().then(({done, value}) => {
                if (done) {
                    $('#ai-send-btn').prop('disabled', false);
                    return;
                }

                const chunk = decoder.decode(value, {stream: true});

                if (!$aiMsg) {
                    $aiMsg = $('<div class="message ai"></div>').appendTo('#ai-chat-messages');
                }

                $aiMsg.text($aiMsg.text() + chunk);
                scrollToBottom();
                read();
            });
        }

        read();
    }).catch(error => {
        $(`#${typingId}`).remove();
        appendMessage('抱歉，发生了错误，请重试。', true);
        $('#ai-send-btn').prop('disabled', false);
        console.error('AI请求错误:', error);
    });
}

function appendMessage(content, isAI = true) {
    const $container = $('#ai-chat-messages');
    const $msg = $('<div class="message"></div>')
        .addClass(isAI ? 'ai' : 'user')
        .text(content);

    $container.append($msg);
    scrollToBottom();
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const $typing = $(`
                <div class="message ai" id="${id}">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `);
    $('#ai-chat-messages').append($typing);
    scrollToBottom();
    return id;
}

function scrollToBottom() {
    const $container = $('#ai-chat-messages');
    $container.scrollTop($container.prop("scrollHeight"));
}

function appendMessage(content, isAI = true) {
    const $container = $('#ai-chat-messages');
    const $msg = $('<div></div>').text(content).css({
        'margin-bottom': '8px',
        'white-space': 'pre-wrap',
        'background': isAI ? '#f1f0f0' : '#007bff',
        'color': isAI ? '#000' : '#fff',
        'padding': '6px 10px',
        'border-radius': '8px',
        'align-self': isAI ? 'flex-start' : 'flex-end'
    });
    $container.append($msg);
    $container.scrollTop($container.prop("scrollHeight"));
}

