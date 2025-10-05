import { socket } from './socket.js';

// Example: chat.js
const roomName = 'lawyer_client_room'; // Use a unique room name per chat
const socket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
);

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    // Update chat UI with data.message and data.sender
};

function sendMessage(message, sender) {
    socket.send(JSON.stringify({
        'message': message,
        'sender': sender
    }));
}


// socket.onopen = () => {

//     const auth_data = {
//         username: 'john_doe',  // Replace with actual username
//         token: 'your_auth_token'  // Replace with actual token
//     };
//     socket.send(JSON.stringify(auth_data));
// };

// socket.onmessage = (event) => {
//     const message = JSON.parse(event.data);
//     if (message && message.sender === 'john_doe') {  // Replace with actual username
//         // update chat UI with the new message
//         console.log('New message from authorized user:', message);
//     } else {
//         // Ignore messages from unauthorised users
//     }
// };

// socket.onclose = () => {
//     console.log('WebSocket connection closed');
// };