document.addEventListener('DOMContentLoaded', function (event) {
    let btn_notify = document.getElementById('send-notify');
    let btn_mailing = document.getElementById('send-mailing');
    let btn_update = document.getElementById('update-history');
    let textarea = document.getElementById('input-text');
    let table_history = document.getElementById('history-table');

    btn_notify.onclick = function () {
        start_broadcast('notify');
    }

    btn_mailing.onclick = function () {
        start_broadcast('mailing');
    }

    btn_update.onclick = function () {
        get_history();
    }

    function start_broadcast(type) {
        let url = 'api/send_mail';
        let data = {'type': type, 'text': textarea.value}
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
                    get_history();
                }
            })
            .catch(error => {
                console.log('[start_broadcast]:', error);
            });
    }

    function get_history() {
        let url = 'api/get_history';
        fetch(url, {
            method: 'GET',
        })
            .then(response => response.json())
            .then(data => {
                console.log('response', data['response']);
                if (data['response'] !== 1) {
                    console.log('Error:', data['error']);
                } else {
                    table_history.innerHTML = data['table'];
                }
            })
            .catch(error => {
                console.log('[get_history]:', error);
            });
    }
})
