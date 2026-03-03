const WebSocket = require('ws');
const http = require('http');
const wss = require('y-websocket/bin/utils');

const server = http.createServer((request, response) => {
    response.writeHead(200, { 'Content-Type': 'text/plain' });
    response.end('okay');
});

const wsserver = new WebSocket.Server({ server });

wsserver.on('connection', (conn, req) => {
    wss.setupWSConnection(conn, req, { docName: req.url.slice(1).split('?')[0] });
});

const PORT = process.env.PORT || 1234;

server.listen(PORT, () => {
    console.log(`🚀 Yjs WebSocket Server running at ws://localhost:${PORT}`);
});
