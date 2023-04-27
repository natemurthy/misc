const http = require("http")
const url = require('url')

const PORT = process.env.PORT || 4000
const jsonHeader = { "Content-Type": "application/json" }

const server = http.createServer(handler)

async function handler(req, res) {
    // for debugging purposes
    console.log(req.method, req.url)

    if (req.method === "POST" && req.url.startsWith("/set")) {
            setKV(req, res)
    }
    else if (req.method === "GET" && req.url.startsWith("/get")) {
            getKV(req, res)
    }
    else {
        res.writeHead(404, jsonHeader)
        const notFoundMsg = `route not found: ${req.method} ${req.url}`
        res.write(JSON.stringify({ message: notFoundMsg }))
    }
    res.end()
}

let inMemoryDb = {}

function setKV(req, res) {
    const queryObject = url.parse(req.url, true).query
    Object.assign(inMemoryDb, queryObject)
    res.writeHead(201, jsonHeader)
    res.write(JSON.stringify(queryObject))
}

function getKV(req, res) {
    const keyName = url.parse(req.url, true).query['key']

    if (keyName in inMemoryDb) {
        let kv = {}
        kv[keyName] = inMemoryDb[keyName]
        res.writeHeader(200, jsonHeader)
        res.write(JSON.stringify(kv)) 
    }
    else {
        res.writeHeader(404, jsonHeader)
        const keyNotFoundMsg = `key "${keyName}" not found`
        res.write(JSON.stringify({ message: keyNotFoundMsg }))
    }
}

server.listen(PORT, () => {
    console.log(`server started on port: ${PORT}`)
})
