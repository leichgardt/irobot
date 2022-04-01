document.addEventListener('DOMContentLoaded', function (event) {
    let btn_notify = document.getElementById('send-notify');
    let btn_mailing = document.getElementById('send-mailing');
    let btn_update = document.getElementById('update-history');
    let textarea = document.getElementById('input-text');
    let table_subs = document.getElementById('table');
    let table_history = document.getElementById('history-table');
    let radio_parse = document.getElementsByName('parse-radio');

    btn_notify.onclick = function () {
        start_broadcast('notify');
    }

    btn_mailing.onclick = function () {
        start_broadcast('mailing');
    }

    btn_update.onclick = function () {
        get_mailing_data();
    }

    function start_broadcast(type) {
        let parse_mode = null;
        for (let i = 0; i < radio_parse.length; i++) {
            if (radio_parse[i].checked) {
                parse_mode = radio_parse[i].value;
            }
        }
        let data = {'type': type, 'text': textarea.value, 'parse_mode': parse_mode};
        let url = 'api/send_mail';
        fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                if (data['response'] !== 1) {
                    console.log('Error:', data['error']);
                } else {
                    get_mailing_data();
                }
            })
            .catch(error => {
                console.log('[start_broadcast]:', error);
            });
    }

    function get_mailing_data() {
        let url = 'api/get_mailing_data';
        fetch(url, {
            method: 'GET',
            headers: {'Authorization': `Bearer ${get_cookie('access_token')}`}
        })
            .then(response => response.json())
            .then(data => {
                console.log('response', data['response']);
                if (data['response'] !== 1) {
                    console.log('Error:', data['error']);
                } else {
                    table_history.innerHTML = data['table'];
                    table_subs.innerHTML = data['subs'];
                }
            })
            .catch(error => {
                console.log('[get_history]:', error);
            });
    }

    get_mailing_data()
});
