function get_cookie(name, parse_int=false) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        const res = parts.pop().split(';').shift();
        return parse_int ? parseInt(res) : res;
    }
    return parse_int ? null : '';
}


document.addEventListener('DOMContentLoaded', function (event) {
    if (get_cookie('oper_name') !== '' && get_cookie('oper_id') !== '') {
        document.getElementById('oper-name').value = get_cookie('oper_name');
        document.getElementById('oper-id').innerText = get_cookie('oper_name');
        document.getElementById('oper-menu').value = get_cookie('oper_id');
        document.getElementById('oper-menu').classList.add('show');
    }
});
