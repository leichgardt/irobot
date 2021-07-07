document.addEventListener('DOMContentLoaded', function (event) {
    let btn_login = {
        'btn': document.getElementById('login-btn'),
        'spinner': document.getElementById('login-btn-spinner'),
        'text': document.getElementById('login-btn-text'),
        'default': document.getElementById('login-btn-text').innerText,
    };

    let input_agrm = document.getElementById('agrm-input');
    let input_pwd = document.getElementById('password-input');
    let agrm_form = document.getElementById('agrm-form');
    let pwd_form = document.getElementById('pwd-form');

    let on_loading = false;

    btn_login['btn'].onclick = function () {
        if (!on_loading) {
            let one = valid(input_pwd, pwd_form),
                two = valid(input_agrm, agrm_form);
            if (one && two)
                on_loading = true;
                login();
        }
    }

    input_agrm.oninput = function () { valid(input_agrm, agrm_form) };
    input_pwd.oninput = function () { valid(input_pwd, pwd_form) };

    function valid(input, form) {
        if (!input.value) {
            form.classList.add('was-validated');
            return false;
        } else {
            if (form.classList.contains('was-validated'))
                form.classList.remove('was-validated');
            return true;
        }
    }

    function btn_status(btn, status, text='Ошибка') {
        if (status === 'start') {
            btn['btn'].classList.remove('btn-danger');
            btn['btn'].classList.add('btn-primary');
            btn['spinner'].classList.remove('show');
            btn['text'].classList.add('show');
            btn['text'].innerText = btn['default'];
        } else if (status === 'loading') {
            btn['text'].classList.remove('show');
            btn['spinner'].classList.add('show');
        } else if (status === 'error') {
            btn['btn'].classList.remove('btn-primary');
            btn['btn'].classList.add('btn-danger');
            btn['spinner'].classList.remove('show');
            btn['text'].classList.add('show');
            btn['text'].innerText = text;
        }
    }

    function login() {
        btn_status(btn_login, 'loading');
        let hash = document.getElementById('hash-code').value;
        let data = {'agrm': input_agrm.value, 'pwd': input_pwd.value, 'hash': hash};
        console.log(data);
        let url = 'api/login'
        fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                if (data['response'] === 1) {
                    btn_status(btn_login, 'start');
                    window.location = `login_success?hash=${hash}`;
                } else if (data['response'] === 2) {
                    btn_status(btn_login, 'error', 'Договор уже был добавлен');
                    setTimeout(btn_status, 5000, btn_login, 'start');
                    input_pwd.value = '';
                    valid(input_pwd, pwd_form);
                } else {
                    btn_status(btn_login, 'error', 'Неверный договор или пароль');
                    setTimeout(btn_status, 5000, btn_login, 'start');
                    input_pwd.value = '';
                    valid(input_pwd, pwd_form);
                }
                on_loading = false;
            })
            .catch(error => {
                console.log('Error [login]:', error);
                on_loading = false;
            });
    }
});