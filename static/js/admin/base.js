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
    delete_cookie('access_token');
    delete_cookie('expires');
    delete_cookie('oper_id');
    delete_cookie('oper_name');
    location.reload();
}


document.addEventListener('DOMContentLoaded', function (event) {
    document.getElementById('btn-logout').onclick = logout;

    let timestamp = document.getElementById('timestamp').value;
    if (get_cookie('access_token') !== '' &&
        get_cookie('expires', true) > parseInt(timestamp)) {

        document.getElementById('oper-name').value = get_cookie('oper_name');
        document.getElementById('oper-id').innerText = get_cookie('oper_name');
        document.getElementById('oper-menu').value = get_cookie('oper_id');
        document.getElementById('oper-menu').classList.add('show');
        document.getElementById('oper-btn').classList.add('show');
    }
});
