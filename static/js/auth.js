document.addEventListener('DOMContentLoaded', function (event) {
    let oper_name = document.getElementById('oper-name');
    let oper_id = document.getElementById('oper-id');
    let oper_menu = document.getElementById('oper-menu');
    let oper_btn = document.getElementById('oper-btn');
    let auth_window = document.getElementById('auth-window');
    let main_window = document.getElementById('main-window');
    let invalid_auth = document.getElementById('invalid-form-data');
    let btn_login = document.getElementById('login-btn');
    let input_login = document.getElementById('login-input');
    let input_pwd = document.getElementById('password-input');
    let on_auth = false;

    btn_login.onclick = function () {
        console.log('click');
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
        btn_login.enabled = !flag;
        input_login.enabled = !flag;
        input_pwd.enabled = !flag;
    }
    
    function show_main_menu() {
        auth_window.classList.add('sr-only');
        main_window.classList.remove('sr-only');
    }

    function save_token(token) {
        document.cookie = `access_token=${token}; `;
    }

    function save_oper(oper_id, oper_name) {
        document.cookie = `oper_id=${oper_id}; `;
        document.cookie = `oper_name=${oper_name}; `;
    }

    function auth() {
        auth_loading(true);
        show_auth_error();
        fetch('api/auth', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded', 'accept': 'application/json'},
            body: `username=${input_login.value}&password=${input_pwd.value}`
        })
            .then(response => response.json())
            .then(data => {
                if (data['access_token']) {
                    console.log('success auth', data);
                    save_token(data['access_token']);
                    show_main_menu();
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
                set_name_on_navbar(data['full_name'], data['oper_id']);
                save_oper(data['oper_id'], data['full_name']);
                location.reload();
            })
            .catch(error => {
                console.log('Error [oper]:', error);
            })
    }

    function set_name_on_navbar(name, id) {
        oper_name.value = name;
        oper_id.value = id;
        oper_btn.innerText = name;
        oper_menu.classList.remove('sr-only');
    }

    if (oper_name.value !== '') {
        show_main_menu();
        set_name_on_navbar(oper_name.value);
        document.getElementById('btn-2').click();
    }
});