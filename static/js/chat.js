document.addEventListener('DOMContentLoaded', function (event) {
    let chat_list = document.getElementById('chat-list');
    let ws = null;
    let current_chat = 0;
    let input = document.getElementById('message-input-text');
    let chat_inputs = {}

    function get_photo(photo_url) {
        let photo = document.createElement('img');
        photo.alt = 'ava';
        photo.src = photo_url;
        return photo;
    }

    function get_chat_about(name, support_mode, datetime) {
        let name_block = document.createElement('div');
        name_block.classList.add('name');
        name_block.innerText = name;
        let status = document.createElement('div');
        status.classList.add('status');
        if (support_mode === true)
            status.innerHTML = `<i class="fa fa-circle online"></i> ${datetime}`;
        else
            status.innerHTML = `<i class="fa fa-circle offline"></i> ${datetime}`;
        let about = document.createElement('div');
        about.classList.add('about');
        about.appendChild(name_block);
        about.appendChild(status);
        return about;
    }

    function set_input_value() {
        input.disabled = false;
        if (chat_inputs[current_chat]) {
            input.value = chat_inputs[current_chat];
        } else {
            input.value = '';
        }
    }

    function select_and_load_chat(chat_id, name, photo, support_mode, page=0) {
        if (current_chat !== chat_id) {
            current_chat = chat_id;
            set_input_value();
            let selected_chat_photo = document.getElementById('selected-photo');
            let selected_chat_name = document.getElementById('selected-man');
            selected_chat_photo.src = photo;
            selected_chat_name.getElementsByTagName('h6')[0].innerText = name;
            selected_chat_name.getElementsByTagName('small')[0].innerText = support_mode === true ? 'Support required' : 'Support disabled';
            let data = {'action': 'get_chat', 'data': {'chat_id': current_chat, 'page': page}}
            ws.send(JSON.stringify(data));
        }
    }

    function get_chat_block(chat_id, name, photo, datetime, support_mode) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'chat-item');
        li.appendChild(get_photo(photo));
        li.appendChild(get_chat_about(name, support_mode, datetime));
        li.onclick = function (event) {
            let chats = document.getElementsByClassName('chat-item');
            select_and_load_chat(chat_id, name, photo, support_mode);
            for (let i = 0; i < chats.length; i++) {
                chats[i].classList.remove('active');
                li.classList.add('active');
            }
        }
        return li;
    }

    function get_chats(data) {
        chat_list.innerHTML = '';
        for (let i in data) {
            let chat = get_chat_block(data[i]['chat_id'], data[i]['first_name'], data[i]['photo'], data[i]['datetime'], data[i]['support_mode'])
            chat_list.appendChild(chat);
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

    function get_chat(data) {
        let chat = document.getElementById('chat-history');
        chat.innerHTML = '';
        for (let i in data) {
            console.log(data[i]);
            add_chat_message(data[i]);
        }
    }

    function connectWS() {
        ws = new WebSocket(`ws://${document.location.host}/ws?access_token=${get_cookie('access_token')}`);
        ws.onclose = function (event) {setTimeout(connectWS, 200)};
        ws.onmessage = function (event) {
            let command = JSON.parse(event.data)['action'];
            let data = JSON.parse(event.data)['data'];
            console.log(`${command}:`, data);
            if (command === 'get_chats')
                get_chats(data);
            else if (command === 'get_chat')
                get_chat(data);
            else if (command === 'get_message')
                add_chat_message(data);
        }
    }

    input.onkeyup = function (event) {
        if (event.key === 'Enter') {
            send_message();
        }
    }

    input.oninput = function (event) {
        chat_inputs[current_chat] = input.value;
    }

    function send_message() {
        let text_input = input;
        if (text_input.value.length > 0) {
            ws.send(JSON.stringify({'action': 'send_message', 'data': {'chat_id': current_chat, 'text': text_input.value}}));
            text_input.value = '';
            chat_inputs[current_chat] = '';
        }
    }

    connectWS();
});