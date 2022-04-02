function open_block(event, block_name, group) {
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent " + group);
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks " + group);
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(block_name).style.display = "block";
    event.currentTarget.className += " active";
}

function get_cookie(name, parse_int=false) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        const res = parts.pop().split(';').shift();
        return parse_int ? parseInt(res) : res;
    }
    return parse_int ? null : '';
}
