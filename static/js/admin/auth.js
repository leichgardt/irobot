document.addEventListener('DOMContentLoaded', function (event) {
    let invalid_auth = document.getElementById('invalid-form-data');
    let btn_login = document.getElementById('login-btn');
    let input_login = document.getElementById('login-input');
    let input_pwd = document.getElementById('password-input');
    let on_auth = false;

    btn_login.onclick = function () {
        if (auth_input_valid())
            auth();
        else
            show_auth_error();
    }

    input_login.onkeypress = function (e) { if (e.key === 'Enter') btn_login.click(); }
    input_pwd.onkeypress = function (e) { if (e.key === 'Enter') btn_login.click(); }

    function auth_input_valid() {
        return input_login.value.length > 0 && input_pwd.value.length > 0;
    }

    function show_auth_error() {
        invalid_auth.classList.remove('sr-only');
    }

    function auth_loading(flag) {
        on_auth = flag;
        btn_login.disabled = flag;
        input_login.disabled = flag;
        input_pwd.disabled = flag;
    }

    function auth() {
        auth_loading(true);
        fetch('api/auth', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'accept': 'application/json'},
            body: `username=${input_login.value}&password=${input_pwd.value}`
        })
            .then(response => response.json())
            .then(data => {
                if (data['access_token']) {
                    set_cookie('access_token', data['access_token'])
                    console.log('success auth');
                    get_oper_data_request();
                }
                else {
                    console.error('Bad request', data);
                    show_auth_error();
                }
            })
            .catch(error => {
                show_auth_error();
                console.log('Error [login]:', error);
            })
            .finally(() => {
                auth_loading(false);
                location.reload();
            });
    }

    function get_oper_data_request() {
        fetch('api/me', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'accept': 'application/json',
                'Authorization': `Bearer ${get_cookie('access_token')}`
            }
        })
            .then(response => response.json())
            .then(data => {
                set_cookie('oper_id', data['oper_id']);
                set_cookie('oper_name', data['full_name']);
            })
            .catch(error => {
                console.log('Error [oper]:', error);
            })
    }
});