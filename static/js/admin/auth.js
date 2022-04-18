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

    function set_auth_status_loading(flag) {
        on_auth = flag;
        btn_login.disabled = flag;
        input_login.disabled = flag;
        input_pwd.disabled = flag;
    }

    function auth() {
        set_auth_status_loading(true);
        fetch('api/auth', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'accept': 'application/json'},
            body: `username=${input_login.value}&password=${input_pwd.value}`
        })
            .then(response => response.json())
            .then(data => {
                if (data['token'] && data['token']['access_token']) {
                    set_cookie('irobot_access_token', data['token']['access_token'])
                    set_cookie('irobot_expires', data['token']['expires'])
                    set_cookie('irobot_oper_id', data['oper_id']);
                    set_cookie('irobot_oper_name', data['full_name']);
                    set_cookie('irobot_oper_root', data['root']);
                    console.log('success auth');
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
                set_auth_status_loading(false);
                location.reload();
            });
    }
});