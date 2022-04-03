document.addEventListener('DOMContentLoaded', function (event) {
    let chat_data = {};
    let chat_list_block = document.getElementById('chat-list');
    let ws = null;
    let selected_chat = 0;
    let input = document.getElementById('message-input-text');
    let chat_inputs = {};
    let btn_take = document.getElementById('btn-take');
    let btn_drop = document.getElementById('btn-drop');
    let input_group = document.getElementById('input-group');

    function get_photo(chat_id) {
        let photo = document.createElement('img');
        photo.alt = 'ava';
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
        return chat_data[chat_id]['oper_id'] ? '<i class="fa fa-circle online"></i>' : '<i class="fa fa-circle offline"></i>'
    }

    function get_chat_support_mode_oper_icon(chat_id) {
        if (chat_data[chat_id]['support_mode'] === true)
            return chat_data[chat_id]['oper_id'] ? '<i class="fa fa-circle online"></i>' : '<i class="fa fa-circle offline"></i>'
        return ''
    }

    function get_chat_about(chat_id) {
        let name_block = document.createElement('div');
        name_block.classList.add('name', 'text-left');
        name_block.innerHTML = get_chat_support_mode_oper_icon(chat_id);
        name_block.innerHTML += chat_data[chat_id]['first_name'];
        let date = document.createElement('div');
        date.classList.add('status', 'text-left', 'last-update-datetime');
        date.innerText = `${chat_data[chat_id]['datetime']}`;
        let about = document.createElement('div');
        about.classList.add('about');
        about.appendChild(name_block);
        about.appendChild(date);
        return about;
    }

    function update_chat_block(chat_id) {
        console.log('update', chat_id);
        let oper = document.getElementById(`chat-${chat_id}`).getElementsByClassName('operator')[0];
        oper.innerHTML = get_chat_operator(chat_id);
        let date = document.getElementById(`chat-${chat_id}`).getElementsByClassName('last-update-datetime')[0];
        date.innerHTML = chat_data[chat_id]['datetime'];
    }

    btn_take.onclick = function (event) {
        take_chat_start();
    }

    function take_chat_start() {
        ws.send(JSON.stringify({'action': 'take_chat', 'data': selected_chat}));
    }

    function oper_take_chat_end(chat_id) {
        chat_data[chat_id]['oper_id'] = get_cookie('oper_id', true);
        chat_data[chat_id]['oper_name'] = get_cookie('oper_name');
        update_chat_block(chat_id);
        new_chat_status(chat_id);
        show_message_buttons(true);
    }

    btn_drop.onclick = function (event) {
        drop_chat_start();
    }

    function drop_chat_start() {
        ws.send(JSON.stringify({'action': 'drop_chat', 'data': selected_chat}));
    }

    function oper_drop_chat_end(chat_id) {
        selected_chat['oper_id'] = null;
        chat_data[chat_id]['oper_id'] = null;
        chat_data[chat_id]['oper_name'] = null;
        update_chat_block(chat_id);
        new_chat_status(chat_id);
        show_message_buttons(false);
    }

    function show_message_buttons(flag) {
        if (flag) {
            btn_take.classList.remove('show');
            btn_drop.classList.add('show');
            input_group.classList.add('show');
        } else {
            btn_take.classList.add('show');
            btn_drop.classList.remove('show');
            input_group.classList.remove('show');
        }
    }

    function load_saved_value_to_input(chat_id) {
        input.disabled = false;
        if (chat_inputs[chat_id]) {
            input.value = chat_inputs[chat_id];
        } else {
            input.value = '';
        }
    }

    function new_chat_status(chat_id) {
        let selected_chat_name = document.getElementById('selected-man');
        let small = selected_chat_name.getElementsByTagName('small');
        small[0].innerText = get_chat_operator(chat_id);
        small[1].innerHTML = get_chat_support_mode_icon(chat_id);
        small[1].innerHTML += chat_data[chat_id]['support_mode'] === true ? ' Требуется поддержка!' : 'Поддержка не требуется';
    }

    function set_chat_name(name) {
        let selected_chat_name = document.getElementById('selected-man');
        selected_chat_name.getElementsByTagName('h6')[0].innerText = name;
    }

    function set_chat_photo(photo) {
        document.getElementById('selected-photo').src = photo ? photo : '';
    }

    function select_and_load_chat(chat_id, page=0) {
        if (selected_chat !== chat_id) {
            selected_chat = chat_id;
            load_saved_value_to_input(chat_id);
            set_chat_photo(chat_data[chat_id]['photo']);
            set_chat_name(chat_data[chat_id]['first_name']);
            new_chat_status(chat_id);
            let data = {'action': 'get_chat', 'data': {'chat_id': selected_chat, 'page': page}};
            ws.send(JSON.stringify(data));
        }
    }

    function check_this_is_my_chat(chat_id) {
        if (chat_data[chat_id]['oper_id'] === get_cookie('oper_id', true)) {
            show_message_buttons(true);
        } else {
            show_message_buttons(false);
        }
    }

    function get_chat_block(chat_id) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'chat-item');
        li.id = `chat-${chat_id}`;
        li.appendChild(get_photo(chat_id));
        li.appendChild(get_chat_about(chat_id));
        li.onclick = function () {
            let chats = document.getElementsByClassName('chat-item');
            select_and_load_chat(chat_id);
            check_this_is_my_chat(chat_id);
            for (let i = 0; i < chats.length; i++) {
                chats[i].classList.remove('active');
                li.classList.add('active');
            }
        }
        return li;
    }

    function save_data_of_chats(data) {
        for (let i in data) {
            chat_data[data[i]['chat_id']] = data[i];
        }
    }

    function fill_chat_list(data) {
        save_data_of_chats(data);
        chat_list_block.innerHTML = '';
        for (let i in data) {
            let chat = get_chat_block(data[i]['chat_id'])
            chat_list_block.appendChild(chat);
        }
    }

    function create_message_datetime(datetime) {
        let span = document.createElement('span');
        span.classList.add('message-data-time');
        span.innerText = `${datetime}`;
        return span;
    }

    function create_message_data(msg) {
        let message_data = document.createElement('div');
        message_data.classList.add('message-data');
        if (msg['from_oper'] === null)
            message_data.classList.add('text-right');
        else
            message_data.classList.add('text-left');
        message_data.appendChild(create_message_datetime(msg['datetime']))
        return message_data;
    }

    function get_message_content(msg) {
        if (msg['content_type'] === 'text') {
            return msg['content']['text'];
        }
    }

    function create_message(msg) {
        let message = document.createElement('div');
        message.classList.add('message');
        if (msg['from_oper'] === null)
            message.classList.add('other-message', 'float-right');
        else
            message.classList.add('my-message', 'float-left');
        message.innerHTML = get_message_content(msg);
        return message;
    }

    function add_chat_message(msg) {
        let li = document.createElement('li');
        li.classList.add('clearfix');
        li.appendChild(create_message_data(msg));
        li.appendChild(create_message(msg));
        let chat = document.getElementById('chat-history');
        chat.appendChild(li);
        li.scrollIntoView(false);
    }

    function fill_chat_history(data) {
        let chat = document.getElementById('chat-history');
        chat.innerHTML = '';
        for (let i in data) {
            add_chat_message(data[i]);
        }
    }

    function new_chat_datetime(chat_id, datetime) {
        console.log(`chat-${chat_id}`);
        let about = document.getElementById(`chat-${chat_id}`);
        about = about.getElementsByClassName('about')[0].getElementsByTagName('div');
        about[1].innerText = datetime;
    }

    function send_message_end(msg) {
        add_chat_message(msg);
        new_chat_datetime(selected_chat, msg['datetime']);
    }

    function connectWS() {
        if (!get_cookie('access_token'))
            return;
        ws = new WebSocket(`ws://${document.location.host}/ws?access_token=${get_cookie('access_token')}`);
        ws.onclose = function (event) {setTimeout(connectWS, 200)};
        ws.onmessage = function (event) {
            let command = JSON.parse(event.data)['action'];
            let data = JSON.parse(event.data)['data'];
            console.log(`${command}:`, data);
            if (command === 'get_chats')
                fill_chat_list(data);
            else if (command === 'get_chat')
                fill_chat_history(data);
            else if (command === 'send_message')
                send_message_end(data);
            else if (command === 'take_chat')
                oper_take_chat_end(data);
            else if (command === 'drop_chat')
                oper_drop_chat_end(data);

        }
    }

    btn_drop.onmouseenter = function () {
        btn_drop.getElementsByTagName('span')[0].classList.add('show');
    }

    btn_drop.onmouseleave = function () {
        btn_drop.getElementsByTagName('span')[0].classList.remove('show');
    }

    input.onkeyup = function (event) {
        if (event.key === 'Enter') {
            send_message();
        }
    }

    input.oninput = function (event) {
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

    connectWS();
});