document.addEventListener('DOMContentLoaded', function (event) {
    let chat_list = document.getElementById('chat-list');
    let ws = null;

    function get_photo(photo_url) {
        let photo = document.createElement('img');
        photo.alt = 'img';
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
        return about
    }

    function get_chat(chat_id, name, photo, datetime, support_mode) {
        let li = document.createElement('li');
        li.classList.add('clearfix', 'chat-item');
        li.appendChild(get_photo(photo));
        li.appendChild(get_chat_about(name, support_mode, datetime));
        // li.onclick = function todo select chat chat_id
        return li
    }

    function get_chats(data) {
        for (let i in data) {
            let chat = get_chat(data[i]['chat_id'], data[i]['first_name'], data[i]['photo'], data[i]['datetime'], data[i]['support_mode'])
            chat_list.appendChild(chat);
        }
    }

    function connectWS() {
        ws = new WebSocket(`ws://${document.location.host}/ws?access_token=${get_cookie('access_token')}`);
        ws.onmessage = function (event) {
            let command = JSON.parse(event.data)['action'];
            let data = JSON.parse(event.data)['data'];
            console.log(command, data);
            if (command === 'get_chats')
                get_chats(data);
        }
    }

    connectWS();
});