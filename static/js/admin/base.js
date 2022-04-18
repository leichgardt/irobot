function get_cookie(name, parse_int=false) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        const res = parts.pop().split(';').shift();
        return parse_int ? parseInt(res) : res;
    }
    return parse_int ? null : '';
}

function set_cookie(name, value) {
    document.cookie = `${name}=${value}; `;
}

function delete_cookie(name) {
    document.cookie = `${name}=; `
}


function logout() {
    delete_cookie('irobot_access_token');
    delete_cookie('irobot_expires');
    delete_cookie('irobot_oper_id');
    delete_cookie('irobot_oper_name');
    delete_cookie('irobot_oper_root');
    location.reload();
}


function change_password() {
    let old_pwd = document.getElementById('password1');
    let new_pwd = document.getElementById('password2');
    let confirm_pwd = document.getElementById('password3');
    let btn = document.getElementById('change-password-btn');

    if (!btn.disabled) {
        if (new_pwd.value !== '' &&
            confirm_pwd.value !== '' &&
            new_pwd.value === confirm_pwd.value &&
            new_pwd.value !== old_pwd.value) {

            set_password_btn_status('loading');
            verify_password_error(false)
            change_password_request(old_pwd.value, new_pwd.value);
        } else {
            set_password_btn_status('ok');
            verify_password_error(true);
        }
    }
}

function set_password_btn_status(status) {
    let btn = document.getElementById('change-password-btn');
    if (status === 'loading') {
        btn.disabled = true;
        btn.innerText = 'Загрузка';
    } else {
        btn.disabled = false;
        if (status === 'error') {
            btn.innerText = 'Ошибка';
            btn.classList.replace('btn-outline-primary', 'btn-outline-danger');
        } else if (status === 'ok') {
            btn.innerText = 'Сменить пароль';
            btn.classList.replace('btn-outline-danger', 'btn-outline-primary');
        }
    }
}

function verify_password_error(flag) {
    let block = document.getElementById('invalid-password-data');
    if (flag)
        block.classList.add('show');
    else
        block.classList.remove('show');
}

function change_password_request(old_password, new_password) {
    fetch('api/change-password', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${get_cookie('irobot_access_token')}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({password: old_password, new_password: new_password})
    })
        .then(response => response.json())
        .then(data => {
            if (data === true) {
                let block = document.createElement('div');
                block.classList.add('text-center');
                block.innerText = 'Пароль успешно изменен!';
                let modal = document.getElementById('modal-change-password');
                modal.innerHTML = '';
                modal.appendChild(block);
                setTimeout(logout, 2000);
            } else {
                set_password_btn_status('error');
            }
        })
        .catch(err => {
            console.error('Change password error:', err);
            set_password_btn_status('error');
            verify_password_error(true);
        })
        .finally(() => {
            setTimeout(set_password_btn_status, 4000, 'ok')
        })
}

function check_root() {
    let link = document.getElementById('create-oper-link');
    if (get_cookie('irobot_oper_root') === 'true')
        link.classList.add('show');
}

function check_new_oper_form_data() {
    let login = document.getElementById('new-oper-login-input');
    let name = document.getElementById('new-oper-name-input');
    let pwd1 = document.getElementById('new-oper-password-input');
    let pwd2 = document.getElementById('new-oper-password-verify-input');
    let root = document.getElementById('new-root-input');

    if (login.value && name.value && pwd1.value && pwd1.value === pwd2.value && login.value) {
        set_create_oper_btn_status('loading');
        show_new_oper_incorrect_data(false);
        create_new_operator(login.value, name.value, pwd1.value, root.checked);
    } else {
        show_new_oper_incorrect_data(true);
    }
}

function set_create_oper_btn_status(status) {
    let btn = document.getElementById('btn-new-operator');
    if (status === 'loading') {
        btn.disabled = true;
        btn.innerText = 'Загрузка';
    } else {
        btn.disabled = false;
        if (status === 'error') {
            btn.innerText = 'Ошибка';
            btn.classList.replace('btn-outline-primary', 'btn-outline-danger');
            setTimeout(set_create_oper_btn_status, 4000, 'ok');
        } else if (status === 'success') {
            btn.innerText = 'Оператор создан!';
            btn.classList.replace('btn-outline-danger', 'btn-outline-success');
            btn.classList.replace('btn-outline-primary', 'btn-outline-success');
            setTimeout(set_create_oper_btn_status, 6000, 'ok');
        } else if (status === 'ok') {
            btn.innerText = 'Зарегистрировать';
            btn.classList.replace('btn-outline-danger', 'btn-outline-primary');
            btn.classList.replace('btn-outline-success', 'btn-outline-primary');
        }
    }
}

function show_new_oper_incorrect_data(flag) {
    let block = document.getElementById('invalid-new-oper-data');
    if (flag) {
        block.classList.add('show');
    } else {
        block.classList.remove('show');
    }
}

function create_new_operator(login, name, password, root) {
    fetch('api/sign-up', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${get_cookie('irobot_access_token')}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({login: login, full_name: name, password: password, root: root})
    })
        .then(response => response.json())
        .then(data => {
            if ('oper_id' in data) {
                set_create_oper_btn_status('success');
            } else {
                console.log('Create operator error:', data);
                set_create_oper_btn_status('error');
            }
        })
        .catch(err => {
            console.log('Create operator error:', err);
            set_create_oper_btn_status('error');
        })
}

document.addEventListener('DOMContentLoaded', function (event) {
    check_root();

    document.getElementById('btn-logout').onclick = logout;

    document.getElementById('change-password-btn').onclick = change_password;
    document.getElementById('password1').onkeyup = function (e) {
        if (e.key === 'Enter') change_password();
    }
    document.getElementById('password2').onkeyup = function (e) {
        if (e.key === 'Enter') change_password();
    }
    document.getElementById('password3').onkeyup = function (e) {
        if (e.key === 'Enter') change_password();
    }

    document.getElementById('btn-new-operator').onclick = check_new_oper_form_data;
    document.getElementById('password1').onkeyup = function (e) {
        if (e.key === 'Enter') check_new_oper_form_data();
    }
    document.getElementById('password2').onkeyup = function (e) {
        if (e.key === 'Enter') check_new_oper_form_data();
    }
    document.getElementById('password3').onkeyup = function (e) {
        if (e.key === 'Enter') check_new_oper_form_data();
    }

    let timestamp = document.getElementById('timestamp').value;
    if (get_cookie('irobot_access_token') !== '' &&
        get_cookie('irobot_expires', true) > parseInt(timestamp)) {

        document.getElementById('oper-name').value = get_cookie('irobot_oper_name');
        document.getElementById('oper-id').innerText = get_cookie('irobot_oper_name');
        document.getElementById('oper-menu').value = get_cookie('irobot_oper_id');
        document.getElementById('oper-menu').classList.add('show');
        document.getElementById('oper-btn').classList.add('show');
    }
});
