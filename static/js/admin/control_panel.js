class Monitor {
    constructor(name) {
        this.name = name;
        this.block = document.getElementById(name);
    }

    on_process(flag) {
        this.block.disabled = flag;
    }

    check() {
        this.block.checked = !this.block.checked;
    }

    set_status(value) {
        this.block.checked = value;
    }
}

function switch_monitor_request(monitor_name) {
    let monitor = new Monitor(monitor_name);
    monitor.on_process(true);

    fetch('api/switch_monitor', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${get_cookie('irobot_access_token')}`
        },
        body: JSON.stringify({monitor: monitor_name})
    })
        .then(response => response.json())
        .then(data => {
            if (data?.response === 1) {
                monitor.set_status(data.enabled);
            } else {
                monitor.check();
            }
        })
        .catch(error => {
            console.log('[switch_monitor_request]:', error);
            monitor.check();
        })
        .finally(() => {
            monitor.on_process(false);
        })
}