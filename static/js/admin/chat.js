function concat_and_sort_arrays(arr1, arr2) {
    return arr1.concat(arr2).filter((value, index, a) => {
        return a.indexOf(value) === index;
    }).sort((a, b) => a - b);
}


function concat_and_sort_objects(obj1, obj2) {
    for (let i in obj2)
        if (!(i in obj1))
            obj1[i] = obj2[i];
    return Object.keys(obj1).sort().reduce((r, k) => (r[k] = obj1[k], r), {});
}


function reverse_object(obj) {
    return Object.keys(obj).reverse().reduce((r, k) => (r[k] = obj[k], r), {});
}


function array_remove(arr, value) {
    return arr.filter(function(ele){
        return ele !== value;
    });
}


class Chat {
    selector;
    control;
    history;

    constructor(url, root_path) {
        this.url = url;
        this.chat_data = new Object({});
        this.selected_chat = 0;
        this.connection = new WSConnection();
        this.notification = new MyNotification(root_path);
        this.selector = new ChatSelector(this);
        this.control = new ChatControlPanel(this);
        this.history = new ChatHistory(this);
        this.chat_input = new ChatTextInput(this);
    }

    start() {
        // connect to server and enable chat
        this.connection.run(this);
        setTimeout(this.notification.request_permission, 3000);
    }

    run_procedure(command, data) {
        console.log(`WebSocket: ${command} >>>`, data);
        if (command === 'get_chats')
            this.get_chats(data);
        else if (command === 'get_chat')
            this.history.get_chat_history(data);
        else if (command === 'load_messages')
            this.history.get_chat_history(data, true);
        else if (command === 'get_message')
            this.get_new_message(data);
        else if (command === 'take_chat')
            this.oper_take_chat_end(data);
        else if (command === 'drop_chat')
            this.oper_drop_chat_end(data);
        else if (command === 'finish_support')
            this.finish_support_end(data);
        else
            console.log('WebSocket unknown command:', command, data);
    }

    get_chats(data) {
        this.save_chat_data(data);
        this.selector.add_chats_to_selector(data);
        this.add_chat_onclick_handler();
        if (this.selected_chat !== 0) {
            this.selector.get_chat(this.selected_chat).classList.add('active');
            this.history.load_chat(this.selected_chat);
        }
    }

    save_chat_data(chats) {
        for (let i in chats)
            this.chat_data[chats[i]['chat_id']] = chats[i];
    }

    add_chat_onclick_handler() {
        for (let i = 0; i < this.selector.chat_list.length; i ++) {
            let li = this.selector.chat_list[i];
            li.onclick = () => {
                let chat_id = parseInt(li.id);
                if (this.selected_chat !== chat_id) {
                    this.selector.deactivate_chats();
                    li.classList.add('active');
                    this.control.select_chat(chat_id);
                    this.history.load_chat(chat_id);
                    this.chat_input.load_saved_input_value(chat_id);
                    this.selected_chat = chat_id;
                }
            }
        }
    }

    get_new_message(message) {
        if (!(message.chat_id in this.chat_data))
            this.force_get_chats();
        if (message.chat_id in this.history.chat_history && message.message_id in this.history.chat_history[message.chat_id])
            return;
        const data = this.get_message_data_to_save(message);
        this.history.save_data_of_chat_messages(message.chat_id, data.messages, data.id_list, data.ts_list);
        const res = this.history.add_new_message(message, this.selected_chat);
        this.selector.update_chat_in_list(message);
        if (this.selected_chat === message.chat_id) {
            this.control.new_selected_chat_status(message.chat_id);
            this.control.check_read_btn(message.chat_id);
        }
        if (res[0] === 'new_message') {
            this.notification.play_audio('/static/audio/mp3/minecraft-drop-block-sound-effect.mp3');
        } else if (res[0] === 'new chat') {
            this.notification.play_audio('/static/audio/mp3/minecraft-level-up-sound-effect.mp3');
        }
        this.notification.send_notification('IroBot Admin - новое сообщение', res[1]);
        this.check_message_list(message.chat_id);
    }

    force_get_chats() {
        this.connection.send({'action': 'get_chats'});
    }

    get_message_data_to_save(message) {
        let messages = {};
        messages[message.message_id] = message;
        let ts_list = {};
        ts_list[message.timestamp] = message.message_id;
        return {messages: messages, id_list: [message.message_id], ts_list: ts_list};
    }

    check_message_list(chat_id) {
        let messages = Object.keys(this.history.chat_history[chat_id]);
        this.connection.send({'action': 'check_messages', 'data': {'list': messages, 'chat_id': chat_id}});
    }

    oper_take_chat_end(data) {
        this.chat_data[data['chat_id']]['oper_id'] = data['oper_id'];
        this.chat_data[data['chat_id']]['oper_name'] = data['oper_name'];
        this.control.new_selected_chat_status(data['chat_id']);
        if (data['oper_id'] === get_cookie('irobot_oper_id', true)) {
            this.control.show_message_buttons(true);
        } else {
            this.control.show_message_buttons(false);
        }
    }

    oper_drop_chat_end(data) {
        this.chat_data[data['chat_id']]['oper_id'] = null;
        this.chat_data[data['chat_id']]['oper_name'] = null;
        this.control.new_selected_chat_status(data['chat_id']);
        if (this.selected_chat === data['chat_id']) {
            this.control.show_message_buttons(false);
        }
    }

    finish_support_end(data) {
        this.get_chats(data['chats']);
        this.control.new_selected_chat_status(data['chat_id']);
        if (data['oper_id'] === get_cookie('irobot_oper_id', true) && this.selected_chat === data['chat_id']) {
            this.control.show_message_buttons(false);
        }
    }
}


let connection_list = [];


class WSConnection {

    constructor() {
        this.socket = null;
    }

    run(chat) {
        this.connect_to_server(this, chat);
        setInterval(this.connect_to_server, 2000, this, chat);
    }

    connect_to_server(self, chat) {
        if ((self.socket !== null && self.socket.readyState === WebSocket.OPEN)) {
            return;
        }

        self.socket = new WebSocket(chat.url);

        self.socket.onopen = () => {
            console.log('WebSocket: connected');
            connection_list.push(self.socket);
            if (connection_list.length > 1)
                window.location.reload();
        }
        self.socket.onerror = () => {
            self.socket.close();
        }
        self.socket.onclose = () => {
            connection_list = array_remove(connection_list, self.socket);
            self.socket = null;
        }
        self.socket.onmessage = (event) => {
            let command = JSON.parse(event.data)['action'];
            let data = JSON.parse(event.data)['data'];
            chat.run_procedure(command, data);
        }
    }

    send(data) {
        if (this.socket !== null && this.socket.readyState === WebSocket.OPEN)
            this.socket.send(JSON.stringify(data));
    }
}


class MyNotification {
    title_updater;

    constructor(root_path) {
        this.root_path = root_path;
        this.page_title = document.title;
        this.title_notification = 0;
        this.stop_title_updater_handler();
    }

    stop_title_updater_handler() {
        document.onmousemove =  () => {
            if (typeof this.title_updater === 'number') {
                clearInterval(this.title_updater);
                this.title_updater = undefined;
                document.title = this.page_title;
            }
        }
    }

    update_title(title) {
        document.title = this.title_notification ? 'Новое сообщение' : title;
        this.title_notification = this.title_notification ? 0 : 1;
    }

    play_audio(url) {
        let audio = new Audio(this.root_path + url);
        audio.play().then().catch();
    }

    send_notification(title, text) {
        if (typeof this.title_updater !== 'number')
            this.title_updater = setInterval(this.update_title, 1000, this.page_title);
        if (('Notification' in window && document.hidden)) {
            let options = {body: text, icon: 'static/img/png/logo.png', dir: 'auto'};
            if (Notification.permission === 'granted') {
                new Notification(title, options);
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission()
                    .then(permission => {
                        if (permission === 'granted') {
                            let notif = new Notification(title, options);
                            notif.onclick = () => { window.focus(); }
                        }
                    })
                    .catch(e => {console.error(e)});
            }
        }
    }

    request_permission() {
        if (('Notification' in window)) {
            if (Notification.permission === 'default') {
                Notification.requestPermission().then().catch();
            }
        }
    }
}


class ChatSelector {

    constructor(chat) {
        this.block = document.getElementById('chat-list');
        this.connection = chat.connection;
        this.chat_data = chat.chat_data;
        // todo search field
        // todo all chats not only support
    }

    add_chats_to_selector(chats) {
        this.block.innerHTML = '';
        for (let i in chats) {
            this.block.appendChild(this.get_chat_block(chats[i]['chat_id']));
        }
    }

    get_chat_block(chat_id) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'chat-item', 'row', 'align-items-center');
        li.id = `${chat_id}`;
        li.appendChild(this.get_photo(chat_id));
        li.appendChild(this.get_chat_about(chat_id));
        li.appendChild(this.get_chat_read_eye(chat_id));
        return li;
    }

    get_photo(chat_id) {
        let photo = document.createElement('img');
        photo.alt = '';
        photo.src = this.chat_data[chat_id]['photo'] ? this.chat_data[chat_id]['photo'] : '';
        return photo;
    }

    get_chat_about(chat_id) {
        let name_block = document.createElement('div');
        name_block.classList.add('name', 'text-left');
        name_block.innerHTML = this.chat_data[chat_id]['first_name'];
        name_block.appendChild(this.get_chat_support_mode_oper_icon(chat_id));
        let date = document.createElement('div');
        date.classList.add('status', 'text-left', 'last-update-datetime');
        date.innerText = `${this.chat_data[chat_id]['time']} ${this.chat_data[chat_id]['date']}`;
        let about = document.createElement('div');
        about.classList.add('about', 'col');
        about.appendChild(name_block);
        about.appendChild(date);
        return about
    }

    get_chat_support_mode_oper_icon(chat_id) {
        let icon = document.createElement('i');
        if (this.chat_data[chat_id]['support_mode'] === true) {
            icon.classList.add('fa', 'fa-circle', 'offline');
            icon.style.marginLeft = '3px';
        }
        return icon
    }

    get_chat_read_eye(chat_id) {
        let block = document.createElement('div');
        block.classList.add('col-1', 'text-right');
        block.innerHTML = this.chat_data[chat_id]['read'] ? '' : '<i class="fa fa-eye-slash" ></i>';
        return block
    }

    get_chat(chat_id) {
        return document.getElementById(`${chat_id}`);
    }

    get chat_list() {
        return this.block.getElementsByClassName('chat-item');
    }

    deactivate_chats() {
        for (let i = 0; i < this.chat_list.length; i++) {
            this.chat_list[i].classList.remove('active');
        }
    }

    update_chat_in_list(message) {
        this.new_chat_datetime(message['chat_id'], message['date'], message['time']);
        this.chat_data[message['chat_id']]['support_mode'] = !!!message['oper_id'];
        this.chat_data[message['chat_id']]['read'] = !!message['oper_id'];
        this.check_read_icon(message['chat_id']);
        this.check_support_icon(message['chat_id']);
    }

    new_chat_datetime(chat_id, date, time) {
        let about = this.get_chat(chat_id);
        about = about.getElementsByClassName('about')[0].getElementsByTagName('div');
        about[1].innerText = `${time} ${date}`;
    }

    check_read_icon(chat_id) {
        let chat_block = document.getElementById(`${chat_id}`);
        chat_block.getElementsByClassName('col-1')[0].remove();
        chat_block.appendChild(this.get_chat_read_eye(chat_id));
    }

    check_support_icon(chat_id) {
        if (this.chat_data[chat_id].support_mode === true) {
            let name = this.get_chat(chat_id).getElementsByClassName('name')[0];
            let block = name.getElementsByClassName('fa');
            if (block.length === 0)
                name.appendChild(this.get_chat_support_mode_oper_icon(chat_id));
        }
    }
}


class ChatTextInput {

    constructor(chat) {
        this.input = document.getElementById('message-input-text');
        this.saved_input = new Object({});
        this.connection = chat.connection;
        this.chat = chat;
        this.chat_input_handler()
    }

    chat_input_handler() {
        this.input.onkeyup = (event) => {
            if (event.key === 'Enter') {
                this.send_message();
            }
        }
        this.saved_input.oninput = () => {
            this.saved_input[this.chat.selected_chat] = this.input.value;
        }
    }

    send_message() {
        if (this.input.value.length > 0) {
            let data = {'chat_id': this.chat.selected_chat, 'text': this.input.value};
            this.connection.send({'action': 'send_message', 'data': data});
            this.input.value = '';
            this.saved_input[this.chat.selected_chat] = '';
        }
    }

    load_saved_input_value(chat_id) {
        this.input.disabled = false;
        if (this.saved_input[chat_id]) {
            this.input.value = this.saved_input[chat_id];
        } else {
            this.input.value = '';
        }
    }
}


class ChatControlPanel {

    constructor(chat) {
        this.header = document.getElementById('selected-chat');
        this.photo = document.getElementById('selected-photo');
        this.input_group = document.getElementById('input-group');
        this.btn = {
            take: new ChatControlButton('btn-take'),
            drop: new ChatControlButton('btn-drop', true),
            read: new ChatControlButton('btn-read', true),
            finish: new ChatControlButton('btn-finish', true),
        }
        this.connection = chat.connection;
        this.chat_data = chat.chat_data;
        this.chat = chat;
        this.btn.take.add_handler(() => { this.take_chat_start() });
        this.btn.drop.add_handler(() => { this.drop_chat_start() });
        this.btn.read.add_handler(() => { this.read_chat_start() });
        this.btn.finish.add_handler(() => { this.finish_support_start() });
    }

    take_chat_start() {
        this.connection.send({'action': 'take_chat', 'data': this.chat.selected_chat});
    }

    drop_chat_start() {
        this.connection.send({'action': 'drop_chat', 'data': this.chat.selected_chat});
    }

    read_chat_start() {
        this.chat_data[this.chat.selected_chat]['read'] = true;
        this.check_read_btn(this.chat.selected_chat);
        this.connection.send({'action': 'read_chat', 'data': this.chat.selected_chat});
    }

    finish_support_start() {
        if (this.btn.finish.block.classList.contains('btn-outline-success')) {
            this.btn.finish.block.classList.replace('btn-outline-success', 'btn-outline-warning');
            this.btn.finish.block.getElementsByTagName('span')[0].innerText = 'Точно завершить?';
        } else {
            this.connection.send({'action': 'finish_support', 'data': this.chat.selected_chat});
            this.btn.finish.block.classList.replace('btn-outline-warning', 'btn-outline-success');
            this.btn.finish.block.getElementsByTagName('span')[0].innerText = 'Завершить поддержку';
        }
    }

    select_chat(chat_id) {
        this.new_selected_chat_photo(chat_id);
        this.new_selected_chat_name(chat_id);
        this.new_selected_chat_status(chat_id);
        this.check_is_my_chat(chat_id);
        this.check_read_btn(chat_id);
    }

    new_selected_chat_photo(chat_id) {
        let photo = this.chat_data[chat_id]['photo'];
        this.photo.src = photo ? photo : '';
    }

    new_selected_chat_name(chat_id) {
        let name_block = this.header.getElementsByTagName('h6')[0];
        name_block.innerHTML = this.chat_data[chat_id]['first_name'];
        for (let i in this.chat_data[chat_id]['accounts']) {
            let span = document.createElement('span');
            span.classList.add('chat-account');
            span.innerText = `[${this.chat_data[chat_id]['accounts'][i]}]`;
            name_block.appendChild(span);
        }
    }

    new_selected_chat_status(chat_id) {
        let small = this.header.getElementsByTagName('small');
        small[0].innerText = this.get_chat_operator(chat_id);
        small[1].innerHTML = this.get_chat_support_mode_icon(chat_id) + this.get_chat_support_mode(chat_id);
    }

    get_chat_operator(chat_id) {
        if (this.chat_data[chat_id]['oper_name']) {
            return `Оператор: ${this.chat_data[chat_id]['oper_name']}`
        } else if (this.chat_data[chat_id]['support_mode'] === true) {
            return 'Нет оператора!'
        } else {
            return 'Проблем нет'
        }
    }

    get_chat_support_mode_icon(chat_id) {
        return this.chat_data[chat_id]['support_mode'] === false ? '<i class="fa fa-circle online"></i>' : '<i class="fa fa-circle offline"></i>'
    }

    get_chat_support_mode(chat_id) {
        return this.chat_data[chat_id]['support_mode'] === true ? ' Требуется поддержка!' : 'Поддержка не требуется';
    }

    check_read_btn(chat_id) {
        this.btn.read.disabled = this.chat_data[chat_id]['read'];
    }

    check_is_my_chat(chat_id) {
        if (this.chat_data[chat_id]['oper_id'] === get_cookie('irobot_oper_id', true)) {
            this.show_message_buttons(true);
        } else {
            this.show_message_buttons(false);
        }
    }

    show_message_buttons(flag) {
        if (flag) {
            this.btn.take.hide();
            this.btn.drop.show();
            this.btn.finish.show();
            this.btn.read.show();
            this.input_group.classList.add('show');
        } else {
            this.btn.take.show();
            this.btn.drop.hide();
            this.btn.finish.hide();
            this.btn.read.hide();
            this.input_group.classList.remove('show');
        }
    }

}


class ChatControlButton {

    constructor(elem_id, show_under_cursor=false) {
        this.block = document.getElementById(elem_id);
        if (show_under_cursor)
            this.add_under_cursor_showing();
    }

    show() {
        this.block.classList.add('show');
    }

    hide() {
        this.block.classList.remove('show');
    }

    add_handler(func) {
        this.block.onclick = () => { func(); }
    }

    add_under_cursor_showing() {
        this.block.onmouseenter = () => {
            this.block.getElementsByTagName('span')[0].classList.add('show');
        }
        this.block.onmouseleave = () => {
            this.block.getElementsByTagName('span')[0].classList.remove('show');
        }
    }
}


class ChatHistory {

    constructor(chat) {
        this.chat_history = {};
        this.message_id_lists = {}
        this.message_ts_lists = {}
        this.block = document.getElementById('chat-history');
        this.connection = chat.connection;
        this.chat_data = chat.chat_data;
    }

    load_chat(chat_id) {
        this.clear();
        if (this.chat_history[chat_id] === undefined) {
            let message_id = ('first_message_id' in this.chat_data[chat_id]) ? this.chat_data[chat_id]['first_message_id'] : 0;
            let data = {'action': 'get_chat', 'data': {'chat_id': chat_id, 'message_id': message_id}};
            this.connection.send(data);
        } else {
            this.show_chat_history(chat_id);
        }
    }

    clear() {
        for (let chat_id in this.chat_history)
            for (let message_id in this.chat_history[chat_id])
                this.chat_history[chat_id][message_id]['showed'] = false;
        this.block.innerHTML = '';
    }

    get_chat_history(data, reverse=false) {
        this.save_data_of_chat_messages(data['chat_id'], data['messages'], data['id_list'], data['ts_list']);
        this.clean_load_links_into_chat();
        this.remove_first_date()
        this.show_chat_history(data['chat_id'], reverse);
    }

    save_data_of_chat_messages(chat_id, messages, id_list, ts_list) {
        for (let message_id in messages) {
            let mid = parseInt(message_id);
            if (!(chat_id in this.chat_history))
                this.chat_history[chat_id] = {};
            if (!(mid in this.chat_history[chat_id]))
                this.chat_history[chat_id][mid] = new ChatMessage(chat_id, messages[message_id], this.chat_data[chat_id]['first_name']);
        }
        if (!(chat_id in this.message_id_lists))
            this.message_id_lists[chat_id] = [];
        if (!(chat_id in this.message_ts_lists))
            this.message_ts_lists[chat_id] = {};
        if (this.message_id_lists[chat_id] === undefined) {
            this.message_id_lists[chat_id] = id_list;
            this.message_ts_lists[chat_id] = ts_list;
        } else {
            this.message_id_lists[chat_id] = concat_and_sort_arrays(this.message_id_lists[chat_id], id_list);
            this.message_ts_lists[chat_id] = concat_and_sort_objects(this.message_ts_lists[chat_id], ts_list);
        }
        this.chat_data[chat_id]['first_message_id'] = Math.min.apply(Math, this.message_id_lists[chat_id]);
        this.message_ts_lists[chat_id] = concat_and_sort_objects(this.message_ts_lists[chat_id], ts_list);
    }

    clean_load_links_into_chat() {
        let messages = this.block.getElementsByTagName('li');
        if (messages.length > 0)
            for (let i in messages)
                if (typeof messages[i] === 'object' && messages[i].classList.contains('load-link'))
                    messages[i].remove();
    }

    remove_first_date() {
        let first_msg = this.block.getElementsByTagName('li');
        if (first_msg !== undefined && first_msg.length > 0)
            for (let i in first_msg)
                if (first_msg[i].classList.contains('message-date')) {
                    first_msg[i].remove()
                    break;
                }
    }

    show_chat_history(chat_id, reverse=false) {
        let messages = this.chat_history[chat_id];
        let ts_list = this.message_ts_lists[chat_id];
        if (reverse)
            ts_list = reverse_object(ts_list);
        for (let i in ts_list) {
            let message_id = ts_list[i];
            if (messages[message_id].showed) {
                continue;
            }
            this.add_chat_message(chat_id, message_id, reverse ? 'top' : 'bottom');
            if (message_id === this.chat_data[chat_id].first_message_id)
                this.add_message_date(messages[message_id], true);
        }
        this.add_message_dates(chat_id);
        this.add_message_download_link(chat_id);
    }

    add_chat_message(chat_id, message_id, direction='') {
        let li = document.createElement('li');
        li.id = `m-${message_id}`;
        li.classList.add('clearfix', 'message-li');
        li.appendChild(this.chat_history[chat_id][message_id].create_element());
        let max = Math.max.apply(Math, this.message_ts_lists[chat_id]);
        if (direction === 'top') {
            this.insert_into_chat_top(li);
        } else if (direction === 'bottom') {
            this.insert_into_chat_bottom(li);
        } else {
            let min = Math.min.apply(Math, this.message_ts_lists[chat_id]);
            this.insert_into_chat(li, chat_id, message_id, this.message_ts_lists[chat_id][min],
                this.message_ts_lists[chat_id][max]);
        }
        this.chat_history[chat_id][message_id].showed = true;
        li.scrollIntoView(false);
    }

    add_message_dates(chat_id) {
        let lines = this.block.getElementsByTagName('li');
        for (let i = 0; i < lines.length - 1; i++) {
            if (lines[i].classList.contains('message-li') && lines[i + 1].classList.contains('message-li')) {
                let msg1 = this.chat_history[chat_id][lines[i].id.slice(2)];
                let msg2 = this.chat_history[chat_id][lines[i + 1].id.slice(2)];
                if (msg1.date !== msg2.date) {
                    let li = document.createElement('li');
                    li.classList.add('clearfix', 'message-date');
                    li.appendChild(this.create_message_date(msg2.date));
                    this.block.insertBefore(li, lines[i + 1]);
                }
            }
        }
    }

    add_message_date(message, to_start=false) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'message-date');
        li.appendChild(this.create_message_date(message['date']));
        if (to_start)
            this.insert_into_chat_top(li);
        else
            this.insert_into_chat_bottom(li);
    }

    create_message_date(date) {
        let message_data = document.createElement('div');
        message_data.classList.add('text-center');
        let span = document.createElement('span');
        span.innerText = date;
        message_data.appendChild(span)
        return message_data;
    }

    insert_into_chat_top(element) {
        this.block.insertBefore(element, this.block.getElementsByTagName('li')[0])
    }

    insert_into_chat_bottom(element) {
        this.block.append(element)
    }

    insert_into_chat(element, chat_id, message_id, min_message_id, max_message_id) {
        if (message_id === min_message_id) {
            this.insert_into_chat_top(element);
        } else if (message_id === max_message_id) {
            this.insert_into_chat_bottom(element);
        } else {
            let ind = this.message_id_lists[chat_id].indexOf(message_id);
            if (ind + 1 in this.message_id_lists[chat_id]) {
                let line = document.getElementById(`m-${this.message_id_lists[chat_id][ind + 1]}`);
                this.block.insertBefore(element, line);
            } else {
                this.insert_into_chat_bottom(element);
            }
        }
    }

    add_message_download_link(chat_id) {
        if (this.chat_data[chat_id]['first_message_id'] > this.chat_data[chat_id]['min_message_id']) {
            let link = document.createElement('a');
            link.onclick = () => {
                this.load_more_messages(chat_id, this.chat_data[chat_id]['first_message_id']);
            }
            link.href = '#';
            link.innerText = 'Загрузить ещё';
            let block = document.createElement('li');
            block.classList.add('text-center', 'load-link');
            block.appendChild(link);
            this.insert_into_chat_top(block);
        }
    }

    load_more_messages(chat_id, first_message_id) {
        let data = {'chat_id': chat_id, 'message_id': first_message_id};
        this.connection.send({'action': 'load_messages', 'data': data});
    }

    add_new_message(message, selected_chat) {
        if (message.chat_id in this.chat_data) {
            if (message['oper_id'] === null)
                this.chat_data[message.chat_id]['support_mode'] = true;
            if (selected_chat === message.chat_id)
                this.add_chat_message(message.chat_id, message['message_id']);
            return ['new_message', this.chat_history[message.chat_id][message['message_id']].get_message_content()]
        } else {
            return ['new_chat', this.chat_history[message.chat_id][message['message_id']].get_message_content()]
        }
    }
}


class ChatMessage {

    constructor(chat_id, message, name) {
        this.chat_id = chat_id;
        this.message_id = message['message_id'];
        this.date = message['date'];
        this.time = message['time'];
        this.oper_id = message['oper_id'];
        this.oper_name = message['oper_name'];
        this.content_type = message['content_type'];
        this.content = message['content'];
        this.name = name;
        this.showed = false;
    }

    create_element() {
        let element = document.createElement('div');
        element.classList.add('message');
        if (this.oper_id === null) {
            element.classList.add('other-message', 'float-right');
            element.appendChild(this.add_message_name(this.name));
        } else if (this.oper_id !== get_cookie('irobot_oper_id', true)) {
            element.classList.add('other-oper-message', 'float-right');
            element.appendChild(this.add_message_name(`Оператор: ${this.oper_name}`));
        } else {
            element.classList.add('my-message', 'float-left');
        }
        element.innerHTML += this.get_message_content();
        element.appendChild(this.add_message_time());
        return element;
    }

    add_message_name(name) {
        let header = document.createElement('div');
        header.classList.add('message-name');
        header.innerHTML = name
        return header;
    }

    get_message_content() {
        if (this.content_type === 'text')
            return this.content['text']
        else
            return JSON.stringify(this.content)
    }

    add_message_time() {
        let time_small = document.createElement('small');
        time_small.classList.add('message-time', 'pl-2');
        time_small.innerText = this.time;
        return time_small;
    }
}


document.addEventListener('DOMContentLoaded', function () {
    let server_host = document.getElementById('server-host').value;
    let root_path = document.getElementById('root-path').value;
    document.getElementById('server-host').remove();
    let url = `ws://${server_host}/ws?access_token=${get_cookie('irobot_access_token')}`;
    let chat = new Chat(url, root_path);
    chat.start();
});