document.addEventListener('DOMContentLoaded', function () {
    let chat_data = {};
    let chat_history = {};
    let ws = null;
    let selected_chat = 0;
    let chat_inputs = {};
    let input = document.getElementById('message-input-text');
    let btn_take = document.getElementById('btn-take');
    let btn_drop = document.getElementById('btn-drop');
    let btn_finish = document.getElementById('btn-finish');
    let btn_read = document.getElementById('btn-read');
    let input_group = document.getElementById('input-group');

    let page_title = document.title;
    let title_notification = 0;
    let title_updater;

    function update_title() {
        document.title = title_notification ? 'Новое сообщение' : page_title;
        title_notification = title_notification ? 0 : 1;
    }

    document.onmousemove = function () {
        if (typeof title_updater === 'number') {
            clearInterval(title_updater);
            title_updater = undefined;
            document.title = page_title;
        }
    }

    function get_photo(chat_id) {
        let photo = document.createElement('img');
        photo.alt = '';
        photo.src = chat_data[chat_id]['photo'] ? chat_data[chat_id]['photo'] : '';
        return photo;
    }

    function get_chat_operator(chat_id) {
        if (chat_data[chat_id]['oper_name']) {
            return `Оператор: ${chat_data[chat_id]['oper_name']}`
        } else if (chat_data[chat_id]['support_mode'] === true) {
            return 'Нет оператора!'
        } else {
            return 'Проблем нет'
        }
    }

    function get_chat_support_mode_icon(chat_id) {
        return chat_data[chat_id]['support_mode'] === false ? '<i class="fa fa-circle online"></i>' : '<i class="fa fa-circle offline"></i>'
    }

    function get_chat_support_mode_oper_icon(chat_id) {
        let icon = document.createElement('i');
        if (chat_data[chat_id]['support_mode'] === true) {
            icon.classList.add('fa', 'fa-circle', 'offline');
            icon.style.marginLeft = '3px';
        }
        return icon
    }

    function get_chat_about(chat_id) {
        let name_block = document.createElement('div');
        name_block.classList.add('name', 'text-left');
        name_block.innerHTML = chat_data[chat_id]['first_name'];
        name_block.appendChild(get_chat_support_mode_oper_icon(chat_id));
        let date = document.createElement('div');
        date.classList.add('status', 'text-left', 'last-update-datetime');
        date.innerText = `${chat_data[chat_id]['time']} ${chat_data[chat_id]['date']}`;
        let about = document.createElement('div');
        about.classList.add('about', 'col');
        about.appendChild(name_block);
        about.appendChild(date);
        return about;
    }

    function get_chat_read_eye(chat_id) {
        let block = document.createElement('div');
        block.classList.add('col-1', 'text-right');
        block.innerHTML = chat_data[chat_id]['read'] ? '' : '<i class="fa fa-eye-slash" ></i>';
        return block
    }

    btn_take.onclick = function () {
        take_chat_start();
    }

    function take_chat_start() {
        ws.send(JSON.stringify({'action': 'take_chat', 'data': selected_chat}));
    }

    function oper_take_chat_end(data) {
        chat_data[data['chat_id']]['oper_id'] = data['oper_id'];
        chat_data[data['chat_id']]['oper_name'] = data['oper_name'];
        new_selected_chat_status(data['chat_id']);
        if (data['oper_id'] === get_cookie('irobot_oper_id', true)) {
            show_message_buttons(true);
        } else {
            show_message_buttons(false);
        }
    }

    btn_drop.onclick = function () {
        drop_chat_start();
    }

    btn_finish.onclick = function () {
        finish_support_start();
    }

    btn_finish.onmouseout = function () {
        reset_finish_button();
    }

    btn_read.onclick = function () {
        read_chat();
    }

    function drop_chat_start() {
        ws.send(JSON.stringify({'action': 'drop_chat', 'data': selected_chat}));
    }

    function finish_support_start() {
        if (btn_finish.classList.contains('btn-outline-success')) {
            btn_finish.classList.replace('btn-outline-success', 'btn-outline-warning');
            btn_finish.getElementsByTagName('span')[0].innerText = 'Точно завершить?';
        } else {
            ws.send(JSON.stringify({'action': 'finish_support', 'data': selected_chat}));
        }
    }

    function reset_finish_button() {
        btn_finish.classList.replace('btn-outline-warning', 'btn-outline-success');
        btn_finish.getElementsByTagName('span')[0].innerText = 'Завершить поддержку';
    }

    function read_chat() {
        chat_data[selected_chat]['read'] = true;
        check_read_icon(selected_chat);
        check_read_btn(selected_chat);
        ws.send(JSON.stringify({'action': 'read_chat', 'data': selected_chat}));
    }

    function oper_drop_chat_end(data) {
        chat_data[data['chat_id']]['oper_id'] = null;
        chat_data[data['chat_id']]['oper_name'] = null;
        new_selected_chat_status(data['chat_id']);
        if (selected_chat === data['chat_id']) {
            show_message_buttons(false);
        }
    }

    function show_message_buttons(flag) {
        if (flag) {
            btn_take.classList.remove('show');
            btn_drop.classList.add('show');
            btn_finish.classList.add('show');
            btn_read.classList.add('show');
            input_group.classList.add('show');
        } else {
            btn_take.classList.add('show');
            btn_drop.classList.remove('show');
            btn_finish.classList.remove('show');
            btn_read.classList.remove('show');
            input_group.classList.remove('show');
        }
    }

    function load_saved_input_value(chat_id) {
        input.disabled = false;
        if (chat_inputs[chat_id]) {
            input.value = chat_inputs[chat_id];
        } else {
            input.value = '';
        }
    }

    function new_selected_chat_status(chat_id) {
        if (selected_chat === chat_id) {
            let selected_chat_name = document.getElementById('selected-chat');
            let small = selected_chat_name.getElementsByTagName('small');
            small[0].innerText = get_chat_operator(chat_id);
            small[1].innerHTML = get_chat_support_mode_icon(chat_id);
            small[1].innerHTML += chat_data[chat_id]['support_mode'] === true ? ' Требуется поддержка!' : 'Поддержка не требуется';
        }
    }

    function new_selected_chat_name(chat_id) {
        let selected_chat_name = document.getElementById('selected-chat');
        let name_block = selected_chat_name.getElementsByTagName('h6')[0];
        name_block.innerHTML = chat_data[chat_id]['first_name'];
        for (let i in chat_data[chat_id]['accounts']) {
            let span = document.createElement('span');
            span.classList.add('chat-account');
            span.innerText = `[${chat_data[chat_id]['accounts'][i]}]`;
            name_block.appendChild(span);
        }
    }

    function new_selected_chat_photo(chat_id) {
        let photo = chat_data[chat_id]['photo'];
        document.getElementById('selected-photo').src = photo ? photo : '';
    }

    function select_chat(chat_id) {
        if (selected_chat !== chat_id) {
            selected_chat = chat_id;
            document.getElementById('chat-history').innerHTML = '';
            load_saved_input_value(chat_id);
            new_selected_chat_photo(chat_id);
            new_selected_chat_name(chat_id);
            new_selected_chat_status(chat_id);
        }
    }

    function load_chat(chat_id) {
        let message_id = ('first_message_id' in chat_data[chat_id]) ? chat_data[chat_id]['first_message_id'] : 0;
        if (chat_history[chat_id] === undefined) {
            let data = {'action': 'get_chat', 'data': {'chat_id': chat_id, 'message_id': message_id}};
            ws.send(JSON.stringify(data));
        } else {
            let old_messages = {'messages': chat_history[chat_id], 'chat_id': chat_id, 'first_message_id': message_id};
            fill_block_of_chat_history(old_messages, true);
        }
    }

    function is_my_chat_check(chat_id) {
        if (chat_data[chat_id]['oper_id'] === get_cookie('irobot_oper_id', true)) {
            show_message_buttons(true);
        } else {
            show_message_buttons(false);
        }
    }

    function get_chat_block(chat_id) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'chat-item', 'row', 'align-items-center');
        li.id = `chat-${chat_id}`;
        li.appendChild(get_photo(chat_id));
        li.appendChild(get_chat_about(chat_id));
        li.appendChild(get_chat_read_eye(chat_id));
        li.onclick = function () {
            if (!(li.classList.contains('active'))) {
                select_chat(chat_id);
                load_chat(chat_id);
                check_read_btn(chat_id);
                is_my_chat_check(chat_id);
                let chats = document.getElementsByClassName('chat-item');
                for (let i = 0; i < chats.length; i++) {
                    chats[i].classList.remove('active');
                }
                li.classList.add('active');
            }
        }
        return li;
    }

    function save_data_of_chats(chats, accounts) {
        for (let i in chats) {
            chat_data[chats[i]['chat_id']] = chats[i];
        }
        for (let chat_id in accounts) {
            chat_data[chat_id]['accounts'] = accounts[chat_id];
        }
    }

    function fill_chat_list(data) {
        let chat_list_block = document.getElementById('chat-list');
        save_data_of_chats(data['chats'], data['accounts']);
        chat_list_block.innerHTML = '';
        for (let i in data['chats']) {
            let chat = get_chat_block(data['chats'][i]['chat_id'])
            chat_list_block.appendChild(chat);
        }
        if (selected_chat !== 0) {
            document.getElementById(`chat-${selected_chat}`).classList.add('active');
            load_chat(selected_chat);
        }
    }

    function create_message_date(msg) {
        let message_data = document.createElement('div');
        message_data.classList.add('text-center');
        let span = document.createElement('span');
        span.innerText = msg['date'];
        message_data.appendChild(span)
        return message_data;
    }

    function get_message_content(msg) {
        if (msg['content_type'] === 'text') {
            return msg['content']['text']
        } else {
            return JSON.stringify(msg['content'])
        }
    }

    function add_message_name(name) {
        let header = document.createElement('div');
        header.classList.add('message-name');
        header.innerHTML = name
        return header
    }

    function add_message_time(time) {
        let time_small = document.createElement('small');
        time_small.classList.add('message-time', 'pl-2');
        time_small.innerText = time;
        return time_small
    }

    function create_message(msg) {
        let message = document.createElement('div');
        message.classList.add('message');
        if (msg['oper_id'] === null) {
            message.classList.add('other-message', 'float-right');
            message.appendChild(add_message_name(chat_data[selected_chat]['first_name']));
        } else if (msg['oper_id'] !== get_cookie('irobot_oper_id', true)) {
            message.classList.add('other-oper-message', 'float-right');
            message.appendChild(add_message_name(`Оператор: ${msg['oper_name']}`));
        } else {
            message.classList.add('my-message', 'float-left');
        }
        message.innerHTML += get_message_content(msg);
        message.appendChild(add_message_time(msg['time']));
        return message;
    }

    function add_chat_message(msg, to_start=false) {
        let li = document.createElement('li');
        li.classList.add('clearfix');
        li.appendChild(create_message(msg));
        let chat = document.getElementById('chat-history');
        if (to_start) {
            insert_into_chat_end(li);
        } else {
            chat.appendChild(li);
        }
        li.scrollIntoView(false);
    }

    function add_message_date(msg, to_start=false) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'message-date');
        li.appendChild(create_message_date(msg));
        let chat = document.getElementById('chat-history');
        if (to_start)
            insert_into_chat_end(li);
        else
            chat.appendChild(li);
    }

    function fill_block_of_chat_history(data, skip_saving=false) {
        let chat_id = data['chat_id'];
        let messages = data['messages'];
        let id_list = data['id_list'];
        let ts_list = data['ts_list'];
        let first_message_id = Math.min.apply(Math, id_list);
        if (!skip_saving)
            save_data_of_chat_messages(chat_id, messages);
        chat_data[chat_id]['first_message_id'] = first_message_id;
        for (let timestamp in ts_list) {
            let message_id = ts_list[timestamp];
            if ((message_id === first_message_id) ||
                (message_id - 1 in messages && messages[message_id - 1]['date'] !== messages[message_id]['date'])) {
                add_message_date(messages[message_id]);
            }
            add_chat_message(messages[message_id]);
        }
        add_message_download_link(chat_id);
    }

    function insert_into_chat_end(element) {
        let chat = document.getElementById('chat-history');
        chat.insertBefore(element, chat.getElementsByTagName('li')[0])
    }

    function save_data_of_chat_messages(chat_id, messages) {
        for (let message_id in messages) {
            let mid = parseInt(message_id);
            if (chat_id in chat_history) {
                chat_history[chat_id][mid] = messages[message_id];
            } else {
                chat_history[chat_id] = {};
                chat_history[chat_id][mid] = messages[message_id];
            }
        }
    }

    function add_new_messages_before(data) {
        let chat_id = data['chat_id'];
        let messages = data['messages'];
        chat_data[chat_id]['first_message_id'] = Math.min.apply(Math, data['id_list']);
        save_data_of_chat_messages(chat_id, messages);
        let chat = document.getElementById('chat-history');
        clean_load_links_into_chat(chat);
        let keys = Object.keys(messages).reverse();
        delete_chat_date_if_one_date(messages[keys[0]]);
        for (let i = 0; i < keys.length; i++) {
            if (i > 0 && messages[keys[i]]['date'] !== messages[keys[i - 1]]['date'])
                add_message_date(messages[keys[i - 1]], true);
            add_chat_message(messages[keys[i]], true);
        }
        add_message_date(messages[keys[keys.length - 1]], true);
        add_message_download_link(chat_id);
    }

    function delete_chat_date_if_one_date(message) {
        let first_msg = document.getElementById('chat-history').getElementsByTagName('li')[0];
        if (first_msg.classList.contains('message-date') && message['date'] === first_msg.innerText)
            first_msg.remove()
    }

    function clean_load_links_into_chat(chat) {
        let messages = chat.getElementsByTagName('li');
        if (messages.length > 0) {
            for (let i in messages) {
                if (typeof messages[i] === 'object' && messages[i].classList.contains('load-link')) {
                    messages[i].remove();
                }
            }
        }
    }

    function add_message_download_link(chat_id) {
        if (chat_data[chat_id]['first_message_id'] > chat_data[chat_id]['min_message_id']) {
            let link = document.createElement('a');
            link.onclick = function () {
                load_messages(chat_id, chat_data[chat_id]['first_message_id']);
            }
            link.href = '#';
            link.innerText = `Загрузить ещё ${chat_data[chat_id]['first_message_id']}`;
            let block = document.createElement('li');
            block.classList.add('text-center', 'load-link');
            block.appendChild(link);
            insert_into_chat_end(block);
        }
    }

    function load_messages(chat_id, first_message_id) {
        let data = {'chat_id': chat_id, 'message_id': first_message_id};
        ws.send(JSON.stringify({'action': 'load_messages', 'data': data}));
    }

    function get_message(msg) {
        let messages = {};
        messages[msg['message_id']] = msg;
        if (msg['chat_id'] in chat_data) {
            if (msg['oper_id'] === null)
                chat_data[msg['chat_id']]['support_mode'] = true;
            new_selected_chat_status(msg['chat_id']);
            if (msg['chat_id'] in chat_history)
                save_data_of_chat_messages(msg['chat_id'], messages);
            update_chat_in_list(msg);
            if (selected_chat === msg['chat_id'])
                add_chat_message(msg);
            play_audio('/static/audio/mp3/minecraft-drop-block-sound-effect.mp3');
        } else {
            force_get_chats();
            play_audio('/static/audio/mp3/minecraft-level-up-sound-effect.mp3');
        }
        send_notification('IroBot Admin - новое сообщение', get_message_content(msg));
    }

    function send_notification(title, text) {
        if (typeof title_updater !== 'number')
            title_updater = setInterval(update_title, 1000);
        window.focus();
        if (('Notification' in window && document.hidden)) {
            let options = {body: text, icon: '/static/img/png/logo.png', dir: 'auto'};
            if (Notification.permission === 'granted') {
                new Notification(title, options);
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission()
                    .then(permission => {
                        if (permission === 'granted') {
                            new Notification(title, options);
                        }
                    })
                    .catch(e => {console.error(e)});
            }
        }
    }

    function play_audio(url) {
        let audio = new Audio(url);
        audio.play().then().catch();
    }

    function update_chat_in_list(msg) {
        new_chat_datetime(msg['chat_id'], msg['date'], msg['time']);
        chat_data[msg['chat_id']]['read'] = !!msg['oper_id'];
        check_read_icon(msg['chat_id']);
        check_read_btn(msg['chat_id']);
    }

    function new_chat_datetime(chat_id, date, time) {
        let about = document.getElementById(`chat-${chat_id}`);
        about = about.getElementsByClassName('about')[0].getElementsByTagName('div');
        about[1].innerText = `${time} ${date}`;
    }

    function check_read_icon(chat_id) {
        let chat_block = document.getElementById(`chat-${chat_id}`);
        chat_block.getElementsByClassName('col-1')[0].remove();
        chat_block.appendChild(get_chat_read_eye(chat_id));
    }

    function check_read_btn(chat_id) {
        btn_read.disabled = chat_data[chat_id]['read'];
    }

    function request_permission() {
        if (('Notification' in window)) {
            if (Notification.permission === 'default') {
                Notification.requestPermission().then().catch();
            }
        }
    }

    setTimeout(request_permission, 1000);

    function force_get_chats() {
        ws.send(JSON.stringify({'action': 'get_chats'}));
    }

    function finish_support_end(data) {
        fill_chat_list(data['chats']);
        new_selected_chat_status(data['chat_id']);
        if (data['oper_id'] === get_cookie('irobot_oper_id', true) && selected_chat === data['chat_id']) {
            reset_finish_button();
            show_message_buttons(false);
        }
    }

    for (let i in document.getElementsByClassName('show-under-mouse')) {
        let btn = document.getElementsByClassName('show-under-mouse')[i];
        btn.onmouseenter = function () {
            btn.getElementsByTagName('span')[0].classList.add('show');
        }

        btn.onmouseleave = function () {
            btn.getElementsByTagName('span')[0].classList.remove('show');
        }
    }

    input.onkeyup = function (event) {
        if (event.key === 'Enter') {
            send_message();
        }
    }

    input.oninput = function () {
        chat_inputs[selected_chat] = input.value;
    }

    function send_message() {
        if (input.value.length > 0) {
            let data = {'chat_id': selected_chat, 'text': input.value};
            ws.send(JSON.stringify({'action': 'send_message', 'data': data}));
            input.value = '';
            chat_inputs[selected_chat] = '';
        }
    }

    function connectWS() {
        if (!get_cookie('irobot_access_token'))
            return;
        let server_host = document.getElementById('server-host').value;
        let root_path = document.getElementById('root-path');
        root_path = root_path ? root_path : '';
        ws = new WebSocket(`ws://${server_host}${root_path}/ws?access_token=${get_cookie('irobot_access_token')}`);
        ws.onclose = function () {
            setTimeout(connectWS, 1500);
        }
        ws.onmessage = function (event) {
            let command = JSON.parse(event.data)['action'];
            let data = JSON.parse(event.data)['data'];
            console.log(`${command}:`, data);
            if (command === 'get_chats')
                fill_chat_list(data);
            else if (command === 'get_chat')
                fill_block_of_chat_history(data);
            else if (command === 'load_messages')
                add_new_messages_before(data);
            else if (command === 'get_message')
                get_message(data);
            else if (command === 'take_chat')
                oper_take_chat_end(data);
            else if (command === 'drop_chat')
                oper_drop_chat_end(data);
            else if (command === 'finish_support')
                finish_support_end(data);
        }
    }

    connectWS();
});