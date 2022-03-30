function post(url, data=null) {
    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
        .then(response => {
            return response.json()
        })
        .catch(err => {
            console.log(`Error on ${url}: ${err}`)
        })
    // return res;
}